import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.security.auth import StaffIdentity, get_current_staff
from src.services import search_service

router = APIRouter()


@router.get("")
async def search(
    q: str = Query(..., min_length=2, description="Search query (min 2 chars)"),
    status: str | None = Query(None),
    document_type_code: str | None = Query(None),
    case_type_code: str | None = Query(None),
    department_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    sort: str = Query("relevance", pattern="^(relevance|submitted_at|updated_at)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    if len(q.strip()) < 2:
        raise HTTPException(status_code=422, detail="Truy vấn tìm kiếm phải có ít nhất 2 ký tự")

    return await search_service.search(
        db=db,
        query=q.strip(),
        clearance_level=staff.clearance_level,
        status=status,
        document_type_code=document_type_code,
        case_type_code=case_type_code,
        department_id=department_id,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        page=page,
        per_page=per_page,
    )
