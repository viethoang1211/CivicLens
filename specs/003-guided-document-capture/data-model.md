# Data Model: Guided Document Capture

**Feature**: 003-guided-document-capture  
**Date**: 2026-04-14  
**Source**: [research.md](research.md) R-001 (snapshot strategy), [spec.md](spec.md) FR-014

---

## Overview

Feature 003 adds **one new column** to the existing `dossier` table. All other entities are reused from Features 001 and 002 without modification. The guided capture flow is a UI-layer concept that maps to the existing `Dossier → DossierDocument → ScannedPage` data pipeline.

---

## Schema Change: `dossier` Table

### New Column: `requirement_snapshot`

| Attribute | Value |
|-----------|-------|
| **Column** | `requirement_snapshot` |
| **Type** | `JSONB` |
| **Nullable** | `true` (null for legacy dossiers created before migration) |
| **Default** | `null` |
| **Immutable** | Yes — populated at dossier creation, never updated |
| **Index** | Not indexed (read by PK lookup only, no queries filter on snapshot content) |

**Purpose**: Freeze the case type's requirement structure at dossier creation time so that subsequent case type changes do not affect in-progress dossiers (FR-014).

### JSONB Schema

```json
{
  "case_type_code": "string",
  "case_type_name": "string",
  "snapshot_at": "ISO 8601 datetime",
  "groups": [
    {
      "id": "UUID string — original DocumentRequirementGroup.id",
      "group_order": 1,
      "label": "string — group display label",
      "is_mandatory": true,
      "slots": [
        {
          "id": "UUID string — original DocumentRequirementSlot.id",
          "document_type_id": "UUID string",
          "document_type_code": "string",
          "document_type_name": "string",
          "description": "string | null — DocumentType.description",
          "classification_prompt": "string | null — DocumentType.classification_prompt",
          "label_override": "string | null"
        }
      ]
    }
  ]
}
```

### Usage

| Context | Reads snapshot? | Details |
|---------|----------------|---------|
| `POST /v1/staff/dossiers` (create) | Writes | Snapshot populated from live `CaseType → Group → Slot → DocumentType` at creation time |
| `GET /v1/staff/dossiers/{id}` (detail) | Reads | Returns `requirement_snapshot` in response for guided capture UI |
| `check_completeness()` | Reads | Validates mandatory groups against snapshot, not live case type |
| Guided capture screen (Flutter) | Reads | Renders step list, document guidance, slot options from snapshot |
| `POST /v1/staff/dossiers/{id}/submit` | Reads | Completeness check uses snapshot |

---

## Alembic Migration: `0003_requirement_snapshot`

```
Table: dossier
  ADD COLUMN requirement_snapshot JSONB DEFAULT NULL
```

**Migration notes**:
- Forward-only: existing dossiers get `requirement_snapshot = null` (they were created before the snapshot concept).
- No data backfill needed — existing dossiers will continue to work via the live case type join (fallback path in `check_completeness`).
- Downgrade: drop column.

---

## Existing Entities (No Changes)

The following entities from Features 001/002 are reused as-is:

### `dossier` (existing columns preserved)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `citizen_id` | UUID FK → citizen | |
| `submitted_by_staff_id` | UUID FK → staff_member | |
| `case_type_id` | UUID FK → case_type | Preserved for reporting (live join still works) |
| `reference_number` | String(20) | Generated at submit: `HS-YYYYMMDD-NNNNN` |
| `status` | String(30) | `draft → scanning → ready → submitted → in_progress → completed/rejected` |
| `security_classification` | SmallInt | 0-3 |
| `priority` | String(10) | normal, urgent |
| `requirement_snapshot` | **JSONB (NEW)** | Frozen requirement structure |
| `rejection_reason` | Text | |
| `submitted_at` | DateTime | |
| `completed_at` | DateTime | |
| `retention_expires_at` | DateTime | |
| `created_at`, `updated_at` | DateTime | |

### `dossier_document` (unchanged)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `dossier_id` | UUID FK → dossier | |
| `requirement_slot_id` | UUID FK → document_requirement_slot | Nullable; links to original slot |
| `document_type_id` | UUID FK → document_type | Nullable |
| `ai_match_result` | JSONB | `{"match": bool, "confidence": float, "reason": str}` |
| `ai_match_overridden` | Boolean | Staff override flag |
| `staff_notes` | Text | |
| `created_at` | DateTime | |

**Constraint**: `UNIQUE(dossier_id, requirement_slot_id)` — one document per slot per dossier.

### `scanned_page` (unchanged)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `submission_id` | UUID FK → submission | Nullable (legacy) |
| `dossier_document_id` | UUID FK → dossier_document | Nullable (case-based) |
| `page_number` | SmallInt | |
| `image_oss_key` | String(512) | |
| `ocr_raw_text` | Text | |
| `ocr_corrected_text` | Text | |
| `ocr_confidence` | Numeric(5,4) | |
| `image_quality_score` | Numeric(5,4) | |
| `synced_at` | DateTime | |
| `created_at` | DateTime | |

**Constraint**: `CHECK (submission_id IS NULL) <> (dossier_document_id IS NULL)` — exactly one owner.

### `case_type`, `document_requirement_group`, `document_requirement_slot`, `document_type`

All unchanged. These are the *source* of the snapshot data but are not modified.

---

## Entity Relationship Summary

```
CaseType ─────────────────────────────── (source, live)
  │                                           │
  │ snapshot at creation ──→ Dossier.requirement_snapshot (JSONB)
  │                             │
  └──→ Dossier ─────────────────┘
         │
         ├── DossierDocument ──→ DocumentRequirementSlot (FK preserved)
         │      │
         │      └── ScannedPage (dual-owner: dossier_document_id)
         │
         └── WorkflowStep (dual-owner: dossier_id)

Submission (legacy) ──→ ScannedPage (dual-owner: submission_id)
         │
         └── WorkflowStep (dual-owner: submission_id)
```

---

## Validation Rules

| Rule | Enforced by | Notes |
|------|-------------|-------|
| `requirement_snapshot` immutable after creation | Application layer (service) | No DB constraint — service never updates this column |
| Completeness against snapshot groups | `check_completeness()` service | Mandatory groups must have ≥1 fulfilled slot |
| One document per slot per dossier | DB UNIQUE constraint | `uq_dossier_document_dossier_slot` |
| Single owner for ScannedPage | DB CHECK constraint | `ck_scanned_page_single_owner` |
| Security classification 0-3 | DB CHECK constraint | `ck_dossier_security_classification` |
