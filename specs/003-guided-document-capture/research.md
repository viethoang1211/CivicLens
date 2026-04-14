# Research: Guided Document Capture

**Feature**: 003-guided-document-capture  
**Date**: 2026-04-14  
**Purpose**: Resolve design decisions and validate technical assumptions before implementation.

---

## R-001: Requirement Snapshot Strategy

**Question**: How should the system snapshot case type requirements at dossier creation time to prevent mid-flight changes from breaking in-progress dossiers (FR-014)?

**Decision**: Store a JSONB column `requirement_snapshot` on the `dossier` table.

**Rationale**:
- The data is read-only after creation — never updated post-snapshot.
- JSONB avoids additional tables and JOIN complexity.
- The snapshot is small (~2-5 KB per dossier, containing group labels, slot IDs, document type codes/names/descriptions/prompts).
- The guided capture UI reads from this snapshot instead of joining through `CaseType → Group → Slot → DocumentType`.
- Existing `case_type_id` FK is preserved for reporting/analytics; the snapshot is for operational integrity.

**Format**:
```json
{
  "case_type_code": "BIRTH_REG",
  "case_type_name": "Đăng ký khai sinh",
  "groups": [
    {
      "id": "uuid",
      "group_order": 1,
      "label": "Tờ khai đăng ký khai sinh",
      "is_mandatory": true,
      "slots": [
        {
          "id": "uuid",
          "document_type_id": "uuid",
          "document_type_code": "BIRTH_REG_FORM",
          "document_type_name": "Tờ khai đăng ký khai sinh",
          "description": "Tờ khai đăng ký khai sinh theo mẫu...",
          "classification_prompt": "Đây là Tờ khai đăng ký khai sinh...",
          "label_override": null
        }
      ]
    }
  ]
}
```

**Alternatives considered**:
- **Separate `dossier_requirement_snapshot` table** with rows per group/slot: More normalized but adds 2 new tables and complex JOINs for data that never changes. Rejected — over-engineering.
- **No snapshot; use live CaseType data**: Simpler but violates FR-014. If an admin removes a requirement group while a dossier is in progress, the dossier's completeness check breaks. Rejected — correctness risk.
- **Copy-on-write with versioned CaseType**: Track version numbers and fetch the correct historical version. Rejected — massive complexity for a rarely-needed feature.

---

## R-002: Guided Capture UI Architecture (Flutter)

**Question**: Should the guided capture screen be a single scrollable screen with expandable steps, or a multi-screen wizard with one step per screen?

**Decision**: Single screen with vertical step list + modal capture sheet.

**Rationale**:
- Staff needs to see overall progress at a glance (which steps done, which remaining).
- A vertical list with step cards (collapsed/expanded) provides this overview.
- Tapping a step card expands it to show document guidance + captured pages + "Capture" button.
- The camera capture itself opens as a full-screen modal (using existing `ScanScreen` camera logic).
- After capture, control returns to the step card which shows page thumbnails and AI validation status.
- This mirrors the existing `DossierScreen` pattern (checklist + per-slot actions) but with enhanced guidance and inline validation feedback.

**Alternatives considered**:
- **Multi-screen wizard (PageView with swipe)**: Clean per-step focus, but staff loses context of overall progress. Also harder to jump back to a specific step. Rejected.
- **Bottom sheet per step**: Too small for document guidance + page previews. Rejected.

---

## R-003: AI Validation Timing and UX

**Question**: When should AI validation run, and how should the UI handle the async result?

**Decision**: Fire-and-forget validation on upload, poll for result, show inline.

**Rationale**:
- The existing `slot_validation_worker.py` Celery task already handles validation asynchronously.
- After `POST /dossiers/{id}/documents` returns (pages uploaded), the `DossierDocument` has `ai_match_result = null`.
- The Flutter widget polls `GET /dossiers/{id}` (which returns all documents with their `ai_match_result`) every 3 seconds for up to 30 seconds, or until the result is non-null.
- The UI shows:
  - **While pending**: spinning indicator with "Đang xác minh..." (Verifying...)
  - **Match (confidence ≥ 0.7)**: green checkmark + "Đã xác minh" (Verified)
  - **Uncertain (0.4 ≤ confidence < 0.7)**: orange warning + "Cần kiểm tra" (Needs review)
  - **Mismatch (confidence < 0.4)**: red X + reason text + "Bỏ qua" override button
  - **Timeout/error**: grey "?" + "Chưa xác minh" (Not verified) + proceed allowed
- No WebSocket needed — simple polling is adequate for < 1000 concurrent staff.

**Alternatives considered**:
- **WebSocket for real-time push**: More responsive but adds infrastructure complexity (WebSocket server, connection management). Rejected for MVP.
- **Synchronous validation (block upload until AI responds)**: Violates FR-007 and FR-015. AI failures would block the entire capture flow. Rejected.

---

## R-004: Quick Scan ↔ Dossier Linking (US-3 AC-2)

**Question**: How should a quick-scanned standalone submission be linked to a dossier slot later?

**Decision**: Defer to a future feature. Quick Scan submissions remain standalone for now.

**Rationale**:
- Linking requires a new API endpoint (`POST /dossiers/{id}/import-submission/{submission_id}`) plus logic to copy `ScannedPage` rows from submission-owned to dossier-document-owned, which violates the dual-owner CHECK constraint without careful handling.
- The primary user flow (guided capture) does not need this.
- Quick Scan is a fallback for ad-hoc intake; users who need a dossier will use the guided flow.
- US-3 AC-2 is marked as P2 with this understanding.

**Alternatives considered**:
- **Copy scanned pages on import**: New ScannedPage rows with `dossier_document_id` set, duplicating images. Works but doubles storage and needs careful page renumbering. Deferred.
- **Relaxing the dual-owner CHECK constraint**: Allow both `submission_id` and `dossier_document_id` to be set. Breaks the fundamental data model assumption. Rejected.

---

## R-005: Completeness Check Source

**Question**: Should the completeness check at submission time use the live `CaseType` requirements or the dossier's `requirement_snapshot`?

**Decision**: Use the `requirement_snapshot`.

**Rationale**:
- Consistency: the guided capture UI was driven by the snapshot, so the completeness check must validate against the same structure.
- If an admin adds a new mandatory group to the case type after the dossier was created, the existing dossier should not suddenly become incomplete.
- Implementation: `check_completeness()` in `dossier_service.py` will be modified to read `dossier.requirement_snapshot['groups']` instead of joining through `CaseType → DocumentRequirementGroup`.

---

## R-006: Home Screen Layout Decision

**Question**: How should "Tạo hồ sơ mới" (guided) and "Quét nhanh" (quick scan) be presented?

**Decision**: Two prominent action cards on the home screen.

**Rationale**:
- "Tạo hồ sơ mới" is the primary action (80% of use). Large card, top position, blue/accent color.
- "Quét nhanh" is secondary (20%). Smaller card or outlined button below, grey/neutral.
- This replaces the current single "New Submission" button with a clear dual-path entry.
- Below the action cards: list of recent/in-progress dossiers for quick resume.

---

## R-007: Page Quality Assessment Reuse

**Question**: Can the existing image quality assessment from Feature 001 be reused in the guided capture flow?

**Decision**: Yes, reuse as-is.

**Rationale**:
- `staff_app/lib/features/submission/scan_screen.dart` already has `assess_image_quality()` which checks brightness, contrast, blur, and skew.
- The guided capture step will invoke the same quality check after each camera capture.
- Pages below threshold are rejected with Vietnamese guidance text (already implemented).
- No backend changes needed — quality assessment happens client-side.

---

## R-008: Document Guidance Content Source

**Question**: Where does the document guidance text (physical characteristics, page count hints) come from?

**Decision**: Use existing `DocumentType.classification_prompt` and `DocumentType.description` fields, both included in the requirement snapshot.

**Rationale**:
- `classification_prompt` already contains physical identification characteristics in Vietnamese (e.g., "Đặc điểm: thẻ nhựa cứng, quốc huy, chip NFC..." for CCCD).
- `description` contains the legal reference and context (e.g., "Căn cứ: Luật Hộ tịch 2014, Điều 16").
- Both fields were enriched in the recent seed data update with detailed Vietnamese content.
- The snapshot stores both fields per slot, so the UI can display them directly without additional API calls.
- **No new `page_count_hint` field** is added. Most Vietnamese administrative documents are 1-2 pages; the staff knows the document.
