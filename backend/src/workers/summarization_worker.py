import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.config import settings
from src.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

sync_engine = create_engine(settings.database_url)


@celery_app.task(
    name="summarization.generate",
    bind=True,
    max_retries=3,
    autoretry_for=(RuntimeError,),
    retry_backoff=True,
    retry_backoff_max=90,
    default_retry_delay=10,
)
def generate_summary(self, submission_id: str):
    """Generate AI summary for a submission after classification."""
    from src.services.summarization_service import generate_submission_summary

    sub_uuid = uuid.UUID(submission_id)
    try:
        with Session(sync_engine) as db:
            generate_submission_summary(db, sub_uuid)
    except RuntimeError:
        raise  # Let Celery retry on AI API errors
    except Exception:
        logger.exception("Summarization failed for submission %s", submission_id)
        # On non-retryable failure, ensure ai_summary stays null
        with Session(sync_engine) as db:
            from sqlalchemy import select

            from src.models.submission import Submission

            sub = db.execute(select(Submission).where(Submission.id == sub_uuid)).scalar_one_or_none()
            if sub:
                sub.ai_summary = None
                db.commit()


@celery_app.task(
    name="summarization.generate_dossier",
    bind=True,
    max_retries=3,
    autoretry_for=(RuntimeError,),
    retry_backoff=True,
    retry_backoff_max=90,
    default_retry_delay=10,
)
def generate_dossier_summary(self, dossier_id: str):
    """Generate AI summary for a dossier after submission."""
    from src.services.summarization_service import generate_dossier_summary as _gen

    dos_uuid = uuid.UUID(dossier_id)
    try:
        with Session(sync_engine) as db:
            _gen(db, dos_uuid)
    except RuntimeError:
        raise  # Let Celery retry on AI API errors
    except Exception:
        logger.exception("Dossier summarization failed for dossier %s", dossier_id)
        with Session(sync_engine) as db:
            from sqlalchemy import select

            from src.models.dossier import Dossier

            dos = db.execute(select(Dossier).where(Dossier.id == dos_uuid)).scalar_one_or_none()
            if dos:
                dos.ai_summary = None
                db.commit()
