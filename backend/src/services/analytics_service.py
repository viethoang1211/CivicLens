import uuid
from datetime import UTC, date, datetime

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.department import Department
from src.models.workflow_step import WorkflowStep


async def get_sla_metrics(
    db: AsyncSession,
    date_from: date,
    date_to: date,
    department_id: uuid.UUID | None = None,
) -> dict:
    """Compute SLA analytics grouped by department."""
    now = datetime.now(UTC)

    # Base filter: steps created within date range
    base_filter = [
        WorkflowStep.created_at >= datetime.combine(date_from, datetime.min.time()).replace(tzinfo=UTC),
        WorkflowStep.created_at <= datetime.combine(date_to, datetime.max.time()).replace(tzinfo=UTC),
    ]
    if department_id:
        base_filter.append(WorkflowStep.department_id == department_id)

    # Delayed: completed late OR pending and overdue
    delayed_case = case(
        (
            and_(
                WorkflowStep.status == "completed",
                WorkflowStep.completed_at > WorkflowStep.expected_complete_by,
                WorkflowStep.expected_complete_by.isnot(None),
            ),
            1,
        ),
        (
            and_(
                WorkflowStep.status.in_(["pending", "active"]),
                WorkflowStep.expected_complete_by.isnot(None),
                WorkflowStep.expected_complete_by < now,
            ),
            1,
        ),
        else_=0,
    )

    # Processing hours for completed steps
    processing_hours = func.extract(
        "epoch",
        WorkflowStep.completed_at - WorkflowStep.started_at,
    ) / 3600.0

    query = (
        select(
            WorkflowStep.department_id,
            Department.name.label("department_name"),
            Department.code.label("department_code"),
            func.count(WorkflowStep.id).label("total_steps"),
            func.count(WorkflowStep.id).filter(WorkflowStep.status == "completed").label("completed_steps"),
            func.count(WorkflowStep.id).filter(WorkflowStep.status.in_(["pending", "active"])).label("pending_steps"),
            func.sum(delayed_case).label("delayed_steps"),
            func.avg(processing_hours).filter(
                WorkflowStep.status == "completed",
                WorkflowStep.started_at.isnot(None),
                WorkflowStep.completed_at.isnot(None),
            ).label("avg_processing_hours"),
        )
        .join(Department, Department.id == WorkflowStep.department_id)
        .where(*base_filter)
        .group_by(WorkflowStep.department_id, Department.name, Department.code)
    )

    result = await db.execute(query)
    rows = result.all()

    departments = []
    totals = {
        "total_steps": 0,
        "completed_steps": 0,
        "pending_steps": 0,
        "delayed_steps": 0,
        "avg_processing_hours": 0.0,
    }
    all_hours = []

    for row in rows:
        total = row.total_steps or 0
        completed = row.completed_steps or 0
        pending = row.pending_steps or 0
        delayed = int(row.delayed_steps or 0)
        avg_hours = float(row.avg_processing_hours) if row.avg_processing_hours else 0.0

        dept = {
            "department_id": str(row.department_id),
            "department_name": row.department_name,
            "department_code": row.department_code,
            "metrics": {
                "total_steps": total,
                "completed_steps": completed,
                "pending_steps": pending,
                "delayed_steps": delayed,
                "avg_processing_hours": round(avg_hours, 1),
                "delay_rate": round(delayed / total, 3) if total > 0 else 0.0,
                "completion_rate": round(completed / total, 3) if total > 0 else 0.0,
            },
        }
        departments.append(dept)

        totals["total_steps"] += total
        totals["completed_steps"] += completed
        totals["pending_steps"] += pending
        totals["delayed_steps"] += delayed
        if avg_hours > 0:
            all_hours.append(avg_hours)

    if all_hours:
        totals["avg_processing_hours"] = round(sum(all_hours) / len(all_hours), 1)
    if totals["total_steps"] > 0:
        totals["delay_rate"] = round(totals["delayed_steps"] / totals["total_steps"], 3)
        totals["completion_rate"] = round(totals["completed_steps"] / totals["total_steps"], 3)
    else:
        totals["delay_rate"] = 0.0
        totals["completion_rate"] = 0.0

    return {
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
        },
        "departments": departments,
        "totals": totals,
    }
