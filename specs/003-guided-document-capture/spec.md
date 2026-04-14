# Feature Specification: Guided Document Capture

**Feature Branch**: `003-guided-document-capture`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "Hiện tại đang cho staff chụp giấy tờ xong classification theo prompt hả, hay cho thêm 1 option là cho staff chọn case trước, xong hệ thống yêu cầu cần phải cấp các loại giấy tờ nào, ví dụ cccd, sổ đỏ. sau đó với staff chụp cccd cho phần cccd, sổ đỏ cho phần sổ đỏ, etc."

## Background & Analysis

### Current Dual-Mode Problem

The platform currently has two coexisting document capture workflows which are disconnected in user experience and AI strategy:

**Mode A — Blind Scan (Feature 001: AI Document Processing)**
Staff scans one document at a time → system runs OCR → AI **classifies** the document type from scratch (open-ended guess from all possible types) → routes to departments. This is inherently unreliable because:
- The AI must guess from 15+ document types with no prior context.
- Classification prompts (even after enrichment to Vietnamese) remain a probability game — the AI picks from a flat list.
- If classification is wrong, the staff must manually correct, and routing may already have started.
- The citizen's purpose (which case they're filing) is never formally recorded.

**Mode B — Case-Based Dossier (Feature 002: Case-Based Submission)**
Staff selects a case type → system presents a document checklist → staff uploads documents per slot → AI **validates** (binary match: "Is this really a CCCD?" yes/no). This is structurally better because:
- The AI only needs to confirm a known hypothesis, not guess from scratch.
- The checklist guides the staff on exactly what to collect.
- Completeness is enforced before submission.
- The citizen gets a reference number and tracks a meaningful case.

**The problem**: These two modes are disconnected in the staff app. There is no unified flow that smoothly guides staff from "citizen walks in" to "all documents captured and submitted." The staff app has no step-by-step capture guidance within the dossier flow, and the legacy flow lacks any case context.

### Recommended Approach: Guided-First with Fallback

After analyzing the requirements images (operational challenges, constraints, desired outcomes) and the existing codebase, the recommended approach is:

1. **Default workflow → Case-type-first (guided capture)**. This is the primary mode. Staff always starts by selecting a case type. The system then walks staff through capturing each required document, one requirement at a time.

2. **Fallback → Quick scan (unguided)**. For walk-in single documents, ad-hoc scans, or when the citizen doesn't yet know what case they're filing. Uses legacy classification but with improved prompts. Available as a secondary option on the home screen.

3. **AI role shifts from classifier to validator**. In the guided flow, AI no longer classifies blind. Instead it validates: "Staff says this is a CCCD — does the image actually look like a CCCD?" This is dramatically more accurate (binary confirmation vs. open-ended classification).

4. **Classification persists only in fallback mode**. When staff uses the quick-scan mode without a case type, the system still runs the full classification pipeline. But the guided flow bypasses classification entirely — the document type is already known from the slot.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Guided Capture: Staff Selects Case, System Directs Scanning (Priority: P1)

A citizen arrives at the reception counter wanting to register a birth. The staff member opens the app, taps "Tạo hồ sơ mới" (New dossier), selects case type "Đăng ký khai sinh." The system displays a step-by-step capture screen: Step 1 of 4 — "Tờ khai đăng ký khai sinh" with a description of what this document looks like and what to photograph. The staff member takes photos of the form. The system immediately runs AI validation (is this really a birth registration form?) and shows a green checkmark if confirmed, or an orange warning if uncertain. Staff proceeds to Step 2 — "Giấy chứng sinh" (Medical birth certificate), and so on through all required documents. Optional documents (e.g., marriage certificate) can be skipped. Once all mandatory documents are captured, the system enables the "Nộp hồ sơ" (Submit) button.

**Why this priority**: This is the core interaction that transforms the staff experience from "scan and hope AI guesses right" to "system tells me exactly what to scan next." Directly addresses all three operational challenges: manual identification, cross-department consolidation, and extended approval cycles. Leverages existing case type and requirement slot data.

**Independent Test**: Can be tested by selecting a case type, following the guided capture steps to photograph documents, and verifying each step validates the correct document type and enables submission when complete.

**Acceptance Scenarios**:

1. **Given** a staff member selects case type "Đăng ký khai sinh," **When** the guided capture screen loads, **Then** the system displays 4 steps corresponding to the case type's requirement groups, with Step 1 highlighted and ready for capture.
2. **Given** a staff member is on Step 1 (Tờ khai đăng ký khai sinh) and photographs the correct form, **When** AI validation completes, **Then** the system shows a confirmation indicator (green checkmark) and enables navigation to Step 2.
3. **Given** a staff member photographs a CCCD instead of the expected birth registration form on Step 1, **When** AI validation completes, **Then** the system shows a warning ("Đây có thể không phải Tờ khai đăng ký khai sinh — vui lòng kiểm tra lại") but allows the staff to override and proceed.
4. **Given** a requirement group has multiple alternative slots (e.g., "CCCD hoặc Hộ chiếu"), **When** the staff member reaches this step, **Then** the system shows both options and lets staff choose which document they are capturing.
5. **Given** all mandatory steps are completed, **When** the staff member taps Submit, **Then** the system runs a completeness check and creates the dossier with a reference number.
6. **Given** some mandatory steps are incomplete, **When** the staff member taps Submit, **Then** the system blocks submission and highlights the missing steps with clear visual indicators.

---

### User Story 2 — Step-Level AI Validation with Staff Override (Priority: P1)

After the staff member captures photos for a given step, the system immediately sends the image to the AI validation service. The AI compares the photograph against the expected document type's classification prompt (e.g., "Does this image look like a Căn cước công dân?"). The result appears within seconds: confirmed (green), uncertain (orange), or mismatch (red). Staff can always override the AI result — the system records the override for audit purposes but does not block progress.

**Why this priority**: AI validation at each step is the key differentiator from a simple checklist. Without it, the guided flow is just manual data collection. With it, the system catches errors immediately (wrong document photographed for wrong slot) before the dossier is submitted and enters the department workflow.

**Independent Test**: Can be tested by uploading a correct document to a slot and verifying green confirmation, then uploading an incorrect document and verifying an orange/red warning appears with an override option.

**Acceptance Scenarios**:

1. **Given** a staff member captures a CCCD for the "CCCD" requirement step, **When** AI validation runs, **Then** the system returns a match result within 10 seconds and displays a green confirmation with confidence score.
2. **Given** a staff member captures a marriage certificate for the "CCCD" step by mistake, **When** AI validation runs, **Then** the system returns a mismatch and displays an orange warning with explanation text in Vietnamese.
3. **Given** a staff member sees an AI mismatch warning, **When** they tap "Bỏ qua cảnh báo" (Override warning), **Then** the system records `ai_match_overridden = true` in the dossier document, the step is marked as captured, and an audit log entry is created.
4. **Given** the AI service is unavailable or times out, **When** the staff member captures a document, **Then** the system shows "Chưa xác minh được — hệ thống sẽ kiểm tra sau" (Could not verify — system will check later) and allows the staff to proceed without blocking.

---

### User Story 3 — Quick Scan Fallback (Unguided Mode) (Priority: P2)

A citizen walks in and hands over a single document without specifying a case. Or the staff member needs to digitize a document before knowing which dossier it belongs to. The staff member taps "Quét nhanh" (Quick scan) from the home screen, photographs the document, and the system runs the full AI classification pipeline (OCR → classify document type → fill template fields). The result is stored as a standalone submission that can later be linked to a dossier, or processed independently via the legacy routing workflow.

**Why this priority**: The guided flow covers 80% of use cases, but the reception desk also handles ad-hoc document intake. This fallback ensures the system doesn't force staff into knowing the case type upfront when it genuinely isn't known.

**Independent Test**: Can be tested by scanning a document without selecting a case type first, and verifying the system classifies the document and creates a standalone submission record.

**Acceptance Scenarios**:

1. **Given** a staff member taps "Quét nhanh" on the home screen, **When** they capture a single document, **Then** the system runs the OCR + classification pipeline and displays the detected document type with confidence score.
2. **Given** a quick-scanned submission exists, **When** a staff member later creates a dossier for a related case type, **Then** they can link the existing scanned document to a dossier slot (import from existing submission).
3. **Given** the AI classification confidence is below 60%, **When** the result is shown, **Then** the system highlights alternative document types ranked by confidence and lets staff manually select the correct type.
4. **Given** no relevant case type exists for a scanned document, **When** classification completes, **Then** the submission proceeds through the legacy single-document routing workflow.

---

### User Story 4 — Step-Level Document Guidance and Preview (Priority: P2)

At each step of the guided capture flow, the system displays helpful context about the expected document: a brief description, what to look for (physical characteristics), and how many pages to expect. After capturing, the system shows a preview of captured pages with options to retake individual pages, add more pages, or remove a page before moving to the next step.

**Why this priority**: Reduces staff errors by providing context at the moment of capture. Without guidance, staff may photograph the wrong page or miss required pages. The descriptions are derived from existing `classification_prompt` and `description` fields on each document type.

**Independent Test**: Can be tested by viewing the capture screen for a specific step and verifying the description, physical characteristics, and page management features are present and functional.

**Acceptance Scenarios**:

1. **Given** a staff member is on the "Giấy chứng sinh" capture step, **When** the screen loads, **Then** the system displays: document name, description ("Giấy chứng sinh do bệnh viện cấp"), physical characteristics ("Có logo bệnh viện, dấu đỏ"), and expected page count (1 page).
2. **Given** a staff member has captured 2 pages for a multi-page document, **When** they review the pages, **Then** they can swipe through page thumbnails, tap to enlarge, retake any page, or delete a page.
3. **Given** a staff member has captured pages for a step, **When** they navigate away from the step and return later, **Then** the previously captured pages are preserved and displayed.

---

### User Story 5 — Dossier Progress Summary and Citizen Receipt (Priority: P3)

After completing all guided capture steps, the staff member sees a summary screen showing: case type, citizen information, all captured documents per step with their validation status, any overridden warnings, and the total completeness percentage. Upon submission, the citizen receives a reference number (shown on screen with option to print a receipt slip). The citizen can immediately use this reference number in the citizen app to track progress.

**Why this priority**: Builds trust and transparency by giving the citizen immediate confirmation that their documents were received and their case is being processed. The receipt replaces informal verbal confirmations with a verifiable tracking reference.

**Independent Test**: Can be tested by completing all dossier steps, submitting, and verifying the summary screen displays correctly and the reference number works in the citizen app.

**Acceptance Scenarios**:

1. **Given** a staff member has completed all mandatory capture steps, **When** they tap Submit, **Then** a summary screen shows case type name, citizen name, document list with status icons (validated/overridden/skipped), and a "Nộp hồ sơ" confirmation button.
2. **Given** a dossier is submitted, **When** the reference number is generated, **Then** the system displays it prominently (large font, QR code for citizen to scan) and offers a "In phiếu" (Print receipt) action.
3. **Given** a citizen receives a reference number, **When** they enter it in the citizen app, **Then** they see the case details, document list (without confidential content), and current processing status.

---

### Edge Cases

- What happens when the citizen doesn't have one of the required documents? → Staff skips the mandatory step; submission is blocked. Staff can mark the dossier as "incomplete — pending citizen return" and save as draft.
- What happens when a case type definition changes while a draft dossier is in progress? → The dossier retains the requirement snapshot from when it was created. New requirements do not retroactively affect in-progress dossiers.
- What happens when the same document needs to appear in multiple dossiers? → Each dossier gets its own scanned copy. Documents are not shared across dossiers (legal requirement: each case has its own physical file).
- What happens when AI validation takes longer than 30 seconds? → Show a loading indicator for 10 seconds, then display "Đang xử lý..." (Processing...) with an option to proceed. Validation result appears asynchronously when ready.
- What if the staff's device camera malfunctions mid-capture? → The system preserves all previously captured pages for that step. Staff can resume capture after fixing the camera issue.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST present a primary "Tạo hồ sơ mới" (New dossier) action that initiates the guided capture flow starting with case type selection.
- **FR-002**: System MUST present a secondary "Quét nhanh" (Quick scan) action that initiates unguided single-document capture with AI classification.
- **FR-003**: After case type selection, the system MUST display a step-by-step capture interface listing all requirement groups in `group_order` sequence, clearly distinguishing mandatory vs. optional steps.
- **FR-004**: For each capture step, the system MUST display the expected document's name, description, and physical identification characteristics (from `classification_prompt` and `description` fields).
- **FR-005**: For requirement groups with multiple slots (OR-logic alternatives), the system MUST let the staff choose which specific document type they are capturing before starting the camera.
- **FR-006**: After capturing pages for a step, the system MUST immediately enqueue AI validation (slot validation) and display the result as confirmed/uncertain/mismatch within the capture screen.
- **FR-007**: AI validation results MUST NOT block staff from proceeding. Staff can override any warning; overrides MUST be recorded with `ai_match_overridden = true` and an audit log entry.
- **FR-008**: The system MUST run image quality assessment on each captured page and reject (with guidance) pages below the minimum quality threshold.
- **FR-009**: The system MUST allow staff to retake, add, or remove individual pages within a capture step before proceeding to the next step.
- **FR-010**: The system MUST enforce completeness checks before submission: all mandatory requirement groups must have at least one captured document.
- **FR-011**: Draft dossiers MUST be persistable and resumable — staff can close the app and return to an in-progress dossier later.
- **FR-012**: In Quick Scan (fallback) mode, the system MUST run the full OCR → classification → template fill pipeline, identical to the existing legacy submission workflow.
- **FR-013**: The system MUST generate a human-readable reference number upon dossier submission (`HS-YYYYMMDD-NNNNN` format).
- **FR-014**: The system MUST snapshot the case type's requirement structure at dossier creation time so that subsequent case type changes do not affect in-progress dossiers.
- **FR-015**: When AI validation service is unavailable, the system MUST allow capture to proceed with an "unverified" status and retry validation asynchronously.

### Key Entities

- **Guided Capture Session**: A transient UI concept (not persisted as a new entity) that maps to the existing `Dossier` + `DossierDocument` + `ScannedPage` models. The "steps" are derived from `DocumentRequirementGroup` / `DocumentRequirementSlot` for the selected case type.
- **AI Validation Result**: Already exists as `DossierDocument.ai_match_result` (JSONB). Enhanced with status display in the capture screen.
- **Requirement Snapshot**: A frozen copy of the case type's requirement groups and slots at dossier creation time. Prevents mid-flight changes from breaking in-progress dossiers.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Staff can complete a standard 4-document dossier capture (select case → capture all docs → submit) in under 5 minutes, compared to the current 15-20 minute manual process.
- **SC-002**: AI validation confirms correct document placement (slot match) with at least 90% accuracy, reducing downstream errors caught by reviewing departments.
- **SC-003**: 95% of dossier submissions pass completeness check on first attempt (no missing mandatory documents).
- **SC-004**: Staff override rate for AI validation warnings stays below 15%, indicating the AI is providing trustworthy results.
- **SC-005**: Citizens receive a trackable reference number within 30 seconds of dossier submission.
- **SC-006**: Quick scan fallback handles at least 20% of document intake for cases where guided flow is not applicable.
- **SC-007**: Average time from citizen arrival at reception to dossier submission decreases by at least 50% compared to manual full-paper process.

## Assumptions

- Staff devices have functioning cameras with at least 8MP resolution, sufficient for document scanning at arm's length.
- Network connectivity is available during capture (online-first). Offline support for guided capture is out of scope for this feature (existing offline scan from Feature 001 continues to work for quick scan mode).
- The existing 15 document types and 6 case types in seed data provide sufficient coverage for initial deployment. New case types can be added via seed data updates until the admin UI (Feature 002 User Story 2) is implemented.
- AI validation (slot matching via `qwen3-vl-plus`) is sufficiently fast for real-time feedback (target: < 10 seconds per document).
- The existing `DossierDocument`, `ScannedPage`, `DocumentRequirementGroup`, and `DocumentRequirementSlot` models support the guided capture workflow without schema changes. The only new data needed is a requirement snapshot mechanism.
- Vietnamese-language classification prompts (already updated in seed data) provide adequate context for AI slot validation in guided mode.
