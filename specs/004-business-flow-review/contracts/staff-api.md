# API Contract Changes: Business Flow Review & Fixes

**Feature**: 004-business-flow-review | **Date**: 2026-04-14

## Overview

No new endpoints. Changes affect **response shapes** of existing endpoints where classification confidence and template validation are surfaced.

## Changed Response Shapes

### GET /v1/staff/submissions/{id}

The submission detail response gains visibility into classification confidence level:

```json
{
  "id": "uuid",
  "status": "pending_classification",
  "classification_method": "ai_low_confidence",  // NEW VALUE (was only "ai" or "manual")
  "classification_confidence": 0.45,
  "document_type_id": "uuid",
  "template_data": {
    "ho_ten": "Nguyễn Văn A",
    "so_cccd": "012345678901",
    "_classification_alternatives": [             // NEW KEY (only when low confidence)
      {"code": "ID_CCCD", "confidence": 0.45},
      {"code": "PASSPORT_VN", "confidence": 0.30}
    ]
  }
}
```

**Changes**:
- `classification_method` can now return `"ai_low_confidence"` (new value)
- `template_data` may include `_classification_alternatives` key when AI confidence is below threshold
- Existing consumers that check `classification_method == "ai"` are unaffected (new value is additive)

### Staff Review Endpoints (no shape change)

The workflow step review endpoints (`POST /v1/staff/workflow-steps/{id}/approve`, `/reject`, `/request-info`) maintain their current response shape. The fix is internal — `advance_workflow()` now correctly handles dossier-owned steps without changing the API contract.

### Citizen Tracking (no shape change)

The citizen dossier tracking endpoint (`GET /v1/citizen/dossiers/{id}`) response shape is unchanged. The fix ensures workflow advancement correctly populates step timestamps and status for dossier mode.

## Behavioral Contract Changes

### Classification Worker Celery Task

**Task**: `classification.run(submission_id)`

**Before**: Always sets `classification_method = "ai"` regardless of confidence.

**After**:
- Confidence ≥ 0.7 → `classification_method = "ai"`
- Confidence < 0.7 → `classification_method = "ai_low_confidence"`, alternatives stored in `template_data._classification_alternatives`
- Confidence < 0.3 (all types) → `classification_method = "ai_low_confidence"`, `document_type_id` set to best guess but clearly flagged

### OCR Worker Celery Task

**Task**: `ocr.run_pipeline(submission_id)`

**Before**: `ocr_confidence = 0.85` hardcoded → fallback never triggers.

**After**: Confidence computed via heuristic:
- Empty text → 0.0 → fallback triggers (< 0.6)
- Short text (< 20 chars) → 0.2 → fallback triggers
- Non-Vietnamese text → 0.3 → fallback triggers
- Reasonable Vietnamese text → 0.7 → no fallback
- Structured text (dates, numbers) → 0.85 → no fallback

Fallback model result REPLACES primary if primary confidence < 0.6. Fallback result gets its own heuristic confidence score.

### Template Service

**Function**: `validate_template_data(template_data, template_schema) -> dict`

**Before**: Pass-through, no validation.

**After**: Type coercion applied:
- String fields → `str()` + strip
- Number fields → `float()`/`int()` parse, `None` on failure
- Date fields → ISO parse attempt, `None` on failure
- All schema-defined fields present in output (existing behavior preserved)

Return shape unchanged: `dict[str, Any]`
