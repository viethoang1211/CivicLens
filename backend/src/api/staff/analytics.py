import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.security.auth import StaffIdentity, get_current_staff
from src.services import analytics_service

router = APIRouter()


@router.get("/sla")
async def get_sla_metrics(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    department_id: uuid.UUID | None = Query(None),
    staff: StaffIdentity = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    if staff.role not in ("manager", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Chỉ quản lý hoặc admin mới được truy cập thống kê SLA",
        )

    if date_from is None:
        date_from = date.today() - timedelta(days=30)
    if date_to is None:
        date_to = date.today()

    return await analytics_service.get_sla_metrics(
        db=db,
        date_from=date_from,
        date_to=date_to,
        department_id=department_id,
    )
