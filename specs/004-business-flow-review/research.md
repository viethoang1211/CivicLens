# Research: Business Flow Review & Fixes

**Feature**: 004-business-flow-review | **Date**: 2026-04-14

## R1: OCR Confidence Parsing from dashscope API

**Decision**: Use heuristic OCR confidence estimation based on text output characteristics — dashscope does NOT return explicit confidence scores.

**Rationale**: The `qwen-vl-ocr` and `qwen3-vl-plus` models via `MultiModalConversation.call()` return `response.output.choices[0].message.content` as a list of text items with no confidence metadata. The API response format is just the extracted text string. There is no `confidence`, `score`, or `probability` field in the dashscope vision API response.

**Approach**: Estimate confidence heuristically:
- If OCR returns empty text or only whitespace → confidence 0.0
- If text length < 20 chars (likely garbage) → confidence 0.2
- If text contains mostly non-Vietnamese characters (mojibake, encoding errors) → confidence 0.3
- If text is reasonable length with Vietnamese characters → confidence 0.7 (baseline)
- If text matches multiple expected structural patterns (numbers, dates, names) → confidence 0.85
- Fallback model result replaces primary ONLY if primary confidence < threshold (0.6), and the heuristic gives the fallback result a higher score

**Alternatives considered**:
1. Ask model to self-report confidence in prompt — rejected because it adds latency and the model's self-reported confidence is unreliable
2. Use token log-probabilities — rejected because dashscope doesn't expose logprobs for vision models
3. Keep hardcoded 0.85 — rejected because it breaks fallback logic entirely (0.85 > 0.6, fallback never triggers)

## R2: Classification Confidence Threshold Enforcement

**Decision**: Add threshold check in `classification_worker.py` after AI classification returns. If confidence < `settings.classification_confidence_threshold` (0.7), set `classification_method = "ai_low_confidence"` and store alternatives for staff manual selection.

**Rationale**: The threshold is already defined in config.py but never enforced. The classification AI prompt already asks for `"confidence": 0.0-1.0` and `"alternatives": [...]` in its JSON response. The worker parses these values but doesn't act on them. Low-confidence classifications currently auto-apply, which can route documents incorrectly.

**Approach**:
- Parse confidence from AI response (already done: `classification.get("confidence", 0.0)`)
- If confidence < threshold:
  - Still set `document_type_id` (best guess)
  - Set `classification_method = "ai_low_confidence"` (instead of "ai")
  - Store full classification result including alternatives in `template_data` under a special `_classification_alternatives` key
  - Submission stays at `pending_classification` for staff review (no behavior change — this already happens)
- If confidence ≥ threshold:
  - Set `classification_method = "ai"` (auto-classified with high confidence)
  - Staff still reviews but system shows confidence indicator
- Staff app already has manual classification fallback — the change is in signaling confidence level

**Alternatives considered**:
1. Block any classification below threshold entirely — rejected because having a best-guess helps staff; they just need to confirm
2. Add a new status like "uncertain_classification" — rejected because submission already stays in `pending_classification` until staff confirms

## R3: Template Validation Enhancement

**Decision**: Enhance `template_service.validate_template_data()` to validate types and check required fields against JSON Schema structure.

**Rationale**: Current implementation is a passthrough that copies values without validation. The template_schema in seed data defines field types (`"type": "string"`, `"type": "number"`) and required fields. AI-extracted template data may contain wrong types (number as string, null for required fields) that should be flagged.

**Approach**:
- For each field in schema:
  - If field has `"type": "string"` → coerce to string, strip whitespace
  - If field has `"type": "number"` or `"type": "integer"` → attempt numeric parsing, mark as error if fails
  - If field has `"type": "date"` → attempt ISO date parsing
- Track validation results: `{"field_name": {"value": ..., "valid": bool, "error": str|null}}`
- Return cleaned dict + validation summary
- Do NOT reject data — AI extraction is advisory. Just flag issues for staff review

**Alternatives considered**:
1. Use jsonschema library for full JSON Schema validation — overkill for simple type checking, adds dependency
2. Reject invalid template data — rejected because this would break the pipeline; staff needs to see what AI extracted even if partial

## R4: Workflow Service Dossier Mode Support

**Decision**: Modify `advance_workflow()` in `workflow_service.py` to support both submission-owned and dossier-owned workflow steps.

**Rationale**: Current `advance_workflow()` always does `select(Submission).where(Submission.id == current_step.submission_id)` which crashes with `NoResultFound` when the step is dossier-owned (submission_id is NULL). The dual-owner pattern requires the workflow service to detect which mode and handle accordingly.

**Approach**:
- Detect mode: check `current_step.submission_id` vs `current_step.dossier_id`
- For submission mode: keep current logic unchanged
- For dossier mode:
  - Load `Dossier` instead of `Submission`
  - On reject: `dossier.status = "rejected"`, call `notify_dossier_status_change()`
  - On complete: `dossier.status = "completed"`, compute retention from `CaseType.retention_years`
  - On advance: find next step using `dossier_id`, call `notify_dossier_status_change()` or `notify_step_advanced()` equivalent
  - Expected completion: look up `CaseTypeRoutingStep` (not `RoutingRule`) for duration
- Both modes converge on same WorkflowStep operations (status, timestamps)

**Alternatives considered**:
1. Create separate `advance_dossier_workflow()` function — rejected because it would duplicate step advancement logic; better to make the existing function polymorphic
2. Make review_service detect mode and call different functions — rejected because the workflow step itself knows its owner, so detection belongs in workflow_service

## R5: Seed Data Legal Accuracy Verification

**Decision**: All seed data legal references verified as accurate. Minor improvements to classification prompts needed.

**Rationale**: Cross-checked all 15+ document types against Vietnamese legal sources:

| Document Type | Legal Reference | Status |
|--------------|----------------|--------|
| ID_CCCD | Luật Căn cước 2023 (hiệu lực 01/07/2024) | ✅ Correct |
| PASSPORT_VN | Luật Xuất cảnh, nhập cảnh 2019 | ✅ Correct |
| BIRTH_REG_FORM | Luật Hộ tịch 2014 Đ.16, NĐ 123/2015 Đ.9, TT 04/2020/TT-BTP | ✅ Correct |
| BIRTH_CERTIFICATE_MEDICAL | TT 17/2012/TT-BYT | ✅ Correct |
| MARRIAGE_CERT | Luật HN&GĐ 2014 Đ.9, Luật Hộ tịch 2014 Đ.18 | ✅ Correct |
| MARITAL_STATUS_FORM | Luật Hộ tịch 2014 Đ.21, NĐ 123/2015 Đ.22 | ✅ Correct |
| RESIDENCE_FORM_CT01 | Luật Cư trú 2020 Đ.20-21, NĐ 62/2021, TT 56/2021/TT-BCA | ✅ Correct |
| BIZ_REG_FORM | NĐ 01/2021/NĐ-CP Đ.82-87, TT 01/2021/TT-BKHĐT | ✅ Correct |
| COMPANY_REG_FORM | Luật DN 2020 Đ.21-27, NĐ 01/2021 | ✅ Correct |
| COMPLAINT | Luật Khiếu nại 2011 Đ.8, Luật Tố cáo 2018 Đ.23 | ✅ Correct |

**Retention policies**:
- Identity docs: Permanent ✅ (per Luật Căn cước)
- Hộ tịch: 75 years ✅ (per NĐ 123/2015 Đ.62 quy định lưu trữ sổ hộ tịch gốc)
- Cư trú: 10 years ✅ (per Luật Cư trú 2020)
- Kinh doanh: 10 years ✅
- Doanh nghiệp: 20 years ✅

**Classification prompt improvements needed**:
- Add distinguishing features between tờ khai (blank form filled by citizen) vs giấy chứng nhận (issued certificate with red seal)
- Add mention of "mẫu theo Thông tư/Nghị định" references so AI understands these are government-standard forms

**RESIDENCE_CONFIRM / RESIDENCE_PROOF**: These are NOT specific form types but supporting documents. Acceptable as seed categories since citizens bring various proof documents (hợp đồng thuê nhà, sổ đỏ, etc.).

## R6: Notification Service for Dossier Workflow

**Decision**: `notify_dossier_status_change()` already exists in notification_service.py. However, `advance_workflow()` doesn't call it for dossier mode, and there's no dossier equivalent for `notify_step_advanced()`.

**Rationale**: The notification function handles `in_progress`, `completed`, and `rejected` statuses. But workflow step advancement (moving between departments) needs a `notify_dossier_step_advanced()` function similar to the submission version. This maps to FR-023 (Vietnamese notifications for all events).

**Approach**: Add `notify_dossier_step_advanced()` that sends "Hồ sơ {ref} đã chuyển sang {department_name}" with the dossier's reference number instead of submission ID.

## R7: Quality Service Interface

**Decision**: Keep size-based heuristic for demo. Add clear protocol/interface documentation as TODO for future OpenCV swap.

**Rationale**: For a demo system, file-size proxy is sufficient. The function signature `assess_image_quality(image_data: bytes) -> dict` is already a clean interface. The return shape `{"score": float, "acceptable": bool, "guidance": list[str]}` is stable. Future implementation can swap internals without changing callers.

**Approach**: Add docstring noting the interface contract and expected production implementation. No code change needed.
