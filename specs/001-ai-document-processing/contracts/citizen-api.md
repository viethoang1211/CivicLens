# API Contracts: Citizen App Backend

**Base URL**: `https://api.{domain}/v1/citizen`
**Auth**: Bearer token (JWT issued after VNeID authentication, contains citizen_id claim)

## Submissions

### GET /submissions
List all submissions for the authenticated citizen.

**Query params**: `status=all|active|completed&page=1&per_page=20`

**Response** `200`:
```json
{
  "items": [
    {
      "id": "uuid",
      "document_type_name": "Birth Certificate Request",
      "status": "in_progress",
      "priority": "normal",
      "submitted_at": "2026-04-08T09:30:00Z",
      "current_step": {
        "step_order": 2,
        "department_name": "Legal Review",
        "status": "active"
      },
      "total_steps": 3,
      "completed_steps": 1,
      "is_delayed": false
    }
  ],
  "total": 5,
  "page": 1
}
```

### GET /submissions/{id}
Get detailed submission with full workflow visualization.

**Response** `200`:
```json
{
  "id": "uuid",
  "document_type_name": "Birth Certificate Request",
  "status": "in_progress",
  "priority": "normal",
  "submitted_at": "2026-04-08T09:30:00Z",
  "completed_at": null,
  "workflow": [
    {
      "step_order": 1,
      "department_name": "Civil Registry",
      "status": "completed",
      "started_at": "2026-04-08T10:00:00Z",
      "completed_at": "2026-04-08T14:00:00Z",
      "result": "approved"
    },
    {
      "step_order": 2,
      "department_name": "Legal Review",
      "status": "active",
      "started_at": "2026-04-08T14:05:00Z",
      "completed_at": null,
      "expected_complete_by": "2026-04-09T17:00:00Z",
      "is_delayed": false
    },
    {
      "step_order": 3,
      "department_name": "Director Approval",
      "status": "pending",
      "started_at": null,
      "completed_at": null
    }
  ],
  "citizen_annotations": [
    {
      "step_order": 2,
      "department_name": "Legal Review",
      "content": "Please provide a certified copy of your marriage certificate.",
      "type": "request_info",
      "created_at": "2026-04-08T15:00:00Z"
    }
  ]
}
```

## Notifications

### GET /notifications
List notifications for the authenticated citizen.

**Query params**: `is_read=false&page=1&per_page=20`

**Response** `200`:
```json
{
  "items": [
    {
      "id": "uuid",
      "submission_id": "uuid",
      "type": "step_advanced",
      "title": "Hồ sơ đã chuyển sang Phòng Pháp lý",
      "body": "Hồ sơ Giấy khai sinh của bạn đã hoàn thành bước Phòng Hộ tịch và chuyển sang Phòng Pháp lý.",
      "is_read": false,
      "sent_at": "2026-04-08T14:05:00Z"
    }
  ],
  "total": 3,
  "unread_count": 2,
  "page": 1
}
```

### PUT /notifications/{id}/read
Mark a notification as read.

**Response** `200`:
```json
{
  "id": "uuid",
  "is_read": true,
  "read_at": "2026-04-10T12:00:00Z"
}
```

## Authentication

### POST /auth/vneid
Exchange VNeID auth code for app JWT.

**Request**:
```json
{
  "vneid_auth_code": "string",
  "redirect_uri": "string"
}
```

**Response** `200`:
```json
{
  "access_token": "jwt-string",
  "refresh_token": "jwt-string",
  "expires_in": 3600,
  "citizen": {
    "id": "uuid",
    "full_name": "Nguyễn Văn A",
    "id_number": "0123456789XX"
  }
}
```

## Error Responses

Same format as staff API:
```json
{
  "error": "error_code",
  "message": "Human-readable description (Vietnamese)",
  "details": {}
}
```

| Code | HTTP Status | Description |
|---|---|---|
| `vneid_auth_failed` | 401 | VNeID authentication failed |
| `submission_not_found` | 404 | Submission not found or not owned by citizen |
| `token_expired` | 401 | JWT expired, use refresh token |
