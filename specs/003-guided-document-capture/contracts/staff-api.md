# API Contracts: Guided Document Capture

**Feature**: 003-guided-document-capture  
**Date**: 2026-04-14  
**Audience**: Staff App (Flutter) — all endpoints under `/v1/staff/`

---

## Summary of Changes

Feature 003 makes **no new API endpoints**. It modifies the response shape of two existing endpoints by adding the `requirement_snapshot` field, and clarifies the existing contract for guided capture usage.

| Endpoint | Method | Change Type | Description |
|----------|--------|-------------|-------------|
| `POST /v1/staff/dossiers` | POST | **MODIFY** | Populate `requirement_snapshot` JSONB at creation; include in response |
| `GET /v1/staff/dossiers/{id}` | GET | **MODIFY** | Include `requirement_snapshot` in response |
| `POST /v1/staff/dossiers/{id}/documents` | POST | No change | Used as-is for guided capture uploads |
| `PATCH /v1/staff/dossiers/{id}/documents/{doc_id}/override-ai` | PATCH | No change | Used for AI override in guided flow |
| `POST /v1/staff/dossiers/{id}/submit` | POST | **MODIFY** | Completeness check reads from snapshot |

---

## Modified Endpoints

### `POST /v1/staff/dossiers` — Create Dossier

**Change**: After creating the dossier, the backend now builds and stores a `requirement_snapshot` JSONB from the selected case type's live requirement groups, slots, and document types. The snapshot is returned in the response.

**Request** (unchanged):
```json
{
  "citizen_id_number": "012345678901",
  "case_type_id": "uuid",
  "security_classification": 0,
  "priority": "normal"
}
```

**Response** (201 — new field highlighted):
```json
{
  "id": "uuid",
  "reference_number": null,
  "status": "draft",
  "case_type": {
    "id": "uuid",
    "code": "BIRTH_REG",
    "name": "Đăng ký khai sinh"
  },
  "citizen": {
    "id": "uuid"
  },
  "security_classification": 0,
  "priority": "normal",

  "requirement_snapshot": {                          // ← NEW
    "case_type_code": "BIRTH_REG",
    "case_type_name": "Đăng ký khai sinh",
    "snapshot_at": "2026-04-14T10:30:00+07:00",
    "groups": [
      {
        "id": "group-uuid-1",
        "group_order": 1,
        "label": "Tờ khai đăng ký khai sinh",
        "is_mandatory": true,
        "slots": [
          {
            "id": "slot-uuid-1a",
            "document_type_id": "dt-uuid-birth-form",
            "document_type_code": "BIRTH_REG_FORM",
            "document_type_name": "Tờ khai đăng ký khai sinh",
            "description": "Tờ khai đăng ký khai sinh theo mẫu...",
            "classification_prompt": "Đây là Tờ khai đăng ký khai sinh...",
            "label_override": null
          }
        ]
      },
      {
        "id": "group-uuid-2",
        "group_order": 2,
        "label": "Giấy chứng sinh",
        "is_mandatory": true,
        "slots": [
          {
            "id": "slot-uuid-2a",
            "document_type_id": "dt-uuid-medical-cert",
            "document_type_code": "BIRTH_CERTIFICATE_MEDICAL",
            "document_type_name": "Giấy chứng sinh",
            "description": "Giấy chứng sinh do cơ sở y tế cấp...",
            "classification_prompt": "Đây là Giấy chứng sinh do bệnh viện...",
            "label_override": null
          }
        ]
      },
      {
        "id": "group-uuid-3",
        "group_order": 3,
        "label": "CCCD/CMND của người đi đăng ký (cha hoặc mẹ)",
        "is_mandatory": true,
        "slots": [
          {
            "id": "slot-uuid-3a",
            "document_type_id": "dt-uuid-cccd",
            "document_type_code": "ID_CCCD",
            "document_type_name": "Căn cước công dân / CMND",
            "description": "Căn cước công dân (CCCD) gắn chip...",
            "classification_prompt": "Đây là Căn cước công dân (CCCD)...",
            "label_override": "CCCD/CMND cha hoặc mẹ"
          },
          {
            "id": "slot-uuid-3b",
            "document_type_id": "dt-uuid-passport",
            "document_type_code": "PASSPORT_VN",
            "document_type_name": "Hộ chiếu Việt Nam",
            "description": "Hộ chiếu phổ thông Việt Nam...",
            "classification_prompt": "Đây là Hộ chiếu Việt Nam...",
            "label_override": "Hộ chiếu (nếu không có CCCD)"
          }
        ]
      },
      {
        "id": "group-uuid-4",
        "group_order": 4,
        "label": "Giấy chứng nhận kết hôn (nếu cha mẹ đã đăng ký kết hôn)",
        "is_mandatory": false,
        "slots": [
          {
            "id": "slot-uuid-4a",
            "document_type_id": "dt-uuid-marriage",
            "document_type_code": "MARRIAGE_CERT",
            "document_type_name": "Giấy chứng nhận kết hôn",
            "description": "Giấy chứng nhận kết hôn do UBND...",
            "classification_prompt": "Đây là Giấy chứng nhận kết hôn...",
            "label_override": null
          }
        ]
      }
    ]
  },

  "completeness": {
    "complete": false,
    "missing_groups": ["group-uuid-1", "group-uuid-2", "group-uuid-3"]
  },
  "requirement_groups": [...],
  "documents": [],
  "workflow_steps": [],
  "created_at": "2026-04-14T10:30:00+07:00",
  "updated_at": "2026-04-14T10:30:00+07:00"
}
```

**Notes**:
- The existing `requirement_groups` field (live join) is preserved for backward compatibility.
- The guided capture UI should prefer `requirement_snapshot` when non-null.
- `requirement_snapshot` is `null` for dossiers created before migration 0003.

---

### `GET /v1/staff/dossiers/{id}` — Get Dossier Detail

**Change**: Response now includes `requirement_snapshot` field (same structure as above).

The guided capture screen calls this endpoint to:
1. Load the step list from `requirement_snapshot.groups` (ordered by `group_order`).
2. Cross-reference with `documents` array to determine which steps have captured documents.
3. Read `ai_match_result` and `ai_match_overridden` per document for validation status display.

**Polling behavior** (for AI validation):
- After uploading a document via `POST /documents`, the Flutter client polls this endpoint every 3 seconds for up to 30 seconds.
- It checks if the newly created document's `ai_match_result` has transitioned from `null` to a result object.
- Polling stops when result is received or timeout is reached.

---

### `POST /v1/staff/dossiers/{id}/submit` — Submit Dossier

**Change**: Internal only — the completeness check now reads from `requirement_snapshot` instead of joining live `CaseType` data. The request/response shape is unchanged.

**Completeness check logic** (modified):
```
For each group in dossier.requirement_snapshot.groups:
  if group.is_mandatory:
    fulfilled = any slot.id in documents[].requirement_slot_id
    if not fulfilled:
      add to missing_groups
If missing_groups is not empty:
  return 422 {"detail": "Hồ sơ chưa đầy đủ", "missing_groups": [...]}
```

---

## Unchanged Endpoints (Used As-Is)

### `POST /v1/staff/dossiers/{id}/documents` — Upload Document to Slot

No changes. The guided capture flow calls this endpoint identically to the existing dossier flow:

```
POST /v1/staff/dossiers/{dossier_id}/documents
Content-Type: multipart/form-data

requirement_slot_id: uuid (from snapshot.groups[].slots[].id)
staff_notes: optional string
pages: File[] (1-30 images, max 10MB each)
```

The slot ID in the request comes from the `requirement_snapshot` instead of from a live API call. The backend validates it against the original `document_requirement_slot` table (FK constraint).

### `GET /v1/staff/dossiers/case-types` — List Active Case Types

No changes. Called by the case type selector screen at the start of the guided capture flow.

### `PATCH /v1/staff/dossiers/{id}/documents/{doc_id}/override-ai` — Override AI Decision

No changes. Called when staff taps "Bỏ qua cảnh báo" (Override warning) on a mismatched document.

---

## Contract Compatibility

| Consumer | Impact | Migration |
|----------|--------|-----------|
| Staff App (Flutter) | New field `requirement_snapshot` in dossier responses | Read new field; fall back to `requirement_groups` if null |
| Citizen App (Flutter) | No impact | Citizen endpoints do not expose `requirement_snapshot` |
| Celery workers | No impact | Workers read `DossierDocument` and `DocumentType` directly |
| Existing tests | Backward compatible | New field is nullable; existing tests pass without changes |
