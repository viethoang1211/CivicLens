# Implementation Plan: Case-Based Dossier Submission

**Branch**: `002-case-based-submission` | **Date**: 2026-04-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-case-based-submission/spec.md`

## Summary

Replace the current per-document-type submission model with a case-based (hồ sơ) model. Each **CaseType** defines the set of required document slots (with OR-group logic for conditional requirements) and its routing workflow. Staff select a CaseType upfront, collect all required documents into a **Dossier**, and submit the dossier as a single unit for routing. Admin users manage CaseTypes and their requirements via API without code changes. The AI classification layer shifts from primary router to assistive slot validator.

All new entities are additive — existing `Submission`, `DocumentType`, and `RoutingRule` tables are preserved for backward compatibility and referenced as the AI slot-validation source during the transition.

## Technical Context

**Language/Version**: Python 3.12 (backend), Dart/Flutter 3.24+ (staff & citizen apps)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2 (async), Alembic, Celery, dashscope (Alibaba Cloud AI), OSS client  
**Storage**: PostgreSQL with JSONB columns; Alibaba Cloud OSS for scanned images  
**Testing**: pytest + pytest-asyncio (backend), Flutter test (mobile)  
**Target Platform**: Linux (Docker), iOS 15+ / Android 8+ (mobile apps)  
**Project Type**: Web service (FastAPI REST) + mobile apps (Flutter)  
**Performance Goals**: Dossier completeness check < 500ms; routing creation < 1s; citizen status lookup < 500ms  
**Constraints**: Additive migrations only (no breaking schema changes in v1); offline scan on staff app (completeness check after sync); Vietnamese government data-retention rules (configurable per CaseType)  
**Scale/Scope**: Supports ~20 case types at launch; ~500 dossier submissions/day per district office

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

> **Note**: The project constitution (`/.specify/memory/constitution.md`) is still in its default template state — no project-specific principles have been ratified. No gates can be evaluated against unfilled placeholders. Constitution should be filled before next feature.

| Gate | Status | Notes |
|------|--------|-------|
| Constitution principles exist | ⚠️ SKIPPED | Constitution is in template/placeholder state |
| Additive schema changes only | ✅ PASS | All new tables; no breaking changes to existing models |
| No cross-feature data sharing | ✅ PASS | New entities cleanly scoped to dossier domain |
| Performance constraints met | ✅ PASS | All operations are simple indexed lookups or paginated lists |

## Project Structure

### Documentation (this feature)

```text
specs/002-case-based-submission/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── admin-case-types.md
│   ├── staff-dossier.md
│   └── citizen-tracking.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── alembic/versions/
│   └── 0002_case_based_submission.py      # New migration
├── src/
│   ├── models/
│   │   ├── case_type.py                   # NEW: CaseType, CaseTypeRoutingStep
│   │   ├── document_requirement.py        # NEW: DocumentRequirementGroup, DocumentRequirementSlot
│   │   ├── dossier.py                     # NEW: Dossier
│   │   ├── dossier_document.py            # NEW: DossierDocument
│   │   └── scanned_page.py               # MODIFIED: add nullable dossier_document_id FK
│   ├── api/staff/
│   │   ├── admin_case_types.py            # NEW: CRUD for CaseType + slots
│   │   └── dossier.py                     # NEW: Staff dossier creation + document upload
│   ├── api/citizen/
│   │   └── dossier.py                     # NEW: Citizen dossier status tracking
│   ├── services/
│   │   ├── dossier_service.py             # NEW: completeness check, reference number gen
│   │   └── routing_service.py            # MODIFIED: support dossier routing
│   ├── workers/
│   │   └── classification_worker.py      # MODIFIED: AI slot validation mode
│   └── seeds/
│       └── seed_data.py                   # MODIFIED: migrate hardcoded data to CaseType DB records

staff_app/lib/
├── features/
│   ├── case_type/                         # NEW: case type selector screen
│   └── dossier/                           # NEW: dossier creation, checklist, upload
│       ├── dossier_screen.dart
│       ├── document_slot_card.dart
│       └── dossier_service.dart

citizen_app/lib/
├── features/
│   └── submissions/                       # MODIFIED: show dossier status by reference number
│       └── dossier_status_screen.dart

shared_dart/lib/src/
├── models/                                # NEW: Dossier, DossierDocument, CaseType shared models
└── api/                                   # NEW: dossier API client methods
```

**Structure Decision**: Mobile + API (Option 3 variant). Backend FastAPI with new routes and models, Flutter staff app with new dossier flow, Flutter citizen app extended with dossier tracking. Shared Dart models updated for new entities.
