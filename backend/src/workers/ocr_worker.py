import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.config import settings
from src.models.scanned_page import ScannedPage
from src.models.submission import Submission
from src.services.ai_client import ai_client
from src.services.oss_client import oss_client
from src.workers.celery_app import celery_app

sync_engine = create_engine(settings.database_url)


@celery_app.task(name="ocr.run_pipeline", bind=True, max_retries=3)
def run_ocr_pipeline(self, submission_id: str):
    sub_uuid = uuid.UUID(submission_id)

    with Session(sync_engine) as db:
        pages = db.execute(
            select(ScannedPage)
            .where(ScannedPage.submission_id == sub_uuid)
            .order_by(ScannedPage.page_number)
        ).scalars().all()

        for page in pages:
            try:
                image_data = oss_client.download(page.image_oss_key)
                result = ai_client.run_ocr(image_data)
                page.ocr_raw_text = result["text"]
                page.ocr_confidence = 0.85  # Placeholder; real impl parses model confidence

                # Fallback for low confidence
                if page.ocr_confidence and float(page.ocr_confidence) < 0.6:
                    fallback_result = ai_client.run_ocr(image_data, use_fallback=True)
                    page.ocr_raw_text = fallback_result["text"]
                    page.ocr_confidence = 0.80

            except Exception as exc:
                page.ocr_raw_text = f"[OCR ERROR: {exc}]"
                page.ocr_confidence = 0.0

        submission = db.execute(select(Submission).where(Submission.id == sub_uuid)).scalar_one()
        submission.status = "pending_classification"
        db.commit()

    # Chain: trigger classification after OCR
    from src.workers.classification_worker import run_classification

    run_classification.delay(submission_id)
