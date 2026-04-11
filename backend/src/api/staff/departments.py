import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.dependencies import get_db
from src.models.department import Department
from src.models.submission import Submission
from src.models.workflow_step import WorkflowStep
from src.security.auth import StaffIdentity, get_current_staff

router = APIRouter()


@router.get("/{department_id}/queue")
async def get_department_queue(
    department_id: uuid.UUID,
    status: str = Query("active"),
    priority: str = Query("all"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(WorkflowStep)
        .join(Submission, WorkflowStep.submission_id == Submission.id)
        .join(Department, WorkflowStep.department_id == Department.id)
        .where(WorkflowStep.department_id == department_id)
        .where(Submission.security_classification <= staff.clearance_level)
    )

    if status != "all":
        query = query.where(WorkflowStep.status == status)
    if priority != "all":
        query = query.where(Submission.priority == priority)

    # Priority ordering: urgent first, then by started_at
    query = query.order_by(
        Submission.priority.desc(),
        WorkflowStep.started_at.asc().nullsfirst(),
    )

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query.options(selectinload(WorkflowStep.submission)))
    steps = result.scalars().all()

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    items = []
    for step in steps:
        is_delayed = False
        if step.expected_complete_by and step.status == "active" and now > step.expected_complete_by:
            is_delayed = True

        items.append({
            "workflow_step_id": str(step.id),
            "submission_id": str(step.submission_id),
            "document_type_name": "",  # Would join through submission.document_type
            "priority": step.submission.priority if step.submission else "normal",
            "started_at": step.started_at.isoformat() if step.started_at else None,
            "expected_complete_by": step.expected_complete_by.isoformat() if step.expected_complete_by else None,
            "is_delayed": is_delayed,
        })

    return {"items": items, "total": total, "page": page}
