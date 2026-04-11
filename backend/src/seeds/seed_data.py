"""Seed database with initial DocumentType definitions and RoutingRule configurations."""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import async_session_factory
from src.models.case_type import CaseType, CaseTypeRoutingStep
from src.models.department import Department
from src.models.document_requirement import DocumentRequirementGroup, DocumentRequirementSlot
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

    case_types_result = await seed_case_types(db, dept_map)

    return {
        "departments_created": created_depts,
        "document_types_created": created_types,
        "routing_rules_created": created_rules,
        **case_types_result,
    }


# ---------------------------------------------------------------------------
# Case type seed data
# ---------------------------------------------------------------------------

CASE_TYPES = [
    {
        "name": "Đăng ký hộ kinh doanh cá thể",
        "code": "HOUSEHOLD_BIZ_REG",
        "description": "Hồ sơ đăng ký hộ kinh doanh cá thể tại UBND cấp huyện/quận.",
        "retention_years": 10,
        "retention_permanent": False,
        "routing": ["RECEPTION", "ADMIN"],
        "groups": [
            {
                "group_order": 1,
                "label": "Bản sao Hộ khẩu",
                "is_mandatory": True,
                "slots": [{"doc_code": "HOUSEHOLD_REG", "label_override": None}],
            },
            {
                "group_order": 2,
                "label": "CMND / CCCD / Hộ chiếu công chứng",
                "is_mandatory": True,
                "slots": [{"doc_code": "MARITAL_STATUS", "label_override": "CMND/CCCD/Hộ chiếu"}],
            },
            {
                "group_order": 3,
                "label": "Giấy tờ địa điểm kinh doanh",
                "is_mandatory": True,
                "slots": [
                    {"doc_code": "COMPLAINT", "label_override": "Hợp đồng thuê địa điểm kinh doanh"},
                    {"doc_code": "BIRTH_CERT", "label_override": "Giấy chủ quyền nhà / đất"},
                ],
            },
            {
                "group_order": 4,
                "label": "Giấy đề nghị đăng ký hộ kinh doanh",
                "is_mandatory": True,
                "slots": [{"doc_code": "COMPLAINT", "label_override": "Đơn đề nghị đăng ký hộ kinh doanh"}],
            },
        ],
    },
    {
        "name": "Đăng ký doanh nghiệp (Công ty TNHH/Cổ phần/Hợp danh)",
        "code": "COMPANY_REG",
        "description": "Hồ sơ đăng ký thành lập doanh nghiệp.",
        "retention_years": 20,
        "retention_permanent": False,
        "routing": ["RECEPTION", "ADMIN", "JUDICIAL"],
        "groups": [
            {
                "group_order": 1,
                "label": "Giấy đề nghị đăng ký doanh nghiệp",
                "is_mandatory": True,
                "slots": [{"doc_code": "COMPLAINT", "label_override": "Đơn đăng ký thành lập doanh nghiệp"}],
            },
            {
                "group_order": 2,
                "label": "Điều lệ công ty",
                "is_mandatory": True,
                "slots": [{"doc_code": "CLASSIFIED_RPT", "label_override": "Điều lệ công ty"}],
            },
            {
                "group_order": 3,
                "label": "Danh sách thành viên / cổ đông sáng lập",
                "is_mandatory": True,
                "slots": [{"doc_code": "HOUSEHOLD_REG", "label_override": "Danh sách thành viên/cổ đông có chữ ký"}],
            },
            {
                "group_order": 4,
                "label": "CMND/CCCD/Hộ chiếu các thành viên",
                "is_mandatory": True,
                "slots": [{"doc_code": "MARITAL_STATUS", "label_override": "CMND/CCCD/Hộ chiếu hợp lệ"}],
            },
        ],
    },
    {
        "name": "Đăng ký khai sinh",
        "code": "BIRTH_CERT",
        "description": "Hồ sơ đăng ký khai sinh cho trẻ em.",
        "retention_years": 75,
        "retention_permanent": False,
        "routing": ["RECEPTION", "JUDICIAL"],
        "groups": [
            {
                "group_order": 1,
                "label": "Tờ khai đăng ký khai sinh",
                "is_mandatory": True,
                "slots": [{"doc_code": "BIRTH_CERT", "label_override": "Tờ khai theo mẫu"}],
            },
            {
                "group_order": 2,
                "label": "CMND/CCCD của cha hoặc mẹ",
                "is_mandatory": True,
                "slots": [{"doc_code": "MARITAL_STATUS", "label_override": "CMND/CCCD bố hoặc mẹ"}],
            },
            {
                "group_order": 3,
                "label": "Giấy chứng nhận kết hôn (nếu có)",
                "is_mandatory": False,
                "slots": [{"doc_code": "MARITAL_STATUS", "label_override": "Giấy chứng nhận kết hôn"}],
            },
        ],
    },
    {
        "name": "Đăng ký hộ khẩu",
        "code": "HOUSEHOLD_REG",
        "description": "Hồ sơ đăng ký hộ khẩu thường trú.",
        "retention_years": 10,
        "retention_permanent": False,
        "routing": ["RECEPTION", "ADMIN"],
        "groups": [
            {
                "group_order": 1,
                "label": "Đơn đề nghị đăng ký hộ khẩu",
                "is_mandatory": True,
                "slots": [{"doc_code": "HOUSEHOLD_REG", "label_override": "Đơn đề nghị theo mẫu"}],
            },
            {
                "group_order": 2,
                "label": "CMND/CCCD",
                "is_mandatory": True,
                "slots": [{"doc_code": "MARITAL_STATUS", "label_override": "CMND/CCCD còn hiệu lực"}],
            },
            {
                "group_order": 3,
                "label": "Giấy tờ về chỗ ở hợp pháp",
                "is_mandatory": True,
                "slots": [
                    {"doc_code": "COMPLAINT", "label_override": "Hợp đồng thuê nhà"},
                    {"doc_code": "BIRTH_CERT", "label_override": "Giấy chứng nhận quyền sử dụng đất/nhà"},
                ],
            },
        ],
    },
    {
        "name": "Xác nhận tình trạng hôn nhân",
        "code": "MARITAL_STATUS",
        "description": "Hồ sơ xin xác nhận tình trạng hôn nhân.",
        "retention_years": 20,
        "retention_permanent": False,
        "routing": ["RECEPTION", "JUDICIAL"],
        "groups": [
            {
                "group_order": 1,
                "label": "Đơn xin xác nhận tình trạng hôn nhân",
                "is_mandatory": True,
                "slots": [{"doc_code": "MARITAL_STATUS", "label_override": "Đơn theo mẫu"}],
            },
            {
                "group_order": 2,
                "label": "CMND/CCCD",
                "is_mandatory": True,
                "slots": [{"doc_code": "MARITAL_STATUS", "label_override": "CMND/CCCD còn hiệu lực"}],
            },
            {
                "group_order": 3,
                "label": "Bản sao Hộ khẩu",
                "is_mandatory": True,
                "slots": [{"doc_code": "HOUSEHOLD_REG", "label_override": None}],
            },
        ],
    },
]


async def seed_case_types(db: AsyncSession, dept_map: dict | None = None) -> dict:
    """Seed CaseType, DocumentRequirementGroup, DocumentRequirementSlot, CaseTypeRoutingStep.

    Idempotent: skips any case type whose code already exists.
    dept_map: optional dict of dept_code -> dept_id; fetched fresh if not provided.
    """
    if dept_map is None:
        result = await db.execute(select(Department))
        dept_map = {d.code: d.id for d in result.scalars().all()}

    # Build doc_type code -> id map
    dt_result = await db.execute(select(DocumentType))
    dt_map = {dt.code: dt.id for dt in dt_result.scalars().all()}

    created_case_types = 0
    created_groups = 0
    created_slots = 0
    created_routing_steps = 0

    for ct_data in CASE_TYPES:
        existing = await db.execute(select(CaseType).where(CaseType.code == ct_data["code"]))
        if existing.scalar_one_or_none() is not None:
            continue

        case_type = CaseType(
            name=ct_data["name"],
            code=ct_data["code"],
            description=ct_data.get("description"),
            retention_years=ct_data["retention_years"],
            retention_permanent=ct_data["retention_permanent"],
        )
        db.add(case_type)
        await db.flush()
        created_case_types += 1

        # Requirement groups + slots
        for group_data in ct_data["groups"]:
            group = DocumentRequirementGroup(
                case_type_id=case_type.id,
                group_order=group_data["group_order"],
                label=group_data["label"],
                is_mandatory=group_data["is_mandatory"],
            )
            db.add(group)
            await db.flush()
            created_groups += 1

            for slot_data in group_data["slots"]:
                doc_type_id = dt_map.get(slot_data["doc_code"])
                if doc_type_id is None:
                    continue  # doc type not yet seeded, skip
                slot = DocumentRequirementSlot(
                    group_id=group.id,
                    document_type_id=doc_type_id,
                    label_override=slot_data.get("label_override"),
                )
                db.add(slot)
                created_slots += 1

        # Routing steps
        for i, dept_code in enumerate(ct_data["routing"], start=1):
            dept_id = dept_map.get(dept_code)
            if dept_id is None:
                continue
            step = CaseTypeRoutingStep(
                case_type_id=case_type.id,
                department_id=dept_id,
                step_order=i,
                expected_duration_hours=48 if i == 1 else 72,
                required_clearance_level=0,
            )
            db.add(step)
            created_routing_steps += 1

    await db.commit()
    return {
        "case_types_created": created_case_types,
        "requirement_groups_created": created_groups,
        "requirement_slots_created": created_slots,
        "case_type_routing_steps_created": created_routing_steps,
    }


async def main():
    async with async_session_factory() as db:
        result = await seed(db)
        print(f"Seed complete: {result}")

if __name__ == "__main__":
    asyncio.run(main())
