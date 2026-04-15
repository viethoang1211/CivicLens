import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.security.abac import check_submission_clearance
from src.security.auth import StaffIdentity, get_current_staff
from src.services.routing_service import create_workflow_for_submission

router = APIRouter()


@router.post("/{submission_id}/route")
async def route_submission(
    submission_id: uuid.UUID,
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    submission = await check_submission_clearance(submission_id, staff, db, action="route")

    if submission.status != "classified":
        raise HTTPException(status_code=409, detail=f"Cannot route submission in status '{submission.status}'")

    if not submission.document_type_id:
        raise HTTPException(status_code=409, detail="Submission must be classified before routing")

    return await create_workflow_for_submission(db, submission)
