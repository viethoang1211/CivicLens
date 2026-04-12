# CLAUDE.md — Agent Instructions for public_sector

This file provides instructions to AI coding agents working on this repository.

## Project Overview

Vietnamese government AI document processing platform. Backend (Python/FastAPI), two Flutter mobile apps (staff + citizen), shared Dart package.

## Repository Layout

```
backend/          Python 3.12 — FastAPI, Celery, SQLAlchemy 2 (async), Alembic
staff_app/        Flutter 3.24+ — Government staff mobile app
citizen_app/      Flutter 3.24+ — Citizen-facing mobile app
shared_dart/      Shared Dart — API client DTOs & network layer
infra/            Docker Compose — Local dev infrastructure
specs/            Feature specifications, plans, tasks (SpecKit)
docs/             Project documentation (always keep up to date)
```

## Commands

```bash
# Backend — run tests and lint
cd backend && pytest tests/ -v && ruff check src/

# Backend — run server
cd backend && uvicorn src.main:app --reload --port 8000

# Backend — run migrations
cd backend && alembic upgrade head

# Backend — seed data
cd backend && python -m src.seeds.seed_data

# Flutter — analyze + test
cd staff_app && flutter analyze && flutter test
cd citizen_app && flutter analyze && flutter test
cd shared_dart && flutter analyze && flutter test

# Flutter — run app
cd staff_app && flutter run
cd citizen_app && flutter run
```

## Post-Implementation Checklist

**After implementing any feature, ALWAYS complete these steps before considering the work done:**

### 1. Update Documentation

- [ ] `docs/api-reference.md` — Add/update any new or changed API endpoints
- [ ] `docs/data-model.md` — Add/update any new or changed database entities, columns, constraints, indexes
- [ ] `docs/architecture.md` — Update component tree if new files/services were added
- [ ] `docs/business-flow.md` — Update if business workflow changed
- [ ] `docs/security.md` — Update audit log table if new audited actions added
- [ ] `docs/getting-started.md` — Update if setup steps changed (new env vars, seed data, etc.)
- [ ] `docs/README.md` — Update capabilities list if a major feature was added

### 2. Write Tests

- [ ] **Unit tests** for new service functions (`backend/tests/unit/`)
- [ ] **Integration tests** for new API endpoints (`backend/tests/integration/`)
- [ ] **Contract tests** for API shape changes (`backend/tests/contract/`)
- [ ] **Flutter widget tests** for new screens (`staff_app/test/`, `citizen_app/test/`)
- [ ] **Dart unit tests** for new models/API clients (`shared_dart/test/`)

### 3. Validate

- [ ] Run `pytest tests/ -v` — all tests pass
- [ ] Run `ruff check src/` — no lint errors
- [ ] Run `flutter analyze` on all Dart packages — no issues
- [ ] Verify Alembic migration applies cleanly: `alembic upgrade head`
- [ ] Verify seed data is idempotent: run `python -m src.seeds.seed_data` twice

## Code Conventions

### Python (Backend)

- Python 3.12, async/await everywhere
- SQLAlchemy 2.0 style (declarative, `mapped_column`, async sessions)
- FastAPI routers with typed Pydantic models or inline dicts for responses
- Alembic for all schema changes (never modify DB directly)
- Services layer (`src/services/`) contains business logic; API layer (`src/api/`) is thin
- Security: ABAC clearance checks on every staff endpoint that accesses classified data
- Audit: log all state transitions via `audit_service.log_access()`

### Dart/Flutter (Mobile Apps)

- Flutter 3.24+, Dart null-safety
- `shared_dart` package for all DTOs and API clients (both apps import it)
- DTOs use `fromJson(Map<String, dynamic>)` factory constructors with snake_case JSON keys
- API clients use `Dio` via the `ApiClient` wrapper class
- Vietnamese UI text by default (this is a Vietnamese government app)
- Barrel exports in `shared_dart/lib/shared_dart.dart` must be updated when adding new files

### Database

- PostgreSQL 16 with UUID primary keys
- JSONB for flexible/AI-generated data (`template_data`, `ai_match_result`, `metadata_`)
- CHECK constraints for domain validation (classification 0–3, exactly-one-owner patterns)
- Row-Level Security enabled on classified tables
- All new tables need an Alembic migration (never use `--autogenerate` blindly, review the diff)

### Naming

- Backend files: `snake_case.py`
- Dart files: `snake_case.dart`
- API routes: `/v1/{audience}/{resource}` (e.g., `/v1/staff/dossiers`, `/v1/citizen/dossiers`)
- DB tables: `snake_case` (SQLAlchemy `__tablename__`)
- Feature branches: `NNN-feature-name` (e.g., `002-case-based-submission`)

## Architecture Notes

### Dual-Owner Pattern

`WorkflowStep` and `ScannedPage` support two owner modes:
- **Legacy**: `submission_id` set, `dossier_id`/`dossier_document_id` null
- **Case-based**: `dossier_id`/`dossier_document_id` set, `submission_id` null
- Enforced by CHECK constraint: exactly one owner must be non-null

### Case Type System

- `CaseType` → `DocumentRequirementGroup` → `DocumentRequirementSlot` (two-level hierarchy)
- Groups use OR-logic: fulfilling any one slot in a group satisfies that group
- `DossierDocument` links to `DocumentRequirementSlot` to track fulfillment
- `CaseTypeRoutingStep` defines the department workflow template (separate from `RoutingRule`)

### AI Integration

- OCR: `qwen-vl-ocr` via dashscope SDK (Celery task)
- Classification: `qwen3.5-flash` via dashscope SDK (Celery task)
- Slot validation: `qwen3-vl-plus` vision model validates document matches slot (Celery task)
- AI results are advisory — staff can always override via `ai_match_overridden` flag
