# Tasks: Citizen App Completion

**Input**: Design documents from `/specs/006-citizen-app-completion/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md, quickstart.md

**Tests**: Not explicitly requested in spec — test tasks omitted.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3, US4, US5)

---

## Phase 1: Setup

**Purpose**: Database migration, seed data, and model updates — shared infrastructure for all stories

- [x] T001 Create Alembic migration adding `dossier_id` UUID FK column to `notification` table and `dossier_id` UUID FK column to `submission` table in `backend/alembic/versions/`
- [x] T002 Add `dossier_id` mapped_column and relationship to Notification model in `backend/src/models/notification.py`
- [x] T003 Add `dossier_id` mapped_column and relationship to Submission model in `backend/src/models/submission.py`
- [x] T004 Seed "Hồ sơ quét nhanh" case_type (code=QUICK_SCAN) in `backend/src/seeds/seed_data.py`

---

## Phase 2: Foundational (Backend API Fixes)

**Purpose**: Fix 3 API mismatches that block all frontend work. Must complete before citizen app UI tasks.

**⚠️ CRITICAL**: No citizen app UI work can begin until these backend fixes are deployed.

- [x] T005 Fix `_build_workflow_steps()` in `backend/src/api/citizen/dossier.py` to join Department table and include `department_name` in each workflow step response (alongside existing `department_id`)
- [x] T006 [P] Add `dossier_id` field to notification list response in `backend/src/api/citizen/notifications.py` (read from new Notification.dossier_id column)
- [x] T007 [P] Update `NotificationDto` in `shared_dart/lib/src/models/models.dart` to add `dossierId` field (from `json['dossier_id']`)
- [x] T008 [P] Fix `CitizenApi.listNotifications()` in `shared_dart/lib/src/api/citizen_api.dart` to send `page`/`per_page` query params instead of `skip`/`limit`

**Checkpoint**: Backend APIs match Dart DTOs. Frontend development can proceed.

---

## Phase 3: User Story 1+2 — Hồ sơ của tôi + Lọc theo trạng thái (Priority: P1) 🎯 MVP

**Goal**: Citizen logs in and sees their dossier list with status filters. Core missing feature.

**Independent Test**: Staff creates dossier for CCCD → Citizen logs in → Sees dossier in list → Filters by status.

### Auth Token Propagation (prerequisite for all authenticated screens)

- [x] T009 Update VNeID auth screen in `citizen_app/lib/features/auth/vneid_auth_screen.dart` to set auth token on ApiClient after successful login and pass ApiClient instance to home screen
- [x] T010 Add app startup token check in `citizen_app/lib/main.dart`: read token from secure storage, if valid skip login and navigate to home with authenticated ApiClient

### Dossier List Screen

- [x] T011 [P] [US1] Create `DossierListScreen` widget in `citizen_app/lib/features/submissions/dossier_list_screen.dart` — StatefulWidget that calls `CitizenDossierApi.listMyDossiers()`, displays list with case_type_name, status badge (Vietnamese), submitted_at, and pull-to-refresh
- [x] T012 [US1] [US2] Add filter chips (Tất cả / Đang xử lý / Hoàn thành / Từ chối) to `DossierListScreen` — pass `status` query param to `listMyDossiers()`
- [x] T013 [US1] Add tap handler on dossier list item to navigate to `DossierStatusScreen` with `dossierId` and `citizenDossierApi` in `citizen_app/lib/features/submissions/dossier_list_screen.dart`
- [x] T014 [US1] Add empty state "Bạn chưa có hồ sơ nào. Vui lòng liên hệ bộ phận tiếp nhận." in `DossierListScreen`

**Checkpoint**: Citizen can log in, see their dossiers, filter by status, and tap to view details.

---

## Phase 4: User Story 3 — Thông báo (Priority: P2)

**Goal**: Citizen sees notifications with unread badge and can tap to navigate to related dossier.

**Independent Test**: Backend creates notification for citizen → Citizen opens app → Sees badge → Taps notification → Opens dossier detail.

- [x] T015 [US3] Overhaul `NotificationsScreen` in `citizen_app/lib/features/notifications/notifications_screen.dart` — use `CitizenApi` with authenticated ApiClient, translate all text to Vietnamese ("Thông báo", "Đánh dấu tất cả đã đọc", empty state "Chưa có thông báo")
- [x] T016 [US3] Add notification tap handler: if `dossierId` is non-null, mark as read then navigate to `DossierStatusScreen`; otherwise just mark as read
- [x] T017 [US3] Add "Đánh dấu tất cả đã đọc" button that calls `markNotificationRead()` for each unread notification in `citizen_app/lib/features/notifications/notifications_screen.dart`

**Checkpoint**: Notification screen functional with Vietnamese UI, navigation to dossier, and mark-read.

---

## Phase 5: User Story 4 — Home Screen Dashboard (Priority: P2)

**Goal**: Personalized home screen with greeting, 3 menu cards with live badges, and logout.

**Independent Test**: Login → See "Xin chào, [Name]" → See badge counts → Tap each menu → Logout works.

- [x] T018 [US4] Convert `_CitizenHomeScreen` in `citizen_app/lib/main.dart` from StatelessWidget to StatefulWidget, accept `ApiClient` and `citizenName` as constructor params
- [x] T019 [US4] Add greeting header "Xin chào, [citizenName]" and 3 menu cards: "Hồ sơ của tôi" (with dossier count badge), "Tra cứu hồ sơ", "Thông báo" (with unread count badge) in `citizen_app/lib/main.dart`
- [x] T020 [US4] Load badge counts on initState: fetch dossier count via `listMyDossiers(pageSize: 1)` response length heuristic, fetch unread_count from `listNotifications(perPage: 1)` response in `citizen_app/lib/main.dart`
- [x] T021 [US4] Add logout button to home screen AppBar: clear secure storage tokens, reset ApiClient, navigate to `/login` in `citizen_app/lib/main.dart`
- [x] T022 [US4] Wire navigation from menu cards: "Hồ sơ của tôi" → DossierListScreen, "Tra cứu hồ sơ" → DossierLookupScreen, "Thông báo" → NotificationsScreen — pass ApiClient and CitizenDossierApi to each in `citizen_app/lib/main.dart`

**Checkpoint**: Home screen is a personal dashboard with live data, navigation, and logout.

---

## Phase 6: User Story 5 — Quick Scan → Dossier Bridge (Priority: P3)

**Goal**: When staff finalizes a quick scan, system auto-creates a Dossier so citizen sees it in "Hồ sơ của tôi".

**Independent Test**: Staff quick scans CCCD X → Finalize scan → Citizen (CCCD X) logs in → Sees auto-created dossier.

- [x] T023 [US5] Implement auto-create Dossier logic in `finalize_scan()` in `backend/src/api/staff/submissions.py`: after setting status=ocr_processing, create Dossier with citizen_id, case_type=QUICK_SCAN, status=submitted, auto-generate reference_number, link back via submission.dossier_id
- [x] T024 [US5] Add reference_number generation helper (format HS-YYYYMMDD-NNNNN) in `backend/src/api/staff/submissions.py` or a shared utility
- [x] T025 [US5] Return `dossier_id` in finalize_scan response (update response dict to include `"dossier_id": str(dossier.id)`) in `backend/src/api/staff/submissions.py`

**Checkpoint**: Quick scan creates both Submission and Dossier. Citizen sees auto-created dossier.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Vietnamese localization for remaining English text, version bump, cleanup.

- [x] T026 [P] Translate all remaining English text in `citizen_app/lib/features/notifications/notifications_screen.dart` to Vietnamese (button labels, error messages, empty states)
- [x] T027 [P] Translate remaining English text in `citizen_app/lib/features/submissions/dossier_lookup_screen.dart` if any remain
- [x] T028 Update version string in `citizen_app/lib/main.dart` from `v0.1.0` to `v0.2.0`

---

## Dependencies

```
Phase 1 (Setup) ──▶ Phase 2 (Backend Fixes)
                         │
                         ├──▶ Phase 3 (US1+2: Dossier List) ──▶ Phase 5 (US4: Home Screen)
                         │
                         ├──▶ Phase 4 (US3: Notifications) ────▶ Phase 5 (US4: Home Screen)
                         │
                         └──▶ Phase 6 (US5: Quick Scan Bridge) [independent]
                         
Phase 5 (Home Screen) ──▶ Phase 7 (Polish)
Phase 6 (Quick Scan)  ──▶ Phase 7 (Polish)
```

### Parallel Execution Opportunities

**Within Phase 1**: T002 + T003 can run in parallel (different model files)
**Within Phase 2**: T006 + T007 + T008 can run in parallel (different files/projects)
**Phase 3 + Phase 6**: Can run in parallel after Phase 2 (no dependencies between them)
**Phase 3 + Phase 4**: DossierListScreen (T011) and NotificationsScreen overhaul (T015) can run in parallel
**Within Phase 7**: T026 + T027 can run in parallel

## Implementation Strategy

**MVP (Phase 1→2→3)**: Citizen can log in and see their dossier list with filters. This alone delivers the core missing feature.

**Increment 2 (Phase 4+5)**: Add notifications + home screen dashboard. Makes the app feel complete.

**Increment 3 (Phase 6+7)**: Quick scan bridge + polish. Ensures all staff actions are visible to citizens.

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 28 |
| **US1 (Dossier List)** | 6 tasks (T009-T014) |
| **US2 (Filters)** | 1 task (T012, shared with US1) |
| **US3 (Notifications)** | 3 tasks (T015-T017) |
| **US4 (Home Screen)** | 5 tasks (T018-T022) |
| **US5 (Quick Scan Bridge)** | 3 tasks (T023-T025) |
| **Setup + Foundational** | 8 tasks (T001-T008) |
| **Polish** | 3 tasks (T026-T028) |
| **Parallel opportunities** | 5 groups identified |
| **Suggested MVP** | Phase 1→2→3 (US1+2: 14 tasks) |
