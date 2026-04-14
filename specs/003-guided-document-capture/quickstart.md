# Quickstart: Guided Document Capture

**Feature**: 003-guided-document-capture  
**Date**: 2026-04-14

---

## Prerequisites

- Backend running (`cd backend && uvicorn src.main:app --reload --port 8000`)
- PostgreSQL database with migrations applied (`cd backend && alembic upgrade head`)
- Seed data loaded (`cd backend && python -m src.seeds.seed_data`)
- Staff app buildable (`cd staff_app && flutter pub get`)

## Step 1: Apply the New Migration

```bash
cd backend && alembic upgrade head
```

This adds the `requirement_snapshot` JSONB column to the `dossier` table. Existing dossiers get `null`.

## Step 2: Verify Seed Data

The guided capture flow depends on case types with requirement groups and document types. Verify they exist:

```bash
cd backend && python -c "
import asyncio
from src.dependencies import async_session_factory
from sqlalchemy import select, func
from src.models.case_type import CaseType
from src.models.document_requirement import DocumentRequirementGroup, DocumentRequirementSlot
from src.models.document_type import DocumentType

async def check():
    async with async_session_factory() as db:
        ct = (await db.execute(select(func.count()).select_from(CaseType))).scalar()
        g = (await db.execute(select(func.count()).select_from(DocumentRequirementGroup))).scalar()
        s = (await db.execute(select(func.count()).select_from(DocumentRequirementSlot))).scalar()
        dt = (await db.execute(select(func.count()).select_from(DocumentType))).scalar()
        print(f'CaseTypes: {ct}, Groups: {g}, Slots: {s}, DocumentTypes: {dt}')

asyncio.run(check())
"
```

Expected: `CaseTypes: 6, Groups: ~20, Slots: ~25, DocumentTypes: 15`

## Step 3: Test the Snapshot on Dossier Creation

```bash
# Create a dossier for birth registration
curl -s -X POST http://localhost:8000/v1/staff/dossiers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <staff-token>" \
  -d '{
    "citizen_id_number": "012345678901",
    "case_type_id": "<birth-reg-case-type-uuid>",
    "security_classification": 0,
    "priority": "normal"
  }' | python -m json.tool
```

Verify the response contains `requirement_snapshot` with groups and slots populated.

## Step 4: Run the Staff App

```bash
cd staff_app && flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Navigation flow:
1. Home screen → tap "Tạo hồ sơ mới"
2. Case type selector → pick "Đăng ký khai sinh"
3. Guided capture screen → step-by-step capture
4. Capture pages per step → see AI validation
5. Complete all mandatory steps → tap "Nộp hồ sơ"
6. Summary screen → reference number displayed

## Step 5: Run Tests

```bash
# Backend
cd backend && pytest tests/ -v

# Staff app
cd staff_app && flutter test

# Lint
cd backend && ruff check src/
cd staff_app && flutter analyze
```

## Test Accounts

| Role | ID | Password | Department |
|------|----|----------|------------|
| Staff (Reception) | NV001 | password123 | RECEPTION |
| Staff (Admin) | NV002 | password123 | ADMIN |
| Staff (Judicial) | NV003 | password123 | JUDICIAL |
| Staff (Finance) | NV004 | password123 | FINANCE |
| Staff (Police) | NV005 | password123 | POLICE |
| Citizen | 012345678901 | VNeID OAuth | — |
| Citizen | 012345678902 | VNeID OAuth | — |
| Citizen | 012345678903 | VNeID OAuth | — |

## Key Files to Modify

| File | Change |
|------|--------|
| `backend/src/models/dossier.py` | Add `requirement_snapshot` mapped column |
| `backend/alembic/versions/0003_*.py` | New migration |
| `backend/src/services/dossier_service.py` | Build snapshot, adjust completeness |
| `backend/src/api/staff/dossier.py` | Include snapshot in responses |
| `staff_app/lib/features/home/home_screen.dart` | Dual-action buttons |
| `staff_app/lib/features/dossier/guided_capture_screen.dart` | New screen |
| `staff_app/lib/features/dossier/capture_step_widget.dart` | New widget |
| `staff_app/lib/features/dossier/page_preview_widget.dart` | New widget |
| `staff_app/lib/features/dossier/dossier_summary_screen.dart` | New screen |
| `staff_app/lib/core/widgets/ai_validation_badge.dart` | New widget |
| `shared_dart/lib/src/models/dossier.dart` | Add snapshot DTO field |
