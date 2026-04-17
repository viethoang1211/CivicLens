import uuid
from datetime import UTC

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.dependencies import get_db
from src.models.department import Department
from src.models.dossier import Dossier
from src.models.document_type import DocumentType
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

    result = await db.execute(query.options(
        selectinload(WorkflowStep.submission).selectinload(Submission.document_type),
    ))
    steps = result.scalars().all()

    from datetime import datetime

    now = datetime.now(UTC)

    items = []
    for step in steps:
        is_delayed = False
        if step.expected_complete_by and step.status == "active" and now > step.expected_complete_by:
            is_delayed = True

        # Get summary preview from submission or dossier
        summary_preview = None
        if step.submission and step.submission.ai_summary:
            summary_preview = step.submission.ai_summary[:100]
        elif step.dossier_id:
            # Load dossier summary for dossier-owned steps
            dos_result = await db.execute(select(Dossier).where(Dossier.id == step.dossier_id))
            dos = dos_result.scalar_one_or_none()
            if dos and dos.ai_summary:
                summary_preview = dos.ai_summary[:100]

        items.append({
            "workflow_step_id": str(step.id),
            "submission_id": str(step.submission_id) if step.submission_id else None,
            "dossier_id": str(step.dossier_id) if step.dossier_id else None,
            "document_type_name": (
                step.submission.document_type.name
                if step.submission and step.submission.document_type
                else ""
            ),
            "priority": step.submission.priority if step.submission else "normal",
            "started_at": step.started_at.isoformat() if step.started_at else None,
            "expected_complete_by": step.expected_complete_by.isoformat() if step.expected_complete_by else None,
            "is_delayed": is_delayed,
            "summary_preview": summary_preview,
        })

    return {"items": items, "total": total, "page": page}
