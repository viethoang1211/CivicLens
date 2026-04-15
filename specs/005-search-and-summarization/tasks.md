# Tasks: Search & AI Summarization

**Input**: Design documents from `/specs/005-search-and-summarization/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/staff-api.md, quickstart.md

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1–US5) this task belongs to
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration, extensions, and shared model changes needed by all user stories.

- [X] T001 Create Alembic migration `0004_search_and_summarization.py` in `backend/alembic/versions/` — enable `unaccent` + `pg_trgm` extensions, create `immutable_unaccent()` function, add `ai_summary` (Text) + `ai_summary_generated_at` (DateTime) columns to `submission` and `dossier`, add `search_vector` (TSVector generated column) to `scanned_page`, create GIN index `idx_scanned_page_search`, GiST index `idx_scanned_page_trgm`, BTREE index `idx_submission_ai_summary`, GiST index `idx_citizen_fullname_trgm` per data-model.md
- [X] T002 [P] Add `ai_summary` and `ai_summary_generated_at` mapped columns to `Submission` model in `backend/src/models/submission.py`
- [X] T003 [P] Add `ai_summary` and `ai_summary_generated_at` mapped columns to `Dossier` model in `backend/src/models/dossier.py`
- [X] T004 [P] Add `search_vector` (TSVector) column to `ScannedPage` model in `backend/src/models/scanned_page.py`
- [X] T005 Add `summarize_document(ocr_text, document_type_name)` and `summarize_dossier(case_type_name, reference_number, document_summaries)` functions to `backend/src/services/ai_client.py` — returns `{"summary": str, "key_points": list, "entities": dict}` using `qwen3.5-flash` with Vietnamese prompts from research.md R-002/R-003

**Checkpoint**: Migration applies cleanly, models reflect new columns, AI client has summarization functions.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Summarization worker + classification chain modification — must complete before US1/US2 can be tested end-to-end.

- [X] T006 Create `backend/src/services/summarization_service.py` — implement `generate_submission_summary(db, submission_id)` that loads OCR text + document type, calls `ai_client.summarize_document()`, stores `ai_summary` + `ai_summary_generated_at` + `template_data["_entities"]` on submission; skip if OCR confidence avg < 0.3 or OCR text empty; implement `generate_dossier_summary(db, dossier_id)` that aggregates document summaries and calls `ai_client.summarize_dossier()`
- [X] T007 Create `backend/src/workers/summarization_worker.py` — Celery task `summarization.generate(submission_id)` with retry policy (3 retries, exponential backoff 10s/30s/90s), on final failure set `ai_summary = null` and log error; task `summarization.generate_dossier(dossier_id)` with same retry policy
- [X] T008 Modify `backend/src/workers/classification_worker.py` — after successful classification in `run_classification()`, chain to `generate_summary.delay(submission_id)` per research.md R-004
- [X] T009 [P] Create `backend/src/workers/backfill_summaries.py` — management command (`python -m src.workers.backfill_summaries`) that queries submissions where `ai_summary IS NULL` and classification is complete, queues Celery tasks with 5/second rate limit, idempotent per research.md R-007

**Checkpoint**: Classification → Summarization chain works. New submissions get AI summaries automatically after classification.

---

## Phase 3: User Story 1 — Full-Text Search (Priority: P1) 🎯 MVP

**Goal**: Cross-department full-text search across submissions, dossiers, and OCR content with clearance filtering (FR-001 through FR-007).

**Independent Test**: Create 10+ submissions with different OCR content, call `GET /v1/staff/search?q=keyword` → results are relevance-ranked, clearance-filtered, paginated.

### Implementation for User Story 1

- [X] T010 [US1] Create `backend/src/services/search_service.py` — implement `search(db, query, clearance_level, filters, sort, page, per_page)` using CTE-based query from research.md R-005: full-text search on `scanned_page.search_vector` via `plainto_tsquery('simple', immutable_unaccent(query))`, JOIN to submission/dossier with clearance filter (`security_classification <= clearance_level`), UNION submission_results + dossier_results, also search `citizen.full_name` (trigram), `citizen.id_number` (exact), `dossier.reference_number` (exact); apply structured filters (status, document_type_code, case_type_code, date_from, date_to, department_id); return paginated results with `ts_rank` relevance score and `ts_headline` highlight snippets; reject query < 2 chars with 422
- [X] T011 [US1] Create `backend/src/api/staff/search.py` — `GET /v1/staff/search` endpoint with query params per contracts/staff-api.md, extract `clearance_level` from JWT, call `search_service.search()`, return response with `results[]`, `pagination`, `query` fields; register router in `backend/src/main.py`
- [X] T012 [P] [US1] Create `backend/tests/unit/test_search_service.py` — test clearance filtering (submission with classification=2, staff clearance=1 → excluded), test query < 2 chars → raises ValidationError, test pagination (total/pages calculation), test combined filters (status + date range), test empty results
- [X] T013 [P] [US1] Create `backend/tests/integration/test_search_api.py` — test `GET /v1/staff/search?q=Nguyễn` returns matching results with correct response shape, test clearance filtering end-to-end, test filter combinations, test 422 on short query, test pagination headers
- [X] T014 [P] [US1] Create `backend/tests/contract/test_search_contract.py` — validate search response JSON shape matches contracts/staff-api.md (results[].type, results[].id, results[].ai_summary, pagination.total, etc.)

**Checkpoint**: Staff can search OCR content cross-department. Results clearance-filtered. Paginated and relevance-ranked.

---

## Phase 4: User Story 2 — AI Document Summarization (Priority: P1)

**Goal**: AI-generated 2-3 sentence Vietnamese summaries on submissions (after classification) and dossiers (on submit) — FR-008 through FR-013.

**Independent Test**: Create submission with OCR text, trigger classification → verify `ai_summary` populated. Modify OCR text → verify summary regenerated.

### Implementation for User Story 2

- [X] T015 [US2] Modify `backend/src/api/staff/classification.py` — add `ai_summary`, `ai_summary_is_ai_generated` (bool), and `entities` (from `template_data["_entities"]`) fields to `GET /v1/staff/submissions/{id}/classification` response per contracts/staff-api.md
- [X] T016 [US2] Modify `backend/src/api/staff/submissions.py` — in `PUT /{id}/ocr-corrections` handler, after saving corrected OCR text, trigger `generate_summary.delay(submission_id)` to regenerate summary (FR-012)
- [X] T017 [US2] Modify dossier submit flow — in `backend/src/api/staff/dossiers.py` or `backend/src/services/dossier_service.py`, after dossier submit, call `summarize_dossier.delay(dossier_id)` to generate dossier-level summary (FR-009)
- [X] T018 [P] [US2] Create `backend/tests/unit/test_summarization_service.py` — test `generate_submission_summary` with valid OCR text → stores summary + entities, test skip when OCR confidence < 0.3 → `ai_summary` remains null, test skip when OCR text empty, test entity extraction stores in `template_data["_entities"]`, test `generate_dossier_summary` aggregates document summaries
- [X] T019 [P] [US2] Create `backend/tests/unit/test_summarization_worker.py` — test retry on AI API failure (mock dashscope error), test final failure sets `ai_summary = null` and logs error, test successful chain from classification

**Checkpoint**: Summaries auto-generated after classification. Empty/low-quality OCR skipped. Staff sees summary in classification endpoint.

---

## Phase 5: User Story 3 — Queue Summary Preview (Priority: P2)

**Goal**: Department queue items show 1-line summary preview — FR-014.

**Independent Test**: Call `GET /v1/staff/departments/{id}/queue` → each item includes `summary_preview` field (truncated to 100 chars or null).

### Implementation for User Story 3

- [X] T020 [US3] Modify `backend/src/api/staff/departments.py` — add `summary_preview` field (first 100 chars of `submission.ai_summary` or `dossier.ai_summary`, or null) to each queue item in `GET /v1/staff/departments/{department_id}/queue` response; JOIN to submission/dossier to access `ai_summary`
- [X] T021 [P] [US3] Create `backend/tests/integration/test_queue_preview.py` — test queue response includes `summary_preview` for items with summary, test null for items without summary, test truncation at 100 chars

**Checkpoint**: Queue items show AI summary previews. Staff can scan queue without opening each item.

---

## Phase 6: User Story 4 — Key Entity Extraction (Priority: P2)

**Goal**: Structured entity extraction (persons, ID numbers, dates, addresses, amounts) stored and searchable — FR-015 through FR-017.

**Independent Test**: Submission with OCR text containing "Nguyễn Văn An, CCCD 012345678901" → `template_data["_entities"]` populated correctly; search by CCCD number finds the submission.

### Implementation for User Story 4

- [X] T022 [US4] Verify entity extraction is already integrated — T005 (AI client returns entities) + T006 (summarization service stores `_entities` in `template_data`) + T010 (search service queries `citizen.id_number`) already cover FR-015/FR-016/FR-017. Create `backend/tests/unit/test_entity_extraction.py` to specifically validate: entities dict structure matches `{"persons": [], "id_numbers": [], "dates": [], "addresses": [], "amounts": []}`, empty OCR returns empty dict, regex validation on extracted CCCD numbers (12 digits)
- [X] T023 [P] [US4] Verify `entities` field already added by T015 in classification response — create integration test in `backend/tests/integration/test_entity_api.py` to confirm entities appear in `GET /v1/staff/submissions/{id}/classification` response

**Checkpoint**: Entities extracted, stored, searchable. Classification endpoint exposes entities alongside summary.

---

## Phase 7: User Story 5 — SLA Analytics Dashboard (Priority: P3)

**Goal**: Aggregate SLA performance metrics per department for managers — FR-018 through FR-020.

**Independent Test**: Call `GET /v1/staff/analytics/sla` with manager JWT → aggregated stats returned. Non-manager → 403.

### Implementation for User Story 5

- [X] T024 [US5] Create `backend/src/services/analytics_service.py` — implement `get_sla_metrics(db, date_from, date_to, department_id=None)` that queries `workflow_step` grouped by `department_id`, compute: `total_steps`, `completed_steps`, `pending_steps`, `delayed_steps` (completed_at > expected_complete_by OR pending AND now > expected_complete_by), `avg_processing_hours` (avg of completed_at - started_at), `delay_rate`, `completion_rate`; also compute `totals` aggregate across all departments
- [X] T025 [US5] Create `backend/src/api/staff/analytics.py` — `GET /v1/staff/analytics/sla` endpoint per contracts/staff-api.md, check staff role is `manager` or `admin` (return 403 otherwise), query params `date_from` (default 30 days ago), `date_to` (default today), `department_id`; register router in `backend/src/main.py`
- [X] T026 [P] [US5] Create `backend/tests/unit/test_analytics_service.py` — test aggregate calculation with mock workflow steps, test delay detection logic, test date range filtering, test department_id filter
- [X] T027 [P] [US5] Create `backend/tests/integration/test_analytics_api.py` — test 200 response for manager role, test 403 for non-manager, test response shape matches contract, test no citizen PII in response

**Checkpoint**: Managers see department SLA metrics. Non-managers blocked. No PII exposed.

---

## Phase 8: Flutter Integration (Staff App)

**Purpose**: Search screen and queue preview in staff_app.

- [X] T028 [P] Create `shared_dart/lib/src/models/search_result.dart` — `SearchResult` DTO with `fromJson` factory: `type` (submission/dossier), `id`, `status`, `submittedAt`, `citizenName`, `documentTypeName`/`caseTypeName`, `aiSummary`, `relevanceScore`, `highlight`; `SearchResponse` with `results`, `pagination`, `query`; update barrel export in `shared_dart/lib/shared_dart.dart`
- [X] T029 [P] Create `shared_dart/lib/src/models/sla_metrics.dart` — `SlaMetrics` DTO with `fromJson` factory per contracts/staff-api.md analytics response shape; update barrel export
- [X] T030 Create `shared_dart/lib/src/api/search_api_client.dart` — `SearchApiClient` using `ApiClient` wrapper, methods: `search(query, {filters})` → `SearchResponse`, `getSlaMetrics({dateFrom, dateTo, departmentId})` → `SlaMetricsResponse`; update barrel export
- [X] T031 Create `staff_app/lib/features/search/search_screen.dart` — search screen with text input, filter chips (status, document type, date range), results list showing type badge + citizen name + summary preview + relevance, pagination, empty state "Không tìm thấy kết quả" with hint to broaden search; Vietnamese UI text; display "AI tạo" badge when `ai_summary_is_ai_generated == true`
- [X] T032 Modify queue display in `staff_app/lib/features/queue/` (or equivalent) — add `summary_preview` line below each queue item title; show "Đang tạo tóm tắt..." if null; display "AI tạo" indicator next to AI-generated summary previews

**Checkpoint**: Staff app has search screen and queue items show summary previews.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, cleanup.

- [X] T033 [P] Update `docs/api-reference.md` — add `GET /v1/staff/search` and `GET /v1/staff/analytics/sla` endpoint documentation, update `GET /departments/{id}/queue` with `summary_preview` field
- [X] T034 [P] Update `docs/data-model.md` — add `ai_summary`, `ai_summary_generated_at` columns on submission/dossier, `search_vector` on scanned_page, new indexes, `unaccent`/`pg_trgm` extensions
- [X] T035 [P] Update `docs/architecture.md` — add `search_service.py`, `summarization_service.py`, `analytics_service.py`, `summarization_worker.py` to component tree; document classification → summarization chain
- [X] T036 [P] Update `docs/business-flow.md` — add search workflow section, AI summarization pipeline section (classification → summarization → entity extraction)
- [X] T037 Run full test suite (`cd backend && pytest tests/ -v && ruff check src/`) and fix any failures or lint errors
- [X] T038 Run `alembic upgrade head` on clean database to verify migration applies cleanly; run `python -m src.seeds.seed_data` twice to verify idempotency

**Checkpoint**: All docs updated. Tests pass. Lint clean. Migration verified.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 (migration + models + AI client)
- **Phase 3 (US1 Search)**: Depends on Phase 1 (search_vector column + indexes must exist)
- **Phase 4 (US2 Summarization)**: Depends on Phase 2 (summarization worker + chain)
- **Phase 5 (US3 Queue Preview)**: Depends on Phase 4 (needs `ai_summary` populated)
- **Phase 6 (US4 Entity Extraction)**: Depends on Phase 2 + Phase 3 (entities stored by summarization, searched by search service)
- **Phase 7 (US5 Analytics)**: Independent of US1–US4, depends only on Phase 1
- **Phase 8 (Flutter)**: Depends on Phase 3 + Phase 5 (API endpoints must exist)
- **Phase 9 (Polish)**: Depends on all previous phases

### User Story Dependencies

- **US1 (Search)** ← Phase 1 only. Can start immediately after setup.
- **US2 (Summarization)** ← Phase 2. Independent of US1.
- **US3 (Queue Preview)** ← US2 (needs `ai_summary` data).
- **US4 (Entity Extraction)** ← US2 (entities generated by summarization) + US1 (entity search).
- **US5 (Analytics)** ← Phase 1 only. Fully independent of US1–US4.

### Parallel Opportunities

- **Phase 1**: T002, T003, T004 can run in parallel (different model files)
- **After Phase 1**: US1 (Phase 3) and US2 (Phase 4) can start in parallel — US1 only needs indexes, US2 needs the worker chain
- **After Phase 2**: US5 (Phase 7) can start immediately in parallel with US1/US2
- **Within each phase**: Tasks marked [P] can run in parallel

### Parallel Example: After Phase 1 completes

```text
┌── Phase 3 (US1: Search)    ──────> Phase 6 (US4: Entities) ──┐
│                                                                │
├── Phase 2 (Foundational) ──> Phase 4 (US2: Summary) ──> Phase 5 (US3: Queue Preview) ──> Phase 8 (Flutter)
│                                                                │
├── Phase 7 (US5: Analytics) ─────────────────────────────────────┤
│                                                                │
└────────────────────────────────────────────────────── Phase 9 (Polish) ──> Done
```

---

## Implementation Strategy

1. **MVP (Phase 1 + 2 + 3)**: Search alone delivers the biggest gap closure — "Centralized Indexing" ❌ → ✅
2. **Core AI (Phase 4)**: Summarization closes the second gap — "AI Summarization" ⚠️ → ✅  
3. **UX Enhancement (Phase 5 + 6)**: Queue preview + entities polish the experience
4. **Management (Phase 7)**: SLA analytics adds value for leadership
5. **Mobile (Phase 8)**: Flutter integration makes features accessible
6. **Ship (Phase 9)**: Docs + validation + clean merge
