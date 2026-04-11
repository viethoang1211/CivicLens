from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db
from src.models.citizen import Citizen
from src.security.auth import create_access_token, create_refresh_token

router = APIRouter()


class VNeIDAuthRequest(BaseModel):
    vneid_auth_code: str
    redirect_uri: str


@router.post("/vneid")
async def vneid_auth(body: VNeIDAuthRequest, db: AsyncSession = Depends(get_db)):
    # In production: exchange vneid_auth_code with VNeID OAuth server
    # For now, simulate lookup by auth code as a citizen identifier
    # This is a placeholder; real VNeID integration uses OAuth2 code exchange

    # Simulate: use auth_code as id_number for demo
    result = await db.execute(select(Citizen).where(Citizen.id_number == body.vneid_auth_code))
    citizen = result.scalar_one_or_none()

    if citizen is None:
        # Auto-register citizen (VNeID verified)
        citizen = Citizen(
            vneid_subject_id=body.vneid_auth_code,
            full_name="VNeID User",  # Would come from VNeID token
            id_number=body.vneid_auth_code,
        )
        db.add(citizen)
        await db.commit()
        await db.refresh(citizen)

    token_data = {"sub": str(citizen.id), "type": "citizen"}

    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "expires_in": 3600,
        "citizen": {
            "id": str(citizen.id),
            "full_name": citizen.full_name,
            "id_number": citizen.id_number,
        },
    }
