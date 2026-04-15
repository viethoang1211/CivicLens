import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.dossier import Dossier
from src.models.dossier_document import DossierDocument
from src.models.scanned_page import ScannedPage
from src.models.submission import Submission
from src.services.ai_client import ai_client

logger = logging.getLogger(__name__)


def generate_submission_summary(db: Session, submission_id) -> None:
    """Generate AI summary for a submission. Stores summary + entities in DB.

    Skips when OCR text is empty or average OCR confidence < 0.3.
    """
    submission = db.execute(
        select(Submission).where(Submission.id == submission_id)
    ).scalar_one_or_none()
    if submission is None:
        logger.warning("Submission %s not found for summarization", submission_id)
        return

    pages = db.execute(
        select(ScannedPage)
        .where(ScannedPage.submission_id == submission_id)
        .order_by(ScannedPage.page_number)
    ).scalars().all()

    if not pages:
        return

    combined_text = "\n\n".join(
        p.ocr_corrected_text or p.ocr_raw_text or "" for p in pages
    )
    if not combined_text.strip():
        return

    # Check average OCR confidence
    confidences = [float(p.ocr_confidence) for p in pages if p.ocr_confidence is not None]
    if confidences and sum(confidences) / len(confidences) < 0.3:
        logger.info("Submission %s: average OCR confidence too low, skipping summary", submission_id)
        return

    # Get document type name
    doc_type_name = "Tài liệu"  # Default
    if submission.document_type_id:
        from src.models.document_type import DocumentType
        dt = db.execute(
            select(DocumentType).where(DocumentType.id == submission.document_type_id)
        ).scalar_one_or_none()
        if dt:
            doc_type_name = dt.name

    result = ai_client.summarize_document(combined_text, doc_type_name)

    submission.ai_summary = result.get("summary") or None
    submission.ai_summary_generated_at = datetime.now(UTC)

    # Store entities in template_data under _entities key
    entities = result.get("entities", {})
    if entities:
        if submission.template_data is None:
            submission.template_data = {}
        submission.template_data = {**submission.template_data, "_entities": entities}

    db.commit()
    logger.info("Submission %s: summary generated", submission_id)


def generate_dossier_summary(db: Session, dossier_id) -> None:
    """Generate AI summary for a dossier by aggregating document summaries."""
    dossier = db.execute(
        select(Dossier).where(Dossier.id == dossier_id)
    ).scalar_one_or_none()
    if dossier is None:
        logger.warning("Dossier %s not found for summarization", dossier_id)
        return

    # Get case type name
    case_type_name = "Hồ sơ"
    if dossier.case_type_id:
        from src.models.case_type import CaseType
        ct = db.execute(
            select(CaseType).where(CaseType.id == dossier.case_type_id)
        ).scalar_one_or_none()
        if ct:
            case_type_name = ct.name

    # Aggregate document summaries from submissions linked via dossier_documents
    docs = db.execute(
        select(DossierDocument).where(DossierDocument.dossier_id == dossier_id)
    ).scalars().all()

    doc_summaries = []
    for doc in docs:
        # Get OCR text from pages of this dossier document
        pages = db.execute(
            select(ScannedPage)
            .where(ScannedPage.dossier_document_id == doc.id)
            .order_by(ScannedPage.page_number)
        ).scalars().all()

        page_text = "\n".join(
            p.ocr_corrected_text or p.ocr_raw_text or "" for p in pages
        ).strip()
        if page_text:
            doc_summaries.append(f"- {page_text[:500]}")

    if not doc_summaries:
        return

    document_summaries_text = "\n".join(doc_summaries)
    reference_number = dossier.reference_number or ""

    result = ai_client.summarize_dossier(case_type_name, reference_number, document_summaries_text)

    dossier.ai_summary = result.get("summary") or None
    dossier.ai_summary_generated_at = datetime.now(UTC)
    db.commit()
    logger.info("Dossier %s: summary generated", dossier_id)
