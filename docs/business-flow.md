# Business Flow

## End-to-End Document Processing

This document describes the complete lifecycle of a citizen's document submission from physical paper to final resolution, covering both the staff and citizen perspectives.

## Overview

```
Citizen          Staff (Reception)       AI System         Department Staff        Citizen
  │                    │                     │                    │                   │
  │  Submit physical   │                     │                    │                   │
  │  document at       │                     │                    │                   │
  │  service window    │                     │                    │                   │
  │───────────────────>│                     │                    │                   │
  │                    │  Scan pages         │                    │                   │
  │                    │  via camera         │                    │                   │
  │                    │─────────────────────>│                    │                   │
  │                    │                     │  OCR extraction    │                   │
  │                    │                     │  Classification    │                   │
  │                    │                     │  Template filling  │                   │
  │                    │  Review & confirm   │<───────────────────│                   │
  │                    │<────────────────────│                    │                   │
  │                    │                     │                    │                   │
  │                    │  Route to           │                    │                   │
  │                    │  departments        │                    │                   │
  │                    │────────────────────────────────────────>│                   │
  │                    │                     │                    │  Review document  │
  │                    │                     │                    │  Approve/Reject   │
  │                    │                     │                    │──────────────────>│
  │                    │                     │                    │   Push            │
  │                    │                     │                    │   notification    │
```

## Phase 1: Document Intake

### Two Intake Modes

The system supports two parallel intake workflows:

#### Mode A: Quick Scan (Quét nhanh)

For simple, single-document submissions where case-type grouping is unnecessary. Staff taps "Quét nhanh" on home screen:

1. **Create submission** — Staff enters citizen CCCD, selects classification and priority
2. **Scan pages** — Staff scans document pages
3. **Finalize scan** — Triggers OCR → classification → template fill pipeline

#### Mode B: Guided Document Capture (Tạo hồ sơ mới)

Primary workflow for multi-document cases. Staff taps "Tạo hồ sơ mới" on home screen:

1. **Case type selection** — Staff selects from active case types (e.g., Đăng ký khai sinh, Đăng ký hộ kinh doanh). Each case type defines which documents are required.
2. **Citizen ID** — Staff enters citizen CCCD number
3. **Dossier creation** — System creates dossier with `requirement_snapshot` (frozen copy of case type requirements at creation time, immune to later admin changes)
4. **Guided capture screen** — Step-by-step screen shows each requirement group with: document name, description, physical identification characteristics ("Đặc điểm nhận dạng"), mandatory/optional badge, and progress indicator
5. **Per-step capture** — Staff taps camera for each group. For multi-slot groups (OR-logic, e.g., "CCCD **hoặc** Hộ chiếu"), staff selects which document type to capture before opening camera
6. **AI validation** — Binary "does this match?" validation (not open-ended classification) runs async via Celery; result shown as badge per step within 3-30 seconds (green=match, orange=uncertain, red=mismatch, grey=processing)
7. **Staff override** — Staff can override AI mismatch warnings ("Bỏ qua cảnh báo"); overrides recorded with `ai_match_overridden = true` for audit
8. **Draft persistence** — Dossier remains in `draft`/`scanning` status on server; staff can resume from "Hồ sơ đang xử lý" section on home screen
9. **Summary review** — DossierSummaryScreen shows all groups with validation status before final submit
10. **Submit** — Completeness checked against snapshot; reference number `HS-YYYYMMDD-NNNNN` generated; workflow created from case type routing steps
11. **Receipt** — Reference number displayed prominently for citizen to track via citizen app

### Staff Actions (Quick Scan Mode)

1. **Create submission** — Staff enters the citizen's CCCD (national ID) number, selects a security classification level, and sets priority (normal/urgent).

2. **Scan pages** — Staff uses the mobile camera to capture each page of the physical document. Pages can be:
   - Re-captured if image quality is poor
   - Reordered via drag-and-drop
   - Scanned offline and queued for upload when connectivity returns

3. **Finalize scan** — Staff confirms all pages are captured. This triggers the AI processing pipeline.

### What Happens Behind the Scenes

- Each scanned image is uploaded to Alibaba Cloud OSS
- Image quality is assessed (blur, resolution, lighting)
- The submission transitions from `draft` → `scanning` → `ocr_processing`

### Offline Support

When the staff app has no network connectivity:
- Scanned images are saved to local device storage
- Metadata is queued in an encrypted local database
- A background sync engine (`workmanager`) periodically attempts upload
- Once connected, all pending scans are synced automatically

## Phase 2: AI Processing

### OCR Pipeline (Celery Task)

For each scanned page:

1. **Primary OCR** — `qwen-vl-ocr` model extracts text from the document image
2. **Confidence check** — If confidence < threshold (0.7), the `qwen3-vl-plus` fallback model processes the page
3. **Results stored** — Both raw OCR text and confidence scores are saved per page

### Classification Pipeline (Celery Task, chained after OCR)

1. **Text aggregation** — All page OCR texts are combined into a single document
2. **AI classification** — `qwen3.5-flash` identifies the document type from configured categories, returning:
   - Primary classification with confidence score
   - Up to 3 alternative classifications
3. **Template filling** — If confidence is high enough, the AI extracts structured fields into the document type's template schema
4. **Submission updated** — Classification results and template data are stored

The submission transitions: `ocr_processing` → `pending_classification` → `classified`

## Phase 3: Human Review & Confirmation

### OCR Review

Staff reviews the AI-extracted text against the original scanned images:
- Side-by-side view of image and extracted text per page
- Confidence indicator shows quality of extraction
- Staff can edit/correct any text before proceeding

### Classification Review

Staff reviews the AI's document classification:
- **If confident (≥ threshold)** — Shows primary classification with confidence %, template fields pre-filled
- **If uncertain** — Shows alternatives for staff to choose from
- **Manual override** — Staff can search all document types and select manually
- **Template editing** — Staff can correct any auto-filled template fields

Staff confirms the final classification. The submission transitions: `classified` → `pending_routing`

## Phase 4: Automated Routing

### Submission Routing (Legacy)

When staff triggers routing:

1. **Rule lookup** — System finds all `RoutingRule` records for the confirmed document type, ordered by `step_order`
2. **Clearance validation** — For each department in the route, verifies at least one active staff member has sufficient clearance for the document's security classification
3. **Workflow creation** — Creates `WorkflowStep` records for each department in sequence
4. **First step activated** — The first department's step is set to `active` with an expected completion deadline

The submission transitions: `pending_routing` → `in_progress`

### Dossier Routing (Case-Based)

When a dossier is submitted:

1. **Case type routing lookup** — System reads `CaseTypeRoutingStep` records for the dossier's case type, ordered by `step_order`
2. **Clearance validation** — Same check as submission routing
3. **Workflow creation** — Creates `WorkflowStep` records with `dossier_id` (not `submission_id`)
4. **Reference number** — Format `HS-YYYYMMDD-NNNNN` where NNNNN is a daily sequential counter
5. **Retention calculation** — `retention_expires_at` computed from the case type's `retention_years`
6. **Citizen notification** — Push notification sent to the citizen

### Example Routing

For a **Birth Certificate Application** (`BIRTH_CERT`):

```
Step 1: Tiếp nhận (Reception)     → 48 hours expected
Step 2: Phòng Tư pháp (Judicial)  → 72 hours expected
```

For a **Classified Report** (`CLASSIFIED_RPT`):

```
Step 1: Tiếp nhận (Reception)       → 48 hours expected
Step 2: Phòng Nội vụ (Internal)     → 72 hours expected
Step 3: Lãnh đạo (Leadership)       → 72 hours expected
```

## Phase 5: Department Review

Each department processes documents sequentially:

### Reviewer Actions

1. **View queue** — Staff sees their department's pending documents, sorted by priority (urgent first) and filtered by their clearance level
2. **Open review** — Full context: scanned images, OCR text, template data, and annotations from prior departments
3. **Decision** — Three options:
   - **Approve** — Step completes, next department activated
   - **Reject** — Entire submission rejected, citizen notified
   - **Request Info** — Step pauses, citizen notified to provide additional information
4. **Annotate** — Add comments with option to make them visible to the citizen

### Cross-Department Consultation

Reviewers can consult other departments without transferring the submission:
- Select target department and enter a question
- Creates a `consultation` annotation on the current step
- The document stays with the current department

### Delay Detection

If `NOW() > expected_complete_by` for any active step:
- The step is flagged as `delayed`
- The citizen is notified
- The department queue highlights delayed items in red

## Phase 6: Completion

When the final department approves:
1. Submission status → `completed`
2. Completion timestamp recorded
3. **Retention calculation** — `retention_expires_at` = `completed_at` + document type's `retention_years` (or permanent for certain document types)
4. Citizen receives "completed" push notification

If any department rejects:
1. Submission status → `rejected`
2. Citizen receives "rejected" notification with the reviewer's citizen-visible annotation

## Citizen Experience

### Authentication

Citizens authenticate via **VNeID** (Vietnam's national digital identity) using OAuth 2.0 authorization code flow:
1. Open citizen app → tap "Đăng nhập bằng VNeID"
2. App requests authorize URL from backend (`GET /v1/citizen/auth/vneid/authorize-url`)
3. Backend returns a `/vneid/authorize` URL with client_id, redirect_uri, state
4. App opens URL in system browser → VNeID login page (mock: citizen selector dropdown)
5. After login, VNeID redirects to `citizen-app://auth/callback?code=xxx&state=yyy`
6. App sends authorization code to backend (`POST /v1/citizen/auth/vneid`)
7. Backend exchanges code with VNeID for access token and citizen identity
8. Citizen record created/updated, app-specific JWT issued

> **Demo mode:** The Mock VNeID server pre-loads 3 citizens (Phạm Văn Dũng, Nguyễn Thị Mai, Trần Văn Hùng). Login page is accessible at `/vneid/authorize`.

### Tracking

The citizen app shows:
- **Submissions list** — All submissions with status badges (in progress, completed, rejected), filter chips by status
- **Dossier list** — All case-based dossiers with status, case type name, and reference number
- **Workflow tracker** — Visual timeline with sequential nodes:
  - Completed step (green checkmark with timestamp)
  - Active step (blue highlight with department name)
  - Pending step (gray dot)
  - Delayed step (red warning indicator)
- **Reference number lookup** — Citizens can check dossier status by entering the reference number (`HS-YYYYMMDD-NNNNN`) without logging in. This public endpoint returns only privacy-safe information (status, case type, progress) without exposing the dossier UUID.
- **Annotations** — Citizen-visible comments from reviewers

### Notifications

Push notifications are sent via Alibaba Cloud EMAS when:

| Event | Notification |
|-------|-------------|
| Workflow step advances | "Your submission has moved to [Department Name]" |
| Information requested | "Additional information needed for your submission" |
| Submission completed | "Your submission has been approved" |
| Submission rejected | "Your submission has been rejected" |
| Step is delayed | "Processing of your submission is delayed" |

## Submission State Machine

```
draft
  │
  ▼ (first page uploaded)
scanning
  │
  ▼ (finalize-scan)
ocr_processing
  │
  ▼ (OCR + classification complete)
pending_classification
  │
  ▼ (staff confirms classification)
classified
  │
  ▼ (staff triggers routing)
pending_routing
  │
  ▼ (workflow created)
in_progress
  │
  ├──────────────────────┐
  ▼                      ▼
completed            rejected
```

## Duplicate Detection

Before classification is confirmed, the system checks for recent duplicate submissions:
- Same citizen + same document type + submitted within last 30 days + not rejected
- If found, staff is warned with details of the existing submission
- Staff can proceed anyway (legitimate re-submission) or cancel
