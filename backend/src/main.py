from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api import vneid_proxy
from src.api.citizen import auth as citizen_auth
from src.api.citizen import dossier as citizen_dossier
from src.api.citizen import notifications as citizen_notifications
from src.api.citizen import submissions as citizen_submissions
from src.api.staff import admin_case_types as staff_admin_case_types
from src.api.staff import admin_document_types, admin_routing_rules
from src.api.staff import analytics as staff_analytics
from src.api.staff import audit as staff_audit
from src.api.staff import auth as staff_auth
from src.api.staff import classification as staff_classification
from src.api.staff import departments as staff_departments
from src.api.staff import dossier as staff_dossier
from src.api.staff import routing as staff_routing
from src.api.staff import search as staff_search
from src.api.staff import submissions as staff_submissions
from src.api.staff import workflow_steps as staff_workflow_steps
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Public Sector Document Processing API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Staff routes
app.include_router(staff_auth.router, prefix="/v1/staff/auth", tags=["staff-auth"])
app.include_router(staff_submissions.router, prefix="/v1/staff/submissions", tags=["staff-submissions"])
app.include_router(staff_classification.router, prefix="/v1/staff/submissions", tags=["staff-classification"])
app.include_router(staff_routing.router, prefix="/v1/staff/submissions", tags=["staff-routing"])
app.include_router(staff_departments.router, prefix="/v1/staff/departments", tags=["staff-departments"])
app.include_router(staff_workflow_steps.router, prefix="/v1/staff/workflow-steps", tags=["staff-workflow-steps"])
app.include_router(admin_document_types.router, prefix="/v1/staff/admin/document-types", tags=["admin-document-types"])
app.include_router(admin_routing_rules.router, prefix="/v1/staff/admin/routing-rules", tags=["admin-routing-rules"])
app.include_router(staff_admin_case_types.router)
app.include_router(staff_dossier.router)
app.include_router(staff_search.router, prefix="/v1/staff/search", tags=["staff-search"])
app.include_router(staff_analytics.router, prefix="/v1/staff/analytics", tags=["staff-analytics"])
app.include_router(staff_audit.router, prefix="/v1/staff/audit", tags=["staff-audit"])

# Citizen routes
app.include_router(citizen_auth.router, prefix="/v1/citizen/auth", tags=["citizen-auth"])
app.include_router(citizen_submissions.router, prefix="/v1/citizen/submissions", tags=["citizen-submissions"])
app.include_router(citizen_notifications.router, prefix="/v1/citizen/notifications", tags=["citizen-notifications"])
app.include_router(citizen_dossier.router)

# Mock VNeID proxy (routes /vneid/* → mock-vneid container)
app.include_router(vneid_proxy.router)

# Serve uploaded files when using local storage
if settings.storage_backend == "local":
    import os
    os.makedirs(settings.local_storage_path, exist_ok=True)
    app.mount("/files", StaticFiles(directory=settings.local_storage_path), name="uploads")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "An unexpected error occurred."},
    )
