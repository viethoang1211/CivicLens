# Data Model: Citizen App Completion

**Feature**: 006-citizen-app-completion  
**Date**: 2026-04-16

## Schema Changes

### Modified: `notification` table

| Column | Type | Constraint | Change |
|--------|------|------------|--------|
| `dossier_id` | `UUID` | FK → `dossier.id`, NULLABLE | **NEW** — links notification to dossier for navigation |

**Migration**: Alembic `ALTER TABLE notification ADD COLUMN dossier_id UUID REFERENCES dossier(id)`

### Modified: `submission` table

| Column | Type | Constraint | Change |
|--------|------|------------|--------|
| `dossier_id` | `UUID` | FK → `dossier.id`, NULLABLE | **NEW** — links quick-scan submission to auto-created dossier |

**Migration**: Alembic `ALTER TABLE submission ADD COLUMN dossier_id UUID REFERENCES dossier(id)`

### New Seed: `case_type` — "Hồ sơ quét nhanh"

| Field | Value |
|-------|-------|
| `name` | Hồ sơ quét nhanh |
| `code` | QUICK_SCAN |
| `description` | Hồ sơ được tạo tự động từ quét nhanh |

**Purpose**: Default case_type assigned to dossiers auto-created from quick scan.

---

## Existing Entities (No Changes)

### `dossier` table (unchanged)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `citizen_id` | UUID FK → citizen | Links dossier to citizen |
| `submitted_by_staff_id` | UUID FK → staff_member | |
| `case_type_id` | UUID FK → case_type | |
| `reference_number` | VARCHAR, UNIQUE, NULLABLE | Format: HS-YYYYMMDD-NNNNN |
| `status` | VARCHAR | draft, submitted, in_progress, completed, rejected |
| `security_classification` | INT, CHECK 0-3 | |
| `priority` | VARCHAR | normal, urgent |
| `submitted_at` | TIMESTAMPTZ | |
| `completed_at` | TIMESTAMPTZ | |
| `rejection_reason` | TEXT | |

### `citizen` table (unchanged)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `vneid_subject_id` | VARCHAR, UNIQUE | From VNeID OAuth |
| `id_number` | VARCHAR, UNIQUE | CCCD number |
| `full_name` | VARCHAR | |
| `phone_number` | VARCHAR | |
| `push_token` | VARCHAR | EMAS push token |

### `workflow_step` table (unchanged)

Dual-owner pattern: exactly one of `submission_id` or `dossier_id` is non-null.

---

## Dart Model Changes

### Modified: `DossierTrackingStepDto`

Currently expects `department_name` from JSON, but backend returns `department_id`. Backend will be updated to also return `department_name` by joining Department table.

### Modified: `NotificationDto`

Add `dossierId` field:
```dart
final String? dossierId;  // from json['dossier_id']
```

### Modified: `DossierTrackingListItemDto`

Add `priority` field to match backend response:
```dart
final String? priority;  // from json['priority']
```

---

## Entity Relationship Summary

```
Citizen ──1:N──▶ Dossier
Citizen ──1:N──▶ Submission
Citizen ──1:N──▶ Notification
Dossier ──1:N──▶ WorkflowStep
Dossier ◀──0:1── Submission (NEW: quick-scan bridge)
Dossier ◀──0:N── Notification (NEW: dossier_id FK)
Submission ◀──0:N── Notification (existing: submission_id FK)
```
