import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.department import Department
from src.models.routing_rule import RoutingRule
from src.models.staff_member import StaffMember
from src.models.submission import Submission
from src.models.workflow_step import WorkflowStep


async def create_workflow_for_submission(db: AsyncSession, submission: Submission) -> dict:
    """Create workflow steps based on routing rules for the submission's document type."""

    # Fetch routing rules ordered by step_order
    result = await db.execute(
        select(RoutingRule)
        .where(RoutingRule.document_type_id == submission.document_type_id)
        .order_by(RoutingRule.step_order)
    )
    rules = result.scalars().all()

    if not rules:
        # No routing rules — flag for manual routing
        submission.status = "pending_routing"
        await db.commit()
        return {
            "submission_id": str(submission.id),
            "status": "pending_routing",
            "message": "No routing rules found for this document type. Manual routing required.",
            "workflow_steps": [],
        }

    # Validate clearance: each department must have staff with adequate clearance
    for rule in rules:
        dept_result = await db.execute(
            select(StaffMember).where(
                StaffMember.department_id == rule.department_id,
                StaffMember.clearance_level >= submission.security_classification,
                StaffMember.is_active.is_(True),
            )
        )
        if not dept_result.scalars().first():
            raise ValueError(
                f"Department for step {rule.step_order} has no staff with clearance level "
                f">= {submission.security_classification}"
            )

    now = datetime.now(timezone.utc)
    steps = []

    for i, rule in enumerate(rules):
        # Fetch department name
        dept_result = await db.execute(select(Department).where(Department.id == rule.department_id))
        dept = dept_result.scalar_one()

        is_first = i == 0
        step = WorkflowStep(
            submission_id=submission.id,
            department_id=rule.department_id,
            step_order=rule.step_order,
            status="active" if is_first else "pending",
            started_at=now if is_first else None,
            expected_complete_by=(
                now + timedelta(hours=rule.expected_duration_hours) if is_first and rule.expected_duration_hours else None
            ),
        )
        db.add(step)
        steps.append({
            "step_order": rule.step_order,
            "department": dept.name,
            "status": "active" if is_first else "pending",
        })

    submission.status = "in_progress"
    await db.commit()

    return {
        "submission_id": str(submission.id),
        "status": "in_progress",
        "workflow_steps": steps,
    }
