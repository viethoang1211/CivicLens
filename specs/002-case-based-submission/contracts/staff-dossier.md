# API Contract: Staff Dossier Management

**Feature**: 002-case-based-submission  
**Base Path**: `/v1/staff/dossiers`  
**Auth**: Staff JWT  
**Date**: 2026-04-11

---

## Endpoints

### `POST /v1/staff/dossiers`

Create a new dossier draft for a citizen. Called at the start of the staff intake workflow after the citizen presents their identity and the staff selects a case type.

**Request Body**:
```json
{
  "citizen_id_number": "038094012345",
  "case_type_id": "uuid",
  "security_classification": 0,
  "priority": "normal"
}
```

**Validation**:
- `citizen_id_number` must match an existing citizen (404 if not found)
- `case_type_id` must reference an active case type (404 / 422 if inactive)
- `security_classification` must be 0–3
- `priority` must be `normal` or `urgent`

**Response 201**:
```json
{
  "id": "uuid",
  "status": "draft",
  "case_type": {
    "id": "uuid",
    "code": "HOUSEHOLD_BIZ_REG",
    "name": "Đăng ký hộ kinh doanh cá thể"
  },
  "citizen": {
    "id": "uuid",
    "display_name": "Nguyễn Văn A",
    "id_number": "038094012345"
  },
  "requirement_groups": [
    {
      "id": "uuid",
      "group_order": 1,
      "label": "Bản sao Hộ khẩu",
      "is_mandatory": true,
      "is_fulfilled": false,
      "slots": [
        { "id": "uuid", "document_type_code": "HOUSEHOLD_REG", "label": "Bản sao Hộ khẩu", "fulfilled_by_document_id": null }
      ]
    }
  ],
  "created_at": "2026-04-11T08:00:00Z"
}
```

**Errors**:
| Status | Code | Condition |
|--------|------|-----------|
| 404 | `citizen_not_found` | No citizen with that ID number |
| 404 | `case_type_not_found` | case_type_id does not exist |
| 422 | `case_type_inactive` | Case type is deactivated |
| 422 | `invalid_security_classification` | Value outside 0–3 range |

---

### `GET /v1/staff/dossiers/{dossier_id}`

Retrieve full dossier state including requirement group fulfillment status and uploaded documents.

**Response 200**:
```json
{
  "id": "uuid",
  "reference_number": null,
  "status": "scanning",
  "case_type": { "id": "uuid", "code": "HOUSEHOLD_BIZ_REG", "name": "..." },
  "citizen": { "id": "uuid", "display_name": "Nguyễn Văn A" },
  "security_classification": 0,
  "priority": "normal",
  "completeness": {
    "complete": false,
    "missing_groups": [
      { "group_id": "uuid", "label": "Giấy tờ địa điểm kinh doanh" }
    ]
  },
  "requirement_groups": [
    {
      "id": "uuid",
      "group_order": 1,
      "label": "Bản sao Hộ khẩu",
      "is_mandatory": true,
      "is_fulfilled": true,
      "slots": [
        {
          "id": "uuid",
          "label": "Bản sao Hộ khẩu",
          "fulfilled_by_document_id": "uuid"
        }
      ]
    }
  ],
  "documents": [
    {
      "id": "uuid",
      "requirement_slot_id": "uuid",
      "slot_label": "Bản sao Hộ khẩu",
      "ai_match_result": { "match": true, "confidence": 0.95, "reason": "Matches household registration format" },
      "ai_match_overridden": false,
      "page_count": 2,
      "created_at": "2026-04-11T08:05:00Z"
    }
  ],
  "workflow_steps": [],
  "created_at": "2026-04-11T08:00:00Z",
  "updated_at": "2026-04-11T08:05:00Z"
}
```

---

### `POST /v1/staff/dossiers/{dossier_id}/documents`

Upload a document to a specific requirement slot. Accepts multipart form data with one or more image files (pages of the document). AI slot validation runs asynchronously after upload.

**Request**: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `requirement_slot_id` | UUID | Yes | Which slot this document fulfills |
| `staff_notes` | string | No | Optional note from staff |
| `pages` | file[] | Yes (1–30) | Ordered page images (JPEG/PNG, max 10MB each) |

**Response 201**:
```json
{
  "id": "uuid",
  "dossier_id": "uuid",
  "requirement_slot_id": "uuid",
  "slot_label": "Bản sao Hộ khẩu",
  "ai_match_result": null,
  "ai_match_overridden": false,
  "page_count": 2,
  "pages": [
    { "page_number": 1, "oss_key": "dossier/.../doc/.../p1.jpg", "quality_score": 0.91 },
    { "page_number": 2, "oss_key": "dossier/.../doc/.../p2.jpg", "quality_score": 0.88 }
  ],
  "created_at": "2026-04-11T08:05:00Z"
}
```

Note: `ai_match_result` is `null` immediately after upload (validation runs async via Celery). Poll `GET /dossiers/{id}` to see the result.

**Errors**:
| Status | Code | Condition |
|--------|------|-----------|
| 404 | `dossier_not_found` | Dossier does not exist |
| 409 | `slot_already_fulfilled` | This slot already has a document (DELETE it first to replace) |
| 422 | `image_quality_low` | Page image quality below threshold; re-scan required |
| 422 | `dossier_not_editable` | Dossier is submitted/in_progress/completed |
| 422 | `slot_not_in_case_type` | requirement_slot_id does not belong to this dossier's case type |
| 413 | `file_too_large` | A page image exceeds 10MB |

---

### `DELETE /v1/staff/dossiers/{dossier_id}/documents/{document_id}`

Remove a document from a dossier (e.g., staff scanned the wrong document). Only allowed in `draft` or `scanning` status.

**Response 204**: No content.

**Errors**: 404 if not found; 422 `dossier_not_editable` if status does not allow deletion.

---

### `PATCH /v1/staff/dossiers/{dossier_id}/documents/{document_id}/override-ai`

Staff dismisses an AI mismatch warning and confirms the document is correctly placed.

**Request Body**:
```json
{ "staff_notes": "Citizen confirmed this is a valid rental contract despite AI flag." }
```

**Response 200**: Updated document object with `ai_match_overridden: true`.

---

### `POST /v1/staff/dossiers/{dossier_id}/submit`

Submit the completed dossier. System checks completeness, assigns a reference number, and triggers routing.

**Request Body**: Empty `{}`

**Response 200**:
```json
{
  "id": "uuid",
  "reference_number": "HS-20260411-00042",
  "status": "submitted",
  "submitted_at": "2026-04-11T08:30:00Z",
  "workflow_initiated": true,
  "first_department": "Tiếp nhận (Reception)"
}
```

**Errors**:
| Status | Code | Condition |
|--------|------|-----------|
| 422 | `dossier_incomplete` | One or more mandatory requirement groups are not fulfilled; body includes `missing_groups` array |
| 422 | `already_submitted` | Dossier is already submitted or in-progress |
| 422 | `no_routing_steps` | Case type has no routing steps configured; manual routing required |

---

### `GET /v1/staff/dossiers`

List dossiers managed by the staff member (or all, if admin).

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status |
| `case_type_id` | UUID | Filter by case type |
| `citizen_id` | UUID | Filter by citizen |
| `page` | int | Pagination (default 1) |
| `page_size` | int | Items per page (default 20, max 100) |

**Response 200**:
```json
{
  "total": 150,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid",
      "reference_number": "HS-20260411-00042",
      "status": "in_progress",
      "case_type_name": "Đăng ký hộ kinh doanh cá thể",
      "citizen_display_name": "Nguyễn Văn A",
      "priority": "normal",
      "submitted_at": "2026-04-11T08:30:00Z",
      "current_department": "Phòng Hành chính (Administrative)"
    }
  ]
}
```
