# Research: Citizen App Completion

**Feature**: 006-citizen-app-completion  
**Date**: 2026-04-16

## Research Task 1: Backend→Dart API Mismatches

### Decision: Fix 3 mismatches before implementing UI

### Findings

**Mismatch 1: `department_name` vs `department_id` in workflow steps**
- Backend `_build_workflow_steps()` returns `department_id` (UUID string)
- Dart `DossierTrackingStepDto.fromJson()` expects `department_name` (String)
- **Fix**: Backend should join Department table and return `department_name` alongside `department_id`

**Mismatch 2: Notification query params**
- `CitizenApi.listNotifications()` sends `skip`/`limit` query params
- Backend `list_notifications()` expects `page`/`per_page` params
- **Fix**: Update `CitizenApi` to send `page`/`per_page` instead of `skip`/`limit`

**Mismatch 3: Notification model missing `dossier_id`**
- `Notification` DB model has `submission_id` FK (legacy) but no `dossier_id` FK
- Notifications for dossier events cannot link to a dossier directly
- **Fix**: Add `dossier_id` FK to Notification model, update notification creation to include it, expose in API response

### Alternatives Considered
- Client-side workaround (fetch department name separately) — rejected: too many API calls
- Skip dossier_id in notifications — rejected: can't navigate from notification to dossier detail

---

## Research Task 2: Quick Scan → Dossier Bridge Strategy

### Decision: Create dossier alongside submission in `finalize_scan`

### Rationale
Quick scan currently creates only a `Submission` entity. For citizen visibility, we need a `Dossier` entity. Two approaches:

**Option A: Create dossier in `create_submission`** (at submission creation time)
- Pro: Dossier exists immediately
- Con: Dossier is empty (no scanned pages yet), staff hasn't finished scanning

**Option B: Create dossier in `finalize_scan`** (after all pages uploaded) ← CHOSEN
- Pro: Dossier created when scan is actually complete, ready for OCR
- Con: Small delay between submission creation and dossier creation
- Rationale: Better UX — dossier appears in citizen app only when there's meaningful content

### Implementation
1. After `finalize_scan` marks submission as `ocr_processing`:
2. Create a `Dossier` with:
   - `citizen_id` = submission.citizen_id
   - `case_type_id` = a default "Hồ sơ quét nhanh" case type (seeded)
   - `status` = "submitted"
   - `submitted_by_staff_id` = submission.submitted_by_staff_id
   - `reference_number` = auto-generated (HS-YYYYMMDD-NNNNN)
3. Link submission to dossier via new `Submission.dossier_id` FK (nullable)

### Alternatives Considered
- Merge Submission and Dossier into one model — rejected: too invasive, breaks feature 001 contracts
- Create dossier only manually by staff — rejected: defeats the purpose of citizen visibility
- Show Submissions in citizen "Hồ sơ của tôi" — rejected: different model, different APIs, inconsistent UX

---

## Research Task 3: Citizen App Home Screen Architecture

### Decision: Stateful Home Screen with lazy-loaded counts

### Rationale
Home screen needs to show:
1. Citizen name (from secure storage, set at login)
2. Dossier count badge (from `GET /v1/citizen/dossiers` with `page_size=1`)
3. Unread notification count (from `GET /v1/citizen/notifications` with `per_page=1` — response includes `unread_count`)

### Implementation
- Convert `_CitizenHomeScreen` from `StatelessWidget` to `StatefulWidget`
- Load counts on `initState()` and on resume
- Pass `apiClient` and `citizenDossierApi` through constructor (already available from VNeID auth flow)
- Store `access_token` in `ApiClient` headers after login

### Alternatives Considered
- Use a state management library (Riverpod, Bloc) — rejected: overkill for this scope, keep it simple with StatefulWidget
- Fetch full dossier list just for count — rejected: wasteful, use `page_size=1` to get count from response

---

## Research Task 4: Auth Token Propagation in Citizen App

### Decision: Set token on ApiClient after VNeID login, read from secure storage on app restart

### Findings
- VNeID auth screen stores `access_token` in `FlutterSecureStorage` after login
- Current `_CitizenHomeScreen` creates a new `ApiClient(baseUrl: kApiBaseUrl)` without token
- `ApiClient` needs the token set via `Authorization: Bearer <token>` header for authenticated endpoints

### Implementation
1. After VNeID login, set token on ApiClient: `apiClient.setAuthToken(accessToken)`
2. On app startup, check secure storage for existing token; if present, skip login and go to home
3. On logout, clear secure storage and ApiClient token

### ApiClient Token Support
- Check if `ApiClient` already supports `setAuthToken()` or if we need to add it
- Dio interceptor pattern: add `Authorization` header to all requests when token is set

---

## Research Task 5: Notification → Dossier Navigation

### Decision: Add `dossier_id` to notification model and use it for deep-link navigation

### Findings
- Current `NotificationDto` has `submissionId` (nullable) — links to legacy submission
- Need `dossierId` (nullable) for case-based navigation  
- When citizen taps a notification with `dossierId`, navigate to `DossierStatusScreen(dossierId: n.dossierId)`
- When notification has neither, just mark read (no navigation)

### Implementation
1. Add `dossier_id` column to `notification` table (Alembic migration)
2. Update Notification model
3. Update backend notification list endpoint to include `dossier_id`
4. Update `NotificationDto` in shared_dart to include `dossierId`
5. Update `NotificationsScreen` to handle tap → navigate to DossierStatusScreen
