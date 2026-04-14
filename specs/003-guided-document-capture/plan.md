# Implementation Plan: Guided Document Capture

**Branch**: `003-guided-document-capture` | **Date**: 2026-04-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-guided-document-capture/spec.md`

## Summary

Unify the two existing document capture workflows (blind-scan + case-based) into a single **guided-first** experience in the staff app. Staff selects a case type, the system presents a step-by-step capture screen driven by `DocumentRequirementGroup`/`DocumentRequirementSlot`, and each captured document is immediately validated by AI (binary match instead of open-ended classification). A "Quick Scan" fallback preserves the legacy classification path for ad-hoc intake. The primary backend change is adding a requirement snapshot to dossiers (JSONB column) so in-progress dossiers are immune to case type definition changes.

## Technical Context

**Language/Version**: Python 3.12 (backend), Dart/Flutter 3.24+ (staff_app, shared_dart)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2 (async), Alembic, Celery, dashscope (Alibaba Cloud AI), Dio (Flutter HTTP)  
**Storage**: PostgreSQL 16 (JSONB), Alibaba Cloud OSS / local filesystem  
**Testing**: pytest (backend unit/integration/contract), flutter test (widget + unit)  
**Target Platform**: Android (staff app), Linux server (backend)  
**Project Type**: Full-stack mobile + API  
**Performance Goals**: AI slot validation < 10s per document, dossier capture < 5 min for 4-document case  
**Constraints**: Online-first (no offline support for guided flow), < 10MB per page upload  
**Scale/Scope**: 7 departments, 15 document types, 6 case types, < 1000 dossiers/day

## Constitution Check

*GATE: Constitution is unpopulated (template placeholders only). No violations to check. Proceeding.*

## Project Structure

### Documentation (this feature)

```text
specs/003-guided-document-capture/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── staff-api.md     # New/modified endpoints
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── alembic/versions/
│   └── 0003_requirement_snapshot.py        # NEW: snapshot JSONB column on dossier
├── src/
│   ├── api/staff/
│   │   └── dossier.py                      # MODIFY: snapshot on create, enrich GET
│   ├── models/
│   │   └── dossier.py                      # MODIFY: add requirement_snapshot column
│   ├── services/
│   │   └── dossier_service.py              # MODIFY: snapshot logic, completeness
│   └── workers/
│       └── slot_validation_worker.py       # EXISTING: no changes needed

staff_app/
├── lib/
│   ├── features/
│   │   ├── home/
│   │   │   └── home_screen.dart            # MODIFY: dual-action (New Dossier + Quick Scan)
│   │   ├── dossier/
│   │   │   ├── case_type_selector_screen.dart  # EXISTING: reuse as-is
│   │   │   ├── guided_capture_screen.dart      # NEW: step-by-step capture wizard
│   │   │   ├── capture_step_widget.dart        # NEW: per-step capture card
│   │   │   ├── page_preview_widget.dart        # NEW: multi-page preview/manage
│   │   │   ├── dossier_summary_screen.dart     # NEW: pre-submit summary + receipt
│   │   │   └── dossier_screen.dart             # EXISTING: adapt for summary
│   │   └── submission/
│   │       └── create_submission_screen.dart    # EXISTING: becomes Quick Scan entry
│   └── core/
│       └── widgets/
│           └── ai_validation_badge.dart        # NEW: green/orange/red indicator

shared_dart/
├── lib/src/
│   ├── models/
│   │   └── dossier.dart                    # MODIFY: add requirementSnapshot field
│   └── api/
│       └── dossier_api.dart                # EXISTING: no API shape changes needed
```

**Structure Decision**: No new directories or packages. Feature 003 adds 4 new Flutter widgets/screens, 1 new Alembic migration, and modifies existing backend and Flutter files. The `guided_capture_screen.dart` is the primary new component.

## Complexity Tracking

> No constitution violations to justify.

| Decision | Rationale | Alternative Rejected |
|----------|-----------|---------------------|
| JSONB snapshot instead of snapshot tables | Single column on `dossier`, no JOINs, immutable after creation | Separate snapshot tables — over-engineering for read-only data |
| Reuse existing DossierDocument + ScannedPage | Guided capture produces identical data to existing dossier flow | New GuidedCapturePage model — unnecessary duplication |
| StatefulWidget over BLoC/Riverpod | Linear wizard flow with existing service layer; complexity not warranted | BLoC pattern — adds abstraction for simple sequential UI |
