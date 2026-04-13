"""Reverse proxy for Mock VNeID — routes /vneid/* to the mock-vneid container."""

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response

from src.config import settings

router = APIRouter(prefix="/vneid", tags=["vneid-proxy"])


@router.api_route("/{path:path}", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def proxy_vneid(path: str, request: Request):
    """Proxy requests to the mock VNeID OAuth server."""
    target = f"{settings.vneid_base_url}/{path}"

    # Forward query params
    if request.url.query:
        target += f"?{request.url.query}"

    # Forward body for POST
    body = await request.body() if request.method in ("POST", "PUT", "PATCH") else None

    # Forward relevant headers
    headers = {}
    for key in ("content-type", "authorization", "accept"):
        if key in request.headers:
            headers[key] = request.headers[key]

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
        resp = await client.request(
            method=request.method,
            url=target,
            content=body,
            headers=headers,
        )

    # For redirects, rewrite Location to go through /vneid/ proxy
    response_headers = dict(resp.headers)
    if "location" in response_headers:
        # Don't rewrite callback redirects (they go to the app)
        location = response_headers["location"]
        if not location.startswith(("citizen-app://", "http://localhost", "https://")):
            response_headers["location"] = location

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers,
        media_type=resp.headers.get("content-type"),
    )
