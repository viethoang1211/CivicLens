# API Contract: Citizen Dossier Tracking

**Feature**: 002-case-based-submission  
**Base Path**: `/v1/citizen/dossiers`  
**Auth**: Citizen JWT (VNeID-authenticated)  
**Date**: 2026-04-11

---

## Endpoints

### `GET /v1/citizen/dossiers`

List all dossiers belonging to the authenticated citizen, ordered by most recent first.

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | string | — | Filter by status |
| `page` | int | 1 | Pagination |
| `page_size` | int | 20 | Max 50 |

**Response 200**:
```json
{
  "total": 3,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid",
      "reference_number": "HS-20260411-00042",
      "case_type_name": "Đăng ký hộ kinh doanh cá thể",
      "status": "in_progress",
      "status_label_vi": "Đang xử lý",
      "current_department": "Phòng Hành chính (Administrative)",
      "priority": "normal",
      "submitted_at": "2026-04-11T08:30:00Z",
      "estimated_completion": "2026-04-14T17:00:00Z"
    }
  ]
}
```

---

### `GET /v1/citizen/dossiers/{dossier_id}`

Get full tracking detail for a specific dossier owned by the citizen.

**Response 200**:
```json
{
  "id": "uuid",
  "reference_number": "HS-20260411-00042",
  "status": "in_progress",
  "status_label_vi": "Đang xử lý",
  "case_type_name": "Đăng ký hộ kinh doanh cá thể",
  "submitted_at": "2026-04-11T08:30:00Z",
  "completed_at": null,
  "rejection_reason": null,
  "workflow_steps": [
    {
      "step_order": 1,
      "department_name": "Tiếp nhận (Reception)",
      "status": "completed",
      "status_label_vi": "Đã hoàn thành",
      "started_at": "2026-04-11T08:30:00Z",
      "completed_at": "2026-04-11T10:00:00Z"
    },
    {
      "step_order": 2,
      "department_name": "Phòng Hành chính (Administrative)",
      "status": "active",
      "status_label_vi": "Đang xử lý",
      "started_at": "2026-04-11T10:00:00Z",
      "completed_at": null,
      "expected_complete_by": "2026-04-14T10:00:00Z"
    }
  ]
}
```

**Privacy**: Does not expose internal staff reviewer names, document content, AI scores, or OSS keys.

**Errors**: 404 if not found or dossier belongs to a different citizen.

---

### `GET /v1/citizen/dossiers/lookup`

Look up a dossier by reference number only (no auth required — for use at public kiosks or when citizen doesn't have the app).

**Query Parameters**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `reference_number` | string | Yes | e.g. `HS-20260411-00042` |

**Auth**: None (public endpoint — reference number acts as the access token for this limited view)

**Response 200**: Same structure as `GET /v1/citizen/dossiers/{dossier_id}` but **without** `id` (UUID) in the response to prevent enumeration.

**Rate Limiting**: 10 requests per minute per IP to prevent enumeration attacks.

**Errors**:
| Status | Condition |
|--------|-----------|
| 404 | Reference number not found |
| 429 | Rate limit exceeded |

---

## Status Label Mapping (Vietnamese)

| Status | `status_label_vi` |
|--------|-------------------|
| `draft` | Đang soạn thảo |
| `scanning` | Đang quét tài liệu |
| `ready` | Sẵn sàng nộp |
| `submitted` | Đã tiếp nhận |
| `in_progress` | Đang xử lý |
| `completed` | Hoàn thành |
| `rejected` | Bị trả lại |

---

## Notes

- All citizen endpoints return minimal information sufficient for tracking only.
- Sensitive fields (staff reviewer identity, document contents, AI results) are never exposed to citizens.
- The `lookup` endpoint intentionally omits the UUID dossier ID to prevent UUID enumeration.
- `estimated_completion` is derived from `workflow_step.expected_complete_by` of the current active step; nullable if no SLA is configured.
