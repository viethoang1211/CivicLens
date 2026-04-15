"""Backfill AI summaries for existing classified submissions.

Usage: python -m src.workers.backfill_summaries

Idempotent: skips submissions where ai_summary is already set.
Rate limit: 5 tasks/second to avoid overwhelming dashscope API.
"""
import time

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.config import settings
from src.models.submission import Submission

RATE_LIMIT = 5  # tasks per second


def main():
    engine = create_engine(settings.database_url)

    with Session(engine) as db:
        submissions = db.execute(
            select(Submission.id)
            .where(Submission.ai_summary.is_(None))
            .where(Submission.status.in_(["pending_classification", "classified", "in_progress", "completed"]))
            .where(Submission.document_type_id.isnot(None))
        ).scalars().all()


    from src.workers.summarization_worker import generate_summary

    for i, sub_id in enumerate(submissions):
        generate_summary.delay(str(sub_id))
        if (i + 1) % RATE_LIMIT == 0:
            time.sleep(1)



if __name__ == "__main__":
    main()
