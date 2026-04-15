# API Contracts: Search & AI Summarization (Staff)

**Feature**: 005-search-and-summarization
**Date**: 2026-04-15
**Base URL**: `/v1/staff`

---

## New Endpoints

### `GET /v1/staff/search`

**Purpose**: Cross-department full-text search across submissions, dossiers, and OCR content with clearance filtering.

**Authentication**: Staff JWT required. Clearance level extracted from token.

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | YES | — | Search query (min 2 chars) |
| `status` | string | NO | — | Filter: `pending`, `in_progress`, `completed`, `rejected` |
| `document_type_code` | string | NO | — | Filter by document type code |
| `case_type_code` | string | NO | — | Filter by case type code |
| `department_id` | UUID | NO | — | Filter by department |
| `date_from` | date | NO | — | Filter: submitted after this date (inclusive) |
| `date_to` | date | NO | — | Filter: submitted before this date (inclusive) |
| `sort` | string | NO | `relevance` | Sort: `relevance`, `submitted_at`, `updated_at` |
| `page` | int | NO | 1 | Page number (1-based) |
| `per_page` | int | NO | 20 | Items per page (max 50) |

**Response 200**:
```json
{
  "results": [
    {
      "type": "submission",
      "id": "uuid",
      "status": "completed",
      "submitted_at": "2026-04-10T08:30:00Z",
      "citizen_name": "Nguyễn Văn An",
      "document_type_name": "Giấy khai sinh",
      "document_type_code": "BIRTH_CERT",
      "ai_summary": "Giấy khai sinh của Nguyễn Văn An, sinh ngày 15/03/2026 tại Bệnh viện Từ Dũ, TP.HCM. Bố: Nguyễn Văn Bình, Mẹ: Trần Thị Cúc.",
      "ai_summary_is_ai_generated": true,
      "relevance_score": 0.85,
      "highlight": "...tên: <em>Nguyễn Văn An</em>, sinh ngày..."
    },
    {
      "type": "dossier",
      "id": "uuid",
      "status": "in_progress",
      "submitted_at": "2026-04-12T09:00:00Z",
      "reference_number": "HS-20260412-001",
      "citizen_name": "Nguyễn Văn An",
      "case_type_name": "Đăng ký khai sinh",
      "case_type_code": "BIRTH_REG",
      "ai_summary": "Hồ sơ đăng ký khai sinh cho Nguyễn Văn An gồm 3 tài liệu: tờ khai, giấy chứng sinh, bản sao CCCD.",
      "ai_summary_is_ai_generated": true,
      "relevance_score": 0.72,
      "highlight": "...đăng ký khai sinh cho <em>Nguyễn Văn An</em>..."
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 42,
    "total_pages": 3
  },
  "query": "Nguyễn Văn An"
}
```

**Response 422** (validation error):
```json
{
  "detail": "Truy vấn tìm kiếm phải có ít nhất 2 ký tự"
}
```

**Security**: Results filtered by `staff.clearance_level >= resource.security_classification`. Cross-department — no department restriction.

---

### `GET /v1/staff/analytics/sla`

**Purpose**: SLA performance analytics aggregated by department.

**Authentication**: Staff JWT required. Must have role `manager` or `admin`.

**Query Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `date_from` | date | NO | 30 days ago | Start date (inclusive) |
| `date_to` | date | NO | today | End date (inclusive) |
| `department_id` | UUID | NO | — | Filter to specific department |

**Response 200**:
```json
{
  "period": {
    "from": "2026-03-16",
    "to": "2026-04-15"
  },
  "departments": [
    {
      "department_id": "uuid",
      "department_name": "Phòng Tư pháp",
      "department_code": "JUSTICE",
      "metrics": {
        "total_steps": 150,
        "completed_steps": 120,
        "pending_steps": 25,
        "delayed_steps": 5,
        "avg_processing_hours": 4.2,
        "delay_rate": 0.033,
        "completion_rate": 0.80
      }
    }
  ],
  "totals": {
    "total_steps": 450,
    "completed_steps": 380,
    "pending_steps": 55,
    "delayed_steps": 15,
    "avg_processing_hours": 5.1,
    "delay_rate": 0.033,
    "completion_rate": 0.844
  }
}
```

**Response 403** (insufficient role):
```json
{
  "detail": "Chỉ quản lý hoặc admin mới được truy cập thống kê SLA"
}
```

**Security**: No citizen PII in response. Only aggregate counts and averages.

---

## Modified Endpoints

### `GET /v1/staff/departments/{department_id}/queue` — Add Summary Preview

**Change**: Add `summary_preview` field to each queue item.

**New fields in response item**:

| Field | Type | Description |
|-------|------|-------------|
| `summary_preview` | string \| null | First 100 chars of `ai_summary`, or `null` if not yet generated |

**Updated response item example**:
```json
{
  "workflow_step_id": "uuid",
  "submission_id": "uuid",
  "dossier_id": null,
  "step_order": 1,
  "status": "active",
  "priority": "urgent",
  "started_at": "2026-04-10T08:30:00Z",
  "citizen_name": "Nguyễn Văn An",
  "document_type_name": "Giấy khai sinh",
  "summary_preview": "Giấy khai sinh của Nguyễn Văn An, sinh ngày 15/03/2026 tại Bệnh viện Từ Dũ, TP.HCM..."
}
```

---

### `GET /v1/staff/submissions/{id}/classification` — Add Summary

**Change**: Include `ai_summary` in classification response.

**New fields**:

| Field | Type | Description |
|-------|------|-------------|
| `ai_summary` | string \| null | AI-generated summary |
| `ai_summary_is_ai_generated` | bool | Always `true` when summary present — UI label hint |
| `entities` | object \| null | Extracted entities from `template_data["_entities"]` |

---

### `GET /v1/citizen/dossiers/{id}` — Add Summary

**Change**: Include `ai_summary` in dossier detail response for citizen app.

**New fields**:

| Field | Type | Description |
|-------|------|-------------|
| `ai_summary` | string \| null | AI-generated dossier summary |

---

## Error Codes

| Code | Endpoint | Condition |
|------|----------|-----------|
| 422 | `GET /search` | Query `q` is less than 2 characters |
| 422 | `GET /search` | Invalid filter parameter values |
| 403 | `GET /analytics/sla` | Staff does not have `manager` or `admin` role |
| 400 | `GET /search` | `per_page` exceeds 50 |
