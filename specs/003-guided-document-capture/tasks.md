# Tasks: Guided Document Capture

**Input**: Design documents from `/specs/003-guided-document-capture/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/staff-api.md

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3, US4, US5)

---

## Phase 1: Setup

**Purpose**: Migration and model changes that all user stories depend on

- [x] T001 Create Alembic migration `0003_requirement_snapshot.py` adding `requirement_snapshot JSONB DEFAULT NULL` to `dossier` table in `backend/alembic/versions/0003_requirement_snapshot.py`
- [x] T002 Add `requirement_snapshot` mapped column to Dossier model in `backend/src/models/dossier.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend snapshot logic + shared Dart DTO — required before any Flutter UI work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Implement `build_requirement_snapshot(case_type, db)` function in `backend/src/services/dossier_service.py` that loads CaseType → Groups → Slots → DocumentTypes and returns the JSONB snapshot dict per data-model.md schema
- [x] T004 Modify dossier creation in `backend/src/api/staff/dossier.py` POST handler to call `build_requirement_snapshot()` and store result on the new dossier's `requirement_snapshot` column
- [x] T005 Modify `check_completeness()` in `backend/src/services/dossier_service.py` to read from `dossier.requirement_snapshot` when non-null, falling back to live CaseType join for legacy dossiers with null snapshot
- [x] T006 [P] Ensure `GET /v1/staff/dossiers/{id}` response in `backend/src/api/staff/dossier.py` includes the `requirement_snapshot` field
- [x] T007 [P] Add `requirementSnapshot` field (nullable `Map<String, dynamic>`) to `DossierDto` in `shared_dart/lib/src/models/dossier.dart` with `fromJson`/`toJson` support
- [x] T008 [P] Update barrel export in `shared_dart/lib/shared_dart.dart` if any new files are added

**Checkpoint**: Backend returns snapshot in dossier responses; Dart DTO can parse it

---

## Phase 3: User Story 1 — Guided Capture (Priority: P1) 🎯 MVP

**Goal**: Staff selects case type → system shows step-by-step capture → documents uploaded per slot → completeness enforced → submit with reference number

**Independent Test**: Select "Đăng ký khai sinh", capture documents for each step, submit, verify reference number generated

### Implementation for User Story 1

- [x] T009 [US1] Create `AiValidationBadge` widget in `staff_app/lib/core/widgets/ai_validation_badge.dart` — displays green/orange/red/grey indicator based on `ai_match_result` JSONB values (match≥0.7 green, 0.4-0.7 orange, <0.4 red, null grey spinner)
- [x] T010 [US1] Create `CaptureStepWidget` in `staff_app/lib/features/dossier/capture_step_widget.dart` — expandable card per requirement group showing: group label, mandatory/optional badge, slot alternatives (if multiple), document guidance text (from snapshot `description` + `classification_prompt`), captured page thumbnails, `AiValidationBadge`, and "Chụp ảnh" (Capture) button
- [x] T011 [US1] Create `PagePreviewWidget` in `staff_app/lib/features/dossier/page_preview_widget.dart` — horizontal scrollable row of page thumbnails with tap-to-enlarge, retake, and delete actions per page
- [x] T012 [US1] Create `GuidedCaptureScreen` in `staff_app/lib/features/dossier/guided_capture_screen.dart` — receives `DossierDto` after creation, renders vertical list of `CaptureStepWidget` from `requirementSnapshot.groups` ordered by `group_order`, tracks which steps have documents via `dossier.documents`, shows completeness progress bar, and "Nộp hồ sơ" (Submit) FAB enabled only when all mandatory groups fulfilled
- [x] T013 [US1] Implement camera capture flow in `GuidedCaptureScreen` — when staff taps "Chụp ảnh" on a step, open camera (reuse existing `ScanScreen` camera logic), run image quality assessment, on success call `dossierApi.uploadDocument(dossierId, slotId, pages)`, then refresh dossier state
- [x] T014 [US1] Implement slot selection for multi-slot groups in `CaptureStepWidget` — when a requirement group has multiple slots (OR-logic alternatives like "CCCD hoặc Hộ chiếu"), show a choice dialog before opening camera so staff picks which document type they are capturing
- [x] T015 [US1] Implement submit flow in `GuidedCaptureScreen` — on "Nộp hồ sơ" tap: call `dossierApi.submitDossier(dossierId)`, handle 422 (incomplete) by highlighting missing steps, on success navigate to summary screen
- [x] T016 [US1] Modify home screen in `staff_app/lib/features/home/home_screen.dart` — replace single "New Submission" button with two action cards: primary "Tạo hồ sơ mới" (navigates to `CaseTypeSelectorScreen` → `GuidedCaptureScreen`) and secondary "Quét nhanh" (navigates to existing `CreateSubmissionScreen`)
- [x] T017 [US1] Wire navigation: `CaseTypeSelectorScreen` → create dossier via API → navigate to `GuidedCaptureScreen` with the created `DossierDto` (including snapshot)

**Checkpoint**: Full guided capture flow functional — staff can select case, capture per step, submit

---

## Phase 4: User Story 2 — AI Validation Display + Override (Priority: P1)

**Goal**: After capturing pages for a step, AI validation result appears inline; staff can override warnings

**Independent Test**: Upload correct document → green badge; upload wrong document → orange warning → tap override → recorded

### Implementation for User Story 2

- [x] T018 [US2] Implement AI validation polling in `GuidedCaptureScreen` — after `uploadDocument()` succeeds, poll `getDossier()` every 3 seconds (max 30s) until the new document's `ai_match_result` transitions from null to a result; update `CaptureStepWidget` with the result
- [x] T019 [US2] Implement override action in `CaptureStepWidget` — when AI shows mismatch (red/orange), display "Bỏ qua cảnh báo" button; on tap call `dossierApi.overrideAiDecision(dossierId, documentId)`, refresh badge to show overridden state
- [x] T020 [US2] Handle AI timeout/unavailability in `CaptureStepWidget` — if polling times out (30s) with `ai_match_result` still null, show grey badge with "Chưa xác minh được" text and allow staff to proceed

**Checkpoint**: AI validation visible per step, override functional, timeout handled gracefully

---

## Phase 5: User Story 3 — Quick Scan Fallback (Priority: P2)

**Goal**: Staff can use legacy single-document scan without selecting a case type first

**Independent Test**: Tap "Quét nhanh", scan document, verify classification pipeline runs and result displayed

### Implementation for User Story 3

- [x] T021 [US3] Ensure `CreateSubmissionScreen` in `staff_app/lib/features/submission/create_submission_screen.dart` is accessible from the new home screen "Quét nhanh" card and functions correctly as the unguided fallback (existing logic, no changes expected — verify navigation wiring)

**Checkpoint**: Quick scan fallback accessible from home screen, legacy classification pipeline works

---

## Phase 6: User Story 4 — Document Guidance + Page Management (Priority: P2)

**Goal**: Each capture step shows document guidance text and staff can manage captured pages (retake, add, delete)

**Independent Test**: View capture step → see document name + description + characteristics; capture pages → manage thumbnails

### Implementation for User Story 4

- [x] T022 [US4] Enhance `CaptureStepWidget` to display document guidance from snapshot: `document_type_name` as title, `description` as subtitle, `classification_prompt` as "Đặc điểm nhận dạng" (Physical characteristics) in an expandable hint section
- [x] T023 [US4] Implement page management in `PagePreviewWidget` — retake button per page (re-opens camera, replaces that page), add button (opens camera, appends new page), delete button per page (calls `dossierApi.deleteDocument` if last page, or needs per-page delete support — if not available, delete entire document and re-capture)
- [x] T024 [US4] Implement draft persistence in `GuidedCaptureScreen` — if staff navigates away (back button or app close), dossier remains in `draft`/`scanning` status on server; add "Hồ sơ đang xử lý" (In-progress dossiers) section to home screen listing draft dossiers with resume navigation

**Checkpoint**: Guidance text displayed per step, page management functional, drafts resumable

---

## Phase 7: User Story 5 — Summary + Citizen Receipt (Priority: P3)

**Goal**: Pre-submit summary screen with validation overview; reference number + QR code after submission

**Independent Test**: Complete all steps → summary shows all docs with status → submit → reference number displayed

### Implementation for User Story 5

- [x] T025 [US5] Create `DossierSummaryScreen` in `staff_app/lib/features/dossier/dossier_summary_screen.dart` — displays: case type name, citizen name, list of requirement groups with captured document status (validated/overridden/skipped/missing), total completeness indicator, and "Nộp hồ sơ" (Submit) confirmation button
- [x] T026 [US5] Implement reference number display in `DossierSummaryScreen` — after successful submit, show reference number in large font, generate QR code (use `qr_flutter` package or simple text-based QR), offer "In phiếu" (Print receipt) action (can be share/screenshot for MVP)
- [x] T027 [US5] Wire `GuidedCaptureScreen` submit to navigate to `DossierSummaryScreen` instead of directly submitting — flow becomes: guided capture → summary review → confirm submit → receipt

**Checkpoint**: Full flow complete with summary review and citizen receipt

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final integration, edge cases, and quality

- [x] T028 [P] Add Vietnamese localization strings for all new UI text in guided capture screens (button labels, status messages, error messages, guidance headers)
- [x] T029 [P] Handle edge case: draft dossier with null `requirement_snapshot` (pre-migration dossiers) — `GuidedCaptureScreen` falls back to loading live requirement groups via existing `requirement_groups` field
- [x] T030 Verify end-to-end flow with seed data: create dossier for each of the 6 case types, capture documents per step, submit, confirm reference numbers work in citizen app

---

## Dependencies

```
Phase 1 (T001-T002) → Phase 2 (T003-T008) → Phase 3 (T009-T017) → Phase 4 (T018-T020)
                                            ↘ Phase 5 (T021)
                                            ↘ Phase 6 (T022-T024)
Phase 3 + Phase 4 → Phase 7 (T025-T027)
All phases → Phase 8 (T028-T030)
```

**Parallelization within phases**:
- Phase 2: T006, T007, T008 can run in parallel after T003-T005
- Phase 3: T009, T010, T011 can run in parallel (different files), then T012-T017 sequential
- Phase 8: T028, T029 can run in parallel

## Implementation Strategy

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1) delivers the core guided capture experience. Staff can select a case type, follow step-by-step capture, and submit. This alone is a major improvement over the current disconnected workflows.

**Incremental delivery**:
1. **MVP (P1)**: Phases 1-3 → guided capture works end-to-end
2. **+AI feedback (P1)**: Phase 4 → validation badges + override
3. **+Fallback (P2)**: Phase 5 → quick scan preserved
4. **+Guidance (P2)**: Phase 6 → rich document descriptions + page management + draft resume
5. **+Polish (P3)**: Phase 7 → summary screen + receipt
6. **+Quality (P3)**: Phase 8 → edge cases + localization + E2E verification
