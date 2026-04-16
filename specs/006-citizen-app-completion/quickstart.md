# Quickstart: Citizen App Completion

**Feature**: 006-citizen-app-completion  
**Date**: 2026-04-16

## Prerequisites

- Python 3.12, PostgreSQL 16 running
- Flutter 3.24+ installed
- Backend running: `cd backend && uvicorn src.main:app --reload --port 8000`
- Seed data loaded: `cd backend && python -m src.seeds.seed_data`

## Implementation Order

### Phase A: Backend Fixes (no frontend changes)

1. **Alembic migration**: Add `dossier_id` to `notification` and `submission` tables
2. **Seed "Hồ sơ quét nhanh" case type** in seed_data.py
3. **Fix `_build_workflow_steps()`** in `backend/src/api/citizen/dossier.py` — join Department to include `department_name`
4. **Add `dossier_id` to notification response** in `backend/src/api/citizen/notifications.py`
5. **Quick scan bridge**: In `finalize_scan()` (`backend/src/api/staff/submissions.py`), auto-create Dossier and link to Submission

### Phase B: Shared Dart Model Updates

6. **Update `NotificationDto`** — add `dossierId` field
7. **Fix `CitizenApi.listNotifications()`** — change `skip`/`limit` to `page`/`per_page`
8. **Update barrel exports** if new files added

### Phase C: Citizen App UI

9. **Token propagation** — Set auth token on ApiClient after VNeID login, restore on app restart
10. **Home Screen overhaul** — greeting, 3 menu cards with badges, logout button
11. **"Hồ sơ của tôi" screen** — replace stub SubmissionsListScreen with real DossierListScreen using `CitizenDossierApi.listMyDossiers()`
12. **Filter chips** — Tất cả / Đang xử lý / Hoàn thành / Từ chối
13. **Notifications screen** — connect to real API, Vietnamese text, tap→navigate to dossier
14. **Vietnamese localization** — all remaining English text → Vietnamese

### Phase D: Testing

15. **Backend tests**: Unit tests for dossier auto-creation in finalize_scan, notification dossier_id
16. **Integration tests**: E2E citizen dossier list, notification flow
17. **Flutter widget tests**: Home screen, dossier list, notification screen

## Verification

```bash
# Backend
cd backend && pytest tests/ -v
cd backend && ruff check src/

# Flutter
cd citizen_app && flutter analyze
cd shared_dart && flutter analyze
```

## Quick Test Flow

1. Staff creates dossier for CCCD `012345678901` via staff app
2. Staff quick scans for CCCD `012345678902`
3. Citizen logs in via VNeID (CCCD `012345678901`)
4. Citizen sees dossier in "Hồ sơ của tôi"
5. Citizen logs in via VNeID (CCCD `012345678902`)
6. Citizen sees auto-created dossier from quick scan
