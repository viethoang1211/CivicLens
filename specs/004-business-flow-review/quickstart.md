# Quickstart: Business Flow Review & Fixes

**Feature**: 004-business-flow-review | **Date**: 2026-04-14

## Prerequisites

- Python 3.12+
- PostgreSQL 16 running (via docker-compose)
- Redis running (for Celery)
- Backend dependencies installed: `cd backend && pip install -e .`

## Setup

```bash
# Start infrastructure
cd infra && docker-compose up -d

# Apply migrations (no new migrations in this feature)
cd backend && alembic upgrade head

# Seed data (includes improved classification prompts)
cd backend && python -m src.seeds.seed_data
```

## Verify Fixes

### 1. OCR Confidence (no longer hardcoded)

```bash
# Run OCR pipeline on a test submission
cd backend && python -c "
from src.workers.ocr_worker import run_ocr_pipeline
# Will use heuristic confidence instead of hardcoded 0.85
# Test with a submission ID that has scanned pages
"
```

### 2. Classification Threshold Enforcement

```bash
# Run classification and check method field
cd backend && python -c "
from src.config import settings
print(f'Classification threshold: {settings.classification_confidence_threshold}')
# Should be 0.7 — now enforced in classification_worker
"
```

### 3. Template Validation

```bash
cd backend && python -c "
from src.services.template_service import validate_template_data

schema = {'ho_ten': {'type': 'string'}, 'so_cccd': {'type': 'string'}, 'ngay_sinh': {'type': 'string'}}
data = {'ho_ten': '  Nguyễn Văn A  ', 'so_cccd': 12345, 'extra_field': 'ignored'}
result = validate_template_data(data, schema)
print(result)
# Should: strip whitespace on ho_ten, coerce so_cccd to string, exclude extra_field, include ngay_sinh as None
"
```

### 4. Dossier Workflow Advancement

```bash
# Run full test suite to verify dossier mode
cd backend && pytest tests/unit/test_workflow_service.py -v
```

## Run Tests

```bash
# All backend tests
cd backend && pytest tests/ -v

# Lint
cd backend && ruff check src/

# Specific test suites
cd backend && pytest tests/unit/test_ocr_worker.py -v
cd backend && pytest tests/unit/test_classification_worker.py -v
cd backend && pytest tests/unit/test_template_service.py -v
cd backend && pytest tests/unit/test_workflow_service.py -v
cd backend && pytest tests/unit/test_dossier_service.py -v
cd backend && pytest tests/integration/test_full_pipeline.py -v
```

## Files Modified

| File | Change |
|------|--------|
| `backend/src/workers/ocr_worker.py` | Heuristic confidence, fix fallback |
| `backend/src/workers/classification_worker.py` | Enforce confidence threshold |
| `backend/src/services/template_service.py` | Type validation |
| `backend/src/services/workflow_service.py` | Dossier mode support |
| `backend/src/services/notification_service.py` | Dossier step notification |
| `backend/src/seeds/seed_data.py` | Classification prompt improvements |
| `backend/tests/unit/test_*.py` | New unit tests |
| `backend/tests/integration/test_full_pipeline.py` | New integration test |
