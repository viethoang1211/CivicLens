from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.case_type import CaseType, CaseTypeRoutingStep
from src.models.department import Department
from src.models.document_type import DocumentType
from src.models.dossier import Dossier
from src.models.routing_rule import RoutingRule
from src.models.submission import Submission
from src.models.workflow_step import WorkflowStep
from src.services.notification_service import (
    notify_completed,
    notify_dossier_status_change,
    notify_dossier_step_advanced,
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


async def _set_dossier_retention_expiry(db: AsyncSession, dossier: Dossier) -> None:
    """Compute and set retention_expires_at based on CaseType retention settings."""
    if not dossier.case_type_id or not dossier.completed_at:
        return
    ct_result = await db.execute(
        select(CaseType).where(CaseType.id == dossier.case_type_id)
    )
    case_type = ct_result.scalar_one_or_none()
    if not case_type:
        return
    if case_type.retention_permanent:
        dossier.retention_expires_at = None
    elif case_type.retention_years:
        dossier.retention_expires_at = dossier.completed_at + timedelta(days=365 * case_type.retention_years)


async def detect_delayed_steps(db: AsyncSession) -> list[WorkflowStep]:
    """Return all active workflow steps that have exceeded their expected_complete_by."""
    now = datetime.now(UTC)
    result = await db.execute(
        select(WorkflowStep).where(
            WorkflowStep.status == "active",
            WorkflowStep.expected_complete_by.isnot(None),
            WorkflowStep.expected_complete_by < now,
        )
    )
    return list(result.scalars().all())


async def advance_workflow(db: AsyncSession, current_step: WorkflowStep, result: str) -> dict:
    """Complete the current step and activate the next one if approved.

    Supports both submission-owned and dossier-owned workflow steps.
    """
    now = datetime.now(UTC)

    current_step.status = "completed"
    current_step.completed_at = now
    current_step.result = result

    # Detect owner mode
    if current_step.dossier_id is not None:
        return await _advance_dossier_workflow(db, current_step, result, now)
    return await _advance_submission_workflow(db, current_step, result, now)


async def _advance_submission_workflow(
    db: AsyncSession, current_step: WorkflowStep, result: str, now: datetime
) -> dict:
    """Handle workflow advancement for submission-owned steps."""
    submission_result = await db.execute(select(Submission).where(Submission.id == current_step.submission_id))
    submission = submission_result.scalar_one()

    if result == "rejected":
        submission.status = "rejected"
        submission.completed_at = now
        await db.commit()
        await notify_completed(db, submission)
        return {"action": "rejected", "submission_status": "rejected"}

    if result == "needs_info":
        await db.commit()
        await notify_info_requested(db, submission, "Cần bổ sung thông tin cho hồ sơ của bạn.")
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
        submission.status = "completed"
        submission.completed_at = now
        await _set_retention_expiry(db, submission)
        await db.commit()
        await notify_completed(db, submission)
        return {"action": "completed", "submission_status": "completed"}

    # Activate next step
    next_step.status = "active"
    next_step.started_at = now

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
    dept_result = await db.execute(select(Department).where(Department.id == next_step.department_id))
    dept = dept_result.scalar_one_or_none()
    dept_name = dept.name if dept else "Phòng tiếp theo"
    await notify_step_advanced(db, submission, dept_name, next_step.step_order)
    return {"action": "advanced", "next_step_order": next_step.step_order, "submission_status": submission.status}


async def _advance_dossier_workflow(
    db: AsyncSession, current_step: WorkflowStep, result: str, now: datetime
) -> dict:
    """Handle workflow advancement for dossier-owned steps."""
    dossier_result = await db.execute(select(Dossier).where(Dossier.id == current_step.dossier_id))
    dossier = dossier_result.scalar_one()

    if result == "rejected":
        dossier.status = "rejected"
        dossier.completed_at = now
        await db.commit()
        await notify_dossier_status_change(db, dossier.id, "rejected", dossier.rejection_reason)
        return {"action": "rejected", "dossier_status": "rejected"}

    if result == "needs_info":
        await db.commit()
        await notify_dossier_status_change(db, dossier.id, "needs_info")
        return {"action": "needs_info", "dossier_status": dossier.status}

    # Find next step
    next_step_result = await db.execute(
        select(WorkflowStep).where(
            WorkflowStep.dossier_id == current_step.dossier_id,
            WorkflowStep.step_order == current_step.step_order + 1,
        )
    )
    next_step = next_step_result.scalar_one_or_none()

    if next_step is None:
        dossier.status = "completed"
        dossier.completed_at = now
        await _set_dossier_retention_expiry(db, dossier)
        await db.commit()
        await notify_dossier_status_change(db, dossier.id, "completed")
        return {"action": "completed", "dossier_status": "completed"}

    # Activate next step
    next_step.status = "active"
    next_step.started_at = now

    # Calculate expected completion from CaseTypeRoutingStep
    routing_step_result = await db.execute(
        select(CaseTypeRoutingStep).where(
            CaseTypeRoutingStep.case_type_id == dossier.case_type_id,
            CaseTypeRoutingStep.step_order == next_step.step_order,
        )
    )
    routing_step = routing_step_result.scalar_one_or_none()
    if routing_step and routing_step.expected_duration_hours:
        next_step.expected_complete_by = now + timedelta(hours=routing_step.expected_duration_hours)

    await db.commit()
    dept_result = await db.execute(select(Department).where(Department.id == next_step.department_id))
    dept = dept_result.scalar_one_or_none()
    dept_name = dept.name if dept else "Phòng tiếp theo"
    await notify_dossier_step_advanced(db, dossier, dept_name, next_step.step_order)
    return {"action": "advanced", "next_step_order": next_step.step_order, "dossier_status": dossier.status}
