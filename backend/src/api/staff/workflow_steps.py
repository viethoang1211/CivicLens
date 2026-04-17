import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.dependencies import get_db
from src.models.department import Department
from src.models.scanned_page import ScannedPage
from src.models.submission import Submission
from src.models.workflow_step import WorkflowStep
from src.security.abac import check_submission_clearance
from src.security.auth import StaffIdentity, get_current_staff
from src.services.oss_client import OSSClient
from src.services.review_service import create_consultation, process_review, validate_reviewer

router = APIRouter(tags=["workflow-steps"])


# ── GET /{id} — full review context ─────────────────────

@router.get("/{step_id}")
async def get_step_detail(
    step_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkflowStep)
        .options(selectinload(WorkflowStep.annotations), selectinload(WorkflowStep.department))
        .where(WorkflowStep.id == step_id)
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(404, "Workflow step not found")

    # Load submission with pages
    from src.models.document_type import DocumentType
    sub_result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.workflow_steps))
        .where(Submission.id == step.submission_id)
    )
    submission = sub_result.scalar_one()

    # Load document type name
    doc_type_name = None
    if submission.document_type_id:
        dt_result = await db.execute(
            select(DocumentType).where(DocumentType.id == submission.document_type_id)
        )
        dt = dt_result.scalar_one_or_none()
        doc_type_name = dt.name if dt else None

    await check_submission_clearance(submission.id, staff, db, action="review", submission=submission)

    pages_result = await db.execute(
        select(ScannedPage)
        .where(ScannedPage.submission_id == submission.id)
        .order_by(ScannedPage.page_number)
    )
    pages = pages_result.scalars().all()

    oss = OSSClient()
    page_list = [
        {
            "page_number": p.page_number,
            "image_url": oss.get_presigned_url(p.image_oss_key),
            "ocr_text": p.ocr_corrected_text or p.ocr_raw_text,
            "ocr_confidence": p.ocr_confidence,
        }
        for p in pages
    ]

    # Collect all annotations across all steps
    all_steps_result = await db.execute(
        select(WorkflowStep)
        .options(selectinload(WorkflowStep.annotations), selectinload(WorkflowStep.department))
        .where(WorkflowStep.submission_id == submission.id)
        .order_by(WorkflowStep.step_order)
    )
    all_steps = all_steps_result.scalars().all()

    annotations_by_dept = {}
    for s in all_steps:
        dept_name = s.department.name if s.department else "Unknown"
        for a in s.annotations:
            annotations_by_dept.setdefault(dept_name, []).append({
                "type": a.annotation_type,
                "content": a.content,
                "target_citizen": a.target_citizen,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })

    return {
        "step": {
            "id": str(step.id),
            "step_order": step.step_order,
            "status": step.status,
            "department_name": step.department.name if step.department else None,
            "started_at": step.started_at.isoformat() if step.started_at else None,
            "expected_complete_by": step.expected_complete_by.isoformat() if step.expected_complete_by else None,
        },
        "submission": {
            "id": str(submission.id),
            "status": submission.status,
            "security_classification": submission.security_classification,
            "document_type_name": doc_type_name,
            "template_data": submission.template_data,
        },
        "pages": page_list,
        "annotations_by_department": annotations_by_dept,
    }


# ── POST /{id}/complete — review decision ───────────────

class CompleteStepRequest(BaseModel):
    result: str  # approved, rejected, needs_info
    comment: str
    target_citizen: bool = False


@router.post("/{step_id}/complete")
async def complete_step(
    step_id: uuid.UUID,
    body: CompleteStepRequest,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkflowStep).where(WorkflowStep.id == step_id)
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(404, "Workflow step not found")

    staff_member = await validate_reviewer(db, step, staff.staff_id)
    return await process_review(db, step, staff_member, body.result, body.comment, body.target_citizen)


# ── POST /{id}/consultations — cross-dept consultation ──

class ConsultationRequest(BaseModel):
    target_department_id: uuid.UUID
    question: str


@router.post("/{step_id}/consultations")
async def create_step_consultation(
    step_id: uuid.UUID,
    body: ConsultationRequest,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkflowStep).where(WorkflowStep.id == step_id)
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(404, "Workflow step not found")

    if step.status != "active":
        raise HTTPException(400, "Step is not active")

    staff_member = await validate_reviewer(db, step, staff.staff_id)

    # Verify target department exists
    dept_result = await db.execute(
        select(Department).where(Department.id == body.target_department_id)
    )
    if not dept_result.scalar_one_or_none():
        raise HTTPException(404, "Target department not found")

    annotation = await create_consultation(db, step, staff_member, body.target_department_id, body.question)
    return {
        "id": str(annotation.id),
        "annotation_type": annotation.annotation_type,
        "content": annotation.content,
        "created_at": annotation.created_at.isoformat() if annotation.created_at else None,
    }
