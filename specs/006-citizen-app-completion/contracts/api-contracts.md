# API Contracts: Citizen App Completion

**Feature**: 006-citizen-app-completion  
**Date**: 2026-04-16

## Existing Endpoints (No Changes to Shape)

### GET /v1/citizen/dossiers (Auth Required)

**Query Params**: `status` (string, optional), `page` (int, default 1), `page_size` (int, default 20, max 50)

**Response 200**:
```json
{
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid-string",
      "reference_number": "HS-20260416-00001",
      "case_type_name": "Đăng ký kinh doanh",
      "status": "in_progress",
      "status_label_vi": "Đang xử lý",
      "current_department_id": "uuid-string",
      "priority": "normal",
      "submitted_at": "2026-04-16T10:00:00+07:00",
      "estimated_completion": "2026-04-23T10:00:00+07:00"
    }
  ]
}
```

### GET /v1/citizen/dossiers/{dossier_id} (Auth Required)

**Response 200**:
```json
{
  "id": "uuid-string",
  "status": "in_progress",
  "status_label_vi": "Đang xử lý",
  "reference_number": "HS-20260416-00001",
  "case_type_name": "Đăng ký kinh doanh",
  "current_department_id": "uuid-string",
  "submitted_at": "2026-04-16T10:00:00+07:00",
  "completed_at": null,
  "rejection_reason": null,
  "estimated_completion": null,
  "workflow_steps": [
    {
      "step_order": 1,
      "department_id": "uuid-string",
      "department_name": "Phòng tiếp nhận",
      "status": "completed",
      "status_label_vi": "Hoàn thành",
      "started_at": "2026-04-16T10:00:00+07:00",
      "completed_at": "2026-04-16T11:00:00+07:00",
      "expected_complete_by": null
    }
  ]
}
```

**Change**: Backend `_build_workflow_steps()` must be updated to include `department_name` by joining Department table.

---

## Modified Endpoints

### GET /v1/citizen/notifications (Auth Required)

**Query Params**: `is_read` (bool, optional), `page` (int, default 1), `per_page` (int, default 20, max 100)

**Response 200 (Updated — adds `dossier_id`)**:
```json
{
  "items": [
    {
      "id": "uuid-string",
      "submission_id": null,
      "dossier_id": "uuid-string",
      "type": "step_advanced",
      "title": "Hồ sơ đã chuyển bước",
      "body": "Hồ sơ HS-20260416-00001 đã chuyển sang bước xử lý tiếp theo.",
      "is_read": false,
      "sent_at": "2026-04-16T12:00:00+07:00"
    }
  ],
  "total": 5,
  "unread_count": 2,
  "page": 1
}
```

**Change**: Add `dossier_id` field to each notification item.

### POST /v1/staff/submissions/{submission_id}/finalize-scan (Auth Required)

**Response 202 (Updated — adds `dossier_id`)**:
```json
{
  "id": "submission-uuid",
  "status": "ocr_processing",
  "estimated_completion_seconds": 15,
  "dossier_id": "auto-created-dossier-uuid"
}
```

**Change**: After finalizing scan, backend auto-creates a Dossier linked to the citizen and returns its ID.

---

## Dart Client Contract Changes

### CitizenApi.listNotifications()

**Before**: `listNotifications({int skip, int limit})`  
**After**: `listNotifications({int page, int perPage})`

Query params change from `skip`/`limit` to `page`/`per_page` to match backend.

### NotificationDto

**Before**: `{id, submissionId, type, title, body, isRead, sentAt, readAt}`  
**After**: `{id, submissionId, dossierId, type, title, body, isRead, sentAt, readAt}`

Add `dossierId` field (nullable String).

### DossierTrackingStepDto

No Dart model change needed — already expects `department_name`. Backend fix adds the field.
