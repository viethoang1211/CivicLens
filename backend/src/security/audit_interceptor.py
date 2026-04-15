"""FastAPI middleware that automatically logs all staff API actions to the audit log."""

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseCallType
from starlette.requests import Request
from starlette.responses import Response

from src.dependencies import async_session_factory
from src.services.audit_service import log_access

# Patterns that trigger automatic audit logging
_AUDITED_PREFIXES = ("/v1/staff/",)

# Map HTTP methods to action verbs
_METHOD_ACTIONS = {
    "GET": "view",
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}


class AuditInterceptor(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseCallType) -> Response:
        response = await call_next(request)

        # Only audit staff endpoints with successful responses
        if not any(request.url.path.startswith(p) for p in _AUDITED_PREFIXES):
            return response

        if response.status_code >= 400:
            return response

        # Extract identity from request state (set by auth dependency)
        staff_id = getattr(request.state, "staff_id", None) if hasattr(request, "state") else None
        if staff_id is None:
            return response

        action = _METHOD_ACTIONS.get(request.method, request.method.lower())
        resource_type = _extract_resource_type(request.url.path)

        try:
            async with async_session_factory() as db:
                await log_access(
                    db=db,
                    actor_type="staff",
                    actor_id=staff_id,
                    action=f"api_{action}",
                    resource_type=resource_type,
                    resource_id=None,
                    metadata={"path": request.url.path, "method": request.method},
                )
                await db.commit()
        except Exception:
            logging.getLogger(__name__).exception("Audit logging failed")

        return response


def _extract_resource_type(path: str) -> str:
    """Extract a resource type from the URL path."""
    parts = path.strip("/").split("/")
    # /v1/staff/{resource} → resource
    if len(parts) >= 3:
        return parts[2]
    return "unknown"
