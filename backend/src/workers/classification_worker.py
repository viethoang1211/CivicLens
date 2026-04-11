import json
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from src.config import settings
from src.models.document_type import DocumentType
from src.models.dossier_document import DossierDocument
from src.models.scanned_page import ScannedPage
from src.models.submission import Submission
from src.services.ai_client import ai_client
from src.workers.celery_app import celery_app

sync_engine = create_engine(settings.database_url)


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
            submission.classification_confidence = classification.get("confidence", 0.0)
            submission.classification_method = "ai"

            # Run template filling
            template_result = ai_client.fill_template(combined_text, matched_type.template_schema)
            try:
                if isinstance(template_result, str):
                    cleaned = template_result.strip()
                    if cleaned.startswith("```"):
                        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
                    submission.template_data = json.loads(cleaned)
                else:
                    submission.template_data = template_result
            except (json.JSONDecodeError, IndexError):
                submission.template_data = {}

        submission.status = "pending_classification"  # Stays pending until staff confirms
        db.commit()


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
            raise self.retry(exc=exc, countdown=30)

        doc.ai_match_result = match_result
        db.commit()
