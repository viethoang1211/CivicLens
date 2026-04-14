# Tasks: Business Flow Review & Fixes

**Input**: Design documents from `/specs/004-business-flow-review/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story. No new models or migrations — all changes are fixes to existing backend code.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Seeds**: `backend/src/seeds/`

---

## Phase 1: Setup

**Purpose**: No project setup needed — existing codebase. Ensure test infrastructure is ready.

- [x] T001 Verify test infrastructure works by running `cd backend && pytest tests/ -v` and `ruff check src/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create helper function used by multiple user stories.

**⚠️ CRITICAL**: OCR confidence heuristic is needed by both US1 (OCR pipeline) and US2 (dossier flow). Must complete before user stories.

- [x] T002 Implement `estimate_ocr_confidence(text: str) -> float` heuristic function in `backend/src/services/ai_client.py` — returns 0.0 for empty, 0.2 for < 20 chars, 0.3 for non-Vietnamese, 0.7 for reasonable Vietnamese text, 0.85 for text with structural patterns (dates, numbers, names). Uses regex to detect Vietnamese diacritics and common document patterns.

**Checkpoint**: Confidence estimation utility ready — user story implementation can begin.

---

## Phase 3: User Story 1 — Hoàn thiện Classification Logic & OCR Pipeline (Priority: P1) 🎯 MVP

**Goal**: Fix hardcoded OCR confidence, enforce classification threshold, enhance template validation. The AI pipeline produces correct confidence values, triggers fallback when needed, and flags low-confidence classifications for staff.

**Independent Test**: Run OCR + classification pipeline with mock AI responses. Verify: fallback triggers on low confidence, threshold enforces `ai_low_confidence` method, template data is type-validated.

### Implementation for User Story 1

- [x] T003 [US1] Fix OCR confidence in `backend/src/workers/ocr_worker.py` — replace hardcoded `0.85` with call to `estimate_ocr_confidence(result["text"])`. Fix fallback logic: if primary confidence < 0.6, run fallback model, compare confidences, keep better result. Also fix fallback confidence (currently hardcoded `0.80`).
- [x] T004 [US1] Enforce classification confidence threshold in `backend/src/workers/classification_worker.py` — after parsing AI classification result, compare `confidence` against `settings.classification_confidence_threshold` (0.7). If below: set `classification_method = "ai_low_confidence"` instead of `"ai"`, store `classification.get("alternatives", [])` in `submission.template_data["_classification_alternatives"]`. If above: set `classification_method = "ai"` as before.
- [x] T005 [US1] Enhance template validation in `backend/src/services/template_service.py` — replace passthrough with type-aware validation: for each field in schema, check `field_def.get("type")`. String → `str()` + strip. Number/integer → attempt `float()`/`int()` parse, set `None` on failure. Required fields (from schema `"required"` list) with `None` values logged as warning. Return cleaned dict (same shape as before).
- [x] T006 [P] [US1] Write unit test `backend/tests/unit/test_ocr_confidence.py` — test `estimate_ocr_confidence()` with: empty string → 0.0, short garbage → 0.2, non-Vietnamese text → 0.3, Vietnamese government text → ≥ 0.7, text with dates/numbers → 0.85.
- [x] T007 [P] [US1] Write unit test `backend/tests/unit/test_classification_worker.py` — mock `ai_client.classify_document()` and `ai_client.fill_template()`. Test: confidence 0.9 → method "ai". Confidence 0.5 → method "ai_low_confidence" + alternatives stored. Confidence 0.0 → still stores best guess. Empty OCR text → early return.
- [x] T008 [P] [US1] Write unit test `backend/tests/unit/test_template_service.py` — test `validate_template_data()` with: string field strips whitespace, number field coerces from string, invalid number → None, missing required field → logged, extra fields excluded, None input → all fields None.

**Checkpoint**: OCR confidence is heuristic-based, fallback triggers correctly, classification flags low confidence, template data is type-validated. US1 independently testable via unit tests.

---

## Phase 4: User Story 2 — Case-Based Dossier Flow Hoàn chỉnh (Priority: P1)

**Goal**: Fix `advance_workflow()` to support dossier-owned workflow steps. Add dossier step advancement notification. Ensure complete dossier lifecycle works end-to-end.

**Independent Test**: Create a dossier with workflow steps, advance through approve/reject/needs_info, verify correct status updates, retention calculation, and notifications for dossier mode.

### Implementation for User Story 2

- [x] T009 [US2] Add `notify_dossier_step_advanced()` function in `backend/src/services/notification_service.py` — accepts `(db, dossier, department_name, step_order)`, creates notification "Hồ sơ {ref} đã chuyển sang {department_name}" using dossier.reference_number. Similar to existing `notify_step_advanced()` but for dossier mode.
- [x] T010 [US2] Refactor `advance_workflow()` in `backend/src/services/workflow_service.py` to support dual-owner mode — detect `current_step.dossier_id` vs `current_step.submission_id`. For dossier mode: load Dossier instead of Submission, on reject set `dossier.status = "rejected"` and call `notify_dossier_status_change()`, on complete set `dossier.status = "completed"` and compute retention from CaseType.retention_years (load via `dossier.case_type_id`), on advance find next step using `dossier_id` and call `notify_dossier_step_advanced()`, look up `CaseTypeRoutingStep` for expected duration. For submission mode: keep existing logic unchanged.
- [x] T011 [US2] Add `_set_dossier_retention_expiry()` helper in `backend/src/services/workflow_service.py` — loads CaseType via dossier.case_type_id, if `retention_permanent` → None, else `completed_at + timedelta(days=365 * retention_years)`. Called from `advance_workflow()` dossier complete path.
- [x] T012 [P] [US2] Write unit test `backend/tests/unit/test_workflow_service.py` — test `advance_workflow()` with: dossier-owned step approve → next step activated + notification, dossier-owned step reject → dossier rejected + notification, dossier-owned step complete (last step) → dossier completed + retention set, submission-owned step → existing behavior unchanged. Mock db queries and notification functions.
- [x] T013 [P] [US2] Write unit test `backend/tests/unit/test_dossier_service.py` — test `check_completeness()` OR-logic: group with 2 slots where 1 fulfilled → complete. Mandatory group unfulfilled → incomplete. Optional group unfulfilled → still complete. All mandatory groups fulfilled → complete.

**Checkpoint**: Dossier workflow advancement works end-to-end. Approve/reject/needs_info all function for dossier-owned steps. Retention computed from CaseType. Notifications sent in Vietnamese.

---

## Phase 5: User Story 3 — Seed Data Pháp Luật Chuẩn Xác (Priority: P1)

**Goal**: Improve classification prompts in seed data to better distinguish similar document types (forms vs certificates). All legal references already verified correct.

**Independent Test**: Review updated classification prompts, verify form/certificate distinction language is present, re-run seed and verify idempotent.

### Implementation for User Story 3

- [x] T014 [US3] Enhance classification prompts for form-type documents in `backend/src/seeds/seed_data.py` — for BIRTH_REG_FORM, MARITAL_STATUS_FORM, RESIDENCE_FORM_CT01, BIZ_REG_FORM, COMPANY_REG_FORM: add distinguishing text "Đây là TỜ KHAI / mẫu đơn do công dân tự điền, thường in trắng đen trên giấy A4, có các dòng chấm/ô trống để điền thông tin. Mẫu theo [TT/NĐ reference]."
- [x] T015 [P] [US3] Enhance classification prompts for certificate-type documents in `backend/src/seeds/seed_data.py` — for MARRIAGE_CERT, BIRTH_CERTIFICATE_MEDICAL, ID_CCCD, PASSPORT_VN: add distinguishing text "Đây là GIẤY CHỨNG NHẬN / văn bản do cơ quan nhà nước cấp, có DẤU ĐỎ tròn của UBND/cơ quan, chữ ký lãnh đạo, quốc hiệu 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM'."
- [x] T016 [US3] Verify seed idempotency by running `cd backend && python -m src.seeds.seed_data` twice — confirm no duplicate records created, updated prompts apply correctly.

**Checkpoint**: Classification prompts now clearly distinguish forms (blank, citizen-filled) from certificates (government-issued, red seal). All legal references remain accurate. Seed is idempotent.

---

## Phase 6: User Story 4 — Citizen Tracking & Workflow Transparency (Priority: P2)

**Goal**: Ensure citizen notifications work for dossier mode and delay detection functions correctly.

**Independent Test**: Create dossier, advance workflow, verify citizen receives correct Vietnamese notifications. Trigger delay detection, verify delayed steps flagged.

### Implementation for User Story 4

- [x] T017 [US4] Verify `notify_dossier_status_change()` is called from `advance_workflow()` dossier path in `backend/src/services/workflow_service.py` — this should already work after T010. Verify the function creates correct Notification records with Vietnamese text for in_progress/completed/rejected statuses.
- [x] T018 [US4] Verify `detect_delayed_steps()` in `backend/src/services/workflow_service.py` works for both submission-owned and dossier-owned steps — the existing query filters by `status == "active"` without checking owner type, so it should work. Verify by reviewing code.
- [x] T019 [P] [US4] Write unit test `backend/tests/unit/test_notification_service.py` — test `notify_dossier_step_advanced()` creates correct notification with reference number and Vietnamese text. Test `notify_dossier_status_change()` for in_progress, completed, rejected statuses.

**Checkpoint**: Citizen notifications work for all events in both submission and dossier modes. Delay detection catches overdue steps regardless of owner type.

---

## Phase 7: User Story 5 — Department Review & Workflow Advancement (Priority: P2)

**Goal**: Ensure review_service → advance_workflow flow works seamlessly for both submission and dossier modes.

**Independent Test**: Call `process_review()` with a dossier-owned step, verify it correctly delegates to `advance_workflow()` and returns proper outcome.

### Implementation for User Story 5

- [x] T020 [US5] Verify `review_service.process_review()` works with dossier-owned steps in `backend/src/services/review_service.py` — the existing code calls `advance_workflow(db, step, result)` which after T010 handles both modes. No code change expected; verify by tracing the call path.
- [x] T021 [P] [US5] Write integration test `backend/tests/integration/test_full_pipeline.py` — test full submission flow: create submission → upload page → run OCR → run classification → route → review approve → complete. Test full dossier flow: create dossier → upload documents → submit → review approve → advance → complete. Verify notification records created, retention computed, status transitions correct. Use mock AI client responses.

**Checkpoint**: Full pipeline works end-to-end for both Legacy (submission) and Case-based (dossier) modes.

---

## Phase 8: User Story 6 — Mock Data (Priority: P3)

**Goal**: Verify existing mock data is sufficient for demo. No changes expected — seed data already has realistic Vietnamese mock citizens and staff.

**Independent Test**: Run seed, verify mock citizens/staff exist with correct properties.

### Implementation for User Story 6

- [x] T022 [US6] Verify mock citizen and staff seed data in `backend/src/seeds/seed_data.py` — confirm ≥ 3 citizens with Vietnamese names and 12-digit CCCD numbers, staff for each department with appropriate clearance levels. Review existing data; only modify if gaps found.
- [x] T023 [US6] Run full demo flow verification — start backend, seed data, create submission via API, verify OCR/classification runs, route, review, complete. Create dossier via API, upload documents, submit, verify workflow created with reference number.

**Checkpoint**: Mock data supports full end-to-end demo for both submission and dossier flows.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final validation.

- [x] T024 [P] Update `docs/business-flow.md` — add note about classification confidence threshold behavior (ai vs ai_low_confidence method)
- [x] T025 [P] Update `docs/data-model.md` — add `ai_low_confidence` to classification_method allowed values description
- [x] T026 [P] Add interface documentation to `backend/src/services/quality_service.py` — expand docstring to document the stable interface contract (`assess_image_quality(image_data: bytes) -> dict` returning `{"score": float, "acceptable": bool, "guidance": list[str]}`), note that production implementation should use PIL/OpenCV for sharpness, contrast, skew detection
- [x] T027 Run full test suite and lint: `cd backend && pytest tests/ -v && ruff check src/`
- [x] T028 Run quickstart.md validation — execute all verification steps from `specs/004-business-flow-review/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify existing infrastructure
- **Foundational (Phase 2)**: Depends on Phase 1 — creates shared utility function
- **US1 (Phase 3)**: Depends on Phase 2 — uses `estimate_ocr_confidence()`
- **US2 (Phase 4)**: Depends on Phase 2 — no dependency on US1
- **US3 (Phase 5)**: No dependency on Phase 2 — seed data changes are independent
- **US4 (Phase 6)**: Depends on US2 (Phase 4) — uses dossier notification path from T010
- **US5 (Phase 7)**: Depends on US1 (Phase 3) + US2 (Phase 4) — integration test covers both
- **US6 (Phase 8)**: Depends on US1 + US2 — demo verification needs fixed pipeline
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational → independent of US2/US3
- **US2 (P1)**: Can start after Foundational → independent of US1/US3
- **US3 (P1)**: Can start immediately → no dependency on Foundational (seed data only)
- **US4 (P2)**: Depends on US2 completion (dossier notification path)
- **US5 (P2)**: Depends on US1 + US2 (integration test covers both)
- **US6 (P3)**: Depends on US1 + US2 (demo verification)

### Parallel Opportunities

```
Phase 2 (Foundational)
    │
    ├──→ Phase 3 (US1: OCR/Classification)  ──┐
    │                                          │
    ├──→ Phase 4 (US2: Dossier Workflow)    ──┤──→ Phase 7 (US5: Integration) ──→ Phase 8 (US6) ──→ Phase 9
    │                                          │
    └──→ Phase 5 (US3: Seed Data) ────────────┘
                                               │
                           Phase 6 (US4: Citizen Tracking) ─┘
```

Within each phase, tasks marked [P] can run in parallel.

---

## Parallel Example: User Story 1

```bash
# After T003 (OCR fix), T004 (classification fix), T005 (template fix) complete sequentially:
# Launch all unit tests in parallel:
T006: "test_ocr_confidence.py"       # [P] — independent file
T007: "test_classification_worker.py" # [P] — independent file
T008: "test_template_service.py"      # [P] — independent file
```

## Parallel Example: US1 + US2 + US3 in parallel

```bash
# After Phase 2 completes:
# Team member A: US1 (T003 → T004 → T005 → T006,T007,T008 in parallel)
# Team member B: US2 (T009 → T010 → T011 → T012,T013 in parallel)
# Team member C: US3 (T014,T015 in parallel → T016)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup verification
2. Complete Phase 2: Foundational (OCR confidence heuristic)
3. Complete Phase 3: User Story 1 (OCR + classification fixes)
4. **STOP and VALIDATE**: Run `pytest tests/unit/test_ocr_confidence.py tests/unit/test_classification_worker.py tests/unit/test_template_service.py -v`
5. The OCR/classification pipeline now produces correct confidence values and flags low confidence for staff

### Incremental Delivery

6. Complete Phase 4: User Story 2 (Dossier workflow)
7. Complete Phase 5: User Story 3 (Seed data prompts)
8. **VALIDATE**: Both submission and dossier flows work end-to-end
9. Complete Phases 6-8: P2/P3 stories (verification + polish)
10. Complete Phase 9: Final validation
