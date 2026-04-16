from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.dependencies import get_db
from src.models.staff_member import StaffMember
from src.security.auth import create_access_token, create_refresh_token, verify_password

router = APIRouter()


class LoginRequest(BaseModel):
    employee_id: str
    password: str


@router.post("/login")
async def staff_login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StaffMember)
        .where(StaffMember.employee_id == body.employee_id, StaffMember.is_active.is_(True))
        .options(selectinload(StaffMember.department))
    )
    staff = result.scalar_one_or_none()

    if staff is None or not verify_password(body.password, staff.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Employee ID or password is incorrect.")

    token_data = {
        "sub": str(staff.id),
        "type": "staff",
        "employee_id": staff.employee_id,
        "department_id": str(staff.department_id),
        "clearance_level": staff.clearance_level,
        "role": staff.role,
    }

    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "expires_in": 3600,
        "staff": {
            "id": str(staff.id),
            "full_name": staff.full_name,
            "department_id": str(staff.department_id),
            "department_name": staff.department.name if staff.department else None,
            "clearance_level": staff.clearance_level,
            "role": staff.role,
        },
    }
