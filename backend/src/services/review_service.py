from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.staff_member import StaffMember
from src.models.step_annotation import StepAnnotation
from src.models.workflow_step import WorkflowStep
from src.services.audit_service import log_access
from src.services.workflow_service import advance_workflow


async def validate_reviewer(db: AsyncSession, step: WorkflowStep, staff_id) -> StaffMember:
    """Validate that the staff member can review this step."""
    staff = await db.execute(select(StaffMember).where(StaffMember.id == staff_id))
    staff = staff.scalar_one()

    if step.status != "active":
        raise ValueError(f"Step is not active (status={step.status})")

    if step.department_id != staff.department_id:
        raise ValueError("Reviewer is not in the assigned department")

    return staff


async def process_review(
    db: AsyncSession,
    step: WorkflowStep,
    staff: StaffMember,
    result: str,
    comment: str,
    target_citizen: bool = False,
) -> dict:
    """Process a review decision and advance the workflow."""
    if result not in ("approved", "rejected", "needs_info"):
        raise ValueError(f"Invalid result: {result}")

    annotation = StepAnnotation(
        workflow_step_id=step.id,
        author_id=staff.id,
        annotation_type=result,
        content=comment,
        target_citizen=target_citizen or result in ("rejected", "needs_info"),
    )
    db.add(annotation)

    step.assigned_reviewer_id = staff.id

    await log_access(
        db,
        actor_type="staff",
        actor_id=str(staff.id),
        action=f"review_{result}",
        resource_type="workflow_step",
        resource_id=str(step.id),
    )

    return await advance_workflow(db, step, result)


async def create_consultation(
    db: AsyncSession,
    step: WorkflowStep,
    staff: StaffMember,
    target_department_id,
    question: str,
) -> StepAnnotation:
    """Create a consultation annotation targeting another department."""
    annotation = StepAnnotation(
        workflow_step_id=step.id,
        author_id=staff.id,
        annotation_type="consultation",
        content=question,
        target_citizen=False,
    )
    db.add(annotation)

    await log_access(
        db,
        actor_type="staff",
        actor_id=str(staff.id),
        action="consultation_created",
        resource_type="workflow_step",
        resource_id=str(step.id),
    )

    await db.commit()
    await db.refresh(annotation)
    return annotation
