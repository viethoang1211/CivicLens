from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from src.config import settings
from src.dependencies import get_db
from src.models.citizen import Citizen
from src.security.auth import create_access_token, create_refresh_token

router = APIRouter()


class VNeIDAuthRequest(BaseModel):
    vneid_auth_code: str
    redirect_uri: str


@router.post("/vneid")
async def vneid_auth(body: VNeIDAuthRequest, db: AsyncSession = Depends(get_db)):
    """Exchange VNeID authorization code for app JWT via OAuth2 code flow."""

    # Step 1: Exchange auth code with VNeID OAuth server for access token
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(
            f"{settings.vneid_base_url}/oauth/token",
            json={
                "grant_type": "authorization_code",
                "code": body.vneid_auth_code,
                "redirect_uri": body.redirect_uri,
                "client_id": settings.vneid_client_id,
                "client_secret": settings.vneid_client_secret,
            },
        )

    if token_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="vneid_auth_failed",
        )

    token_data = token_resp.json()
    vneid_access_token = token_data["access_token"]

    # Step 2: Fetch citizen info from VNeID userinfo endpoint
    async with httpx.AsyncClient(timeout=10.0) as client:
        userinfo_resp = await client.get(
            f"{settings.vneid_base_url}/oauth/userinfo",
            headers={"Authorization": f"Bearer {vneid_access_token}"},
        )

    if userinfo_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="vneid_userinfo_failed",
        )

    vneid_user = userinfo_resp.json()
    id_number = vneid_user["id_number"]
    full_name = vneid_user["full_name"]
    phone_number = vneid_user.get("phone_number")

    # Step 3: Find or create citizen
    result = await db.execute(select(Citizen).where(Citizen.id_number == id_number))
    citizen = result.scalar_one_or_none()

    if citizen is None:
        citizen = Citizen(
            vneid_subject_id=vneid_user.get("sub", id_number),
            full_name=full_name,
            id_number=id_number,
            phone_number=phone_number,
        )
        db.add(citizen)
        await db.commit()
        await db.refresh(citizen)
    else:
        # Update name/phone from VNeID in case it changed
        citizen.full_name = full_name
        if phone_number:
            citizen.phone_number = phone_number
        await db.commit()

    app_token_data = {"sub": str(citizen.id), "type": "citizen"}

    return {
        "access_token": create_access_token(app_token_data),
        "refresh_token": create_refresh_token(app_token_data),
        "expires_in": settings.jwt_access_token_expire_minutes * 60,
        "citizen": {
            "id": str(citizen.id),
            "full_name": citizen.full_name,
            "id_number": citizen.id_number,
        },
    }


@router.get("/vneid/authorize-url")
async def get_authorize_url(redirect_uri: str, request: Request):
    """Returns the VNeID OAuth authorize URL for the client to open in browser."""
    import secrets
    state = secrets.token_urlsafe(16)
    # Build URL through the /vneid/ proxy on the same host so the browser
    # can reach the mock VNeID login page via port 80 (SLB).
    base_url = str(request.base_url).rstrip("/")
    url = (
        f"{base_url}/vneid/authorize"
        f"?client_id={settings.vneid_client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&state={state}"
    )
    return {"authorize_url": url, "state": state}
