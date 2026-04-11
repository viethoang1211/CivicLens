# Data Model: AI-Powered Public Sector Document Processing

**Feature Branch**: `001-ai-document-processing`
**Date**: 2026-04-10

## Entities

### Citizen

Represents a person who submits documents and tracks their processing status.

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Internal identifier |
| vneid_subject_id | VARCHAR(64) | UNIQUE, NOT NULL | VNeID identity subject ID |
| full_name | VARCHAR(255) | NOT NULL | Full legal name from VNeID |
| id_number | VARCHAR(20) | UNIQUE, NOT NULL | CCCD number (Citizen ID) |
| phone_number | VARCHAR(15) | | Mobile phone for notifications |
| email | VARCHAR(255) | | Optional email |
| push_token | TEXT | | Device push notification token |
| created_at | TIMESTAMPTZ | NOT NULL | Registration timestamp |
| updated_at | TIMESTAMPTZ | NOT NULL | Last update |

### StaffMember

A government employee who scans, classifies, reviews, or routes documents.

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | Internal identifier |
| employee_id | VARCHAR(50) | UNIQUE, NOT NULL | Government employee number |
| full_name | VARCHAR(255) | NOT NULL | |
| department_id | UUID | FK → Department | Primary department assignment |
| clearance_level | SMALLINT | NOT NULL, CHECK(0-3) | 0=Unclassified, 1=Confidential, 2=Secret, 3=TopSecret |
| role | VARCHAR(50) | NOT NULL | e.g., intake_staff, reviewer, supervisor, admin |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

### Department

An organizational unit responsible for one or more workflow steps.

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | Department name |
| code | VARCHAR(20) | UNIQUE, NOT NULL | Short code (e.g., "LAND", "CIVIL") |
| description | TEXT | | |
| min_clearance_level | SMALLINT | NOT NULL, DEFAULT 0 | Minimum clearance in this department |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | |
| created_at | TIMESTAMPTZ | NOT NULL | |

### DocumentType

A category of administrative document with associated template and routing rules.

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | e.g., "Birth Certificate Request" |
| code | VARCHAR(50) | UNIQUE, NOT NULL | Machine-readable code |
| description | TEXT | | |
| template_schema | JSONB | NOT NULL | Field definitions for the template |
| classification_prompt | TEXT | | Prompt hints for AI classification |
| retention_years | INTEGER | NOT NULL, DEFAULT 5 | Retention period after case closure |
| retention_permanent | BOOLEAN | NOT NULL, DEFAULT false | Override for permanent retention |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

### RoutingRule

Defines the sequential department routing for a document type.

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | |
| document_type_id | UUID | FK → DocumentType, NOT NULL | |
| department_id | UUID | FK → Department, NOT NULL | |
| step_order | SMALLINT | NOT NULL | Sequential position (1, 2, 3…) |
| expected_duration_hours | INTEGER | | Expected processing time at this step |
| required_clearance_level | SMALLINT | NOT NULL, DEFAULT 0 | Minimum clearance for this step |
| created_at | TIMESTAMPTZ | NOT NULL | |

**Unique constraint**: (document_type_id, step_order)
**Unique constraint**: (document_type_id, department_id)

### Submission

A citizen's complete submission — one or more scanned documents for a single request.

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | |
| citizen_id | UUID | FK → Citizen, NOT NULL | |
| submitted_by_staff_id | UUID | FK → StaffMember, NOT NULL | Staff who scanned |
| document_type_id | UUID | FK → DocumentType | NULL until classified |
| classification_confidence | DECIMAL(5,4) | | AI confidence score (0.0000–1.0000) |
| classification_method | VARCHAR(20) | | "ai", "manual", "ai_confirmed" |
| security_classification | SMALLINT | NOT NULL, CHECK(0-3) | Document security level |
| status | VARCHAR(30) | NOT NULL | See state machine below |
| priority | VARCHAR(10) | NOT NULL, DEFAULT 'normal' | "normal", "urgent" |
| template_data | JSONB | | Extracted/corrected fields matching template_schema |
| submitted_at | TIMESTAMPTZ | NOT NULL | |
| completed_at | TIMESTAMPTZ | | When final response issued |
| retention_expires_at | TIMESTAMPTZ | | Computed: completed_at + retention period |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

**Submission Status State Machine**:
```
draft → scanning → ocr_processing → pending_classification →
classified → pending_routing → in_progress → completed
                                          ↘ rejected
```

### ScannedPage

Individual scanned page images belonging to a submission.

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | |
| submission_id | UUID | FK → Submission, NOT NULL | |
| page_number | SMALLINT | NOT NULL | Order within submission |
| image_oss_key | VARCHAR(512) | NOT NULL | OSS object key for scanned image |
| ocr_raw_text | TEXT | | Raw OCR output |
| ocr_corrected_text | TEXT | | Staff-corrected text |
| ocr_confidence | DECIMAL(5,4) | | OCR confidence score |
| image_quality_score | DECIMAL(5,4) | | Scan quality assessment |
| synced_at | TIMESTAMPTZ | | When image uploaded from device |
| created_at | TIMESTAMPTZ | NOT NULL | |

**Unique constraint**: (submission_id, page_number)

### WorkflowStep

A single node in a submission's processing workflow.

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | |
| submission_id | UUID | FK → Submission, NOT NULL | |
| department_id | UUID | FK → Department, NOT NULL | |
| step_order | SMALLINT | NOT NULL | Position in sequence |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | pending, active, completed, delayed |
| assigned_reviewer_id | UUID | FK → StaffMember | |
| started_at | TIMESTAMPTZ | | When step became active |
| completed_at | TIMESTAMPTZ | | |
| expected_complete_by | TIMESTAMPTZ | | Deadline based on routing rule duration |
| result | VARCHAR(20) | | "approved", "rejected", "needs_info" |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

**Unique constraint**: (submission_id, step_order)

### StepAnnotation

Comments, notes, or requests attached to a workflow step by reviewers.

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | |
| workflow_step_id | UUID | FK → WorkflowStep, NOT NULL | |
| author_id | UUID | FK → StaffMember, NOT NULL | |
| annotation_type | VARCHAR(20) | NOT NULL | "comment", "request_info", "consultation", "decision" |
| content | TEXT | NOT NULL | |
| target_citizen | BOOLEAN | NOT NULL, DEFAULT false | If true, visible to citizen |
| created_at | TIMESTAMPTZ | NOT NULL | |

### AuditLogEntry

Immutable record of every document access or action.

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | |
| actor_type | VARCHAR(10) | NOT NULL | "staff", "citizen", "system" |
| actor_id | UUID | NOT NULL | StaffMember or Citizen ID |
| action | VARCHAR(50) | NOT NULL | "view", "scan", "classify", "route", "approve", "reject", etc. |
| resource_type | VARCHAR(30) | NOT NULL | "submission", "scanned_page", "workflow_step" |
| resource_id | UUID | NOT NULL | |
| clearance_check_result | VARCHAR(10) | | "granted", "denied" |
| metadata | JSONB | | Additional context (IP, device, etc.) |
| created_at | TIMESTAMPTZ | NOT NULL | Immutable timestamp |

**Note**: AuditLogEntry is append-only — no UPDATE or DELETE allowed. Also written to SLS for long-term retention and search.

### Notification

Push notifications sent to citizens.

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | UUID | PK | |
| citizen_id | UUID | FK → Citizen, NOT NULL | |
| submission_id | UUID | FK → Submission | |
| type | VARCHAR(30) | NOT NULL | "step_advanced", "info_requested", "completed", "delayed" |
| title | VARCHAR(255) | NOT NULL | |
| body | TEXT | NOT NULL | |
| is_read | BOOLEAN | NOT NULL, DEFAULT false | |
| sent_at | TIMESTAMPTZ | NOT NULL | |
| read_at | TIMESTAMPTZ | | |

## Relationships

```
Citizen 1──* Submission
StaffMember 1──* Submission (submitted_by)
StaffMember *──1 Department
Department 1──* RoutingRule
DocumentType 1──* RoutingRule
DocumentType 1──* Submission
Submission 1──* ScannedPage
Submission 1──* WorkflowStep
WorkflowStep *──1 Department
WorkflowStep 1──* StepAnnotation
StaffMember 1──* StepAnnotation (author)
StaffMember 1──* WorkflowStep (assigned_reviewer)
Citizen 1──* Notification
```

## Validation Rules

1. `StaffMember.clearance_level >= Submission.security_classification` — enforced via RLS policy for any access
2. `RoutingRule.required_clearance_level <= Department.min_clearance_level` — validated on rule creation
3. `WorkflowStep.step_order` must be sequential (1, 2, 3…) with no gaps per submission
4. `Submission.template_data` must validate against `DocumentType.template_schema` when finalized
5. `Submission.retention_expires_at` = `completed_at + DocumentType.retention_years` (NULL if retention_permanent)
6. `ScannedPage.page_number` must be sequential starting from 1 per submission

## Indexes (Key)

- `submission(citizen_id, status)` — citizen app: list my submissions
- `submission(document_type_id, status)` — department queues
- `workflow_step(submission_id, step_order)` — workflow progression
- `workflow_step(department_id, status)` — department work queue
- `audit_log_entry(resource_type, resource_id, created_at)` — audit trail queries
- `audit_log_entry(actor_id, created_at)` — actor history
