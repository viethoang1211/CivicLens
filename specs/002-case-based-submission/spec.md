# Feature Specification: Case-Based Dossier Submission

**Feature Branch**: `002-case-based-submission`  
**Created**: 2026-04-11  
**Status**: Draft  
**Input**: User description: "Hiện tại phần data vẫn đang được hardcode. Mình muốn chuyển từ cơ chế xử lý từng tờ giấy sang xử lý theo hồ sơ (case). Mỗi loại hồ sơ yêu cầu bộ giấy tờ khác nhau — ví dụ đăng ký hộ kinh doanh cá thể và đăng ký doanh nghiệp cần các loại giấy tờ khác nhau. Staff cần nhập trước loại hồ sơ để hệ thống biết cần thu thập những gì."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE.
-->

### User Story 1 - Staff Selects Case Type to Define Dossier Requirements (Priority: P1)

A government intake staff member receives a citizen who wants to register a household business. The staff member opens the staff app, selects "Business Registration" as the case category, then selects the specific case type ("Household Business / Hộ kinh doanh cá thể"). The system immediately presents the required document checklist for that case type — e.g., Hộ khẩu copy, CMND/CCCD, rental contract or proof of premises, and the application form. The staff member works through the checklist, scanning and attaching each required document.

**Why this priority**: This is the foundation of the case-based model. Without knowing the case type upfront, the system cannot validate dossier completeness or guide the staff member. Replaces the current per-document, hardcoded approach.

**Independent Test**: Can be fully tested by selecting a case type and verifying the checklist of required documents is shown correctly, with the ability to mark each document as collected.

**Acceptance Scenarios**:

1. **Given** a staff member is creating a new submission, **When** they select "Household Business Registration" as the case type, **Then** the system presents a checklist of required documents specific to that type (e.g., 4–6 items).
2. **Given** a staff member selects "Company Registration" instead, **When** the checklist is displayed, **Then** at least one document requirement differs from the household business checklist (e.g., Company Charter replaces Household Application Form).
3. **Given** a case type has conditional document requirements (e.g., rental contract OR proof of ownership), **When** the checklist is displayed, **Then** the system shows both options and marks the requirement as fulfilled when either is provided.
4. **Given** a staff member has not attached all required documents, **When** they attempt to submit the dossier, **Then** the system blocks submission and highlights the missing documents.

---

### User Story 2 - Configurable Case Types and Document Requirements (Priority: P1)

An administrative super-user (or system administrator) needs to add a new case type — for example, "Partnership Business Registration / Công ty hợp danh" — without requiring a code change or system restart. They access the admin panel, create the new case type, define its required document list and routing steps, and publish it. Staff members can then immediately select this new case type when processing submissions.

**Why this priority**: The current system hardcodes document types in `seed_data.py`. Making case types and their document requirements configurable via the admin UI is essential for long-term maintainability and enables the government office to adapt without developer involvement.

**Independent Test**: Can be tested by creating a new case type in the admin panel and verifying it immediately appears as a selectable option in the staff submission flow.

**Acceptance Scenarios**:

1. **Given** an admin is on the case type management page, **When** they create a new case type with a document requirements list, **Then** the new type is saved and visible in the staff app without restarting the system.
2. **Given** an existing case type has an outdated document requirement, **When** an admin edits and removes that requirement, **Then** new submissions of that case type no longer require the removed document; in-progress submissions are unaffected.
3. **Given** an admin deactivates a case type, **When** a staff member views the case type selector, **Then** the deactivated type no longer appears; historical submissions of that type remain accessible.
4. **Given** no case types are configured, **When** a staff member opens the new submission screen, **Then** the system shows a clear message that case types must be configured before submissions can be accepted.

---

### User Story 3 - Dossier Completeness Check and Submission (Priority: P2)

After scanning and attaching all required documents for a dossier, the staff member initiates submission. The system verifies completeness against the case type requirements, provides a summary of the full dossier, and upon confirmation routes the dossier as a unit to the first department in the workflow. Citizens can then track the dossier's progress as a whole, not per individual document.

**Why this priority**: Shifts the citizen-facing experience from tracking individual documents to tracking a meaningful case outcome, and ensures routing decisions are made at the dossier level.

**Independent Test**: Can be tested by completing all required documents for a case type, submitting, and verifying the dossier appears in the first department's queue as a single unit.

**Acceptance Scenarios**:

1. **Given** all required documents for a dossier are attached, **When** the staff member submits, **Then** the system confirms completeness and creates a dossier record with a unique reference number.
2. **Given** a dossier is submitted, **When** the routing service processes it, **Then** the entire dossier is routed to the first department — not individual documents.
3. **Given** a citizen looks up their submission by reference number, **When** the dossier is in-progress, **Then** they see the overall status ("Received", "Under Review at Finance Dept", "Completed") without needing to track each document separately.
4. **Given** a dossier is rejected due to an invalid document, **When** the department staff marks the rejection, **Then** the citizen is notified with which document failed and what action is required to resubmit.

---

### User Story 4 - AI Classification Assists Document Identity Within a Dossier (Priority: P3)

When a staff member scans a document and attaches it to a specific dossier slot (e.g., "CMND/CCCD"), the AI classification assists by confirming whether the scanned image matches the expected document type. This acts as a validation layer — not as the primary classifier — since the case type and required slot are already known from the staff's selection.

**Why this priority**: With the case type known upfront, full AI classification is less critical. AI assists as a spot-check to prevent human error (e.g., attaching a birth certificate to the ID card slot) rather than driving the routing decision.

**Independent Test**: Can be tested by scanning a clearly wrong document type for a given slot and verifying the system flags a mismatch warning while still allowing the staff member to override.

**Acceptance Scenarios**:

1. **Given** a staff member scans a document for the "CMND/CCCD" slot, **When** the AI determines the scanned image is not an ID document, **Then** the system shows a warning: "This may not be a CMND/CCCD — please verify before saving."
2. **Given** the AI flags a mismatch, **When** the staff member confirms it is correctly placed anyway, **Then** the system records the override and allows the document to be saved to that slot.
3. **Given** the AI confidence for a document match is high, **When** the document is attached, **Then** no manual confirmation is required and the slot is automatically marked as fulfilled.

---

### Edge Cases

- What happens when two citizens bring in the same case type simultaneously and the system is under load?
- What if a required document cannot be scanned (damaged, refused by citizen)?
- What if a case type definition is updated while a dossier of that type is already in-progress?
- What if the same document is physically a single page that counts for two required slots (e.g., a land certificate covers both address proof and property ownership)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support configuration of multiple **Case Types** (e.g., Household Business Registration, Company Registration, Partnership Registration), each with a distinct set of required documents.
- **FR-002**: Staff MUST be able to select a Case Type at the start of a new submission, and the system MUST display the corresponding required document checklist.
- **FR-003**: A Case Type's document requirements MUST be configurable by authorized admin users through the admin interface without code changes.
- **FR-004**: The system MUST prevent dossier submission when one or more required documents are missing, and MUST indicate which documents are absent.
- **FR-005**: Document requirements within a Case Type MUST support conditional (OR) logic — e.g., "Rental Contract OR Proof of Ownership", where satisfying either fulfills the requirement.
- **FR-006**: The system MUST route submitted dossiers as a single unit to the first department in the Case Type's configured workflow, not as individual documents.
- **FR-007**: Citizens MUST be able to track the status of their dossier (as a whole) using a reference number the system generates at submission time.
- **FR-008**: The system MUST notify citizens when their dossier advances through the workflow and when action is required (e.g., resubmit a rejected document).
- **FR-009**: AI classification MUST serve as an assistive validation layer — confirming whether a scanned document matches its assigned slot — and MUST NOT block submission when the staff member overrides the warning.
- **FR-010**: Admin users MUST be able to deactivate a Case Type, preventing new submissions of that type while preserving historical records.
- **FR-011**: The system MUST maintain an audit log of all dossier state transitions, including which staff member made each change.
- **FR-012**: All Case Type and document requirement definitions currently hardcoded in `seed_data.py` MUST be migrated to be database-driven and manageable via the admin interface.

### Key Entities

- **Case Type** (`CaseType`): A category of administrative request (e.g., "Household Business Registration"). Defines required document slots and the routing workflow. Has active/inactive status.
- **Document Requirement Slot** (`DocumentRequirementSlot`): A single required-document entry within a Case Type. May be mandatory or conditional (OR group). References expected document type(s).
- **Dossier** (`Dossier`): A complete submission package submitted by a citizen for a specific Case Type. Contains multiple attached documents, has a lifecycle (Draft → Submitted → In Review → Completed/Rejected), and a citizen-facing reference number.
- **Dossier Document** (`DossierDocument`): A single scanned-and-attached document within a Dossier, linked to a specific Document Requirement Slot. Records AI match result and any staff override.
- **Case Type Workflow** (`CaseTypeWorkflow`): The ordered sequence of departments through which a Dossier of a given Case Type must pass.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Staff can create and submit a complete dossier for any supported case type in under 10 minutes, measured from case type selection to submission confirmation.
- **SC-002**: Zero dossiers are submitted with missing mandatory documents — the system enforces 100% completeness before accepting submission.
- **SC-003**: Admin users can add a new Case Type with document requirements and routing in under 15 minutes, without developer involvement.
- **SC-004**: Citizens can retrieve current dossier status using their reference number within 5 seconds of querying.
- **SC-005**: AI document slot validation correctly flags mismatched document types in at least 85% of cases (measured on a labeled test set of common Vietnamese government documents).
- **SC-006**: All existing hardcoded case types from `seed_data.py` are migrated and fully functional via the database-driven configuration within the same release.

## Assumptions

- The existing staff app and citizen app will be extended to support the dossier model; no new standalone apps are required.
- Citizens are identified via VNeID (as established in the original 001 spec) — the dossier is associated with their verified identity.
- The routing workflow for a Dossier follows the Case Type's configured department sequence (sequential only, as per existing 001 spec clarification).
- Initial Case Types will cover at minimum: Household Business Registration, Company Registration (including Partnership and LLC types as shown in the referenced business registration certificate form).
- Document type definitions for OCR and AI classification continue to exist but serve a supporting role (slot validation) rather than the primary routing driver.
- Offline scanning (staff app) is still supported — dossier completeness checks and AI slot validation occur after sync, not in offline mode.
- The existing `DocumentType` model is retained and reused as the expected-type reference within a `DocumentRequirementSlot`; it is not replaced.
