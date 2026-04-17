import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.models.audit_log import AuditLogEntry
from src.models.staff_member import StaffMember
from src.security.auth import StaffIdentity, get_current_staff

router = APIRouter(tags=["audit"])


@router.get("/logs")
async def list_audit_logs(
    resource_type: str | None = Query(None),
    resource_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """List audit log entries with optional filters."""
    query = select(AuditLogEntry)

    if resource_type:
        query = query.where(AuditLogEntry.resource_type == resource_type)
    if resource_id:
        query = query.where(AuditLogEntry.resource_id == resource_id)
    if action:
        query = query.where(AuditLogEntry.action == action)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(desc(AuditLogEntry.created_at))
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    entries = result.scalars().all()

    items = []
    for entry in entries:
        actor_name = None
        if entry.actor_type == "staff":
            staff_result = await db.execute(
                select(StaffMember).where(StaffMember.id == entry.actor_id)
            )
            s = staff_result.scalar_one_or_none()
            actor_name = s.full_name if s else None

        items.append({
            "id": str(entry.id),
            "actor_type": entry.actor_type,
            "actor_id": str(entry.actor_id),
            "actor_name": actor_name,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": str(entry.resource_id),
            "clearance_check_result": entry.clearance_check_result,
            "metadata": entry.metadata_,
            "created_at": entry.created_at.isoformat(),
        })

    return {"items": items, "total": total, "page": page}


@router.get("/submissions/{submission_id}/trail")
async def get_submission_audit_trail(
    submission_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Get complete audit trail for a specific submission.

    Returns all audit events related to this submission, including
    scans, classifications, reviews, and workflow transitions.
    """
    from src.models.department import Department
    from src.models.step_annotation import StepAnnotation
    from src.models.submission import Submission
    from src.models.workflow_step import WorkflowStep

    # Load submission
    sub_result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = sub_result.scalar_one_or_none()
    if not submission:
        from fastapi import HTTPException
        raise HTTPException(404, "Submission not found")

    # Get audit log entries for this submission
    audit_result = await db.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.resource_id == submission_id)
        .order_by(AuditLogEntry.created_at)
    )
    audit_entries = audit_result.scalars().all()

    # Get workflow steps and their annotations
    steps_result = await db.execute(
        select(WorkflowStep)
        .where(WorkflowStep.submission_id == submission_id)
        .order_by(WorkflowStep.step_order)
    )
    steps = steps_result.scalars().all()

    # Also get audit entries for workflow steps
    step_ids = [s.id for s in steps]
    step_audit = []
    if step_ids:
        step_audit_result = await db.execute(
            select(AuditLogEntry)
            .where(
                AuditLogEntry.resource_type == "workflow_step",
                AuditLogEntry.resource_id.in_(step_ids),
            )
            .order_by(AuditLogEntry.created_at)
        )
        step_audit = step_audit_result.scalars().all()

    # Build timeline
    timeline = []

    # Submission events
    for entry in audit_entries:
        actor_name = await _resolve_actor(db, entry)
        timeline.append({
            "timestamp": entry.created_at.isoformat(),
            "action": entry.action,
            "actor_type": entry.actor_type,
            "actor_name": actor_name,
            "resource_type": entry.resource_type,
            "details": entry.metadata_,
        })

    # Workflow step events
    for entry in step_audit:
        actor_name = await _resolve_actor(db, entry)
        # Find which step this belongs to
        step_dept = ""
        for s in steps:
            if s.id == entry.resource_id:
                dept_result = await db.execute(select(Department).where(Department.id == s.department_id))
                dept = dept_result.scalar_one_or_none()
                step_dept = dept.name if dept else ""
                break

        timeline.append({
            "timestamp": entry.created_at.isoformat(),
            "action": entry.action,
            "actor_type": entry.actor_type,
            "actor_name": actor_name,
            "resource_type": "workflow_step",
            "department": step_dept,
            "details": entry.metadata_,
        })

    # Add annotations to timeline
    for step in steps:
        ann_result = await db.execute(
            select(StepAnnotation).where(StepAnnotation.workflow_step_id == step.id)
        )
        dept_result = await db.execute(select(Department).where(Department.id == step.department_id))
        dept = dept_result.scalar_one_or_none()
        for ann in ann_result.scalars().all():
            author_name = None
            if ann.author_id:
                author_result = await db.execute(select(StaffMember).where(StaffMember.id == ann.author_id))
                author = author_result.scalar_one_or_none()
                author_name = author.full_name if author else None

            timeline.append({
                "timestamp": ann.created_at.isoformat(),
                "action": f"annotation_{ann.annotation_type}",
                "actor_type": "staff",
                "actor_name": author_name,
                "resource_type": "annotation",
                "department": dept.name if dept else "",
                "details": {"content": ann.content, "target_citizen": ann.target_citizen},
            })

    # Sort by timestamp
    timeline.sort(key=lambda x: x["timestamp"])

    return {
        "submission_id": str(submission_id),
        "status": submission.status,
        "security_classification": submission.security_classification,
        "submitted_at": submission.submitted_at.isoformat(),
        "completed_at": submission.completed_at.isoformat() if submission.completed_at else None,
        "timeline": timeline,
        "total_events": len(timeline),
    }


async def _resolve_actor(db: AsyncSession, entry: AuditLogEntry) -> str | None:
    if entry.actor_type == "staff":
        result = await db.execute(select(StaffMember).where(StaffMember.id == entry.actor_id))
        s = result.scalar_one_or_none()
        return s.full_name if s else None
    return None
