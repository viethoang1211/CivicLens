# Implementation Plan: Citizen App Completion

**Branch**: `006-citizen-app-completion` | **Date**: 2026-04-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-citizen-app-completion/spec.md`

## Summary

Complete the citizen app by connecting existing backend APIs to the Flutter UI. The citizen app currently only supports public dossier lookup by reference number. This plan adds: (1) authenticated "My Dossiers" list screen, (2) notification screen connected to real API, (3) personalized home screen with badges, (4) quick scan → auto-create dossier bridge in backend. Three API mismatches must be fixed first: `department_name` missing from workflow steps, notification query param mismatch, and missing `dossier_id` FK on notifications.

## Technical Context

**Language/Version**: Python 3.12 (backend), Dart/Flutter 3.24+ (citizen_app, shared_dart)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2 (async), Alembic, Celery, Dio (Flutter HTTP)  
**Storage**: PostgreSQL 16 (JSONB, UUID PKs), Alibaba Cloud OSS  
**Testing**: pytest (backend), flutter test (Dart)  
**Target Platform**: Android (citizen_app APK), Linux server (backend)  
**Project Type**: Mobile app + web service  
**Performance Goals**: Dossier list loads in <3 seconds  
**Constraints**: Vietnamese-only UI, VNeID OAuth authentication  
**Scale/Scope**: ~6 citizen-facing screens, ~3 backend endpoint changes, 1 Alembic migration

## Constitution Check

*GATE: Constitution is an unfilled template — no specific gates to enforce.*

No violations. Proceeding to design.

## Project Structure

### Documentation (this feature)

```text
specs/006-citizen-app-completion/
├── plan.md              # This file
├── research.md          # Phase 0 output — 5 research tasks resolved
├── data-model.md        # Phase 1 output — schema changes + Dart model changes
├── quickstart.md        # Phase 1 output — implementation order + verification
├── contracts/
│   └── api-contracts.md # Phase 1 output — endpoint request/response shapes
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── notification.py    # MODIFY: add dossier_id FK
│   │   └── submission.py      # MODIFY: add dossier_id FK
│   ├── api/
│   │   ├── citizen/
│   │   │   ├── dossier.py     # MODIFY: add department_name to workflow_steps
│   │   │   └── notifications.py # MODIFY: add dossier_id to response
│   │   └── staff/
│   │       └── submissions.py # MODIFY: auto-create dossier in finalize_scan
│   └── seeds/
│       └── seed_data.py       # MODIFY: add "Hồ sơ quét nhanh" case_type
├── alembic/
│   └── versions/
│       └── xxx_add_dossier_id_to_notification_submission.py  # NEW migration
└── tests/

shared_dart/
├── lib/
│   └── src/
│       ├── models/
│       │   └── models.dart    # MODIFY: NotificationDto add dossierId
│       └── api/
│           └── citizen_api.dart # MODIFY: fix listNotifications params
└── test/

citizen_app/
├── lib/
│   ├── main.dart              # MODIFY: home screen overhaul, token propagation
│   └── features/
│       ├── auth/
│       │   └── vneid_auth_screen.dart # MODIFY: pass token to ApiClient
│       ├── submissions/
│       │   ├── dossier_list_screen.dart    # NEW: "Hồ sơ của tôi" screen
│       │   ├── dossier_lookup_screen.dart  # EXISTING (minor Vietnamese fixes)
│       │   ├── dossier_status_screen.dart  # EXISTING (no changes)
│       │   └── submissions_list_screen.dart # EXISTING stub (replaced by dossier_list_screen)
│       └── notifications/
│           └── notifications_screen.dart   # MODIFY: connect to API, Vietnamese text, tap→navigate
└── test/
```

**Structure Decision**: Mobile + API pattern. Backend serves citizen API endpoints; citizen_app is the Flutter mobile client; shared_dart provides DTOs and API clients shared between citizen_app and staff_app.

## Key Design Decisions

### 1. Quick Scan → Dossier Bridge (Research Task 2)

Auto-create Dossier in `finalize_scan()` after all pages are uploaded. Uses seeded "Hồ sơ quét nhanh" case type. Submission gets a `dossier_id` FK linking back to the auto-created dossier. Reference number auto-generated.

### 2. API Mismatch Fixes (Research Task 1)

- **department_name**: Backend joins Department table in `_build_workflow_steps()` — requires `selectinload(WorkflowStep.department)` or subquery
- **Notification params**: Dart `CitizenApi.listNotifications()` changes from `skip`/`limit` to `page`/`per_page`
- **Notification dossier_id**: New column + migration + response field

### 3. Home Screen Architecture (Research Task 3)

StatefulWidget with lazy-loaded counts. No state management library — keep simple. Counts fetched via minimal API calls (`page_size=1` for dossier count, `per_page=1` for notification `unread_count`).

### 4. Auth Token Propagation (Research Task 4)

VNeID auth sets token on ApiClient after login. On app restart, read token from secure storage and set on ApiClient before navigating to home. Logout clears storage + ApiClient token.

## Complexity Tracking

No constitution violations to justify.
