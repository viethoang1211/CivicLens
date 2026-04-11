import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document_type import DocumentType
from src.models.routing_rule import RoutingRule
from src.models.submission import Submission
from src.models.workflow_step import WorkflowStep
from src.services.notification_service import (
    notify_completed,
    notify_info_requested,
    notify_step_advanced,
)


async def _set_retention_expiry(db: AsyncSession, submission: Submission) -> None:
    """Compute and set retention_expires_at based on DocumentType retention settings."""
    if not submission.document_type_id or not submission.completed_at:
        return
    dt_result = await db.execute(
        select(DocumentType).where(DocumentType.id == submission.document_type_id)
    )
    doc_type = dt_result.scalar_one_or_none()
    if not doc_type:
        return
    if doc_type.retention_permanent:
        submission.retention_expires_at = None  # Never expires
    elif doc_type.retention_years:
        submission.retention_expires_at = submission.completed_at + timedelta(days=365 * doc_type.retention_years)


async def detect_delayed_steps(db: AsyncSession) -> list[WorkflowStep]:
    """Return all active workflow steps that have exceeded their expected_complete_by."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(WorkflowStep).where(
            WorkflowStep.status == "active",
            WorkflowStep.expected_complete_by.isnot(None),
            WorkflowStep.expected_complete_by < now,
        )
    )
    return list(result.scalars().all())


async def advance_workflow(db: AsyncSession, current_step: WorkflowStep, result: str) -> dict:
    """Complete the current step and activate the next one if approved."""
    now = datetime.now(timezone.utc)

    current_step.status = "completed"
    current_step.completed_at = now
    current_step.result = result

    submission = await db.execute(select(Submission).where(Submission.id == current_step.submission_id))
    submission = submission.scalar_one()

    if result == "rejected":
        submission.status = "rejected"
        submission.completed_at = now
        await db.commit()
        await notify_completed(db, submission, rejected=True)
        return {"action": "rejected", "submission_status": "rejected"}

    if result == "needs_info":
        # Step stays completed but submission doesn't advance automatically
        await db.commit()
        await notify_info_requested(db, submission, current_step)
        return {"action": "needs_info", "submission_status": submission.status}

    # Find next step
    next_step_result = await db.execute(
        select(WorkflowStep).where(
            WorkflowStep.submission_id == current_step.submission_id,
            WorkflowStep.step_order == current_step.step_order + 1,
        )
    )
    next_step = next_step_result.scalar_one_or_none()

    if next_step is None:
        # No more steps — submission is complete
        submission.status = "completed"
        submission.completed_at = now
        await _set_retention_expiry(db, submission)
        await db.commit()
        await notify_completed(db, submission)
        return {"action": "completed", "submission_status": "completed"}

    # Activate next step
    next_step.status = "active"
    next_step.started_at = now

    # Calculate expected completion
    rule_result = await db.execute(
        select(RoutingRule).where(
            RoutingRule.document_type_id == submission.document_type_id,
            RoutingRule.step_order == next_step.step_order,
        )
    )
    rule = rule_result.scalar_one_or_none()
    if rule and rule.expected_duration_hours:
        next_step.expected_complete_by = now + timedelta(hours=rule.expected_duration_hours)

    await db.commit()
    await notify_step_advanced(db, submission, next_step)
    return {"action": "advanced", "next_step_order": next_step.step_order, "submission_status": submission.status}
