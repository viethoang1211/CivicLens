# Implementation Plan: Business Flow Review & Fixes

**Branch**: `004-business-flow-review` | **Date**: 2026-04-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-business-flow-review/spec.md`

## Summary

Fix critical logic bugs in the OCR/classification pipeline (hardcoded confidence, unenforced threshold), make `advance_workflow()` work for both submission and dossier modes, enhance template validation with type checking, and improve classification prompts to distinguish similar document types. All seed data legal references are verified accurate — no schema gaps found. This is a code-fix feature with no new models or migrations.

## Technical Context

**Language/Version**: Python 3.12 (backend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2 (async), Celery, dashscope (Alibaba Cloud AI)
**Storage**: PostgreSQL 16 (JSONB), local filesystem
**Testing**: pytest (unit/integration/contract)
**Target Platform**: Linux server (backend)
**Project Type**: Full-stack API + mobile (backend changes only in this feature)
**Performance Goals**: OCR pipeline < 30s per page, classification < 10s, slot validation < 10s
**Constraints**: Demo scope (≤ 10 concurrent users), no security hardening needed
**Scale/Scope**: 7 departments, 15+ document types, 6 case types, < 1000 dossiers/day

## Constitution Check

*GATE: Constitution is unpopulated (template placeholders only). No violations to check. Proceeding.*

## Project Structure

### Documentation (this feature)

```text
specs/004-business-flow-review/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── staff-api.md     # Changed response shapes
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── workers/
│   │   ├── ocr_worker.py                  # FIX: parse real OCR confidence, fix fallback
│   │   └── classification_worker.py       # FIX: enforce confidence threshold
│   ├── services/
│   │   ├── template_service.py            # FIX: add type validation + required field check
│   │   ├── workflow_service.py            # FIX: support dossier-owned steps
│   │   ├── quality_service.py             # MINOR: document interface for future swap
│   │   └── notification_service.py        # FIX: notification function signatures
│   ├── seeds/
│   │   └── seed_data.py                   # ENHANCE: improve classification prompts
│   └── config.py                          # NO CHANGE (threshold already defined)
└── tests/
    ├── unit/
    │   ├── test_ocr_worker.py             # NEW: test confidence parsing + fallback
    │   ├── test_classification_worker.py  # NEW: test threshold enforcement
    │   ├── test_template_service.py       # NEW: test type validation
    │   ├── test_workflow_service.py        # NEW: test dossier mode advancement
    │   └── test_dossier_service.py        # NEW: test OR-logic completeness
    └── integration/
        └── test_full_pipeline.py          # NEW: end-to-end submission + dossier flow
```

**Structure Decision**: No new directories, models, or migrations. All changes are fixes to existing backend service/worker files + new test files. No Flutter changes in this feature.

## Complexity Tracking

> No constitution violations to justify. No new abstractions introduced.
