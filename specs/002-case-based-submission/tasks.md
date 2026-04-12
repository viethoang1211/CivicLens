---
description: "Task list for 002-case-based-submission"
---

# Tasks: Case-Based Dossier Submission

**Feature Branch**: `002-case-based-submission`  
**Input**: Design documents from `/specs/002-case-based-submission/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US4)
- All paths are relative to repository root

---

## Phase 1: Setup

**Purpose**: Alembic migration, model registration, and seed data scaffolding. Must complete before any user story phase.

- [X] T001 Create Alembic migration `backend/alembic/versions/0002_case_based_submission.py` — add tables: `case_type`, `case_type_routing_step`, `document_requirement_group`, `document_requirement_slot`, `dossier`, `dossier_document`; alter `scanned_page` (add nullable `dossier_document_id` FK, make `submission_id` nullable, add CHECK constraint); alter `workflow_step` (add nullable `dossier_id` FK, make `submission_id` nullable, add CHECK constraint, add UNIQUE `(dossier_id, step_order)`)
- [X] T002 [P] Create SQLAlchemy model `backend/src/models/case_type.py` — `CaseType` and `CaseTypeRoutingStep` classes with all columns, relationships, and `__table_args__` constraints per data-model.md
- [X] T003 [P] Create SQLAlchemy model `backend/src/models/document_requirement.py` — `DocumentRequirementGroup` and `DocumentRequirementSlot` classes with all columns, FK relationships, and unique constraints per data-model.md
- [X] T004 [P] Create SQLAlchemy model `backend/src/models/dossier.py` — `Dossier` class with all columns, status enum values, relationships to `CaseType`, `Citizen`, `StaffMember`, `DossierDocument`, `WorkflowStep` per data-model.md
- [X] T005 [P] Create SQLAlchemy model `backend/src/models/dossier_document.py` — `DossierDocument` class with all columns, nullable `requirement_slot_id`, `ai_match_result` JSONB column, relationships to `Dossier`, `DocumentRequirementSlot`, `ScannedPage` per data-model.md
- [X] T006 Update `backend/src/models/scanned_page.py` — add nullable `dossier_document_id` FK column, make `submission_id` nullable, add CHECK constraint `(submission_id IS NULL) <> (dossier_document_id IS NULL)`; update relationship
- [X] T007 Update `backend/src/models/workflow_step.py` — add nullable `dossier_id` FK column, make `submission_id` nullable, add CHECK constraint, add unique constraint `(dossier_id, step_order)`; add `dossier` relationship
- [X] T008 Register all new models in `backend/src/models/__init__.py` so Alembic autogenerate detects them
- [X] T009 Extend `backend/src/seeds/seed_data.py` — add `seed_case_types()` function that inserts `CaseType`, `DocumentRequirementGroup`, `DocumentRequirementSlot`, and `CaseTypeRoutingStep` records for the 5 initial case types: `HOUSEHOLD_BIZ_REG`, `COMPANY_REG`, `BIRTH_CERT`, `HOUSEHOLD_REG`, `MARITAL_STATUS` per research.md R-007; preserve existing `DEPARTMENTS` and `DOCUMENT_TYPES` seeding unchanged; call `seed_case_types()` from `seed()` and `main()`

---

## Phase 2: Foundational Services

**Purpose**: Core business logic shared by all user stories. Must complete before Phase 3+.

- [X] T010 Create `backend/src/services/dossier_service.py` — implement `check_completeness(dossier_id, db)` returning `{"complete": bool, "missing_groups": [...]}` per data-model.md validation rules; implement `generate_reference_number(db, submitted_date)` using transactional COUNT+1 with row-lock; implement `create_dossier_workflow(dossier, db)` that reads `CaseTypeRoutingStep` records and creates `WorkflowStep` rows with `dossier_id` set (port logic from `routing_service.create_workflow_for_submission`)
- [X] T011 Update `backend/src/services/routing_service.py` — extract shared workflow-step creation logic into a reusable helper `_create_workflow_steps(owner_id_field, owner_id, routing_steps, security_classification, db)` used by both submission and dossier workflows; existing public API `create_workflow_for_submission` must remain unchanged

---

## Phase 3: User Story 1 — Staff Selects Case Type and Fills Dossier

**Story Goal**: Staff can select a case type, see the required document checklist, scan and upload each document, and have completeness tracked in real time.

**Independent Test**: `POST /v1/staff/dossiers` with `HOUSEHOLD_BIZ_REG` case type → response includes all 4+ requirement groups; upload one document → `GET /v1/staff/dossiers/{id}` shows that group as `is_fulfilled: true`; missing groups shown in `completeness.missing_groups`.

- [X] T012 [US1] Create `backend/src/api/staff/dossier.py` — implement `POST /v1/staff/dossiers` endpoint: validate citizen by `id_number`, validate case type is active, create `Dossier(status="draft")`, return full dossier response including requirement groups with slots and initial `is_fulfilled: false` per contracts/staff-dossier.md
- [X] T013 [US1] Add `GET /v1/staff/dossiers/{dossier_id}` to `backend/src/api/staff/dossier.py` — return full dossier detail with per-group fulfillment status computed from uploaded `DossierDocument` records, `completeness` block, and document list with `ai_match_result`
- [X] T014 [US1] Add `POST /v1/staff/dossiers/{dossier_id}/documents` to `backend/src/api/staff/dossier.py` — accept multipart with `requirement_slot_id` + `pages[]` files; validate slot belongs to dossier's case type; validate dossier status is editable; check image quality per existing `quality_service`; upload pages to OSS under `dossier/{dossier_id}/doc/{doc_id}/p{n}.jpg`; create `DossierDocument` and `ScannedPage` records with `dossier_document_id`; update dossier status to `scanning`; enqueue async AI slot validation task; return 201 with document + page list per contracts/staff-dossier.md
- [X] T015 [US1] Add `DELETE /v1/staff/dossiers/{dossier_id}/documents/{document_id}` to `backend/src/api/staff/dossier.py` — remove `DossierDocument` and its `ScannedPage` records; delete OSS objects; only allowed in `draft`/`scanning` status; return 204
- [X] T016 [P] [US1] Add `GET /v1/staff/dossiers` to `backend/src/api/staff/dossier.py` — paginated list with filters `status`, `case_type_id`, `citizen_id`; each item includes `current_department` derived from active `WorkflowStep` per contracts/staff-dossier.md
- [X] T017 [US1] Register `backend/src/api/staff/dossier.py` router in `backend/src/main.py` under prefix `/v1/staff`
- [X] T018 [P] [US1] Add Dart model `shared_dart/lib/src/models/case_type.dart` — `CaseType`, `DocumentRequirementGroup`, `DocumentRequirementSlot` with `fromJson`/`toJson`, matching the API response shape in contracts/admin-case-types.md
- [X] T019 [P] [US1] Add Dart model `shared_dart/lib/src/models/dossier.dart` — `Dossier`, `DossierDocument`, `DossierCompleteness` with `fromJson`/`toJson`, matching contracts/staff-dossier.md response shape
- [X] T020 [P] [US1] Add Dart API client `shared_dart/lib/src/api/dossier_api.dart` — methods: `getCaseTypes()`, `createDossier(...)`, `getDossier(id)`, `listDossiers(...)`, `uploadDocument(dossierId, slotId, pages)`, `deleteDocument(dossierId, docId)`, `submitDossier(id)` wiring to endpoints in contracts/staff-dossier.md
- [X] T021 [US1] Create staff app feature `staff_app/lib/features/case_type/` — case type selector screen: fetches active case types from `DossierApi.getCaseTypes()`; groups by category; tapping a type navigates to dossier creation screen
- [X] T022 [US1] Create `staff_app/lib/features/dossier/dossier_screen.dart` — main dossier creation screen: shows checklist of `DocumentRequirementGroup` items with fulfilled/missing status badges; floating action button to submit when `completeness.complete = true`; calls `DossierApi.createDossier` on entry
- [X] T023 [US1] Create `staff_app/lib/features/dossier/document_slot_card.dart` — widget for a single requirement group: shows label, OR-slot options, fulfilled indicator; tapping an unfulfilled slot opens camera/gallery picker; on image capture calls `DossierApi.uploadDocument`; shows AI match result badge after poll completes
- [X] T024 [US1] Create `staff_app/lib/features/dossier/dossier_service.dart` — local state management (ChangeNotifier or Riverpod provider): holds current `Dossier` state; polls `getDossier` every 3s while any document has `ai_match_result = null`; exposes `completeness` computed from server response

---

## Phase 4: User Story 2 — Admin Configures Case Types

**Story Goal**: Admin can create, update, deactivate, and manage case types and their document requirements entirely through the API, without code changes.

**Independent Test**: `POST /v1/staff/admin/case-types` creates a new case type with 2 requirement groups (one OR-group) and 2 routing steps → `GET /v1/staff/admin/case-types?active_only=true` includes the new type → `POST /v1/staff/dossiers` with the new case type returns correct checklist → `POST /v1/staff/admin/case-types/{id}/deactivate` removes it from the selector.

- [X] T025 [US2] Create `backend/src/api/staff/admin_case_types.py` — implement all endpoints per contracts/admin-case-types.md: `GET /v1/staff/admin/case-types`, `POST /v1/staff/admin/case-types` (atomic create with groups+routing), `GET /v1/staff/admin/case-types/{id}`, `PUT /v1/staff/admin/case-types/{id}` (metadata only), `POST .../deactivate`, `POST .../activate`, `PUT .../requirement-groups` (atomic replace, blocked if active dossiers), `PUT .../routing-steps` (atomic replace, blocked if active dossiers); enforce `is_admin` check on all write operations
- [X] T026 [US2] Register `backend/src/api/staff/admin_case_types.py` router in `backend/src/main.py`
- [X] T027 [P] [US2] Add Dart API client methods to `shared_dart/lib/src/api/dossier_api.dart` — `adminCreateCaseType(...)`, `adminUpdateCaseType(...)`, `adminDeactivateCaseType(id)`, `adminActivateCaseType(id)`, `adminReplaceRequirementGroups(id, groups)`, `adminReplaceRoutingSteps(id, steps)` per contracts/admin-case-types.md

---

## Phase 5: User Story 3 — Dossier Submission, Routing, and Citizen Tracking

**Story Goal**: Staff submits a complete dossier → reference number assigned → dossier routed to first department as a unit → citizen can look up status by reference number.

**Independent Test**: Complete a `HOUSEHOLD_BIZ_REG` dossier → `POST /v1/staff/dossiers/{id}/submit` returns `reference_number` like `HS-20260411-00001` and `first_department`; `WorkflowStep` row with `dossier_id` and `status="active"` exists in DB; `GET /v1/citizen/dossiers/lookup?reference_number=HS-...` returns current department name without auth.

- [X] T028 [US3] Add `POST /v1/staff/dossiers/{dossier_id}/submit` to `backend/src/api/staff/dossier.py` — call `dossier_service.check_completeness`; return 422 with `missing_groups` if incomplete; generate reference number via `dossier_service.generate_reference_number`; set `status="submitted"`, `submitted_at`, `retention_expires_at`; call `dossier_service.create_dossier_workflow` to create `WorkflowStep` rows; set `status="in_progress"`; commit; return response per contracts/staff-dossier.md
- [X] T029 [P] [US3] Create `backend/src/api/citizen/dossier.py` — implement `GET /v1/citizen/dossiers` (auth required, citizen JWT), `GET /v1/citizen/dossiers/{dossier_id}` (auth, owned by citizen only), `GET /v1/citizen/dossiers/lookup` (public, by `reference_number` query param, rate-limited 10 req/min/IP); return only privacy-safe fields per contracts/citizen-tracking.md; include `status_label_vi` mapping
- [X] T030 [P] [US3] Register `backend/src/api/citizen/dossier.py` router in `backend/src/main.py`
- [X] T031 [P] [US3] Update `backend/src/services/notification_service.py` — add `notify_dossier_status_change(dossier_id, new_status, rejection_reason, db)` that composes and sends a push/notification to the citizen linked to the dossier when status transitions to `in_progress`, `completed`, or `rejected` (reuse existing notification plumbing from `notification_service`)
- [X] T032 [P] [US3] Add Dart model `shared_dart/lib/src/models/dossier_tracking.dart` — `DossierTrackingItem` and `WorkflowStepStatus` for the citizen-facing tracking response, with `statusLabelVi` getter matching the status label mapping in contracts/citizen-tracking.md
- [X] T033 [P] [US3] Add citizen API client `shared_dart/lib/src/api/citizen_dossier_api.dart` — `getDossiers()`, `getDossier(id)`, `lookupByReferenceNumber(referenceNumber)` per contracts/citizen-tracking.md
- [X] T034 [US3] Create `citizen_app/lib/features/submissions/dossier_status_screen.dart` — screen showing dossier tracking timeline: step-by-step workflow progress with department names and timestamps; status badge at top; reference number displayed prominently; uses `CitizenDossierApi.getDossier(id)` with auto-refresh every 30s when `status = in_progress`
- [X] T035 [P] [US3] Add reference number lookup screen to `citizen_app/lib/features/submissions/` — text field for reference number, calls `CitizenDossierApi.lookupByReferenceNumber(...)`, navigates to `DossierStatusScreen` on success; show 404 message if not found
- [X] T036 [US3] Update staff app submit flow: add confirmation dialog in `staff_app/lib/features/dossier/dossier_screen.dart` showing `completeness` summary before calling `DossierApi.submitDossier(id)`; on success display reference number in a prominent card with copy-to-clipboard button

---

## Phase 6: User Story 4 — AI Slot Validation

**Story Goal**: After a document is uploaded to a slot, the AI asynchronously validates whether the scanned image matches the expected document type; staff sees a match/warning badge and can override.

**Independent Test**: Upload a JPEG of a blank piece of paper to the "CMND/CCCD" slot → Celery task runs → `GET /v1/staff/dossiers/{id}` shows `ai_match_result: {"match": false, "confidence": 0.12, "reason": "..."}` on that document → `PATCH .../override-ai` with notes sets `ai_match_overridden: true`.

- [X] T037 [US4] Update `backend/src/workers/classification_worker.py` — add new Celery task `validate_document_slot(dossier_document_id: str)`: load `DossierDocument` + its `ScannedPage` (first page image); load slot's `DocumentType.classification_prompt`; call dashscope vision API with prompt "Does this image show a [prompt]? Respond JSON: match (bool), confidence (0–1), reason (str)"; parse response; update `DossierDocument.ai_match_result` JSONB; commit; if `match=false` and `confidence < 0.80` trigger notification to staff (via existing notification service or websocket)
- [X] T038 [US4] Add `PATCH /v1/staff/dossiers/{dossier_id}/documents/{document_id}/override-ai` to `backend/src/api/staff/dossier.py` — set `ai_match_overridden=true`, update `staff_notes`; only allowed when `ai_match_result.match = false`; return updated document per contracts/staff-dossier.md
- [X] T039 [P] [US4] Update `staff_app/lib/features/dossier/document_slot_card.dart` — display AI badge: green check for `match=true`, yellow warning for `match=false`; show warning dialog with `ai_match_result.reason` text when warning badge tapped; include "Override / Xác nhận vẫn đúng" and "Re-scan / Quét lại" action buttons; "Override" calls `DossierApi.overrideAi(dossierId, documentId, notes)`

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T040 [P] Update `backend/src/security/audit_interceptor.py` — ensure dossier status transitions (`submit`, `reject`, cancel) are logged to `audit_log` with `entity_type="dossier"`, `entity_id=dossier.id`, `actor_id=staff.id`, `action=new_status`
- [X] T041 [P] Update `backend/src/models/__init__.py` — export all new models; confirm Alembic `env.py` `target_metadata` picks up new tables (verify no manual `__all__` filter blocks them)
- [X] T042 [P] Add input validation for `POST /v1/staff/dossiers` and `POST /v1/staff/admin/case-types` — enforce max page count (30 per document), max file size (10MB per page), `security_classification` range 0–3, non-empty `requirement_groups` on case type create
- [X] T043 [P] Add rate limiting to `GET /v1/citizen/dossiers/lookup` — 10 requests/min/IP using SlowAPI or FastAPI middleware; return 429 with `Retry-After` header when exceeded
- [X] T044 [P] Update `backend/src/seeds/seed_data.py` — verify `seed_case_types()` is idempotent (uses `SELECT ... WHERE code = ?` before insert, same pattern as existing `seed()`); add `case_types_created` count to returned dict
- [X] T045 [P] Update `shared_dart/lib/shared_dart.dart` barrel export — export all new model and API client files added in T018, T019, T020, T027, T032, T033
- [X] T046 [P] Update `backend/src/api/staff/dossier.py` — add `PATCH /v1/staff/dossiers/{dossier_id}` to update `priority` field on dossiers in `draft` or `scanning` status (small quality-of-life completeness per FR-002 implicit requirements)

---

## Dependencies (User Story Completion Order)

```
Phase 1 (Setup: T001–T009)
    └── Phase 2 (Foundational: T010–T011)
            ├── Phase 3 (US1: T012–T024)   ← MVP: deliver first
            ├── Phase 4 (US2: T025–T027)   ← can start in parallel with US1 backend (T025–T026)
            ├── Phase 5 (US3: T028–T036)   ← depends on US1 submit endpoint T028
            └── Phase 6 (US4: T037–T039)   ← depends on T014 (document upload)
                    └── Phase 7 (Polish: T040–T046)
```

**Phase 1 internal order**: T001 (migration) must be created first. T002–T005 (models) can run in parallel. T006–T007 (model modifications) parallel. T008 after T002–T007. T009 after T008.

**Phase 2 internal order**: T010 after T008; T011 after T010.

## Parallel Execution Examples

**US1 backend + US2 backend** (once Phase 2 complete):
- Developer A: T012 → T013 → T014 → T015 → T016 → T017
- Developer B: T025 → T026

**US1 shared Dart models + US1 backend** (independent files):
- Developer A: T018, T019, T020 (shared_dart models + API client)
- Developer B: T012, T013, T014 (FastAPI endpoints)

**US3 backend + US3 Flutter** (once T028 complete):
- Developer A: T029, T030, T031
- Developer B: T032, T033, T034, T035

## Implementation Strategy

**MVP = Phase 1 + Phase 2 + Phase 3 (US1)**

This delivers a complete, independently testable slice:
- Staff can select `HOUSEHOLD_BIZ_REG` (seeded case type), create a dossier, scan and upload documents, see completeness status, and understand what's missing.
- No admin UI needed (case types exist via seed data).
- No submission/routing needed (dossier stays in `scanning` / `ready` status).
- No AI validation needed (badge shows "pending").

Add US2 (admin) → configurable without seed data  
Add US3 (submit + citizen) → closes the full workflow loop  
Add US4 (AI) → quality assurance layer
