from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.submission import Submission


async def check_duplicate(
    db: AsyncSession,
    citizen_id,
    document_type_id,
    days_window: int = 30,
) -> dict | None:
    """Check if a similar submission already exists within recent timeframe.

    Returns duplicate info if found, None otherwise.
    """
    if not citizen_id or not document_type_id:
        return None

    cutoff = datetime.now(UTC) - timedelta(days=days_window)

    result = await db.execute(
        select(Submission).where(
            Submission.citizen_id == citizen_id,
            Submission.document_type_id == document_type_id,
            Submission.submitted_at >= cutoff,
            Submission.status.notin_(["rejected"]),
        ).order_by(Submission.submitted_at.desc()).limit(1)
    )
    existing = result.scalar_one_or_none()

    if existing:
        return {
            "duplicate_found": True,
            "existing_submission_id": str(existing.id),
            "existing_status": existing.status,
            "submitted_at": existing.submitted_at.isoformat() if existing.submitted_at else None,
        }

    return None
