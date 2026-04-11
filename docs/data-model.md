# Data Model

## Entity Relationship Diagram

```
┌──────────┐       ┌─────────────┐       ┌────────────┐
│ Citizen  │       │ StaffMember │──────>│ Department │
└────┬─────┘       └──────┬──────┘       └─────┬──────┘
     │                    │                     │
     │                    │                     │
     ▼                    ▼                     ▼
┌──────────────────────────────┐       ┌──────────────┐
│        Submission            │       │ RoutingRule  │
│                              │<──────│              │
│  citizen_id (FK)             │       │ doc_type_id  │
│  submitted_by_staff_id (FK)  │       │ dept_id      │
│  document_type_id (FK)       │       │ step_order   │
│  security_classification     │       └──────────────┘
│  status (state machine)      │              │
│  template_data (JSONB)       │              │
└──────┬───────────┬───────────┘              │
       │           │                          │
       ▼           ▼                          │
┌─────────────┐  ┌──────────────┐             │
│ ScannedPage │  │ WorkflowStep │<────────────┘
│             │  │              │
│ image_oss_  │  │ dept_id      │
│   key       │  │ step_order   │
│ ocr_text    │  │ status       │
│ confidence  │  │ reviewer_id  │
└─────────────┘  └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │StepAnnotation│
                 │              │
                 │ author_id    │
                 │ type         │
                 │ content      │
                 │ target_       │
                 │   citizen    │
                 └──────────────┘

┌───────────────┐       ┌──────────────┐
│ AuditLogEntry │       │ Notification │
│               │       │              │
│ actor_type    │       │ citizen_id   │
│ actor_id      │       │ submission_id│
│ action        │       │ type         │
│ resource_type │       │ title, body  │
│ resource_id   │       │ is_read      │
│ clearance_    │       └──────────────┘
│   check_result│
│ metadata (J)  │
└───────────────┘
```

## Core Entities

### Citizen

Represents a citizen who interacts with the system via the citizen mobile app.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `vneid_subject_id` | String (unique) | VNeID identity subject ID |
| `full_name` | String | Citizen's full name |
| `id_number` | String (unique) | CCCD national ID number |
| `phone_number` | String | Contact phone |
| `email` | String | Contact email |
| `push_token` | String | EMAS push notification device token |
| `created_at` | Timestamp | Registration date |
| `updated_at` | Timestamp | Last update |

### StaffMember

Government staff user with department assignment and clearance level.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `employee_id` | String (unique) | Staff employee ID (e.g., "NV001") |
| `full_name` | String | Staff name |
| `department_id` | UUID (FK → Department) | Assigned department |
| `clearance_level` | SmallInt (0–3) | Security clearance: 0=Unclassified, 1=Confidential, 2=Secret, 3=Top Secret |
| `role` | String | Staff role (e.g., "reviewer", "admin") |
| `is_active` | Boolean | Active/deactivated |
| `password_hash` | String | bcrypt password hash |
| `created_at` | Timestamp | |
| `updated_at` | Timestamp | |

**Constraint:** `CHECK (clearance_level BETWEEN 0 AND 3)`

### Department

Organizational unit within the government office.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `name` | String | Department name (Vietnamese) |
| `code` | String (unique) | Short code (e.g., "JUDICIAL") |
| `description` | Text | Description |
| `min_clearance_level` | SmallInt | Minimum clearance for department staff |
| `is_active` | Boolean | Active/deactivated |

### DocumentType

Configurable document category with template schema and AI classification prompt.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `name` | String | Human-readable name |
| `code` | String (unique) | Machine code (e.g., "BIRTH_CERT") |
| `template_schema` | JSONB | JSON Schema defining structured fields for this document type |
| `classification_prompt` | Text | Prompt used by the AI model to identify this document type |
| `retention_years` | Integer | Number of years to retain after completion |
| `retention_permanent` | Boolean | If true, document is retained permanently |

### RoutingRule

Defines the sequential department workflow for a document type.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `document_type_id` | UUID (FK → DocumentType) | Which document type |
| `department_id` | UUID (FK → Department) | Which department handles this step |
| `step_order` | SmallInt | Position in sequence (1, 2, 3...) |
| `expected_duration_hours` | Integer | Expected processing time for SLA tracking |
| `required_clearance_level` | SmallInt | Minimum clearance needed for this step |

**Constraints:**
- Unique: `(document_type_id, department_id)` — a department appears once per document type
- Unique: `(document_type_id, step_order)` — step orders are unique per document type

### Submission

Central entity representing a citizen's document submission through its entire lifecycle.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `citizen_id` | UUID (FK → Citizen) | Submitting citizen |
| `submitted_by_staff_id` | UUID (FK → StaffMember) | Staff who scanned the document |
| `document_type_id` | UUID (FK → DocumentType) | Classified document type (null until classified) |
| `classification_confidence` | Float | AI classification confidence score |
| `classification_method` | String | "auto" or "manual" |
| `security_classification` | SmallInt (0–3) | Document sensitivity level |
| `status` | String | Current state (see state machine below) |
| `priority` | String | "normal" or "urgent" |
| `template_data` | JSONB | Structured fields extracted/filled for the document type |
| `submitted_at` | Timestamp | When originally submitted |
| `completed_at` | Timestamp | When completed or rejected |
| `retention_expires_at` | Timestamp | When document can be archived/deleted |
| `created_at` | Timestamp | |
| `updated_at` | Timestamp | |

**Constraint:** `CHECK (security_classification BETWEEN 0 AND 3)`

**Status values:** `draft`, `scanning`, `ocr_processing`, `pending_classification`, `classified`, `pending_routing`, `in_progress`, `completed`, `rejected`

### ScannedPage

Individual page within a submission, with image storage and OCR results.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `submission_id` | UUID (FK → Submission) | Parent submission |
| `page_number` | SmallInt | Page order (1, 2, 3...) |
| `image_oss_key` | String | Alibaba Cloud OSS object key |
| `ocr_raw_text` | Text | Raw AI-extracted text |
| `ocr_corrected_text` | Text | Staff-corrected text (null if no correction) |
| `ocr_confidence` | Float | OCR confidence score (0.0–1.0) |
| `image_quality_score` | Float | Image quality assessment score |
| `synced_at` | Timestamp | When image was synced from offline queue |

### WorkflowStep

Single step in the sequential department processing workflow.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `submission_id` | UUID (FK → Submission) | Parent submission |
| `department_id` | UUID (FK → Department) | Assigned department |
| `step_order` | SmallInt | Position in sequence |
| `status` | String | `pending`, `active`, `completed` |
| `assigned_reviewer_id` | UUID (FK → StaffMember, nullable) | Staff who reviewed |
| `started_at` | Timestamp | When step became active |
| `completed_at` | Timestamp | When step was completed |
| `expected_complete_by` | Timestamp | SLA deadline |
| `result` | String | `approved`, `rejected`, `needs_info` (null if pending) |

**Constraint:** Unique `(submission_id, step_order)`

A step is considered **delayed** when `status = 'active' AND NOW() > expected_complete_by`.

### StepAnnotation

Comments, decisions, and consultations attached to workflow steps.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `workflow_step_id` | UUID (FK → WorkflowStep) | Parent step |
| `author_id` | UUID (FK → StaffMember) | Staff who created |
| `annotation_type` | String | `approved`, `rejected`, `needs_info`, `consultation` |
| `content` | Text | The annotation text |
| `target_citizen` | Boolean | If true, visible to the citizen in their app |
| `created_at` | Timestamp | |

### AuditLogEntry

Immutable, append-only log of all security-relevant actions.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `actor_type` | String | `staff` or `citizen` |
| `actor_id` | UUID | ID of the acting user |
| `action` | String | Action performed (e.g., `view`, `review_approved`, `route`) |
| `resource_type` | String | Type of resource accessed (e.g., `submission`, `workflow_step`) |
| `resource_id` | UUID | ID of resource accessed |
| `clearance_check_result` | String | `granted` or `denied` |
| `metadata_` | JSONB | Additional context (path, method, etc.) |
| `created_at` | Timestamp | When the action occurred |

**Design:** This table is append-only. No UPDATE or DELETE operations are permitted. Records are also shipped to Alibaba Cloud SLS for long-term retention.

### Notification

Push notification records for citizen status updates.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `citizen_id` | UUID (FK → Citizen) | Target citizen |
| `submission_id` | UUID (FK → Submission) | Related submission |
| `type` | String | `step_advanced`, `info_requested`, `completed`, `delayed` |
| `title` | String | Notification title |
| `body` | Text | Notification body text |
| `is_read` | Boolean | Read status |
| `sent_at` | Timestamp | When sent |
| `read_at` | Timestamp | When read by citizen |

## Database Security

### Row-Level Security (RLS)

PostgreSQL RLS policies are enabled on `submission` and `scanned_page` tables:

```sql
-- Submissions: staff can only see documents at or below their clearance level
CREATE POLICY submission_clearance ON submission
  USING (security_classification <= current_setting('app.clearance_level')::int);

-- Scanned pages: inherits submission clearance via join
CREATE POLICY page_clearance ON scanned_page
  USING (submission_id IN (
    SELECT id FROM submission
    WHERE security_classification <= current_setting('app.clearance_level')::int
  ));
```

The `app.clearance_level` session variable is set by the API's database dependency when creating a session for authenticated staff requests.

## Indexes

| Table | Index | Purpose |
|-------|-------|---------|
| `submission` | `citizen_id` | Citizen's submission list |
| `submission` | `department_id` (via workflow_step) | Department queue |
| `scanned_page` | `submission_id, page_number` | Page retrieval |
| `workflow_step` | `submission_id, step_order` (unique) | Step lookup |
| `audit_log_entry` | `actor_id` | Actor audit history |
| `audit_log_entry` | `resource_type, resource_id` | Resource audit history |
