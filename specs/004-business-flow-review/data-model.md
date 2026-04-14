# Data Model: Business Flow Review & Fixes

**Feature**: 004-business-flow-review | **Date**: 2026-04-14

## Overview

This feature introduces **NO new database entities or migrations**. All changes are to existing service/worker logic, seed data quality, and test coverage. The data model documented here describes the **existing entities** that are affected by the fixes, and any new fields or behavioral changes to existing models.

## Entities Affected (No Schema Changes)

### Submission (existing)

No column changes. Behavioral change in how `classification_method` and `classification_confidence` are set:

| Field | Type | Change |
|-------|------|--------|
| `classification_method` | String(20) | **NEW VALUE**: `"ai_low_confidence"` added alongside existing `"ai"` and `"manual"` |
| `classification_confidence` | Numeric(5,4) | No change — already parsed from AI response |
| `template_data` | JSONB | **NEW KEY**: `_classification_alternatives` may be stored when confidence is low |

The `classification_method` field gains a new semantic value:
- `"ai"` — AI classified with confidence ≥ threshold (0.7)
- `"ai_low_confidence"` — AI classified with confidence < threshold; staff must confirm
- `"manual"` — Staff classified manually (existing)

### ScannedPage (existing)

No column changes. Behavioral change in how `ocr_confidence` is computed:

| Field | Type | Change |
|-------|------|--------|
| `ocr_confidence` | Numeric(5,4) | **FIX**: Computed via heuristic instead of hardcoded 0.85 |

Heuristic confidence scoring:
- `0.0` — OCR error or empty result
- `0.2` — Text < 20 characters (likely garbage)
- `0.3` — Text mostly non-Vietnamese (encoding issues)
- `0.7` — Reasonable text with Vietnamese characters
- `0.85` — Text with structural patterns (dates, numbers, names)

### WorkflowStep (existing)

No column changes. Behavioral change in `advance_workflow()`:

| Owner Mode | Lookup | Notifications | Retention |
|-----------|--------|---------------|-----------|
| Submission (submission_id set) | Load Submission, RoutingRule | `notify_step_advanced()`, `notify_completed()` | From DocumentType.retention_years |
| Dossier (dossier_id set) | Load Dossier, CaseTypeRoutingStep | `notify_dossier_step_advanced()`, `notify_dossier_status_change()` | From CaseType.retention_years |

### template_service Validation Output (behavioral)

Current return: `dict[str, Any]` — simple key→value mapping

New return: `dict[str, Any]` — same structure but with type coercion applied:
- String fields: stripped whitespace
- Numeric fields: parsed to float/int or set to None with log warning
- Date fields: parsed to ISO format or set to None with log warning
- Required fields with None values: logged as warning

No schema change — just cleaner data.

## Seed Data Changes (No Migration)

### Classification Prompt Improvements

Each document type's `classification_prompt` enhanced with:

1. **Form vs Certificate distinction**: 
   - Forms (tờ khai): "Đây là mẫu đơn do công dân tự điền, thường in trắng đen, có dòng chấm để điền thông tin"
   - Certificates (giấy chứng nhận): "Đây là văn bản do cơ quan nhà nước cấp, có DẤU ĐỎ tròn, chữ ký lãnh đạo, quốc hiệu"

2. **Legal reference in prompt**: Add "theo mẫu ban hành kèm Thông tư/Nghị định số..." to help AI contextualize

### No New Document Types or Case Types

All existing 15+ document types and 6 case types remain. No additions in this feature (case type expansion deferred to separate feature).

## Entity Relationship (unchanged)

```
CaseType ─1:N─→ DocumentRequirementGroup ─1:N─→ DocumentRequirementSlot
    │                                                      │
    │ 1:N                                                  │ 1:N
    ▼                                                      ▼
CaseTypeRoutingStep                               DossierDocument ─1:N─→ ScannedPage
    │                                                      │
    │ refs                                                 │ N:1
    ▼                                                      ▼
Department                                          Dossier ──1:N──→ WorkflowStep
    │                                                 │                    │
    │ 1:N                                             │ N:1                │ 1:N
    ▼                                                 ▼                    ▼
StaffMember                                       Citizen            StepAnnotation

Submission ──1:N──→ ScannedPage
    │ ──1:N──→ WorkflowStep
    │ N:1 ──→ DocumentType
    │ N:1 ──→ Citizen
```

No changes to relationships. The dual-owner pattern on WorkflowStep and ScannedPage (submission_id XOR dossier_id) remains enforced by existing CHECK constraints.
