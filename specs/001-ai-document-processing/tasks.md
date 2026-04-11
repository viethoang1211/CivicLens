# Tasks: AI-Powered Public Sector Document Processing

**Input**: Design documents from `/specs/001-ai-document-processing/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: Not explicitly requested in the feature specification — test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dev environment, shared packages

- [X] T001 Create top-level project directories: `backend/`, `staff_app/`, `citizen_app/`, `shared_dart/`, `infra/`
- [X] T002 Initialize Python 3.12 project with FastAPI, Celery, SQLAlchemy, Alembic, dashscope, pydantic, httpx, python-multipart in `backend/pyproject.toml`
- [X] T003 [P] Initialize Flutter project for staff app in `staff_app/pubspec.yaml` with camera, image_picker, workmanager, sqflite, flutter_secure_storage, dio dependencies
- [X] T004 [P] Initialize Flutter project for citizen app in `citizen_app/pubspec.yaml` with dio, flutter_secure_storage, aliyun_push (Alibaba Cloud EMAS Push SDK) dependencies
- [X] T005 [P] Initialize shared Dart package in `shared_dart/pubspec.yaml` with API DTOs and model classes
- [X] T006 [P] Create `infra/docker-compose.yml` with PostgreSQL 16, Redis (Tair-compatible), RocketMQ containers for local development
- [X] T007 [P] Configure ruff linting and formatting in `backend/pyproject.toml`
- [X] T008 [P] Configure Dart analysis options in `staff_app/analysis_options.yaml`, `citizen_app/analysis_options.yaml`, `shared_dart/analysis_options.yaml`
- [X] T009 Create `backend/Dockerfile` for containerized backend deployment
- [X] T010 Create `backend/src/config.py` with environment-based settings (DATABASE_URL, OSS credentials, Model Studio API key, RocketMQ config, Redis URL)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & ORM

- [X] T011 Create Alembic configuration and initial migration setup in `backend/alembic/` and `backend/alembic.ini`
- [X] T012 Create SQLAlchemy base model with UUID primary key mixin and timestamp columns in `backend/src/models/base.py`
- [X] T013 Create Citizen model in `backend/src/models/citizen.py` (fields: id, vneid_subject_id, full_name, id_number, phone_number, email, push_token, created_at, updated_at)
- [X] T014 [P] Create StaffMember model in `backend/src/models/staff_member.py` (fields: id, employee_id, full_name, department_id FK, clearance_level CHECK 0-3, role, is_active, timestamps)
- [X] T015 [P] Create Department model in `backend/src/models/department.py` (fields: id, name, code UNIQUE, description, min_clearance_level, is_active, created_at)
- [X] T016 Create DocumentType model in `backend/src/models/document_type.py` (fields: id, name, code UNIQUE, description, template_schema JSONB, classification_prompt, retention_years, retention_permanent, is_active, timestamps)
- [X] T017 Create RoutingRule model in `backend/src/models/routing_rule.py` (fields: id, document_type_id FK, department_id FK, step_order, expected_duration_hours, required_clearance_level; unique constraints on (document_type_id, step_order) and (document_type_id, department_id))
- [X] T018 Create Submission model in `backend/src/models/submission.py` (fields: id, citizen_id FK, submitted_by_staff_id FK, document_type_id FK nullable, classification_confidence, classification_method, security_classification CHECK 0-3, status, priority, template_data JSONB, submitted_at, completed_at, retention_expires_at, timestamps; status state machine: draft→scanning→ocr_processing→pending_classification→classified→pending_routing→in_progress→completed/rejected)
- [X] T019 [P] Create ScannedPage model in `backend/src/models/scanned_page.py` (fields: id, submission_id FK, page_number, image_oss_key, ocr_raw_text, ocr_corrected_text, ocr_confidence, image_quality_score, synced_at, created_at; unique constraint on (submission_id, page_number))
- [X] T020 [P] Create WorkflowStep model in `backend/src/models/workflow_step.py` (fields: id, submission_id FK, department_id FK, step_order, status DEFAULT 'pending', assigned_reviewer_id FK nullable, started_at, completed_at, expected_complete_by, result, timestamps; unique constraint on (submission_id, step_order))
- [X] T021 [P] Create StepAnnotation model in `backend/src/models/step_annotation.py` (fields: id, workflow_step_id FK, author_id FK, annotation_type, content, target_citizen BOOLEAN, created_at)
- [X] T022 [P] Create AuditLogEntry model in `backend/src/models/audit_log.py` (fields: id, actor_type, actor_id, action, resource_type, resource_id, clearance_check_result, metadata JSONB, created_at; append-only — no update/delete)
- [X] T023 [P] Create Notification model in `backend/src/models/notification.py` (fields: id, citizen_id FK, submission_id FK nullable, type, title, body, is_read, sent_at, read_at)
- [X] T024 Create `backend/src/models/__init__.py` exporting all models
- [X] T025 Generate Alembic migration for all models in `backend/alembic/versions/`

### Database Indexes & RLS

- [X] T026 Add key indexes to migration: submission(citizen_id, status), submission(document_type_id, status), workflow_step(submission_id, step_order), workflow_step(department_id, status), audit_log_entry(resource_type, resource_id, created_at), audit_log_entry(actor_id, created_at)
- [X] T027 Implement Row-Level Security policies for Submission and ScannedPage tables — enforce `user.clearance_level >= document.security_classification` at DB level in `backend/alembic/versions/` migration

### API & Middleware Foundation

- [X] T028 Create FastAPI application factory with CORS, error handling, and router registration in `backend/src/main.py`
- [X] T029 [P] Implement JWT authentication middleware — decode token, extract staff identity (employee_id, department_id, clearance_level, role) or citizen identity (citizen_id) in `backend/src/security/auth.py`
- [X] T030 [P] Implement ABAC authorization middleware — clearance-level validation for document access in `backend/src/security/abac.py`
- [X] T031 [P] Create database session dependency and connection pool configuration in `backend/src/dependencies.py`
- [X] T032 [P] Implement audit logging utility — write access events to database and SLS in `backend/src/services/audit_service.py`

### External Service Clients

- [X] T033 [P] Implement Alibaba Cloud OSS client — upload, download, presigned URLs for scanned page images in `backend/src/services/oss_client.py`
- [X] T034 [P] Implement Model Studio (dashscope) client — send images for OCR and text for classification in `backend/src/services/ai_client.py`

### Celery Workers

- [X] T035 Create Celery application configuration with RocketMQ broker in `backend/src/workers/celery_app.py`

### Shared Dart Package

- [X] T036 Create API model DTOs (Submission, ScannedPage, WorkflowStep, Notification, Classification result) in `shared_dart/lib/src/models/`
- [X] T037 [P] Create base API client with JWT auth header injection and error handling in `shared_dart/lib/src/api/api_client.dart`
- [X] T038 Export all public types from `shared_dart/lib/shared_dart.dart`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Document Scanning & Digitization (Priority: P1) 🎯 MVP

**Goal**: Staff scan physical documents via mobile app, system performs OCR on handwritten Vietnamese text, creates digital records

**Independent Test**: Staff member scans a physical document → system creates a digital record with accurately extracted text content

### Backend — API Endpoints

- [X] T039 [US1] Implement POST `/v1/staff/submissions` — create new submission (citizen lookup by id_number, set status=draft) in `backend/src/api/staff/submissions.py`
- [X] T040 [US1] Implement POST `/v1/staff/submissions/{id}/pages` — upload scanned page image (multipart, validate image quality score, store to OSS, create ScannedPage record) in `backend/src/api/staff/submissions.py`
- [X] T041 [US1] Implement POST `/v1/staff/submissions/{id}/finalize-scan` — transition status to ocr_processing, dispatch Celery OCR task in `backend/src/api/staff/submissions.py`
- [X] T042 [US1] Implement GET `/v1/staff/submissions/{id}/ocr-results` — return OCR extraction results per page for staff review in `backend/src/api/staff/submissions.py`
- [X] T043 [US1] Implement PUT `/v1/staff/submissions/{id}/ocr-corrections` — save staff corrections to ScannedPage.ocr_corrected_text in `backend/src/api/staff/submissions.py`

### Backend — Services & Workers

- [X] T044 [US1] Implement image quality assessment service — score image sharpness, contrast, skew; reject below threshold with guidance message in `backend/src/services/quality_service.py`
- [X] T045 [US1] Implement OCR Celery worker — call `qwen-vl-ocr` via dashscope for each ScannedPage, store ocr_raw_text and ocr_confidence, fallback to `qwen3-vl-plus` for low-confidence pages in `backend/src/workers/ocr_worker.py`
- [X] T046 [US1] Implement OSS upload logic in page upload endpoint — generate key as `scans/{year}/{month}/{day}/{submission_id}/page_{NNN}.jpg`, store image_oss_key in `backend/src/services/oss_client.py` (extend existing client)

### Staff App — Scanning Feature

- [X] T047 [P] [US1] Create staff authentication flow (JWT login) in `staff_app/lib/features/auth/`
- [X] T048 [US1] Implement camera capture screen — photograph documents with quality preview in `staff_app/lib/features/scan/scan_screen.dart`
- [X] T049 [US1] Implement multi-page scan flow — sequential page capture with page counter and reorder in `staff_app/lib/features/scan/multi_page_scan.dart`
- [X] T050 [US1] Implement offline scan queue — store captured images locally using flutter_secure_storage, queue for sync in `staff_app/lib/core/sync/offline_queue.dart`
- [X] T051 [US1] Implement background sync engine — upload queued scans to backend when connectivity available using workmanager in `staff_app/lib/core/sync/sync_engine.dart`
- [X] T052 [US1] Implement OCR review screen — display extracted text per page, allow staff to edit/correct in `staff_app/lib/features/scan/ocr_review_screen.dart`
- [X] T053 [US1] Implement submission creation flow — enter citizen CCCD number, set security classification, set priority in `staff_app/lib/features/scan/create_submission_screen.dart`

### Staff App — API Integration

- [X] T054 [US1] Create staff submissions API client methods (create, uploadPage, finalizeScan, getOcrResults, submitCorrections) in `shared_dart/lib/src/api/staff_submissions_api.dart`

**Checkpoint**: Staff can scan documents, system performs OCR, staff reviews and corrects text — US1 independently functional

---

## Phase 4: User Story 2 — AI Document Classification & Template Filling (Priority: P1)

**Goal**: System automatically classifies document type, auto-fills standardized template with OCR-extracted data

**Independent Test**: Submit a scanned document → system identifies document type with confidence score → template fields are auto-populated

### Backend — API Endpoints

- [X] T055 [US2] Implement GET `/v1/staff/submissions/{id}/classification` — return AI classification result with confidence, alternatives, and auto-filled template_data in `backend/src/api/staff/classification.py`
- [X] T056 [US2] Implement POST `/v1/staff/submissions/{id}/confirm-classification` — staff confirms or overrides document_type_id, corrects template_data, set classification_method, transition status to classified in `backend/src/api/staff/classification.py`

### Backend — Services & Workers

- [X] T057 [US2] Implement classification Celery worker — call `qwen3.5-flash` with OCR text + document type descriptions prompt, parse structured response (type_id, confidence, alternatives), auto-fill template_data from OCR text in `backend/src/workers/classification_worker.py`
- [X] T058 [US2] Implement template filling service — map OCR-extracted fields to DocumentType.template_schema fields in `backend/src/services/template_service.py`
- [X] T059 [US2] Trigger classification worker automatically after OCR completes — chain OCR → classification in `backend/src/workers/ocr_worker.py` (extend to dispatch classification task on completion)

### Staff App — Classification Feature

- [X] T060 [US2] Implement classification review screen — show document type, confidence score, alternatives dropdown, template fields for editing in `staff_app/lib/features/classify/classification_review_screen.dart`
- [X] T061 [US2] Implement manual classification flow — search/select document type when AI classification fails in `staff_app/lib/features/classify/manual_classify_screen.dart`

### Staff App — API Integration

- [X] T062 [US2] Create classification API client methods (getClassification, confirmClassification) in `shared_dart/lib/src/api/staff_classification_api.dart`

**Checkpoint**: Scanned documents are automatically classified and template auto-filled — US1 + US2 together provide complete scan-to-structured-data pipeline

---

## Phase 5: User Story 3 — Automated Department Routing (Priority: P2)

**Goal**: System determines sequential department routing based on document type, creates workflow steps, advances documents through the chain

**Independent Test**: Submit a classified document → system creates correct department workflow → document appears in first department's queue

### Backend — API Endpoints

- [X] T063 [US3] Implement POST `/v1/staff/submissions/{id}/route` — look up RoutingRule for document_type_id, create WorkflowStep records in sequence, activate first step, transition status to in_progress in `backend/src/api/staff/routing.py`
- [X] T064 [US3] Implement GET `/v1/staff/departments/{id}/queue` — list active WorkflowSteps for a department with pagination, priority sorting, delay detection in `backend/src/api/staff/departments.py`

### Backend — Services

- [X] T065 [US3] Implement routing service — resolve RoutingRule chain for a document type, validate clearance levels of receiving departments, create WorkflowStep records, flag for manual routing when no rules exist in `backend/src/services/routing_service.py`
- [X] T066 [US3] Implement workflow advancement service — complete current step, activate next step, update expected_complete_by timestamps, mark submission completed/rejected when final step done in `backend/src/services/workflow_service.py`

### Staff App — Routing Feature

- [X] T067 [US3] Implement route confirmation screen — show proposed department workflow sequence, allow staff to trigger routing in `staff_app/lib/features/classify/route_confirmation_screen.dart`
- [X] T068 [US3] Implement department queue screen — list submissions assigned to reviewer's department with priority indicators and delay flags in `staff_app/lib/features/review/department_queue_screen.dart`

### Staff App — API Integration

- [X] T069 [US3] Create routing API client methods (routeSubmission) and department API methods (getDepartmentQueue) in `shared_dart/lib/src/api/staff_routing_api.dart`

**Checkpoint**: Documents are auto-routed through department chain and appear in department queues — US3 independently functional

---

## Phase 6: User Story 4 — Citizen Status Tracking (Priority: P2)

**Goal**: Citizens see real-time visual workflow of their submission's processing status with notifications

**Independent Test**: Citizen logs in → sees list of submissions → views visual workflow with completed/active/pending nodes → receives push notification on step advancement

### Backend — API Endpoints

- [X] T070 [US4] Implement POST `/v1/citizen/auth/vneid` — exchange VNeID auth code for app JWT, upsert Citizen record in `backend/src/api/citizen/auth.py`
- [X] T071 [US4] Implement GET `/v1/citizen/submissions` — list citizen's submissions with current step summary, pagination in `backend/src/api/citizen/submissions.py`
- [X] T072 [US4] Implement GET `/v1/citizen/submissions/{id}` — return full submission detail with workflow steps array (step_order, department_name, status, timestamps, result) and citizen-visible annotations in `backend/src/api/citizen/submissions.py`
- [X] T073 [US4] Implement GET `/v1/citizen/notifications` — list notifications with unread count, pagination in `backend/src/api/citizen/notifications.py`
- [X] T074 [US4] Implement PUT `/v1/citizen/notifications/{id}/read` — mark notification as read in `backend/src/api/citizen/notifications.py`

### Backend — Notification Service

- [X] T075 [US4] Implement notification service — create Notification records and trigger push via Alibaba Cloud EMAS when workflow step advances, info requested, or submission completes/delays in `backend/src/services/notification_service.py`
- [X] T076 [US4] Integrate notification triggers into workflow advancement service — call notification_service when step completes or delay detected in `backend/src/services/workflow_service.py` (extend)

### Citizen App

- [X] T077 [P] [US4] Implement VNeID authentication flow in `citizen_app/lib/features/auth/vneid_auth_screen.dart`
- [X] T078 [US4] Implement submissions list screen — show all submissions with status badge, document type, current step in `citizen_app/lib/features/submissions/submissions_list_screen.dart`
- [X] T079 [US4] Implement visual workflow tracker — sequential node visualization with completed (✓), active (highlighted), pending (grayed) states, timestamps, delay flags in `citizen_app/lib/features/workflow/workflow_tracker_screen.dart`
- [X] T080 [US4] Implement notifications screen — list notifications grouped by submission, mark as read in `citizen_app/lib/features/notifications/notifications_screen.dart`
- [X] T081 [US4] Implement push notification handling — register device token, handle foreground/background pushes, navigate to relevant submission in `citizen_app/lib/core/push/push_service.dart`

### Citizen App — API Integration

- [X] T082 [US4] Create citizen API client methods (auth, listSubmissions, getSubmission, listNotifications, markRead) in `shared_dart/lib/src/api/citizen_api.dart`

**Checkpoint**: Citizens can log in, view visual workflow progress, and receive notifications — US4 independently functional

---

## Phase 7: User Story 5 — Department Review & Collaboration Workflow (Priority: P3)

**Goal**: Reviewers process documents in their queue — view content, add annotations, approve/reject/request-info, cross-department consultation

**Independent Test**: Reviewer opens queued document → sees digitized content + template + prior annotations → completes review with annotation → document advances to next step

### Backend — API Endpoints

- [X] T083 [US5] Implement GET `/v1/staff/workflow-steps/{id}` — return full review context: submission detail, scanned pages (presigned OSS URLs), template_data, all prior StepAnnotations grouped by department in `backend/src/api/staff/workflow_steps.py`
- [X] T084 [US5] Implement POST `/v1/staff/workflow-steps/{id}/complete` — process review result (approved/rejected/needs_info), create StepAnnotation, trigger workflow advancement or citizen notification in `backend/src/api/staff/workflow_steps.py`
- [X] T085 [US5] Implement POST `/v1/staff/workflow-steps/{id}/consultations` — create consultation annotation targeting another department, no ownership transfer in `backend/src/api/staff/workflow_steps.py`

### Backend — Services

- [X] T086 [US5] Implement review service — validate reviewer assignment and clearance, process review result, create citizen-facing notification on needs_info/reject in `backend/src/services/review_service.py`

### Staff App — Review Feature

- [X] T087 [US5] Implement document review screen — display scanned page images, OCR text, filled template, prior annotations from earlier departments in `staff_app/lib/features/review/document_review_screen.dart`
- [X] T088 [US5] Implement review action sheet — approve/reject/needs_info buttons with annotation input, citizen-visible message toggle in `staff_app/lib/features/review/review_action_sheet.dart`
- [X] T089 [US5] Implement cross-department consultation dialog — select target department, enter question in `staff_app/lib/features/review/consultation_dialog.dart`

### Staff App — API Integration

- [X] T090 [US5] Create workflow step API client methods (getStepDetail, completeStep, createConsultation) in `shared_dart/lib/src/api/staff_workflow_api.dart`

**Checkpoint**: Full review loop functional — reviewers can process, annotate, approve/reject, consult — US5 independently functional

---

## Phase 8: User Story 6 — Security Classification & Access Control (Priority: P3)

**Goal**: Multi-level security (Unclassified→Top Secret) enforcement with audit logging of all access

**Independent Test**: User with insufficient clearance attempts to access classified document → access denied → attempt logged in audit trail

### Backend — Security Implementation

- [X] T091 [US6] Implement clearance validation in ABAC middleware — check `staff.clearance_level >= submission.security_classification` on every submission/page access, return 403 with audit log on denial in `backend/src/security/abac.py` (extend)
- [X] T092 [US6] Implement audit logging interceptor — automatically log all document view, classify, route, approve, reject actions with actor identity, resource, timestamp, clearance check result in `backend/src/security/audit_interceptor.py`
- [X] T093 [US6] Add clearance validation to routing service — verify receiving department has personnel with adequate clearance before allowing document transfer in `backend/src/services/routing_service.py` (extend)
- [X] T094 [US6] Implement SLS log shipping — async export of AuditLogEntry records to Alibaba Cloud SLS for long-term compliance retention in `backend/src/services/audit_service.py` (extend)

### Staff App — Security Features

- [X] T095 [US6] Add security classification validation enforcement — prevent submission without classification, show clearance-level warning when staff assigns above their own level in `staff_app/lib/features/scan/create_submission_screen.dart` (extend)
- [X] T096 [US6] Filter department queue by staff clearance level — hide submissions above clearance in `staff_app/lib/features/review/department_queue_screen.dart` (extend)

**Checkpoint**: Multi-level security enforced at DB and application level, full audit trail — US6 independently functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T097a [P] Implement admin CRUD endpoints for DocumentType (create, update, list, deactivate) in `backend/src/api/staff/admin_document_types.py` — covers FR-009
- [X] T097b [P] Implement admin CRUD endpoints for RoutingRule (create, update, delete, list by document type) in `backend/src/api/staff/admin_routing_rules.py` — covers FR-009, spec assumption on configurable routing
- [X] T097 [P] Add data retention computation — set Submission.retention_expires_at = completed_at + DocumentType.retention_years on submission completion, handle retention_permanent flag in `backend/src/services/workflow_service.py` (extend)
- [X] T098 [P] Add delay detection — flag WorkflowSteps where NOW() > expected_complete_by, expose is_delayed in department queue and citizen workflow views in `backend/src/services/workflow_service.py` (extend)
- [X] T099 [P] Implement priority queue ordering — urgent submissions appear at top of department queues in `backend/src/api/staff/departments.py` (extend)
- [X] T100 [P] Add submission duplicate detection — warn when citizen+document_type+recent_date match exists in `backend/src/services/submission_service.py`
- [X] T101 [P] Seed database with initial DocumentType definitions and RoutingRule configurations for common document types in `backend/src/seeds/seed_data.py`
- [X] T102 [P] Validate quickstart.md — run through full local development setup to verify all steps work end-to-end
- [X] T103 Performance review — verify OCR + classification < 30s, API responses < 500ms p95

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational phase ← **MVP target**
- **US2 (Phase 4)**: Depends on US1 (builds on OCR pipeline output)
- **US3 (Phase 5)**: Depends on US2 (needs classified documents to route)
- **US4 (Phase 6)**: Depends on Foundational phase only (citizen API is independent, but richer with US3 data)
- **US5 (Phase 7)**: Depends on US3 (needs routed documents in department queues)
- **US6 (Phase 8)**: Depends on Foundational phase (extends existing ABAC/audit)
- **Polish (Phase 9)**: Depends on US1–US6 completion

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational)
                         ↓
         ┌───────────────┼────────────────┐
         ↓               ↓                ↓
    US1 (Phase 3)   US4 (Phase 6)   US6 (Phase 8)
         ↓
    US2 (Phase 4)
         ↓
    US3 (Phase 5)
         ↓
    US5 (Phase 7)
         ↓
    Phase 9 (Polish)
```

### Within Each User Story

- Models before services
- Services before endpoints
- Endpoints before app UI
- Core implementation before integration

### Parallel Opportunities

- **Phase 1**: T003, T004, T005, T006, T007, T008 can all run in parallel after T001
- **Phase 2**: T014+T015, T019+T020+T021+T022+T023, T029+T030+T031+T032, T033+T034 are parallel groups
- **Phase 3**: T047 (staff auth) can run in parallel with backend tasks
- **Phase 6**: US4 (citizen tracking) can start in parallel with US1→US2→US3 chain (different app, different API)
- **Phase 8**: US6 (security) can start in parallel with US4 (independent concerns)

---

## Implementation Strategy

### MVP Scope (Recommended)

**Phase 1 + Phase 2 + Phase 3 (US1)**: Staff can scan documents, OCR processes text, staff reviews/corrects — delivers immediate value by digitizing the paper intake process.

**MVP+1**: Add Phase 4 (US2) for AI classification — completes the scan-to-structured-data pipeline.

### Incremental Delivery

1. **Increment 1** (Phases 1–3): Scan & OCR — staff app usable for document digitization
2. **Increment 2** (Phase 4): Classification — adds AI intelligence layer
3. **Increment 3** (Phases 5–6): Routing + Citizen Tracking — full workflow automation + transparency
4. **Increment 4** (Phases 7–8): Review + Security — completes end-to-end processing with compliance
5. **Increment 5** (Phase 9): Polish — production hardening
