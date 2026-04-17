import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.dependencies import get_db
from src.models.department import Department
from src.models.document_type import DocumentType
from src.models.step_annotation import StepAnnotation
from src.models.submission import Submission
from src.security.auth import CitizenIdentity, get_current_citizen

router = APIRouter()


async def _doc_type_name(db: AsyncSession, doc_type_id) -> str:
    if not doc_type_id:
        return ""
    dt = await db.execute(select(DocumentType).where(DocumentType.id == doc_type_id))
    dt = dt.scalar_one_or_none()
    return dt.name if dt else ""


@router.get("")
async def list_submissions(
    status: str = Query("all"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    citizen: CitizenIdentity = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    query = select(Submission).where(Submission.citizen_id == citizen.citizen_id)
    if status != "all":
        if status == "active":
            query = query.where(Submission.status.notin_(["completed", "rejected"]))
        elif status == "completed":
            query = query.where(Submission.status.in_(["completed", "rejected"]))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Submission.submitted_at.desc()).offset((page - 1) * per_page).limit(per_page)
    query = query.options(selectinload(Submission.workflow_steps))

    result = await db.execute(query)
    submissions = result.scalars().all()

    now = datetime.now(UTC)
    items = []
    for sub in submissions:
        current_step = None
        completed_steps = 0
        for step in sub.workflow_steps:
            if step.status == "completed":
                completed_steps += 1
            if step.status == "active":
                dept_result = await db.execute(select(Department).where(Department.id == step.department_id))
                dept = dept_result.scalar_one_or_none()
                current_step = {
                    "step_order": step.step_order,
                    "department_name": dept.name if dept else "",
                    "status": step.status,
                }

        is_delayed = any(
            s.status == "active" and s.expected_complete_by and now > s.expected_complete_by
            for s in sub.workflow_steps
        )

        items.append({
            "id": str(sub.id),
            "document_type_name": await _doc_type_name(db, sub.document_type_id),
            "status": sub.status,
            "priority": sub.priority,
            "submitted_at": sub.submitted_at.isoformat(),
            "current_step": current_step,
            "total_steps": len(sub.workflow_steps),
            "completed_steps": completed_steps,
            "is_delayed": is_delayed,
        })

    return {"items": items, "total": total, "page": page}


@router.get("/{submission_id}")
async def get_submission_detail(
    submission_id: uuid.UUID,
    citizen: CitizenIdentity = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Submission)
        .where(Submission.id == submission_id, Submission.citizen_id == citizen.citizen_id)
        .options(selectinload(Submission.workflow_steps))
    )
    submission = result.scalar_one_or_none()
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")

    now = datetime.now(UTC)
    workflow = []
    for step in sorted(submission.workflow_steps, key=lambda s: s.step_order):
        dept_result = await db.execute(select(Department).where(Department.id == step.department_id))
        dept = dept_result.scalar_one_or_none()

        is_delayed = (
            step.status == "active" and step.expected_complete_by and now > step.expected_complete_by
        )

        workflow.append({
            "step_order": step.step_order,
            "department_name": dept.name if dept else "",
            "status": step.status,
            "started_at": step.started_at.isoformat() if step.started_at else None,
            "completed_at": step.completed_at.isoformat() if step.completed_at else None,
            "expected_complete_by": step.expected_complete_by.isoformat() if step.expected_complete_by else None,
            "is_delayed": is_delayed,
            "result": step.result,
        })

    # Citizen-visible annotations
    citizen_annotations = []
    for step in submission.workflow_steps:
        ann_result = await db.execute(
            select(StepAnnotation).where(
                StepAnnotation.workflow_step_id == step.id,
                StepAnnotation.target_citizen.is_(True),
            )
        )
        for ann in ann_result.scalars().all():
            dept_result = await db.execute(select(Department).where(Department.id == step.department_id))
            dept = dept_result.scalar_one_or_none()
            citizen_annotations.append({
                "step_order": step.step_order,
                "department_name": dept.name if dept else "",
                "content": ann.content,
                "type": ann.annotation_type,
                "created_at": ann.created_at.isoformat(),
            })

    return {
        "id": str(submission.id),
        "document_type_name": await _doc_type_name(db, submission.document_type_id),
        "status": submission.status,
        "priority": submission.priority,
        "submitted_at": submission.submitted_at.isoformat(),
        "completed_at": submission.completed_at.isoformat() if submission.completed_at else None,
        "workflow": workflow,
        "citizen_annotations": citizen_annotations,
    }
