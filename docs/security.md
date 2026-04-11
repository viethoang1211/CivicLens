# Security & Compliance

## Overview

This system processes sensitive government documents ranging from routine public filings to classified reports. The security model is designed around three principles:

1. **Defense-in-depth** — Multiple independent layers enforce access control
2. **Least privilege** — Staff see only what their clearance level permits
3. **Complete audit trail** — Every access and action is logged immutably

## Document Classification Levels

Documents are assigned one of four security classification levels:

| Level | Name | Example Documents | Access |
|-------|------|-------------------|--------|
| 0 | Unclassified | Birth certificate request, household registration | All staff |
| 1 | Confidential | Financial records, tax applications | Clearance ≥ 1 |
| 2 | Secret | Internal affairs reports, personnel investigations | Clearance ≥ 2 |
| 3 | Top Secret | National security documents, classified directives | Clearance ≥ 3 |

Staff members are assigned a `clearance_level` (0–3) that determines which documents they can access.

## Authentication

### Staff Authentication

Staff authenticate via employee ID and password:

1. `POST /v1/staff/auth/login` with `employee_id` + `password`
2. Password is verified against bcrypt hash stored in `StaffMember.password_hash`
3. JWT issued containing: `staff_id`, `employee_id`, `department_id`, `clearance_level`, `role`
4. Token expires after 8 hours (configurable via `JWT_EXPIRE_MINUTES`)

JWT is signed using HS256 with a configurable `JWT_SECRET_KEY`.

### Citizen Authentication

Citizens authenticate via **VNeID** (Vietnam's national digital identity platform):

1. Citizen opens app → redirected to VNeID OAuth authorization endpoint
2. Citizen authenticates with VNeID credentials
3. Authorization code returned to the app
4. App sends code to `POST /v1/citizen/auth/vneid`
5. Backend exchanges code with VNeID for citizen identity
6. Citizen record created or updated in database
7. App-specific JWT issued

Citizens have no clearance level — they can only access their own submissions.

## Authorization

### Attribute-Based Access Control (ABAC)

Every staff request that accesses a submission goes through the ABAC check:

```python
# Enforcement: staff.clearance_level >= submission.security_classification
async def check_submission_clearance(submission_id, staff, db, action):
    submission = load(submission_id)

    if staff.clearance_level < submission.security_classification:
        # Log denied access
        log_access(actor=staff, action=action, result="denied")
        raise HTTP 403 "Insufficient clearance level"

    # Log granted access
    log_access(actor=staff, action=action, result="granted")
    return submission
```

This check is applied on **every** endpoint that reads or modifies a submission:
- Viewing submission details
- Uploading scanned pages
- Reviewing OCR results
- Confirming classification
- Triggering routing
- Reviewing workflow steps

### Row-Level Security (RLS)

As a second layer of defense, PostgreSQL RLS policies enforce clearance at the database level:

```sql
ALTER TABLE submission ENABLE ROW LEVEL SECURITY;

CREATE POLICY submission_clearance ON submission
  USING (security_classification <= current_setting('app.clearance_level')::int);
```

The API sets the `app.clearance_level` session variable on each request:

```sql
SET LOCAL app.clearance_level = 2;  -- staff's clearance level
```

Even if an application-level bug bypasses the ABAC check, the RLS policy prevents the database from returning classified rows.

### Citizen Data Isolation

Citizen API endpoints filter by `citizen_id` from the JWT:
- `GET /v1/citizen/submissions` only returns the authenticated citizen's submissions
- Citizens cannot access other citizens' data
- Citizens cannot access staff endpoints

### Routing Clearance Validation

When creating a workflow, the system verifies that each department in the route has at least one active staff member with adequate clearance:

```python
for rule in routing_rules:
    staff_with_clearance = query(StaffMember).filter(
        department_id == rule.department_id,
        clearance_level >= submission.security_classification,
        is_active == True
    )
    if count(staff_with_clearance) == 0:
        raise "Department has no staff with adequate clearance"
```

### Staff App Clearance Enforcement

The staff mobile app applies clearance filtering at the UI level:

1. **Department queue** — Submissions above the staff's clearance level are hidden
2. **Submission creation** — A warning is shown if staff assigns a classification above their own clearance level (they can proceed but won't be able to access the document afterward)

## Audit Logging

### What Is Logged

Every security-relevant action creates an immutable `AuditLogEntry`:

| Action | Logged Data |
|--------|------------|
| Document viewed | Staff ID, submission ID, clearance check result |
| Page uploaded | Staff ID, submission ID, page number |
| OCR text corrected | Staff ID, submission ID |
| Classification confirmed | Staff ID, submission ID, document type, method (auto/manual) |
| Routing triggered | Staff ID, submission ID, workflow steps created |
| Review decision | Staff ID, step ID, result (approved/rejected/needs_info) |
| Consultation created | Staff ID, step ID, target department |
| Clearance denied | Staff ID, submission ID, attempted action |
| Citizen login | VNeID subject ID |
| Citizen viewed submission | Citizen ID, submission ID |

### Audit Log Structure

```json
{
  "id": "uuid",
  "actor_type": "staff",
  "actor_id": "uuid",
  "action": "review_approved",
  "resource_type": "workflow_step",
  "resource_id": "uuid",
  "clearance_check_result": "granted",
  "metadata": {
    "path": "/v1/staff/workflow-steps/{id}/complete",
    "method": "POST"
  },
  "created_at": "2026-04-10T10:00:00Z"
}
```

### Immutability

The audit log is designed as **append-only**:
- No UPDATE or DELETE operations are permitted in application code
- Database migrations should never modify audit data
- Records serve as legal evidence for compliance audits

### Automatic API Audit Interceptor

In addition to explicit audit logging in business logic, a FastAPI middleware (`AuditInterceptor`) automatically logs all successful staff API calls:
- Captures HTTP method, path, and staff identity
- Runs after the response is sent (non-blocking)
- Failures in the interceptor never break API operations

### Long-Term Retention (SLS)

Audit log entries are shipped to **Alibaba Cloud Simple Log Service (SLS)** for long-term compliance retention:
- SLS provides tamper-proof storage with configurable retention policies
- Searchable via SLS query language for compliance investigations
- Separate from the operational database — survives database migrations and rebuilds

## Data Retention

Documents follow configurable retention policies per document type:

| Document Type | Retention |
|--------------|-----------|
| Birth Certificate | 75 years |
| Household Registration | 10 years |
| Marital Status Confirmation | 20 years |
| Classified Report | Permanent |
| Complaint/Petition | 5 years |

When a submission is completed:
1. `retention_expires_at` is computed: `completed_at + retention_years`
2. For permanent retention types, `retention_expires_at` is set to `null` (never expires)
3. Documents whose retention has expired can be archived or purged per organizational policy

## Secure Communication

| Channel | Security |
|---------|----------|
| Mobile app → Backend | HTTPS (TLS 1.2+) |
| Backend → PostgreSQL | TLS connection (RDS enforced) |
| Backend → OSS | HTTPS with presigned URLs (time-limited) |
| Backend → Model Studio | HTTPS with API key |
| Celery → RocketMQ | Internal VPC network |
| Backend → SLS | HTTPS with Alibaba Cloud credentials |

### Presigned URLs

Scanned document images stored in OSS are never directly accessible. Access is via time-limited presigned URLs generated by the backend:
- URLs expire after a configurable duration
- Each URL is scoped to a single object
- Generation is gated by the ABAC clearance check

## Offline Security (Staff App)

When the staff app operates offline:
- Scanned images are stored in local device storage
- Queue metadata is stored in `flutter_secure_storage` (encrypted by the platform's keychain/keystore)
- No classified content remains unencrypted on disk
- The sync engine uses the same JWT authentication when uploading

## Threat Model Summary

| Threat | Mitigation |
|--------|-----------|
| Staff accessing documents above clearance | ABAC check + PostgreSQL RLS (two independent layers) |
| Citizen accessing another citizen's data | JWT-scoped queries, no cross-citizen endpoints |
| Database compromise leaking classified data | RLS policies active even for direct DB access |
| API bug bypassing access control | RLS as independent database-level enforcement |
| Audit log tampering | Append-only design + SLS off-site replication |
| Offline data theft from staff device | flutter_secure_storage (platform keychain encryption) |
| Man-in-the-middle interception | TLS on all external connections |
| Token theft | Short-lived JWTs (8h), no refresh tokens |
| Brute-force staff login | bcrypt password hashing (high work factor) |
