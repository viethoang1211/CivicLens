import json
import logging
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.config import settings
from src.models.citizen import Citizen
from src.models.document_type import DocumentType
from src.models.dossier import Dossier
from src.models.dossier_document import DossierDocument
from src.models.scanned_page import ScannedPage
from src.models.submission import Submission
from src.services.ai_client import ai_client
from src.workers.celery_app import celery_app

sync_engine = create_engine(settings.database_url)

logger = logging.getLogger(__name__)


def _try_auto_link_citizen(submission: Submission, db: Session) -> None:
    """Auto-link citizen to submission (and its dossier) if CCCD number found in template_data."""
    if not isinstance(submission.template_data, dict):
        return

    so_cccd = submission.template_data.get("so_cccd")
    if not so_cccd or not isinstance(so_cccd, str):
        return

    so_cccd = so_cccd.strip()
    if not so_cccd:
        return

    citizen = db.execute(
        select(Citizen).where(Citizen.id_number == so_cccd)
    ).scalar_one_or_none()

    if citizen is None:
        # Auto-create citizen from extracted data
        ho_ten = submission.template_data.get("ho_ten", "").strip() or f"Công dân {so_cccd}"
        citizen = Citizen(
            vneid_subject_id=f"auto_{so_cccd}",
            full_name=ho_ten,
            id_number=so_cccd,
        )
        db.add(citizen)
        db.flush()
        logger.info("Auto-created citizen %s (%s) from OCR data", so_cccd, ho_ten)

    submission.citizen_id = citizen.id
    logger.info("Auto-linked submission %s to citizen %s", submission.id, so_cccd)

    # Also link the dossier if it exists and has no citizen
    if submission.dossier_id:
        dossier = db.execute(
            select(Dossier).where(Dossier.id == submission.dossier_id)
        ).scalar_one_or_none()
        if dossier and dossier.citizen_id is None:
            dossier.citizen_id = citizen.id
            logger.info("Auto-linked dossier %s to citizen %s", dossier.id, so_cccd)


def _try_auto_link_citizen_from_image(dossier: Dossier, image_data: bytes, doc_type: DocumentType, db: Session) -> None:
    """Run OCR + template fill on a CCCD image to extract citizen info and auto-link to dossier."""
    try:
        ocr_text = ai_client.run_ocr(image_data)
        if not ocr_text or not ocr_text.strip():
            return

        template_result = ai_client.fill_template(ocr_text, doc_type.template_schema)
        if isinstance(template_result, str):
            cleaned = template_result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            filled = json.loads(cleaned)
        else:
            filled = template_result

        so_cccd = filled.get("so_cccd", "").strip() if isinstance(filled, dict) else ""
        if not so_cccd:
            return

        citizen = db.execute(
            select(Citizen).where(Citizen.id_number == so_cccd)
        ).scalar_one_or_none()

        if citizen is None:
            ho_ten = filled.get("ho_ten", "").strip() or f"Công dân {so_cccd}"
            citizen = Citizen(
                vneid_subject_id=f"auto_{so_cccd}",
                full_name=ho_ten,
                id_number=so_cccd,
            )
            db.add(citizen)
            db.flush()
            logger.info("Auto-created citizen %s (%s) from CCCD image", so_cccd, ho_ten)

        dossier.citizen_id = citizen.id
        db.commit()
        logger.info("Auto-linked dossier %s to citizen %s from CCCD image", dossier.id, so_cccd)

    except Exception:
        logger.exception("Failed to auto-link citizen from CCCD image for dossier %s", dossier.id)


@celery_app.task(name="classification.run", bind=True, max_retries=3)
def run_classification(self, submission_id: str):
    sub_uuid = uuid.UUID(submission_id)

    with Session(sync_engine) as db:
        # Gather OCR text from all pages
        pages = db.execute(
            select(ScannedPage)
            .where(ScannedPage.submission_id == sub_uuid)
            .order_by(ScannedPage.page_number)
        ).scalars().all()

        combined_text = "\n\n".join(
            p.ocr_corrected_text or p.ocr_raw_text or "" for p in pages
        )

        if not combined_text.strip():
            return  # Nothing to classify

        # Fetch active document types
        doc_types = db.execute(
            select(DocumentType).where(DocumentType.is_active.is_(True))
        ).scalars().all()

        type_dicts = [
            {"code": dt.code, "name": dt.name, "description": dt.description or ""}
            for dt in doc_types
        ]

        # Run AI classification
        raw_result = ai_client.classify_document(combined_text, type_dicts)

        # Parse result
        try:
            if isinstance(raw_result, str):
                # Strip markdown code fences if present
                cleaned = raw_result.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                classification = json.loads(cleaned)
            else:
                classification = raw_result
        except (json.JSONDecodeError, IndexError):
            return  # Failed to parse; leave in pending_classification

        # Match document type by code
        matched_type = None
        for dt in doc_types:
            if dt.code == classification.get("document_type_code"):
                matched_type = dt
                break

        submission = db.execute(select(Submission).where(Submission.id == sub_uuid)).scalar_one()

        if matched_type:
            submission.document_type_id = matched_type.id
            confidence = classification.get("confidence", 0.0)
            submission.classification_confidence = confidence

            # Enforce confidence threshold
            if confidence >= settings.classification_confidence_threshold:
                submission.classification_method = "ai"
            else:
                submission.classification_method = "ai_low_confidence"
                # Store alternatives for staff review
                alternatives = classification.get("alternatives", [])
                if alternatives:
                    if submission.template_data is None:
                        submission.template_data = {}
                    submission.template_data["_classification_alternatives"] = alternatives

            # Run template filling
            template_result = ai_client.fill_template(combined_text, matched_type.template_schema)
            try:
                if isinstance(template_result, str):
                    cleaned = template_result.strip()
                    if cleaned.startswith("```"):
                        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                    filled = json.loads(cleaned)
                else:
                    filled = template_result
            except (json.JSONDecodeError, IndexError):
                filled = {}

            # Merge template data, preserving _classification_alternatives
            if submission.template_data and "_classification_alternatives" in submission.template_data:
                alts = submission.template_data["_classification_alternatives"]
                submission.template_data = filled if isinstance(filled, dict) else {}
                submission.template_data["_classification_alternatives"] = alts
            else:
                submission.template_data = filled if isinstance(filled, dict) else {}

        # Auto-link citizen if CCCD number found in template data
        if submission.citizen_id is None:
            _try_auto_link_citizen(submission, db)

        submission.status = "pending_classification"  # Stays pending until staff confirms
        db.commit()

    # Chain to summarization after successful classification
    try:
        from src.workers.summarization_worker import generate_summary
        generate_summary.delay(submission_id)
    except Exception:
        logging.getLogger(__name__).exception("Summarization enqueue failed")


@celery_app.task(name="classification.validate_slot", bind=True, max_retries=3)
def validate_document_slot(self, dossier_document_id: str):
    """Validate whether a DossierDocument matches its expected slot's document type.

    Uses dashscope vision model in binary (match/no-match) mode.
    Stores result in DossierDocument.ai_match_result as JSONB.
    """
    doc_uuid = uuid.UUID(dossier_document_id)

    with Session(sync_engine) as db:
        doc = db.execute(
            select(DossierDocument).where(DossierDocument.id == doc_uuid)
        ).scalar_one_or_none()

        if doc is None:
            return  # Document was deleted before task ran

        # Get first page image
        first_page = db.execute(
            select(ScannedPage)
            .where(ScannedPage.dossier_document_id == doc_uuid)
            .order_by(ScannedPage.page_number)
        ).scalars().first()

        if first_page is None:
            return  # No pages uploaded yet

        # Load expected document type prompt
        if doc.document_type_id is None:
            return  # No expected type to validate against

        doc_type = db.execute(
            select(DocumentType).where(DocumentType.id == doc.document_type_id)
        ).scalar_one_or_none()

        if doc_type is None or not doc_type.classification_prompt:
            return

        # Download image from OSS
        try:
            from src.services.oss_client import oss_client as _oss
            image_data = _oss.download(first_page.image_oss_key)
        except Exception:
            return  # OSS unavailable; leave ai_match_result as null

        # Call AI for slot validation
        try:
            match_result = ai_client.validate_document_slot(image_data, doc_type.classification_prompt)
        except Exception as exc:
            raise self.retry(exc=exc, countdown=30) from exc

        doc.ai_match_result = match_result
        db.commit()

        # Auto-link citizen if this is a CCCD document and the dossier has no citizen
        if doc_type.code == "ID_CCCD" and doc.dossier_id:
            dossier = db.execute(
                select(Dossier).where(Dossier.id == doc.dossier_id)
            ).scalar_one_or_none()
            if dossier and dossier.citizen_id is None:
                _try_auto_link_citizen_from_image(dossier, image_data, doc_type, db)
