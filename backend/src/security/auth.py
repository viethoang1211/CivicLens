import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config import settings

security_scheme = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass
class StaffIdentity:
    staff_id: uuid.UUID
    employee_id: str
    department_id: uuid.UUID
    clearance_level: int
    role: str


@dataclass
class CitizenIdentity:
    citizen_id: uuid.UUID


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from e


def get_current_staff(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> StaffIdentity:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "staff":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff access required")
    return StaffIdentity(
        staff_id=uuid.UUID(payload["sub"]),
        employee_id=payload["employee_id"],
        department_id=uuid.UUID(payload["department_id"]),
        clearance_level=payload["clearance_level"],
        role=payload["role"],
    )


def get_current_citizen(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> CitizenIdentity:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "citizen":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Citizen access required")
    return CitizenIdentity(citizen_id=uuid.UUID(payload["sub"]))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)
