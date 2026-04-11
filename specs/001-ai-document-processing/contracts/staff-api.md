# API Contracts: Staff App Backend

**Base URL**: `https://api.{domain}/v1/staff`
**Auth**: Bearer token (JWT with staff identity, department, clearance_level claims)

## Authentication

### POST /auth/login
Authenticate a staff member and obtain JWT.

**Request**:
```json
{
  "employee_id": "string",
  "password": "string"
}
```

**Response** `200`:
```json
{
  "access_token": "jwt-string",
  "refresh_token": "jwt-string",
  "expires_in": 3600,
  "staff": {
    "id": "uuid",
    "full_name": "Nguyễn Văn B",
    "department_id": "uuid",
    "clearance_level": 1,
    "role": "reviewer"
  }
}
```

**Response** `401`:
```json
{
  "error": "invalid_credentials",
  "message": "Employee ID or password is incorrect."
}
```

## Admin

### GET /admin/document-types
List all document types.

**Query params**: `is_active=true&page=1&per_page=50`

**Response** `200`: Array of DocumentType objects.

### POST /admin/document-types
Create a new document type.

**Request**:
```json
{
  "name": "string",
  "code": "string",
  "description": "string",
  "template_schema": {},
  "classification_prompt": "string",
  "retention_years": 5,
  "retention_permanent": false
}
```

**Response** `201`: Created DocumentType object.

### PUT /admin/document-types/{id}
Update a document type.

**Response** `200`: Updated DocumentType object.

### DELETE /admin/document-types/{id}
Deactivate a document type (soft delete).

**Response** `204`

### GET /admin/routing-rules?document_type_id={id}
List routing rules for a document type.

**Response** `200`: Array of RoutingRule objects ordered by step_order.

### POST /admin/routing-rules
Create a routing rule.

**Request**:
```json
{
  "document_type_id": "uuid",
  "department_id": "uuid",
  "step_order": 1,
  "expected_duration_hours": 24,
  "required_clearance_level": 0
}
```

**Response** `201`: Created RoutingRule object.

### PUT /admin/routing-rules/{id}
Update a routing rule.

**Response** `200`: Updated RoutingRule object.

### DELETE /admin/routing-rules/{id}
Delete a routing rule.

**Response** `204`

## Scanning & Ingestion

### POST /submissions
Create a new submission for a citizen.

**Request**:
```json
{
  "citizen_id_number": "string (CCCD number)",
  "security_classification": 0,
  "priority": "normal | urgent"
}
```

**Response** `201`:
```json
{
  "id": "uuid",
  "citizen_id": "uuid",
  "status": "draft",
  "security_classification": 0,
  "priority": "normal",
  "created_at": "2026-04-10T10:00:00Z"
}
```

### POST /submissions/{id}/pages
Upload a scanned page image (multipart/form-data).

**Request**: `multipart/form-data`
- `image`: JPEG/PNG file (max 20MB)
- `page_number`: integer

**Response** `201`:
```json
{
  "id": "uuid",
  "submission_id": "uuid",
  "page_number": 1,
  "image_oss_key": "scans/2026/04/10/{submission_id}/page_001.jpg",
  "image_quality_score": 0.87,
  "quality_acceptable": true,
  "created_at": "2026-04-10T10:01:00Z"
}
```

**Response** `422` (quality too low):
```json
{
  "error": "image_quality_low",
  "message": "Image quality score 0.32 is below threshold 0.5. Please re-scan.",
  "quality_score": 0.32,
  "guidance": ["Ensure adequate lighting", "Hold device steady", "Avoid shadows"]
}
```

### POST /submissions/{id}/finalize-scan
Trigger OCR processing after all pages are uploaded.

**Response** `202`:
```json
{
  "id": "uuid",
  "status": "ocr_processing",
  "estimated_completion_seconds": 15
}
```

## OCR Review

### GET /submissions/{id}/ocr-results
Get OCR extraction results for review.

**Response** `200`:
```json
{
  "submission_id": "uuid",
  "status": "pending_classification",
  "pages": [
    {
      "page_number": 1,
      "ocr_raw_text": "string",
      "ocr_confidence": 0.89
    }
  ]
}
```

### PUT /submissions/{id}/ocr-corrections
Submit staff corrections to OCR output.

**Request**:
```json
{
  "pages": [
    {
      "page_number": 1,
      "corrected_text": "string"
    }
  ]
}
```

**Response** `200`: Updated submission.

## Classification

### GET /submissions/{id}/classification
Get AI classification result for confirmation.

**Response** `200`:
```json
{
  "submission_id": "uuid",
  "classification": {
    "document_type_id": "uuid",
    "document_type_name": "Birth Certificate Request",
    "confidence": 0.92,
    "alternatives": [
      {"document_type_id": "uuid", "name": "Name Change Request", "confidence": 0.06}
    ]
  },
  "template_data": {
    "applicant_name": "Nguyễn Văn A",
    "date_of_birth": "1990-05-15",
    "place_of_birth": "Hà Nội"
  }
}
```

### POST /submissions/{id}/confirm-classification
Confirm or override classification.

**Request**:
```json
{
  "document_type_id": "uuid",
  "template_data": { "field": "corrected_value" },
  "classification_method": "ai_confirmed | manual"
}
```

**Response** `200`: Updated submission with status `classified`.

### POST /submissions/{id}/route
Trigger workflow routing after classification confirmation.

**Response** `200`:
```json
{
  "submission_id": "uuid",
  "status": "in_progress",
  "workflow_steps": [
    {"step_order": 1, "department": "Civil Registry", "status": "active"},
    {"step_order": 2, "department": "Legal Review", "status": "pending"},
    {"step_order": 3, "department": "Director Approval", "status": "pending"}
  ]
}
```

## Department Queue & Review

### GET /departments/{id}/queue
List submissions in department's review queue.

**Query params**: `status=active&priority=all&page=1&per_page=20`

**Response** `200`:
```json
{
  "items": [
    {
      "workflow_step_id": "uuid",
      "submission_id": "uuid",
      "document_type_name": "Land Registration",
      "citizen_name": "Trần Thị B",
      "priority": "urgent",
      "started_at": "2026-04-09T08:00:00Z",
      "expected_complete_by": "2026-04-10T17:00:00Z",
      "is_delayed": false
    }
  ],
  "total": 45,
  "page": 1
}
```

### GET /workflow-steps/{id}
Get full review context for a workflow step.

**Response** `200`:
```json
{
  "id": "uuid",
  "submission_id": "uuid",
  "step_order": 2,
  "department": {"id": "uuid", "name": "Legal Review"},
  "status": "active",
  "submission": {
    "document_type_name": "Land Registration",
    "security_classification": 1,
    "template_data": {},
    "scanned_pages": [
      {"page_number": 1, "image_url": "signed-oss-url", "ocr_text": "..."}
    ]
  },
  "prior_annotations": [
    {"step_order": 1, "department": "Civil Registry", "annotations": []}
  ]
}
```

### POST /workflow-steps/{id}/complete
Complete a review step.

**Request**:
```json
{
  "result": "approved | rejected | needs_info",
  "annotation": {
    "content": "Approved. All documents verified.",
    "visible_to_citizen": false
  },
  "citizen_request": {
    "content": "Please provide a certified copy of your marriage certificate.",
    "visible_to_citizen": true
  }
}
```

**Response** `200`: Updated workflow step. Next step activated if approved.

### POST /workflow-steps/{id}/consultations
Initiate cross-department consultation.

**Request**:
```json
{
  "target_department_id": "uuid",
  "question": "string"
}
```

**Response** `201`: Consultation annotation created.

## Error Responses

All errors follow:
```json
{
  "error": "error_code",
  "message": "Human-readable description",
  "details": {}
}
```

| Code | HTTP Status | Description |
|---|---|---|
| `clearance_denied` | 403 | User clearance insufficient for document classification |
| `submission_not_found` | 404 | |
| `invalid_state_transition` | 409 | Action not valid for current submission/step status |
| `image_quality_low` | 422 | Scanned image below quality threshold |
| `routing_rule_missing` | 422 | No routing rule exists for this document type |
