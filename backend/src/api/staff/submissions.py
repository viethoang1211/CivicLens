import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.models.case_type import CaseType
from src.models.citizen import Citizen
from src.models.dossier import Dossier
from src.models.scanned_page import ScannedPage
from src.models.submission import Submission
from src.security.abac import check_submission_clearance
from src.security.auth import StaffIdentity, get_current_staff
from src.services.oss_client import oss_client
from src.services.quality_service import assess_image_quality
from src.workers.ocr_worker import run_ocr_pipeline

router = APIRouter()


class _CreateSubmissionBody(BaseModel):
    citizen_id_number: str
    security_classification: int = 0
    priority: str = "normal"


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_submission(
    body: _CreateSubmissionBody,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    if body.security_classification < 0 or body.security_classification > 3:
        raise HTTPException(status_code=422, detail="security_classification must be 0-3")
    if body.priority not in ("normal", "urgent"):
        raise HTTPException(status_code=422, detail="priority must be 'normal' or 'urgent'")

    result = await db.execute(select(Citizen).where(Citizen.id_number == body.citizen_id_number))
    citizen = result.scalar_one_or_none()
    if citizen is None:
        raise HTTPException(status_code=404, detail="Citizen not found. Verify CCCD number.")

    submission = Submission(
        citizen_id=citizen.id,
        submitted_by_staff_id=staff.staff_id,
        security_classification=body.security_classification,
        priority=body.priority,
        status="draft",
        submitted_at=datetime.now(UTC),
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    return {
        "id": str(submission.id),
        "citizen_id": str(submission.citizen_id),
        "status": submission.status,
        "security_classification": submission.security_classification,
        "priority": submission.priority,
        "created_at": submission.created_at.isoformat(),
    }


@router.post("/{submission_id}/pages", status_code=status.HTTP_201_CREATED)
async def upload_page(
    submission_id: uuid.UUID,
    page_number: int = Form(...),
    image: UploadFile = File(...),
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    submission = await check_submission_clearance(submission_id, staff, db, action="scan")

    image_data = await image.read()
    quality_result = assess_image_quality(image_data)

    if not quality_result["acceptable"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "image_quality_low",
                "message": f"Image quality score {quality_result['score']:.2f} is below threshold. Please re-scan.",
                "quality_score": quality_result["score"],
                "guidance": quality_result["guidance"],
            },
        )

    oss_key = oss_client.generate_key(str(submission_id), page_number)
    oss_client.upload(oss_key, image_data)

    page = ScannedPage(
        submission_id=submission_id,
        page_number=page_number,
        image_oss_key=oss_key,
        image_quality_score=quality_result["score"],
        synced_at=datetime.now(UTC),
    )
    db.add(page)

    if submission.status == "draft":
        submission.status = "scanning"

    await db.commit()
    await db.refresh(page)

    return {
        "id": str(page.id),
        "submission_id": str(page.submission_id),
        "page_number": page.page_number,
        "image_oss_key": page.image_oss_key,
        "image_quality_score": float(page.image_quality_score) if page.image_quality_score else None,
        "quality_acceptable": True,
        "created_at": page.created_at.isoformat(),
    }


@router.post("/{submission_id}/finalize-scan", status_code=status.HTTP_202_ACCEPTED)
async def finalize_scan(
    submission_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    submission = await check_submission_clearance(submission_id, staff, db, action="finalize_scan")

    if submission.status not in ("draft", "scanning"):
        raise HTTPException(status_code=409, detail=f"Cannot finalize scan in status '{submission.status}'")

    submission.status = "ocr_processing"

    # Auto-create a Dossier so citizen can track this scan
    dossier_id = None
    case_type_result = await db.execute(
        select(CaseType).where(CaseType.code == "QUICK_SCAN")
    )
    quick_scan_type = case_type_result.scalar_one_or_none()
    if quick_scan_type and submission.citizen_id:
        ref_number = _generate_reference_number()
        dossier = Dossier(
            citizen_id=submission.citizen_id,
            submitted_by_staff_id=staff.staff_member_id,
            case_type_id=quick_scan_type.id,
            status="submitted",
            reference_number=ref_number,
            submitted_at=datetime.now(UTC),
        )
        db.add(dossier)
        await db.flush()
        dossier_id = dossier.id
        submission.dossier_id = dossier.id

    await db.commit()

    run_ocr_pipeline.delay(str(submission_id))

    resp = {
        "id": str(submission.id),
        "status": "ocr_processing",
        "estimated_completion_seconds": 15,
    }
    if dossier_id:
        resp["dossier_id"] = str(dossier_id)
    return resp


def _generate_reference_number() -> str:
    """Generate reference number in format HS-YYYYMMDD-NNNNN."""
    now = datetime.now(UTC)
    date_part = now.strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:5].upper()
    return f"HS-{date_part}-{random_part}"


@router.get("/{submission_id}/ocr-results")
async def get_ocr_results(
    submission_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    submission = await check_submission_clearance(submission_id, staff, db, action="view")

    result = await db.execute(
        select(ScannedPage)
        .where(ScannedPage.submission_id == submission_id)
        .order_by(ScannedPage.page_number)
    )
    pages = result.scalars().all()

    return {
        "submission_id": str(submission_id),
        "status": submission.status,
        "pages": [
            {
                "page_number": p.page_number,
                "ocr_raw_text": p.ocr_raw_text,
                "ocr_confidence": float(p.ocr_confidence) if p.ocr_confidence else None,
            }
            for p in pages
        ],
    }


class _OcrCorrectionsBody(BaseModel):
    pages: list[dict]


@router.put("/{submission_id}/ocr-corrections")
async def submit_ocr_corrections(
    submission_id: uuid.UUID,
    body: _OcrCorrectionsBody,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    await check_submission_clearance(submission_id, staff, db, action="correct_ocr")

    for page_correction in body.pages:
        result = await db.execute(
            select(ScannedPage).where(
                ScannedPage.submission_id == submission_id,
                ScannedPage.page_number == page_correction["page_number"],
            )
        )
        page = result.scalar_one_or_none()
        if page:
            page.ocr_corrected_text = page_correction["corrected_text"]

    await db.commit()

    # Regenerate AI summary with updated OCR text
    try:
        from src.workers.summarization_worker import generate_summary
        generate_summary.delay(str(submission_id))
    except Exception:
        logging.getLogger(__name__).exception("Summarization enqueue failed")

    return {"status": "ok"}
