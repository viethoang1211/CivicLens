import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.models.submission import Submission
from src.security.auth import StaffIdentity, get_current_staff
from src.services.audit_service import log_access


async def check_submission_clearance(
    submission_id: uuid.UUID,
    staff: StaffIdentity,
    db: AsyncSession,
    action: str = "view",
    *,
    submission: Submission | None = None,
) -> Submission:
    if submission is None:
        result = await db.execute(select(Submission).where(Submission.id == submission_id))
        submission = result.scalar_one_or_none()
        if submission is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if staff.clearance_level < submission.security_classification:
        await log_access(
            db=db,
            actor_type="staff",
            actor_id=staff.staff_id,
            action=action,
            resource_type="submission",
            resource_id=submission.id,
            clearance_check_result="denied",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient clearance level for this document",
        )

    await log_access(
        db=db,
        actor_type="staff",
        actor_id=staff.staff_id,
        action=action,
        resource_type="submission",
        resource_id=submission.id,
        clearance_check_result="granted",
    )
    return submission
