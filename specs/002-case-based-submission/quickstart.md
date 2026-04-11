# Quickstart: Case-Based Dossier Submission (Feature 002)

**Date**: 2026-04-11  
**Branch**: `002-case-based-submission`

This guide gets you from a clean checkout to a running local environment where you can exercise the full dossier submission flow.

---

## Prerequisites

- Docker + Docker Compose v2
- Python 3.12 with `uv` or `pip`
- Flutter 3.24+ (for mobile apps)
- Access to dashscope API key (Alibaba Cloud)

---

## 1. Start Infrastructure

```bash
cd infra
docker compose up -d
```

This starts PostgreSQL, Redis (Celery broker), and a MinIO bucket (OSS emulation).

Verify:
```bash
docker compose ps
# All services should show "running"
```

---

## 2. Apply Database Migrations

```bash
cd backend
pip install -e ".[dev]"   # or: uv sync
alembic upgrade head
```

Migration `0002_case_based_submission` adds:
- `case_type`, `case_type_routing_step`
- `document_requirement_group`, `document_requirement_slot`
- `dossier`, `dossier_document`
- Modified `scanned_page` (nullable `submission_id`, new `dossier_document_id`)
- Modified `workflow_step` (nullable `submission_id`, new `dossier_id`)

---

## 3. Seed Initial Data

```bash
cd backend
python -m src.seeds.seed_data
```

This seeds departments, document types (unchanged from 001), and the new case types:
- `HOUSEHOLD_BIZ_REG` — Đăng ký hộ kinh doanh cá thể (4 requirement groups, 2 routing steps)
- `COMPANY_REG` — Đăng ký doanh nghiệp (4 groups, 3 routing steps)
- `BIRTH_CERT`, `HOUSEHOLD_REG`, `MARITAL_STATUS` — migrated from hardcoded 001 data

---

## 4. Start the Backend

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

Start the Celery worker (for AI slot validation):
```bash
celery -A src.workers.celery_app worker --loglevel=info -Q classification,ocr
```

API docs available at: http://localhost:8000/docs

---

## 5. End-to-End Dossier Flow (cURL)

### Step 1: Login as staff

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/v1/staff/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"staff@example.com","password":"dev-password"}' \
  | jq -r .access_token)
```

### Step 2: Get available case types

```bash
curl -s http://localhost:8000/v1/staff/admin/case-types?active_only=true \
  -H "Authorization: Bearer $TOKEN" | jq '.items[].code'
```

### Step 3: Create a dossier

```bash
DOSSIER=$(curl -s -X POST http://localhost:8000/v1/staff/dossiers \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "citizen_id_number": "038094012345",
    "case_type_id": "<paste HOUSEHOLD_BIZ_REG uuid from step 2>",
    "security_classification": 0,
    "priority": "normal"
  }')
DOSSIER_ID=$(echo $DOSSIER | jq -r .id)
echo "Dossier ID: $DOSSIER_ID"
```

### Step 4: Upload a document to a slot

```bash
# Get requirement_groups[0].slots[0].id from the dossier response
SLOT_ID=$(echo $DOSSIER | jq -r '.requirement_groups[0].slots[0].id')

curl -s -X POST http://localhost:8000/v1/staff/dossiers/$DOSSIER_ID/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "requirement_slot_id=$SLOT_ID" \
  -F "staff_notes=Clear scan, confirmed as household registration book." \
  -F "pages=@/path/to/scan_page1.jpg" \
  -F "pages=@/path/to/scan_page2.jpg"
```

### Step 5: Check completeness and submit

```bash
# Check dossier state
curl -s http://localhost:8000/v1/staff/dossiers/$DOSSIER_ID \
  -H "Authorization: Bearer $TOKEN" | jq '.completeness'

# Submit when complete
curl -s -X POST http://localhost:8000/v1/staff/dossiers/$DOSSIER_ID/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{}' | jq '{reference_number, status, first_department}'
```

### Step 6: Citizen tracks the dossier (no auth needed)

```bash
curl -s "http://localhost:8000/v1/citizen/dossiers/lookup?reference_number=HS-20260411-00001" \
  | jq '{status, status_label_vi, current_department: .workflow_steps[] | select(.status == "active") | .department_name}'
```

---

## 6. Run Tests

```bash
cd backend
pytest tests/unit/test_dossier_service.py -v
pytest tests/integration/test_dossier_api.py -v
pytest tests/contract/ -v
```

---

## 7. Staff App (Flutter)

```bash
cd staff_app
flutter pub get
flutter run
```

Navigate to: **New Submission → Select Case Type → Đăng ký hộ kinh doanh cá thể → Fill document checklist**

---

## 8. Common Issues

| Issue | Fix |
|-------|-----|
| `alembic.exc.IntegrityError` on migration | DB has stale data from 001; run `alembic downgrade base && alembic upgrade head` on dev DB only |
| `slot_already_fulfilled` on document upload | DELETE existing document for that slot first: `DELETE /v1/staff/dossiers/{id}/documents/{doc_id}` |
| AI match result stays `null` | Celery worker not running; start with `celery -A src.workers.celery_app worker` |
| `case_type_inactive` error | Seed data not run or case type was deactivated; run seed or re-activate via admin API |
