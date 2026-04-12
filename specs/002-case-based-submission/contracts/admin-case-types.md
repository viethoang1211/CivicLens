# API Contract: Admin Case Type Management

**Feature**: 002-case-based-submission  
**Base Path**: `/v1/staff/admin/case-types`  
**Auth**: Staff JWT — role `admin` required for write operations; `staff` for read  
**Date**: 2026-04-11

---

## Endpoints

### `GET /v1/staff/admin/case-types`

List all case types (active and inactive).

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `active_only` | bool | `false` | Filter to `is_active = true` only |

**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Đăng ký hộ kinh doanh cá thể",
      "code": "HOUSEHOLD_BIZ_REG",
      "description": "Hồ sơ đăng ký hộ kinh doanh cá thể tại UBND cấp huyện/quận.",
      "is_active": true,
      "retention_years": 10,
      "retention_permanent": false,
      "requirement_groups": [
        {
          "id": "uuid",
          "group_order": 1,
          "label": "Bản sao Hộ khẩu",
          "is_mandatory": true,
          "slots": [
            { "id": "uuid", "document_type_id": "uuid", "document_type_code": "HOUSEHOLD_REG", "label_override": null }
          ]
        },
        {
          "id": "uuid",
          "group_order": 3,
          "label": "Giấy tờ địa điểm kinh doanh",
          "is_mandatory": true,
          "slots": [
            { "id": "uuid", "document_type_id": "uuid", "document_type_code": "RENTAL_CONTRACT", "label_override": "Hợp đồng thuê địa điểm" },
            { "id": "uuid", "document_type_id": "uuid", "document_type_code": "PROPERTY_CERT", "label_override": "Giấy chủ quyền nhà" }
          ]
        }
      ],
      "routing_steps": [
        { "id": "uuid", "step_order": 1, "department_id": "uuid", "department_name": "Tiếp nhận (Reception)", "expected_duration_hours": 48, "required_clearance_level": 0 },
        { "id": "uuid", "step_order": 2, "department_id": "uuid", "department_name": "Phòng Hành chính (Administrative)", "expected_duration_hours": 72, "required_clearance_level": 0 }
      ],
      "created_at": "2026-04-11T00:00:00Z",
      "updated_at": "2026-04-11T00:00:00Z"
    }
  ]
}
```

---

### `POST /v1/staff/admin/case-types`

Create a new case type with its requirement groups and routing steps.

**Request Body**:
```json
{
  "name": "Đăng ký hộ kinh doanh cá thể",
  "code": "HOUSEHOLD_BIZ_REG",
  "description": "Optional description",
  "retention_years": 10,
  "retention_permanent": false,
  "requirement_groups": [
    {
      "group_order": 1,
      "label": "Bản sao Hộ khẩu",
      "is_mandatory": true,
      "slots": [
        { "document_type_id": "uuid" }
      ]
    },
    {
      "group_order": 3,
      "label": "Giấy tờ địa điểm kinh doanh",
      "is_mandatory": true,
      "slots": [
        { "document_type_id": "uuid", "label_override": "Hợp đồng thuê địa điểm" },
        { "document_type_id": "uuid", "label_override": "Giấy chủ quyền nhà" }
      ]
    }
  ],
  "routing_steps": [
    { "step_order": 1, "department_id": "uuid", "expected_duration_hours": 48, "required_clearance_level": 0 },
    { "step_order": 2, "department_id": "uuid", "expected_duration_hours": 72, "required_clearance_level": 0 }
  ]
}
```

**Validation**:
- `code` must be unique (409 if duplicate)
- `requirement_groups[*].slots` must not be empty (at least 1 slot per group)
- `routing_steps[*].step_order` must be unique within the request
- `routing_steps[*].department_id` must reference an existing active department

**Response 201**:
```json
{ "id": "uuid", "code": "HOUSEHOLD_BIZ_REG", "name": "Đăng ký hộ kinh doanh cá thể" }
```

**Errors**:
| Status | Code | Condition |
|--------|------|-----------|
| 409 | `case_type_code_conflict` | Code already exists |
| 422 | `empty_slots` | A requirement group has no slots |
| 404 | `department_not_found` | A referenced department_id does not exist |

---

### `GET /v1/staff/admin/case-types/{case_type_id}`

Get a single case type with full detail (same structure as list items).

**Errors**: 404 if not found.

---

### `PUT /v1/staff/admin/case-types/{case_type_id}`

Update a case type's metadata. Does **not** replace requirement groups or routing steps — use sub-resource endpoints for those.

**Request Body** (all fields optional):
```json
{
  "name": "New name",
  "description": "Updated description",
  "retention_years": 15,
  "retention_permanent": false
}
```

**Response 200**: Updated case type object (same as GET).

---

### `POST /v1/staff/admin/case-types/{case_type_id}/deactivate`

Deactivate a case type. In-progress dossiers are unaffected. New dossiers cannot be created for an inactive case type.

**Response 200**: `{ "id": "uuid", "is_active": false }`

---

### `POST /v1/staff/admin/case-types/{case_type_id}/activate`

Re-activate a previously deactivated case type.

**Response 200**: `{ "id": "uuid", "is_active": true }`

---

### `PUT /v1/staff/admin/case-types/{case_type_id}/requirement-groups`

Replace the entire requirement groups (and their slots) for a case type. Atomic operation — old groups deleted and new groups inserted within a transaction. Only allowed if no dossiers are in `submitted` / `in_progress` status for this case type.

**Request Body**: Same as `requirement_groups` array in POST.

**Errors**:
| Status | Code | Condition |
|--------|------|-----------|
| 409 | `active_dossiers_exist` | There are dossiers in-progress for this case type |

---

### `PUT /v1/staff/admin/case-types/{case_type_id}/routing-steps`

Replace routing steps for a case type. Same atomicity and constraints as requirement groups replacement.

**Request Body**: Same as `routing_steps` array in POST.

---

## Notes

- All write endpoints require staff JWT with `is_admin = true`.
- Read endpoints (`GET`) are accessible to any authenticated staff member.
- All timestamps are ISO 8601 with timezone.
