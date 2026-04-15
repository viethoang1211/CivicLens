import uuid
from datetime import date

from sqlalchemy import func, literal, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.case_type import CaseType
from src.models.citizen import Citizen
from src.models.document_type import DocumentType
from src.models.dossier import Dossier
from src.models.dossier_document import DossierDocument
from src.models.scanned_page import ScannedPage
from src.models.submission import Submission
from src.models.workflow_step import WorkflowStep


async def search(
    db: AsyncSession,
    query: str,
    clearance_level: int,
    status: str | None = None,
    document_type_code: str | None = None,
    case_type_code: str | None = None,
    department_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort: str = "relevance",
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """Cross-department full-text search with clearance filtering."""
    ts_query = func.plainto_tsquery("simple", func.immutable_unaccent(query))

    # --- Submission results via OCR FTS ---
    sub_rank = func.max(func.ts_rank(ScannedPage.search_vector, ts_query)).label("relevance_score")
    sub_highlight = func.ts_headline(
        "simple",
        func.coalesce(ScannedPage.ocr_corrected_text, ScannedPage.ocr_raw_text, ""),
        ts_query,
        "MaxFragments=1,MaxWords=30,MinWords=10",
    ).label("highlight")

    sub_query = (
        select(
            literal("submission").label("type"),
            Submission.id.label("id"),
            Submission.status.label("status"),
            Submission.submitted_at.label("submitted_at"),
            Citizen.full_name.label("citizen_name"),
            DocumentType.name.label("document_type_name"),
            DocumentType.code.label("document_type_code"),
            literal(None).label("case_type_name"),
            literal(None).label("case_type_code"),
            literal(None).label("reference_number"),
            Submission.ai_summary.label("ai_summary"),
            sub_rank,
            sub_highlight,
        )
        .join(ScannedPage, ScannedPage.submission_id == Submission.id)
        .join(Citizen, Citizen.id == Submission.citizen_id)
        .outerjoin(DocumentType, DocumentType.id == Submission.document_type_id)
        .where(ScannedPage.search_vector.op("@@")(ts_query))
        .where(Submission.security_classification <= clearance_level)
        .group_by(Submission.id, Citizen.full_name, DocumentType.name, DocumentType.code,
                  ScannedPage.ocr_corrected_text, ScannedPage.ocr_raw_text)
    )

    # --- Dossier results via OCR FTS ---
    dos_rank = func.max(func.ts_rank(ScannedPage.search_vector, ts_query)).label("relevance_score")
    dos_highlight = func.ts_headline(
        "simple",
        func.coalesce(ScannedPage.ocr_corrected_text, ScannedPage.ocr_raw_text, ""),
        ts_query,
        "MaxFragments=1,MaxWords=30,MinWords=10",
    ).label("highlight")

    dos_query = (
        select(
            literal("dossier").label("type"),
            Dossier.id.label("id"),
            Dossier.status.label("status"),
            Dossier.submitted_at.label("submitted_at"),
            Citizen.full_name.label("citizen_name"),
            literal(None).label("document_type_name"),
            literal(None).label("document_type_code"),
            CaseType.name.label("case_type_name"),
            CaseType.code.label("case_type_code"),
            Dossier.reference_number.label("reference_number"),
            Dossier.ai_summary.label("ai_summary"),
            dos_rank,
            dos_highlight,
        )
        .join(DossierDocument, DossierDocument.dossier_id == Dossier.id)
        .join(ScannedPage, ScannedPage.dossier_document_id == DossierDocument.id)
        .join(Citizen, Citizen.id == Dossier.citizen_id)
        .outerjoin(CaseType, CaseType.id == Dossier.case_type_id)
        .where(ScannedPage.search_vector.op("@@")(ts_query))
        .where(Dossier.security_classification <= clearance_level)
        .group_by(Dossier.id, Citizen.full_name, CaseType.name, CaseType.code,
                  ScannedPage.ocr_corrected_text, ScannedPage.ocr_raw_text)
    )

    # --- Citizen name / ID / reference number direct search ---
    citizen_sub_query = (
        select(
            literal("submission").label("type"),
            Submission.id.label("id"),
            Submission.status.label("status"),
            Submission.submitted_at.label("submitted_at"),
            Citizen.full_name.label("citizen_name"),
            DocumentType.name.label("document_type_name"),
            DocumentType.code.label("document_type_code"),
            literal(None).label("case_type_name"),
            literal(None).label("case_type_code"),
            literal(None).label("reference_number"),
            Submission.ai_summary.label("ai_summary"),
            literal(0.5).label("relevance_score"),
            literal("").label("highlight"),
        )
        .join(Citizen, Citizen.id == Submission.citizen_id)
        .outerjoin(DocumentType, DocumentType.id == Submission.document_type_id)
        .where(Submission.security_classification <= clearance_level)
        .where(
            (Citizen.id_number == query)
            | (func.immutable_unaccent(Citizen.full_name).ilike(f"%{query}%"))
        )
    )

    citizen_dos_query = (
        select(
            literal("dossier").label("type"),
            Dossier.id.label("id"),
            Dossier.status.label("status"),
            Dossier.submitted_at.label("submitted_at"),
            Citizen.full_name.label("citizen_name"),
            literal(None).label("document_type_name"),
            literal(None).label("document_type_code"),
            CaseType.name.label("case_type_name"),
            CaseType.code.label("case_type_code"),
            Dossier.reference_number.label("reference_number"),
            Dossier.ai_summary.label("ai_summary"),
            literal(0.5).label("relevance_score"),
            literal("").label("highlight"),
        )
        .join(Citizen, Citizen.id == Dossier.citizen_id)
        .outerjoin(CaseType, CaseType.id == Dossier.case_type_id)
        .where(Dossier.security_classification <= clearance_level)
        .where(
            (Citizen.id_number == query)
            | (func.immutable_unaccent(Citizen.full_name).ilike(f"%{query}%"))
            | (Dossier.reference_number == query)
        )
    )

    # Apply structured filters to all sub-queries
    for q_ref in [sub_query, citizen_sub_query]:
        if status:
            q_ref = q_ref.where(Submission.status == status)
        if document_type_code:
            q_ref = q_ref.where(DocumentType.code == document_type_code)
        if date_from:
            q_ref = q_ref.where(Submission.submitted_at >= date_from)
        if date_to:
            q_ref = q_ref.where(Submission.submitted_at <= date_to)
        if department_id:
            q_ref = q_ref.where(
                Submission.id.in_(
                    select(WorkflowStep.submission_id).where(WorkflowStep.department_id == department_id)
                )
            )
        # Re-assign since .where() returns a new object
        if "sub_query" in str(type(q_ref)):
            pass  # handled below

    # Since SQLAlchemy .where returns new objects, we need to rebuild with filters inline
    # Let's use a simpler approach: build filters as lists, then apply
    sub_filters = []
    dos_filters = []
    if status:
        sub_filters.append(Submission.status == status)
        dos_filters.append(Dossier.status == status)
    if document_type_code:
        sub_filters.append(DocumentType.code == document_type_code)
    if case_type_code:
        dos_filters.append(CaseType.code == case_type_code)
    if date_from:
        sub_filters.append(Submission.submitted_at >= date_from)
        dos_filters.append(Dossier.submitted_at >= date_from)
    if date_to:
        sub_filters.append(Submission.submitted_at <= date_to)
        dos_filters.append(Dossier.submitted_at <= date_to)
    if department_id:
        dept_sub_ids = select(WorkflowStep.submission_id).where(
            WorkflowStep.department_id == department_id,
            WorkflowStep.submission_id.isnot(None),
        )
        dept_dos_ids = select(WorkflowStep.dossier_id).where(
            WorkflowStep.department_id == department_id,
            WorkflowStep.dossier_id.isnot(None),
        )
        sub_filters.append(Submission.id.in_(dept_sub_ids))
        dos_filters.append(Dossier.id.in_(dept_dos_ids))

    for f in sub_filters:
        sub_query = sub_query.where(f)
        citizen_sub_query = citizen_sub_query.where(f)
    for f in dos_filters:
        dos_query = dos_query.where(f)
        citizen_dos_query = citizen_dos_query.where(f)

    # Union all result sets
    combined = union_all(sub_query, dos_query, citizen_sub_query, citizen_dos_query).subquery()

    # Deduplicate by (type, id) — take best rank
    deduped = (
        select(
            combined.c.type,
            combined.c.id,
            combined.c.status,
            combined.c.submitted_at,
            combined.c.citizen_name,
            combined.c.document_type_name,
            combined.c.document_type_code,
            combined.c.case_type_name,
            combined.c.case_type_code,
            combined.c.reference_number,
            combined.c.ai_summary,
            func.max(combined.c.relevance_score).label("relevance_score"),
            func.max(combined.c.highlight).label("highlight"),
        )
        .group_by(
            combined.c.type, combined.c.id, combined.c.status, combined.c.submitted_at,
            combined.c.citizen_name, combined.c.document_type_name, combined.c.document_type_code,
            combined.c.case_type_name, combined.c.case_type_code, combined.c.reference_number,
            combined.c.ai_summary,
        )
    )

    # Count total
    count_q = select(func.count()).select_from(deduped.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Sort
    deduped_sub = deduped.subquery()
    final = select(deduped_sub)
    if sort == "submitted_at":
        final = final.order_by(deduped_sub.c.submitted_at.desc().nullslast())
    else:  # relevance
        final = final.order_by(deduped_sub.c.relevance_score.desc())

    # Paginate
    offset = (page - 1) * per_page
    final = final.offset(offset).limit(per_page)

    result = await db.execute(final)
    rows = result.all()

    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    results = []
    for row in rows:
        item = {
            "type": row.type,
            "id": str(row.id),
            "status": row.status,
            "submitted_at": row.submitted_at.isoformat() if row.submitted_at else None,
            "citizen_name": row.citizen_name,
            "ai_summary": row.ai_summary,
            "ai_summary_is_ai_generated": row.ai_summary is not None,
            "relevance_score": float(row.relevance_score) if row.relevance_score else 0.0,
            "highlight": row.highlight or "",
        }
        if row.type == "submission":
            item["document_type_name"] = row.document_type_name
            item["document_type_code"] = row.document_type_code
        else:
            item["case_type_name"] = row.case_type_name
            item["case_type_code"] = row.case_type_code
            item["reference_number"] = row.reference_number
        results.append(item)

    return {
        "results": results,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
        "query": query,
    }
