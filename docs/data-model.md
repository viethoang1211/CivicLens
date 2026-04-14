# Data Model

## Entity Relationship Diagram

```
┌──────────┐       ┌─────────────┐       ┌────────────┐
│ Citizen  │       │ StaffMember │──────>│ Department │
└────┬─────┘       └──────┬──────┘       └─────┬──────┘
     │                    │                     │
     │         ┌──────────┴──────────┐          │
     │         ▼                     ▼          │
     │  ┌──────────────┐    ┌────────────────┐  │
     │  │ Submission   │    │    Dossier     │  │
     │  │              │    │               │  │
     │  │ citizen_id   │    │ citizen_id    │  │
     │  │ doc_type_id  │    │ case_type_id  │  │
     │  │ status       │    │ ref_number    │  │
     │  └──┬───────┬───┘    │ status        │  │
     │     │       │        └──┬───────┬────┘  │
     │     ▼       ▼           │       │       │
     │ ┌────────┐ ┌─────────┐ │       │       │
     │ │Scanned │ │Workflow │<┘       │       │
     │ │Page    │ │Step     │◄────────┘       │
     │ │        │ │         │                 │
     │ │oss_key │ │dept_id  │                 │
     │ │ocr_text│ │status   │                 │
     │ └────────┘ └────┬────┘                 │
     │                 ▼                      │
     │          ┌──────────────┐              │
     │          │StepAnnotation│              │
     │          └──────────────┘              │
     │                                        │
     │    ┌──────────────┐                    │
     │    │  CaseType    │                    │
     │    │              │◄────────────────────┘
     │    │ code, name   │    CaseTypeRoutingStep
     │    └──────┬───────┘
     │           │
     │    ┌──────┴───────┐
     │    │  DocReqGroup │
     │    │              │
     │    │ is_mandatory │
     │    └──────┬───────┘
     │           │
     │    ┌──────┴───────┐
     │    │ DocReqSlot   │
     │    │              │
     │    │doc_type_id   │
     │    └──────────────┘
     │
     │    ┌────────────────┐
     ▼    │DossierDocument │──── ScannedPage
          │                │
          │ai_match_result │
          │slot_id         │
          └────────────────┘

┌───────────────┐       ┌──────────────┐
│ AuditLogEntry │       │ Notification │
└───────────────┘       └──────────────┘
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

### CaseType

Configurable case type defining a bundle of required documents and a routing template.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `name` | String | Display name (Vietnamese) |
| `code` | String (unique) | Machine code (e.g., `HOUSEHOLD_BIZ_REG`) |
| `description` | Text | Admin description |
| `is_active` | Boolean | Only active types available for new dossiers |
| `retention_years` | Integer | Years to retain after completion |
| `retention_permanent` | Boolean | If true, retained permanently |
| `created_at` | Timestamp | |
| `updated_at` | Timestamp | |

### CaseTypeRoutingStep

Sequential department routing template for a case type (analogous to `RoutingRule` but linked to case types instead of document types).

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `case_type_id` | UUID (FK → CaseType) | Parent case type |
| `department_id` | UUID (FK → Department) | Target department |
| `step_order` | SmallInt | Position in sequence |
| `expected_duration_hours` | Integer | SLA tracking |
| `required_clearance_level` | SmallInt | Minimum clearance for this step |

**Constraints:** Unique `(case_type_id, step_order)`, Unique `(case_type_id, department_id)`

### DocumentRequirementGroup

A group of alternative documents within a case type. Fulfilling any one slot in the group satisfies the requirement.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `case_type_id` | UUID (FK → CaseType) | Parent case type |
| `group_order` | SmallInt | Display order within case type |
| `label` | String | Group label (e.g., "Giấy tờ tùy thân") |
| `is_mandatory` | Boolean | If true, must be fulfilled to submit dossier |

**Constraint:** Unique `(case_type_id, group_order)`

### DocumentRequirementSlot

A specific document type option within a requirement group. OR-logic: any fulfilled slot satisfies the group.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `group_id` | UUID (FK → DocumentRequirementGroup) | Parent group |
| `document_type_id` | UUID (FK → DocumentType) | Expected document type |
| `label_override` | String | Custom label (falls back to DocumentType.name) |

**Constraint:** Unique `(group_id, document_type_id)`

### Dossier

A case-based submission containing multiple documents. Central entity for the hồ sơ workflow.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `reference_number` | String (unique, nullable) | Citizen-facing reference (e.g., `HS-20260411-00001`), assigned on submit |
| `citizen_id` | UUID (FK → Citizen) | Submitting citizen |
| `submitted_by_staff_id` | UUID (FK → StaffMember) | Staff who created the dossier |
| `case_type_id` | UUID (FK → CaseType) | Which case type this dossier follows |
| `status` | String | `draft`, `scanning`, `ready`, `submitted`, `in_progress`, `completed`, `rejected` |
| `security_classification` | SmallInt (0–3) | Document sensitivity level |
| `priority` | String | `low`, `normal`, `high`, `urgent` |
| `requirement_snapshot` | JSONB (nullable) | Frozen snapshot of case type requirement groups/slots at creation time. Used by guided capture UI and completeness check. Null for dossiers created before migration 0003. |
| `rejection_reason` | Text | Populated when status = `rejected` |
| `submitted_at` | Timestamp | When dossier was submitted |
| `completed_at` | Timestamp | When processing completed |
| `retention_expires_at` | Timestamp | Computed from case type retention rules |
| `created_at` | Timestamp | |
| `updated_at` | Timestamp | |

**Constraint:** `CHECK (security_classification BETWEEN 0 AND 3)`

### DossierDocument

One uploaded document within a dossier, linked to a requirement slot.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `dossier_id` | UUID (FK → Dossier) | Parent dossier |
| `requirement_slot_id` | UUID (FK → DocumentRequirementSlot, nullable) | Which slot this fulfills |
| `document_type_id` | UUID (FK → DocumentType, nullable) | Copied from slot for convenience |
| `ai_match_result` | JSONB | `{"match": bool, "confidence": float, "reason": str}` |
| `ai_match_overridden` | Boolean | Staff overrode AI decision |
| `staff_notes` | Text | Staff notes |
| `created_at` | Timestamp | |

**Constraint:** Unique `(dossier_id, requirement_slot_id)`

### ScannedPage

Individual page within a submission or dossier document, with image storage and OCR results.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `submission_id` | UUID (FK → Submission, nullable) | Parent submission (legacy mode) |
| `dossier_document_id` | UUID (FK → DossierDocument, nullable) | Parent dossier document (case-based mode) |
| `page_number` | SmallInt | Page order (1, 2, 3...) |
| `image_oss_key` | String | Alibaba Cloud OSS object key |
| `ocr_raw_text` | Text | Raw AI-extracted text |
| `ocr_corrected_text` | Text | Staff-corrected text (null if no correction) |
| `ocr_confidence` | Float | OCR confidence score (0.0–1.0) |
| `image_quality_score` | Float | Image quality assessment score |
| `synced_at` | Timestamp | When image was synced from offline queue |

**Constraint:** `CHECK ((submission_id IS NULL) <> (dossier_document_id IS NULL))` — exactly one owner

### WorkflowStep

Single step in the sequential department processing workflow. Can belong to either a Submission (legacy) or a Dossier (case-based).

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `submission_id` | UUID (FK → Submission, nullable) | Parent submission (legacy mode) |
| `dossier_id` | UUID (FK → Dossier, nullable) | Parent dossier (case-based mode) |
| `department_id` | UUID (FK → Department) | Assigned department |
| `step_order` | SmallInt | Position in sequence |
| `status` | String | `pending`, `active`, `completed` |
| `assigned_reviewer_id` | UUID (FK → StaffMember, nullable) | Staff who reviewed |
| `started_at` | Timestamp | When step became active |
| `completed_at` | Timestamp | When step was completed |
| `expected_complete_by` | Timestamp | SLA deadline |
| `result` | String | `approved`, `rejected`, `needs_info` (null if pending) |

**Constraints:**
- `CHECK ((submission_id IS NULL) <> (dossier_id IS NULL))` — exactly one owner
- Unique `(submission_id, step_order)`
- Unique `(dossier_id, step_order)`

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
| `scanned_page` | `dossier_document_id` | Document page retrieval |
| `workflow_step` | `submission_id, step_order` (unique) | Step lookup (legacy) |
| `workflow_step` | `dossier_id, step_order` (unique) | Step lookup (case-based) |
| `dossier` | `citizen_id` | Citizen's dossier list |
| `dossier` | `reference_number` (unique) | Public reference lookup |
| `dossier` | `case_type_id, status` | Case type filtered queries |
| `dossier_document` | `dossier_id, requirement_slot_id` (unique) | Slot fulfillment check |
| `case_type` | `code` (unique) | Seed idempotency |
| `audit_log_entry` | `actor_id` | Actor audit history |
| `audit_log_entry` | `resource_type, resource_id` | Resource audit history |
