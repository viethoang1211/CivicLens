import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.dependencies import get_db
from src.models.dossier import Dossier
from src.models.workflow_step import WorkflowStep
from src.security.auth import CitizenIdentity, get_current_citizen

router = APIRouter(prefix="/v1/citizen/dossiers", tags=["citizen-dossiers"])

_STATUS_LABELS_VI = {
    "draft": "Đang soạn thảo",
    "scanning": "Đang quét tài liệu",
    "ready": "Sẵn sàng nộp",
    "submitted": "Đã tiếp nhận",
    "in_progress": "Đang xử lý",
    "pending_routing": "Chờ phân tuyến",
    "completed": "Hoàn thành",
    "rejected": "Bị trả lại",
}


def _build_workflow_steps(workflow_steps: list) -> list[dict]:
    return [
        {
            "step_order": ws.step_order,
            "department_id": str(ws.department_id),
            "department_name": ws.department.name if ws.department else None,
            "status": ws.status,
            "status_label_vi": _STATUS_LABELS_VI.get(ws.status, ws.status),
            "started_at": ws.started_at.isoformat() if ws.started_at else None,
            "completed_at": ws.completed_at.isoformat() if ws.completed_at else None,
            "expected_complete_by": ws.expected_complete_by.isoformat() if ws.expected_complete_by else None,
        }
        for ws in sorted(workflow_steps, key=lambda s: s.step_order)
    ]


def _build_tracking_response(dossier: Dossier, include_id: bool = True) -> dict:
    active_step = next(
        (ws for ws in sorted(dossier.workflow_steps, key=lambda s: s.step_order) if ws.status == "active"),
        None,
    )
    out = {
        "status": dossier.status,
        "status_label_vi": _STATUS_LABELS_VI.get(dossier.status, dossier.status),
        "reference_number": dossier.reference_number,
        "case_type_name": dossier.case_type.name if dossier.case_type else None,
        "current_department_id": str(active_step.department_id) if active_step else None,
        "submitted_at": dossier.submitted_at.isoformat() if dossier.submitted_at else None,
        "completed_at": dossier.completed_at.isoformat() if dossier.completed_at else None,
        "rejection_reason": dossier.rejection_reason,
        "estimated_completion": (
            active_step.expected_complete_by.isoformat() if active_step and active_step.expected_complete_by else None
        ),
        "workflow_steps": _build_workflow_steps(dossier.workflow_steps),
    }
    if include_id:
        out["id"] = str(dossier.id)
    return out


async def _load_dossier_tracking(dossier_id: uuid.UUID, db: AsyncSession) -> Dossier:
    result = await db.execute(
        select(Dossier)
        .where(Dossier.id == dossier_id)
        .options(
            selectinload(Dossier.case_type),
            selectinload(Dossier.workflow_steps).selectinload(WorkflowStep.department),
        )
    )
    dossier = result.scalar_one_or_none()
    if dossier is None:
        raise HTTPException(status_code=404, detail="Dossier not found")
    return dossier


# ---------------------------------------------------------------------------
# GET /v1/citizen/dossiers  (auth required)
# ---------------------------------------------------------------------------

@router.get("")
async def list_citizen_dossiers(
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    citizen: CitizenIdentity = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Dossier)
        .where(Dossier.citizen_id == citizen.citizen_id)
        .options(
            selectinload(Dossier.case_type),
            selectinload(Dossier.workflow_steps).selectinload(WorkflowStep.department),
        )
        .order_by(Dossier.created_at.desc())
    )
    if status_filter:
        query = query.where(Dossier.status == status_filter)

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    dossiers = result.scalars().all()

    items = []
    for d in dossiers:
        active_step = next(
            (ws for ws in sorted(d.workflow_steps, key=lambda s: s.step_order) if ws.status == "active"), None
        )
        items.append({
            "id": str(d.id),
            "reference_number": d.reference_number,
            "case_type_name": d.case_type.name if d.case_type else None,
            "status": d.status,
            "status_label_vi": _STATUS_LABELS_VI.get(d.status, d.status),
            "current_department_id": str(active_step.department_id) if active_step else None,
            "priority": d.priority,
            "submitted_at": d.submitted_at.isoformat() if d.submitted_at else None,
            "estimated_completion": (
                active_step.expected_complete_by.isoformat()
                if active_step and active_step.expected_complete_by
                else None
            ),
        })

    return {"page": page, "page_size": page_size, "items": items}


# ---------------------------------------------------------------------------
# GET /v1/citizen/dossiers/lookup  (public — no auth; rate-limited at infra)
# ---------------------------------------------------------------------------

@router.get("/lookup")
async def lookup_dossier(
    reference_number: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Dossier)
        .where(Dossier.reference_number == reference_number)
        .options(
            selectinload(Dossier.case_type),
            selectinload(Dossier.workflow_steps).selectinload(WorkflowStep.department),
        )
    )
    dossier = result.scalar_one_or_none()
    if dossier is None:
        raise HTTPException(status_code=404, detail="Reference number not found")
    # Omit UUID to prevent enumeration
    return _build_tracking_response(dossier, include_id=False)


# ---------------------------------------------------------------------------
# GET /v1/citizen/dossiers/{dossier_id}  (auth required, owned by citizen)
# ---------------------------------------------------------------------------

@router.get("/{dossier_id}")
async def get_citizen_dossier(
    dossier_id: uuid.UUID,
    citizen: CitizenIdentity = Depends(get_current_citizen),
    db: AsyncSession = Depends(get_db),
):
    dossier = await _load_dossier_tracking(dossier_id, db)
    if dossier.citizen_id != citizen.citizen_id:
        raise HTTPException(status_code=404, detail="Dossier not found")
    return _build_tracking_response(dossier, include_id=True)
