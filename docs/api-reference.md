# API Reference

Base URL: `http://localhost:8000` (development)

All endpoints return JSON. Authentication is via JWT Bearer token in the `Authorization` header.

Interactive API documentation (Swagger UI): **http://localhost:8000/docs**

---

## Staff API (`/v1/staff/`)

### Authentication

#### `POST /v1/staff/auth/login`

Authenticate staff member and receive a JWT token.

**Request:**
```json
{
  "employee_id": "NV001",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "staff_id": "uuid",
  "employee_id": "NV001",
  "full_name": "Nguyen Van A",
  "department_id": "uuid",
  "clearance_level": 2
}
```

The JWT payload includes `sub` (staff_id), `employee_id`, `department_id`, `clearance_level`, and `role`.

---

### Submissions (Scanning)

#### `POST /v1/staff/submissions`

Create a new submission draft.

**Request:**
```json
{
  "citizen_id_number": "001234567890",
  "security_classification": 0,
  "priority": "normal"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "status": "draft",
  "security_classification": 0,
  "priority": "normal"
}
```

#### `POST /v1/staff/submissions/{id}/pages`

Upload a scanned page image. Multipart form data.

**Request:** `multipart/form-data`
- `file`: Image file (JPEG, PNG)
- `page_number`: Integer

**Response (201):**
```json
{
  "page_id": "uuid",
  "page_number": 1,
  "image_oss_key": "scans/uuid/page_1.jpg",
  "quality_score": 0.85
}
```

Transitions submission from `draft` → `scanning` on first page upload.

#### `POST /v1/staff/submissions/{id}/finalize-scan`

Finalize scanning and trigger OCR + classification pipeline.

**Response (200):**
```json
{
  "status": "ocr_processing",
  "total_pages": 3,
  "message": "OCR processing started"
}
```

#### `GET /v1/staff/submissions/{id}/ocr-results`

Retrieve OCR results for all pages.

**Response (200):**
```json
{
  "pages": [
    {
      "page_number": 1,
      "ocr_raw_text": "...",
      "ocr_corrected_text": null,
      "ocr_confidence": 0.87,
      "image_url": "https://oss.../presigned"
    }
  ]
}
```

#### `PUT /v1/staff/submissions/{id}/ocr-corrections`

Submit staff corrections to OCR text.

**Request:**
```json
{
  "corrections": [
    {
      "page_number": 1,
      "corrected_text": "Nguyen Van A, sinh ngay 15/03/1990..."
    }
  ]
}
```

---

### Classification

#### `GET /v1/staff/submissions/{id}/classification`

Get AI classification results.

**Response (200):**
```json
{
  "document_type": {
    "id": "uuid",
    "name": "Birth Certificate Application",
    "code": "BIRTH_CERT"
  },
  "confidence": 0.92,
  "alternatives": [
    {"code": "HOUSEHOLD_REG", "name": "Household Registration", "confidence": 0.05}
  ],
  "template_data": {
    "child_name": "Nguyen Van B",
    "date_of_birth": "2024-01-15",
    "place_of_birth": "Ho Chi Minh City"
  }
}
```

#### `POST /v1/staff/submissions/{id}/confirm-classification`

Confirm or override the AI classification.

**Request:**
```json
{
  "document_type_id": "uuid",
  "template_data": {
    "child_name": "Nguyen Van B",
    "date_of_birth": "2024-01-15"
  }
}
```

---

### Routing

#### `POST /v1/staff/submissions/{id}/route`

Trigger automated workflow creation based on routing rules.

**Response (200):**
```json
{
  "submission_id": "uuid",
  "status": "in_progress",
  "workflow_steps": [
    {"step_order": 1, "department": "Reception", "status": "active"},
    {"step_order": 2, "department": "Judicial", "status": "pending"}
  ]
}
```

**Error (400):** If department has no staff with adequate clearance for the document's security classification.

---

### Department Queue

#### `GET /v1/staff/departments/{id}/queue`

List active workflow steps for a department.

**Query Parameters:**
- `status` — Filter by step status (`active`, `all`). Default: `active`
- `priority` — Filter by submission priority (`normal`, `urgent`, `all`). Default: `all`
- `page` — Page number (1-indexed). Default: `1`
- `per_page` — Items per page (1–100). Default: `20`

**Response (200):**
```json
{
  "items": [
    {
      "workflow_step_id": "uuid",
      "submission_id": "uuid",
      "document_type_name": "Birth Certificate",
      "priority": "urgent",
      "started_at": "2026-04-10T08:00:00Z",
      "expected_complete_by": "2026-04-12T08:00:00Z",
      "is_delayed": false,
      "security_classification": 0
    }
  ],
  "total": 42,
  "page": 1
}
```

Items are sorted: urgent first, then by `started_at` ascending. Items above the requesting staff's clearance level are excluded.

---

### Workflow Steps (Review)

#### `GET /v1/staff/workflow-steps/{id}`

Get full review context for a workflow step.

**Response (200):**
```json
{
  "step": {
    "id": "uuid",
    "step_order": 2,
    "status": "active",
    "department_name": "Judicial",
    "started_at": "2026-04-10T10:00:00Z",
    "expected_complete_by": "2026-04-13T10:00:00Z"
  },
  "submission": {
    "id": "uuid",
    "status": "in_progress",
    "security_classification": 1,
    "template_data": {"child_name": "Nguyen Van B"}
  },
  "pages": [
    {
      "page_number": 1,
      "image_url": "https://oss.../presigned",
      "ocr_text": "...",
      "ocr_confidence": 0.87
    }
  ],
  "annotations_by_department": {
    "Reception": [
      {
        "type": "approved",
        "content": "Document verified, forwarding to Judicial",
        "target_citizen": false,
        "created_at": "2026-04-10T09:30:00Z"
      }
    ]
  }
}
```

#### `POST /v1/staff/workflow-steps/{id}/complete`

Submit a review decision.

**Request:**
```json
{
  "result": "approved",
  "comment": "All documents verified and complete",
  "target_citizen": true
}
```

`result` must be one of: `approved`, `rejected`, `needs_info`

**Response (200):**
```json
{
  "action": "advanced",
  "next_step_order": 3,
  "submission_status": "in_progress"
}
```

#### `POST /v1/staff/workflow-steps/{id}/consultations`

Create a cross-department consultation (no ownership transfer).

**Request:**
```json
{
  "target_department_id": "uuid",
  "question": "Can you verify the land registry reference number?"
}
```

---

### Admin — Document Types

#### `GET /v1/staff/admin/document-types`

List all document types.

#### `POST /v1/staff/admin/document-types`

Create a new document type.

**Request:**
```json
{
  "name": "Land Title Application",
  "code": "LAND_TITLE",
  "template_schema": {"type": "object", "properties": {"parcel_id": {"type": "string"}}},
  "classification_prompt": "Identify land title registration applications",
  "retention_years": 0,
  "retention_permanent": true
}
```

#### `PUT /v1/staff/admin/document-types/{id}`

Update a document type (name, template_schema, classification_prompt, retention).

#### `DELETE /v1/staff/admin/document-types/{id}`

Delete a document type.

### Admin — Routing Rules

#### `GET /v1/staff/admin/routing-rules?document_type_id={uuid}`

List routing rules, optionally filtered by document type.

#### `POST /v1/staff/admin/routing-rules`

Create a routing rule.

**Request:**
```json
{
  "document_type_id": "uuid",
  "department_id": "uuid",
  "step_order": 1,
  "expected_duration_hours": 48,
  "required_clearance_level": 0
}
```

#### `PUT /v1/staff/admin/routing-rules/{id}`

Update a routing rule's duration or clearance requirement.

#### `DELETE /v1/staff/admin/routing-rules/{id}`

Delete a routing rule.

---

## Citizen API (`/v1/citizen/`)

### Authentication

#### `POST /v1/citizen/auth/vneid`

Exchange VNeID authorization code for app JWT.

**Request:**
```json
{
  "code": "vneid-auth-code",
  "id_number": "001234567890"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "citizen_id": "uuid",
  "full_name": "Nguyen Thi C"
}
```

---

### Submissions

#### `GET /v1/citizen/submissions`

List the citizen's own submissions.

**Query Parameters:**
- `skip` — Offset. Default: `0`
- `limit` — Max items. Default: `20`
- `status` — Filter by status

**Response (200):**
```json
{
  "submissions": [
    {
      "id": "uuid",
      "status": "in_progress",
      "document_type_name": "Birth Certificate Application",
      "submitted_at": "2026-04-08T14:00:00Z",
      "current_step": {
        "department_name": "Judicial",
        "status": "active",
        "is_delayed": false
      }
    }
  ]
}
```

#### `GET /v1/citizen/submissions/{id}`

Get detailed submission with full workflow visualization.

**Response (200):**
```json
{
  "id": "uuid",
  "status": "in_progress",
  "submitted_at": "2026-04-08T14:00:00Z",
  "workflow_steps": [
    {
      "step_order": 1,
      "department_name": "Reception",
      "status": "completed",
      "started_at": "2026-04-08T14:30:00Z",
      "completed_at": "2026-04-09T10:00:00Z",
      "is_delayed": false,
      "citizen_annotations": ["Document received and verified"]
    },
    {
      "step_order": 2,
      "department_name": "Judicial",
      "status": "active",
      "started_at": "2026-04-09T10:00:00Z",
      "completed_at": null,
      "is_delayed": false,
      "citizen_annotations": []
    }
  ]
}
```

---

### Notifications

#### `GET /v1/citizen/notifications`

List notifications with unread count.

**Query Parameters:**
- `skip` — Offset. Default: `0`
- `limit` — Max items. Default: `50`

**Response (200):**
```json
{
  "notifications": [
    {
      "id": "uuid",
      "type": "step_advanced",
      "title": "Submission moved to Judicial",
      "body": "Your birth certificate application has moved to the next department",
      "is_read": false,
      "sent_at": "2026-04-09T10:00:00Z"
    }
  ],
  "unread_count": 3
}
```

#### `PUT /v1/citizen/notifications/{id}/read`

Mark a notification as read.

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad request — invalid input or state transition |
| 401 | Unauthorized — missing or invalid JWT |
| 403 | Forbidden — insufficient clearance level |
| 404 | Not found |
| 409 | Conflict — duplicate resource |
| 422 | Validation error — request body doesn't match schema |
