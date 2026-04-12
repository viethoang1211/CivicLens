# Data Model: Case-Based Dossier Submission

**Feature**: 002-case-based-submission  
**Date**: 2026-04-11  
**Depends On**: [research.md](research.md)

---

## Entity Overview

```
CaseType ──────────────────────────────────────────────────┐
  │ 1                                                       │ 1
  │ N                                                       │ N
CaseTypeRoutingStep          DocumentRequirementGroup ◄────┘
  │ N                           │ 1
  │ 1                           │ N
Department              DocumentRequirementSlot
                                │ N
                                │ 1
                            DocumentType (existing)

Dossier ────────────────── CaseType (N:1)
  │ 1                      Citizen (N:1)
  │ N
DossierDocument ─────────── DocumentRequirementSlot (N:1, nullable*)
  │ 1
  │ N
ScannedPage (MODIFIED: add nullable dossier_document_id FK)

WorkflowStep (MODIFIED: add nullable dossier_id FK; submission_id becomes nullable)
  │ N──1 Dossier
  │ N──1 Department
  │ N──1 StaffMember (optional reviewer)
```

_* A DossierDocument may be uploaded against a slot (normal case) or free-form (override, slot = null)._

---

## New Entities

### `CaseType`

Top-level category of administrative request. Replaces `DocumentType` as the routing driver for new submissions.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default uuid4 | |
| `name` | VARCHAR(255) | NOT NULL | Vietnamese display name |
| `code` | VARCHAR(50) | UNIQUE, NOT NULL | Machine-readable code, e.g. `HOUSEHOLD_BIZ_REG` |
| `description` | TEXT | nullable | For admin UI |
| `is_active` | BOOLEAN | NOT NULL, default true | Inactive = hidden from staff selector |
| `retention_years` | INTEGER | NOT NULL, default 5 | Data retention per gov regulations |
| `retention_permanent` | BOOLEAN | NOT NULL, default false | |
| `created_at` | TIMESTAMPTZ | NOT NULL, server_default now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, server_default now(), onupdate | |

**Relationships**:
- `routing_steps` → `CaseTypeRoutingStep[]` (ordered by `step_order`)
- `requirement_groups` → `DocumentRequirementGroup[]` (ordered by `group_order`)
- `dossiers` → `Dossier[]`

**Indices**: `idx_case_type_code` UNIQUE on `code`; `idx_case_type_is_active` on `is_active`

---

### `CaseTypeRoutingStep`

Ordered sequence of departments a dossier of a given case type must pass through. Mirrors `RoutingRule` but keyed to `CaseType`.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default uuid4 | |
| `case_type_id` | UUID | FK → case_type.id, NOT NULL | |
| `department_id` | UUID | FK → department.id, NOT NULL | |
| `step_order` | SMALLINT | NOT NULL | 1-based |
| `expected_duration_hours` | INTEGER | nullable | SLA hint |
| `required_clearance_level` | SMALLINT | NOT NULL, default 0 | Minimum staff clearance |
| `created_at` | TIMESTAMPTZ | NOT NULL, server_default now() | |

**Constraints**:
- UNIQUE `(case_type_id, step_order)` — no two steps at same position
- UNIQUE `(case_type_id, department_id)` — a department appears once per case type

---

### `DocumentRequirementGroup`

A single logical document requirement for a case type (e.g., "Proof of Premises"). May offer multiple acceptable document types (OR logic) via child `DocumentRequirementSlot` records.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default uuid4 | |
| `case_type_id` | UUID | FK → case_type.id, NOT NULL | |
| `group_order` | SMALLINT | NOT NULL | Display order in checklist |
| `label` | VARCHAR(255) | NOT NULL | Human-readable, e.g. "Proof of Premises / Giấy tờ địa điểm" |
| `is_mandatory` | BOOLEAN | NOT NULL, default true | False = entire group is optional |
| `created_at` | TIMESTAMPTZ | NOT NULL, server_default now() | |

**Constraints**:
- UNIQUE `(case_type_id, group_order)`

**Business Rule**: Group is satisfied when at least one of its `DocumentRequirementSlot` records is fulfilled by an uploaded `DossierDocument`.

---

### `DocumentRequirementSlot`

One acceptable document type within a `DocumentRequirementGroup`. Multiple slots in the same group implement OR logic.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default uuid4 | |
| `group_id` | UUID | FK → document_requirement_group.id, NOT NULL | |
| `document_type_id` | UUID | FK → document_type.id, NOT NULL | Reuses existing `DocumentType` for AI validation prompt |
| `label_override` | VARCHAR(255) | nullable | Custom display label (overrides `document_type.name` in UI) |
| `created_at` | TIMESTAMPTZ | NOT NULL, server_default now() | |

**Constraints**:
- UNIQUE `(group_id, document_type_id)` — same doc type not offered twice in same group

---

### `Dossier`

A citizen's filing package for a specific `CaseType`. The dossier is the unit of submission, tracking, and routing.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default uuid4 | |
| `reference_number` | VARCHAR(20) | UNIQUE, nullable | Set on submit: `HS-YYYYMMDD-NNNNN` |
| `citizen_id` | UUID | FK → citizen.id, NOT NULL | |
| `submitted_by_staff_id` | UUID | FK → staff_member.id, NOT NULL | Staff who created/submitted the dossier |
| `case_type_id` | UUID | FK → case_type.id, NOT NULL | |
| `status` | VARCHAR(30) | NOT NULL, default `draft` | See state machine below |
| `security_classification` | SMALLINT | NOT NULL, default 0, CHECK 0–3 | |
| `priority` | VARCHAR(10) | NOT NULL, default `normal` | `normal` \| `urgent` |
| `rejection_reason` | TEXT | nullable | Populated when status = `rejected` |
| `submitted_at` | TIMESTAMPTZ | nullable | Set when status transitions to `submitted` |
| `completed_at` | TIMESTAMPTZ | nullable | Set when status = `completed` or `rejected` |
| `retention_expires_at` | TIMESTAMPTZ | nullable | Computed from `case_type.retention_years` on submit |
| `created_at` | TIMESTAMPTZ | NOT NULL, server_default now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, server_default now(), onupdate | |

**State Machine**:
```
draft ──► scanning ──► ready ──► submitted ──► in_progress ──► completed
                                    │                              ▲
                                    └────────────────► rejected ──┘
                                                  (resubmit possible)
```

| Status | Meaning |
|--------|---------|
| `draft` | Created, no documents uploaded yet |
| `scanning` | Staff uploading documents |
| `ready` | All mandatory groups satisfied; ready to submit |
| `submitted` | Staff confirmed submission; reference number assigned |
| `in_progress` | Routed to first department; workflow steps active |
| `completed` | All departments approved |
| `rejected` | A department rejected the dossier |

**Indices**:
- `idx_dossier_reference_number` UNIQUE on `reference_number` WHERE `reference_number IS NOT NULL`
- `idx_dossier_citizen_id` on `citizen_id`
- `idx_dossier_status` on `status`
- `idx_dossier_case_type_id` on `case_type_id`

---

### `DossierDocument`

A single document uploaded to a dossier, fulfilling (or attempted to fulfill) a document slot requirement.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default uuid4 | |
| `dossier_id` | UUID | FK → dossier.id, NOT NULL | |
| `requirement_slot_id` | UUID | FK → document_requirement_slot.id, nullable | Null = free-form upload not bound to a slot |
| `document_type_id` | UUID | FK → document_type.id, nullable | Actual detected or staff-confirmed doc type |
| `ai_match_result` | JSONB | nullable | `{"match": bool, "confidence": float, "reason": str}` |
| `ai_match_overridden` | BOOLEAN | NOT NULL, default false | True if staff dismissed AI warning |
| `staff_notes` | TEXT | nullable | Optional staff annotation |
| `created_at` | TIMESTAMPTZ | NOT NULL, server_default now() | |

**Relationships**:
- `scanned_pages` → `ScannedPage[]` (via new `dossier_document_id` FK on `ScannedPage`)

**Constraints**:
- UNIQUE `(dossier_id, requirement_slot_id)` WHERE `requirement_slot_id IS NOT NULL` — one document per slot per dossier

---

## Modified Entities

### `ScannedPage` (MODIFIED)

Add a nullable `dossier_document_id` FK. Either `submission_id` or `dossier_document_id` is set (never both, never neither).

**New column**:
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `dossier_document_id` | UUID | FK → dossier_document.id, nullable | Set for case-based dossier pages |

**Modified constraint**: `submission_id` changes from NOT NULL to nullable.  
**New check constraint**: `(submission_id IS NULL) <> (dossier_document_id IS NULL)` — exactly one owner.

---

### `WorkflowStep` (MODIFIED)

Add a nullable `dossier_id` FK. Either `submission_id` or `dossier_id` is set.

**New column**:
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `dossier_id` | UUID | FK → dossier.id, nullable | Set for case-based dossier workflow |

**Modified constraint**: `submission_id` changes from NOT NULL to nullable.  
**New check constraint**: `(submission_id IS NULL) <> (dossier_id IS NULL)` — exactly one owner.  
**Modified unique constraint**: `(dossier_id, step_order)` added alongside existing `(submission_id, step_order)`.

---

## Validation Rules

### Dossier Completeness

A dossier is **complete** (eligible for submission) when:

```
for each group in case_type.requirement_groups where group.is_mandatory = true:
    assert any(
        dossier_document exists with requirement_slot_id in group.slots
    )
```

Implementation: `DossierService.check_completeness(dossier_id)` returns:
```json
{
  "complete": false,
  "missing_groups": [
    { "group_id": "...", "label": "Proof of Premises / Giấy tờ địa điểm" }
  ]
}
```

### Reference Number Generation

```python
def generate_reference_number(date: date, daily_sequence: int) -> str:
    return f"HS-{date.strftime('%Y%m%d')}-{daily_sequence:05d}"
```

Daily sequence: `SELECT COUNT(*) FROM dossier WHERE submitted_at::date = today` + 1, executed inside the submission transaction with a row-level lock on a `DossierDailySequence` counter table (or a PostgreSQL sequence reset daily via a scheduled job).

Simpler alternative: use a PostgreSQL sequence per-day via `nextval` on a day-partitioned sequence — document as future optimization; for v1 use a transactional COUNT + 1.

---

## Migration Plan

**Migration file**: `alembic/versions/0002_case_based_submission.py`

Order of operations:
1. Create `case_type` table
2. Create `case_type_routing_step` table
3. Create `document_requirement_group` table
4. Create `document_requirement_slot` table
5. Create `dossier` table
6. Create `dossier_document` table
7. ALTER `scanned_page`: add nullable `dossier_document_id` FK; alter `submission_id` to nullable; add CHECK constraint
8. ALTER `workflow_step`: add nullable `dossier_id` FK; alter `submission_id` to nullable; add CHECK constraint; add UNIQUE `(dossier_id, step_order)`
9. Run `seed_case_types()` inline (idempotent; skips existing)

**Rollback**: All ALTER steps use Alembic `op.drop_constraint` / `op.drop_column`; new tables use `op.drop_table`.
