import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.case_type import CaseTypeRoutingStep
from src.models.department import Department
from src.models.document_requirement import DocumentRequirementGroup
from src.models.dossier import Dossier
from src.models.dossier_document import DossierDocument
from src.models.staff_member import StaffMember
from src.models.workflow_step import WorkflowStep


async def check_completeness(dossier_id: uuid.UUID, db: AsyncSession) -> dict:
    """Return completeness status for a dossier.

    A dossier is complete when every mandatory DocumentRequirementGroup has at
    least one DossierDocument linked to one of its slots.
    """
    # Load the dossier to get case_type_id
    dossier_result = await db.execute(select(Dossier).where(Dossier.id == dossier_id))
    dossier = dossier_result.scalar_one_or_none()
    if dossier is None:
        return {"complete": False, "missing_groups": []}

    # Load all mandatory groups for this case type, eager-loading slots
    from sqlalchemy.orm import selectinload

    groups_result = await db.execute(
        select(DocumentRequirementGroup)
        .where(
            DocumentRequirementGroup.case_type_id == dossier.case_type_id,
            DocumentRequirementGroup.is_mandatory.is_(True),
        )
        .options(selectinload(DocumentRequirementGroup.slots))
    )
    groups = groups_result.scalars().all()

    # Load all dossier documents with their slot IDs
    docs_result = await db.execute(
        select(DossierDocument.requirement_slot_id).where(
            DossierDocument.dossier_id == dossier_id,
            DossierDocument.requirement_slot_id.is_not(None),
        )
    )
    fulfilled_slot_ids = {row[0] for row in docs_result.all()}

    missing_groups = []
    for group in groups:
        slot_ids = {slot.id for slot in group.slots}
        if not slot_ids.intersection(fulfilled_slot_ids):
            missing_groups.append({"group_id": str(group.id), "label": group.label})

    return {"complete": len(missing_groups) == 0, "missing_groups": missing_groups}


async def generate_reference_number(db: AsyncSession, submitted_date: date) -> str:
    """Generate a unique citizen-friendly reference number: HS-YYYYMMDD-NNNNN.

    Uses a transactional COUNT to determine the daily sequence number.
    Safe for low-to-moderate concurrency (< 1000 submissions/day/office).
    """
    date_str = submitted_date.strftime("%Y%m%d")
    start_of_day = datetime.combine(submitted_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_of_day = start_of_day + timedelta(days=1)

    count_result = await db.execute(
        select(func.count(Dossier.id)).where(
            Dossier.submitted_at >= start_of_day,
            Dossier.submitted_at < end_of_day,
            Dossier.reference_number.is_not(None),
        )
    )
    daily_count = count_result.scalar_one()
    sequence = daily_count + 1
    return f"HS-{date_str}-{sequence:05d}"


async def create_dossier_workflow(dossier: Dossier, db: AsyncSession) -> dict:
    """Create WorkflowStep rows for a dossier based on its CaseType routing steps."""
    result = await db.execute(
        select(CaseTypeRoutingStep)
        .where(CaseTypeRoutingStep.case_type_id == dossier.case_type_id)
        .order_by(CaseTypeRoutingStep.step_order)
    )
    routing_steps = result.scalars().all()

    if not routing_steps:
        dossier.status = "pending_routing"
        await db.commit()
        return {
            "dossier_id": str(dossier.id),
            "status": "pending_routing",
            "message": "No routing steps configured for this case type. Manual routing required.",
            "workflow_steps": [],
        }

    # Validate clearance availability per department
    for step in routing_steps:
        staff_result = await db.execute(
            select(StaffMember).where(
                StaffMember.department_id == step.department_id,
                StaffMember.clearance_level >= dossier.security_classification,
                StaffMember.is_active.is_(True),
            )
        )
        if not staff_result.scalars().first():
            raise ValueError(
                f"Department for step {step.step_order} has no staff with clearance level "
                f">= {dossier.security_classification}"
            )

    now = datetime.now(timezone.utc)
    steps_out = []

    for i, step in enumerate(routing_steps):
        dept_result = await db.execute(select(Department).where(Department.id == step.department_id))
        dept = dept_result.scalar_one()

        is_first = i == 0
        workflow_step = WorkflowStep(
            dossier_id=dossier.id,
            department_id=step.department_id,
            step_order=step.step_order,
            status="active" if is_first else "pending",
            started_at=now if is_first else None,
            expected_complete_by=(
                now + timedelta(hours=step.expected_duration_hours)
                if is_first and step.expected_duration_hours
                else None
            ),
        )
        db.add(workflow_step)
        steps_out.append({
            "step_order": step.step_order,
            "department": dept.name,
            "status": "active" if is_first else "pending",
        })

    return {
        "dossier_id": str(dossier.id),
        "status": "in_progress",
        "first_department": steps_out[0]["department"] if steps_out else None,
        "workflow_steps": steps_out,
    }
