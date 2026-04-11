"""Seed database with initial DocumentType definitions and RoutingRule configurations."""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import async_session_factory
from src.models.department import Department
from src.models.document_type import DocumentType
from src.models.routing_rule import RoutingRule


DEPARTMENTS = [
    {"name": "Tiếp nhận (Reception)", "code": "RECEPTION", "min_clearance_level": 0},
    {"name": "Phòng Hành chính (Administrative)", "code": "ADMIN", "min_clearance_level": 0},
    {"name": "Phòng Tư pháp (Judicial)", "code": "JUDICIAL", "min_clearance_level": 1},
    {"name": "Phòng Tài chính (Finance)", "code": "FINANCE", "min_clearance_level": 0},
    {"name": "Phòng Nội vụ (Internal Affairs)", "code": "INTERNAL", "min_clearance_level": 2},
    {"name": "Lãnh đạo (Leadership)", "code": "LEADERSHIP", "min_clearance_level": 2},
]

DOCUMENT_TYPES = [
    {
        "name": "Đơn xin cấp giấy khai sinh (Birth Certificate Application)",
        "code": "BIRTH_CERT",
        "retention_years": 75,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "child_name": {"type": "string"},
                "date_of_birth": {"type": "string"},
                "place_of_birth": {"type": "string"},
                "father_name": {"type": "string"},
                "mother_name": {"type": "string"},
            },
        },
        "classification_prompt": "Identify birth certificate applications with fields: child name, DOB, place, parents.",
        "route": ["RECEPTION", "JUDICIAL"],
    },
    {
        "name": "Đơn xin cấp giấy chứng nhận hộ khẩu (Household Registration)",
        "code": "HOUSEHOLD_REG",
        "retention_years": 10,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "applicant_name": {"type": "string"},
                "address": {"type": "string"},
                "household_members": {"type": "integer"},
            },
        },
        "classification_prompt": "Identify household registration applications with address and member count.",
        "route": ["RECEPTION", "ADMIN"],
    },
    {
        "name": "Đơn xin xác nhận tình trạng hôn nhân (Marital Status Confirmation)",
        "code": "MARITAL_STATUS",
        "retention_years": 20,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "applicant_name": {"type": "string"},
                "id_number": {"type": "string"},
                "current_status": {"type": "string"},
            },
        },
        "classification_prompt": "Identify marital status confirmation with applicant identity and status.",
        "route": ["RECEPTION", "JUDICIAL"],
    },
    {
        "name": "Báo cáo mật (Classified Report)",
        "code": "CLASSIFIED_RPT",
        "retention_years": 0,
        "retention_permanent": True,
        "template_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "classification_level": {"type": "integer"},
                "originating_department": {"type": "string"},
            },
        },
        "classification_prompt": "Identify classified government reports requiring elevated clearance.",
        "route": ["RECEPTION", "INTERNAL", "LEADERSHIP"],
    },
    {
        "name": "Đơn khiếu nại (Complaint/Petition)",
        "code": "COMPLAINT",
        "retention_years": 5,
        "retention_permanent": False,
        "template_schema": {
            "type": "object",
            "properties": {
                "complainant_name": {"type": "string"},
                "subject": {"type": "string"},
                "description": {"type": "string"},
            },
        },
        "classification_prompt": "Identify citizen complaints and petitions with subject and description.",
        "route": ["RECEPTION", "ADMIN", "LEADERSHIP"],
    },
]


async def seed(db: AsyncSession) -> dict:
    """Insert seed data. Skips existing records by code."""
    created_depts = 0
    created_types = 0
    created_rules = 0

    # Seed departments
    dept_map = {}
    for dept_data in DEPARTMENTS:
        existing = await db.execute(select(Department).where(Department.code == dept_data["code"]))
        dept = existing.scalar_one_or_none()
        if dept is None:
            dept = Department(**dept_data)
            db.add(dept)
            await db.flush()
            created_depts += 1
        dept_map[dept_data["code"]] = dept.id

    # Seed document types and routing rules
    for dt_data in DOCUMENT_TYPES:
        route_codes = dt_data.pop("route")
        existing = await db.execute(select(DocumentType).where(DocumentType.code == dt_data["code"]))
        doc_type = existing.scalar_one_or_none()
        if doc_type is None:
            doc_type = DocumentType(**dt_data)
            db.add(doc_type)
            await db.flush()
            created_types += 1

            # Create routing rules
            for i, dept_code in enumerate(route_codes, start=1):
                rule = RoutingRule(
                    document_type_id=doc_type.id,
                    department_id=dept_map[dept_code],
                    step_order=i,
                    expected_duration_hours=48 if i == 1 else 72,
                    required_clearance_level=0,
                )
                db.add(rule)
                created_rules += 1

    await db.commit()
    return {
        "departments_created": created_depts,
        "document_types_created": created_types,
        "routing_rules_created": created_rules,
    }


async def main():
    async with async_session_factory() as db:
        result = await seed(db)
        print(f"Seed complete: {result}")


if __name__ == "__main__":
    asyncio.run(main())
