# Research: Case-Based Dossier Submission

**Feature**: 002-case-based-submission  
**Date**: 2026-04-11  
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## R-001: Architecture Strategy — Extend Submission vs. New Dossier Entity

**Decision**: Add a new `Dossier` entity alongside the existing `Submission` model. **Do not** rename or modify `Submission` beyond adding a nullable `dossier_document_id` FK to `ScannedPage`.

**Rationale**:
- `Submission` is the current unit of work for individual document processing (OCR, classification, single-page scan). It has existing FK references in `WorkflowStep`, `StepAnnotation`, `ScannedPage`, and citizen tracking endpoints. Changing its semantics mid-flight risks breaking running workflows.
- A new `Dossier` entity has a clearly different lifecycle (draft → submitted → in_review → completed/rejected) and citizen-facing identity (reference number) from a scan-level `Submission`.
- The two entities coexist during the transition: old submissions remain individual-doc, new dossier flow uses `Dossier` + `DossierDocument`.

**Alternatives Considered**:
- Evolve `Submission` in-place with `case_type_id` nullable FK → Rejected: pollutes working model with dual-purpose nullability; all existing queries need `WHERE case_type_id IS NULL` guards.
- Full replacement / removing `Submission` → Rejected: would require rewriting OCR worker, classification worker, all existing staff and citizen API endpoints simultaneously.

---

## R-002: OR-Group Modeling for Conditional Document Requirements

**Decision**: Use a two-level structure: `DocumentRequirementGroup` (one per logical requirement, e.g., "Proof of Premises") contains 1..N `DocumentRequirementSlot` records (each slot = one acceptable document type). A group is satisfied if **any one** of its slots is fulfilled. A slot is "mandatory = false" only when the entire group is optional.

**Rationale**:
- Vietnamese administrative practice frequently offers alternatives (e.g., "Hợp đồng thuê nhà OR Giấy chủ quyền nhà"). Encoding this as either/or at the group level (not slot level) is the clearest conceptual model.
- Keeps the constraint logic in a single place: "all mandatory groups satisfied" = dossier complete.
- JSONB alternative (storing slot list in a JSONB column) was evaluated — rejected because it cannot be validated by foreign key constraints and makes individual slot status tracking impossible.

**Alternatives Considered**:
- Single `DocumentRequirementSlot` table with `alternative_group_id` self-reference → Rejected: harder to query and explain.
- JSONB requirements blob on `CaseType` → Rejected: no FK integrity, no per-slot status tracking.

---

## R-003: Routing for Dossiers — Reuse WorkflowStep vs. New Table

**Decision**: Reuse the existing `WorkflowStep` model. Add a nullable `dossier_id` FK column to `WorkflowStep` alongside the existing nullable `submission_id` FK (make `submission_id` nullable in migration). Enforce check constraint: exactly one of `submission_id` or `dossier_id` must be non-null.

**Rationale**:
- `WorkflowStep` already captures exactly what is needed (department, step order, status, reviewer, timestamps). Duplicating the model as `DossierWorkflowStep` creates dead code and divergence.
- PostgreSQL CHECK constraint (`(submission_id IS NULL) <> (dossier_id IS NULL)`) cleanly enforces the single-owner invariant.

**Alternatives Considered**:
- Separate `DossierWorkflowStep` table → Rejected: code duplication; two nearly identical models to maintain.
- Embedding routing state as JSONB on `Dossier` → Rejected: can't query per-step without unpacking JSONB; no FK to `Department`.

---

## R-004: Case Type Routing — Reuse RoutingRule vs. New Table

**Decision**: Add a new `CaseTypeRoutingStep` table (similar structure to `RoutingRule` but with `case_type_id` FK instead of `document_type_id`). Do **not** add `case_type_id` to `RoutingRule`.

**Rationale**:
- `RoutingRule` has a unique constraint on `(document_type_id, step_order)`. Adding a nullable `case_type_id` would require a complex partial-unique index. A separate clean table is simpler.
- Allows `CaseTypeRoutingStep` to evolve independently (e.g., add per-step SLA fields later).

**Alternatives Considered**:
- Extend `RoutingRule` with nullable `case_type_id` → Rejected: schema complexity, partial unique constraint maintenance.

---

## R-005: AI Slot Validation Approach

**Decision**: Reuse the existing `classification_worker` / `ai_client` (dashscope) with a new prompt mode: **slot validation**. Instead of open-ended classification, the AI is given the expected `DocumentType.classification_prompt` for the target slot and asked to return a binary match + confidence. Result stored in `DossierDocument.ai_match_result` (JSONB).

**Rationale**:
- dashscope is already integrated and proven for document classification. The existing prompt engineering approach (per `DocumentType.classification_prompt`) can be repurposed as a validation oracle when the target document type is known.
- New dashscope API call: vision model with image + prompt = "Does this image show a [document_type_prompt]? Respond: match/no_match, confidence 0–1, reason."

**Alternatives Considered**:
- Dedicated fine-tuned classifier model → Rejected: out of scope, significant additional cost and training time.
- Skip AI entirely for slot validation → Rejected: spec requirement US4; catches common human errors (wrong document in wrong slot).

**Threshold**: Staff override is always allowed. AI warning shown when confidence < 0.80.

---

## R-006: Citizen Reference Number Format

**Decision**: `HS-YYYYMMDD-NNNNN` where `YYYYMMDD` is the submission date and `NNNNN` is a zero-padded daily sequence number (e.g., `HS-20260411-00042`). Generated server-side at first `submit` action, stored as a unique indexed column on `Dossier`.

**Rationale**:
- Short enough for a citizen to write down or communicate by phone.
- Date prefix allows staff to quickly identify when the dossier was submitted.
- Daily sequence (not global) resets each day, keeping numbers short (5 digits supports 99,999 submissions/day per office — far above expected volume).

**Alternatives Considered**:
- UUID as reference number → Rejected: too long for citizens to use verbally.
- Random alphanumeric codes (e.g., `A3F7K`) → Rejected: no date information; potential for collision; harder to audit.

---

## R-007: Seed Data Migration Strategy

**Decision**: In `seed_data.py`, after inserting existing `Department` and `DocumentType` records (unchanged), add a new `seed_case_types()` routine that creates `CaseType`, `DocumentRequirementGroup`, `DocumentRequirementSlot`, and `CaseTypeRoutingStep` records for the initial 5 case types derived from the existing hardcoded `DOCUMENT_TYPES`. The hardcoded list in `seed_data.py` is preserved for backward compatibility (existing test fixtures), but the routing driver for new submissions is `CaseType`, not `DocumentType`.

**Initial Case Types at Launch** (derived from spec user stories and Vietnamese business registration practice):

| Code | Name | Required Documents (Groups) |
|------|------|-----------------------------|
| `HOUSEHOLD_BIZ_REG` | Đăng ký hộ kinh doanh cá thể | Hộ khẩu copy; CMND/CCCD; Proof of Premises (Hợp đồng thuê OR Giấy chủ quyền); Đơn đề nghị đăng ký |
| `COMPANY_REG` | Đăng ký doanh nghiệp | Đơn đăng ký; Điều lệ công ty; Danh sách thành viên/cổ đông; CMND/CCCD các thành viên |
| `BIRTH_CERT` | Xin cấp giấy khai sinh | Đơn xin cấp; CMND/CCCD bố hoặc mẹ; Giấy chứng nhận kết hôn (if applicable) |
| `HOUSEHOLD_REG` | Đăng ký hộ khẩu | Đơn đề nghị; CMND/CCCD; Giấy tờ nhà ở |
| `MARITAL_STATUS` | Xác nhận tình trạng hôn nhân | Đơn xin xác nhận; CMND/CCCD; Hộ khẩu |

---

## R-008: Offline Dossier Draft on Staff App

**Decision**: Staff app stores the dossier in a local SQLite / Drift database as a `DossierDraft` during offline mode. Draft includes: selected `case_type_id`, `case_type_code` (cached name), list of slot fulfillments with local image paths. On sync, the draft is POSTed to `POST /v1/staff/dossiers` (creates server record), then each `DossierDocument` is uploaded slot by slot. Completeness checking and AI slot validation happen server-side after all uploads.

**Rationale**:
- Matches existing offline pattern for `ScannedPage` uploads (from 001 spec).
- Local draft avoids data loss when connectivity drops mid-scan.

---

## All NEEDS CLARIFICATION Resolved

| Item | Resolution |
|------|-----------|
| Dossier vs Submission entity split | R-001: New Dossier entity, additive |
| OR-group document requirements | R-002: DocumentRequirementGroup + Slot |
| WorkflowStep for dossiers | R-003: Add nullable dossier_id FK to WorkflowStep |
| CaseType routing | R-004: New CaseTypeRoutingStep table |
| AI slot validation | R-005: Reuse dashscope with validation prompt |
| Citizen reference number | R-006: HS-YYYYMMDD-NNNNN format |
| Seed data migration | R-007: Preserve existing + add CaseType seeding |
| Offline dossier draft | R-008: Local Drift DB draft, sync on reconnect |
