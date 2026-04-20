# Document Classification Flow

> How the system automatically identifies document types after scanning.

## Overview

When staff scan a document (quick scan or dossier slot upload), the system runs a
**dual-path ensemble classification** pipeline. Two independent AI models analyze
the document from different angles, and their results are combined for higher accuracy.

```
┌─────────────┐
│  Staff scans │
│  document    │
└──────┬──────┘
       │
       ▼
┌──────────────┐     ┌──────────────────────────────────────────────┐
│  OCR Worker  │────▶│  ScannedPage.ocr_raw_text stored in DB      │
└──────┬───────┘     └──────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                  classification_worker.py                        │
│                                                                  │
│  ┌─────────────────┐                                             │
│  │ OCR Quality Gate │──── confidence < 0.3 → SKIP, flag warning  │
│  └────────┬────────┘                                             │
│           │ pass                                                 │
│           ▼                                                      │
│  ┌────────────────┐    ┌─────────────────┐                       │
│  │ Path 1: TEXT   │    │ Path 2: VISION  │                       │
│  │ (qwen-plus)    │    │ (qwen-vl-max)   │                       │
│  │ Analyzes OCR   │    │ Analyzes image  │                       │
│  │ text content   │    │ directly        │                       │
│  └────────┬───────┘    └────────┬────────┘                       │
│           │                     │                                │
│           └──────┬──────────────┘                                │
│                  ▼                                                │
│         ┌────────────────┐                                       │
│         │   ENSEMBLE     │                                       │
│         │  Combine both  │                                       │
│         │  results       │                                       │
│         └────────┬───────┘                                       │
│                  │                                                │
│                  ▼                                                │
│         ┌────────────────┐                                       │
│         │ Template Fill  │── Extract fields (name, CCCD, etc.)   │
│         └────────┬───────┘                                       │
│                  │                                                │
│                  ▼                                                │
│         ┌────────────────┐                                       │
│         │ Citizen Link   │── Auto-link via CCCD number           │
│         └────────────────┘                                       │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────┐
│ Summarization    │ (chained Celery task)
│ Worker           │
└──────────────────┘
```

---

## Step-by-Step Flow

### 1. OCR Quality Gate

Before spending API calls on classification, the system checks OCR text quality
using `estimate_ocr_confidence()`:

| Score   | Meaning                        | Action             |
|---------|--------------------------------|--------------------|
| < 0.2   | Empty or near-empty text       | Skip classification |
| 0.2–0.3 | Very short / garbage text      | Skip, flag `_ocr_quality_too_low` |
| 0.3–0.5 | Low quality, few Vietnamese chars | Proceed with caution |
| 0.7+    | Good Vietnamese text           | Proceed normally   |
| 0.85+   | Rich text with dates/numbers   | High confidence input |

**Config:** `classification_confidence_threshold = 0.7` (in `src/config.py`)

### 2. Path 1 — Text-Based Classification

**Model:** `qwen-plus` (via dashscope `Generation` API)

The OCR text (up to 8,000 chars) is sent to the LLM along with all active
`DocumentType` records. The prompt asks the model to:

1. Identify characteristic keywords (form names, titles, issuing authority)
2. Identify personal information (name, CCCD number, date of birth)
3. Match to the best document type

**Output format:**
```json
{
  "document_type_code": "BIRTH_REG_FORM",
  "confidence": 0.92,
  "reasoning": "Tờ khai có tiêu đề 'Đăng ký khai sinh', ghi rõ họ tên cha mẹ...",
  "key_signals": ["đăng ký khai sinh", "theo mẫu TT04"],
  "alternatives": [
    {"code": "BIRTH_CERTIFICATE_MEDICAL", "confidence": 0.15}
  ]
}
```

### 3. Path 2 — Vision-Based Classification

**Model:** `qwen-vl-max` (via dashscope `MultiModalConversation` API)

The actual document image (first page, base64-encoded) is sent to the multimodal
model. The prompt asks the model to classify based on **visual features**:

1. Layout (card vs A4, form with fill-in boxes, free-form text)
2. Official elements (red stamps, national emblem, bold headers)
3. Prominent content (names, ID numbers, dates)

Each `DocumentType` has an optional `classification_prompt` field with visual
identification hints (e.g., "Thẻ nhựa có quốc huy, ảnh 3x4" for CCCD).

**Output format:**
```json
{
  "document_type_code": "BIRTH_REG_FORM",
  "confidence": 0.88,
  "reasoning": "Văn bản A4 có tiêu đề in đậm, con dấu đỏ UBND...",
  "visual_features": ["con dấu đỏ", "biểu mẫu A4", "tiêu đề 'Tờ khai'"],
  "alternatives": [
    {"code": "MARITAL_STATUS_FORM", "confidence": 0.10}
  ]
}
```

### 4. Ensemble Combination

The `_ensemble_classification()` function merges both results:

#### Both models agree (same `document_type_code`)
```
confidence = average(text_conf, vision_conf) + 0.10 bonus
method = "ensemble_agree"
```
Example: Text says `BIRTH_REG_FORM` (0.92), Vision says `BIRTH_REG_FORM` (0.88)
→ Final: `BIRTH_REG_FORM` at **min(1.0, (0.92+0.88)/2 + 0.10) = 1.0**

#### Models disagree (different codes)
```
gap = |primary_conf - secondary_conf|
penalty = 0.20 - (0.15 × gap)     # ranges 0.20 → 0.05
confidence = primary_conf × (1.0 - penalty)
method = "ensemble_disagree"
```
The confidence-gap-aware penalty means: if the winner is far ahead, it's likely
correct and gets a smaller penalty. If both are close in confidence, the
disagreement is genuinely ambiguous — apply full penalty.

Example: Text says `BIRTH_REG_FORM` (0.90), Vision says `MARRIAGE_CERT` (0.40)
→ gap = 0.50, penalty = 0.20 - 0.075 = 0.125
→ Final: `BIRTH_REG_FORM` at **0.90 × 0.875 = 0.7875**
→ `MARRIAGE_CERT` stored as first alternative for staff review.

#### One path failed
```
method = "text_only" or "vision_only"
confidence = surviving path's confidence (no penalty)
```

### 5. Confidence Threshold Enforcement

| Confidence        | `classification_method` | Meaning                     |
|-------------------|-------------------------|-----------------------------|
| ≥ 0.70            | `"ai"`                  | High confidence — auto-classified |
| 0.30 – 0.69       | `"ai_low_confidence"`   | Needs staff review          |
| < 0.30            | _(no template fill)_    | Too uncertain for field extraction |

In all cases the submission status becomes `"pending_classification"` — staff
must confirm before the document proceeds through the workflow.

### 6. Template Filling

After classification, the system extracts structured fields from the OCR text
using the matched `DocumentType.template_schema`:

```
DocumentType: BIRTH_REG_FORM
template_schema: {
  "properties": {
    "ho_ten_con": {"title": "Họ và tên con", "type": "string"},
    "ngay_sinh":  {"title": "Ngày sinh",     "type": "string"},
    "gioi_tinh":  {"title": "Giới tính",     "type": "string"},
    "ho_ten_me":  {"title": "Họ tên mẹ",     "type": "string"},
    "ho_ten_cha": {"title": "Họ tên cha",    "type": "string"},
    "cccd_me":    {"title": "Số CCCD mẹ",    "type": "string"}
  }
}
```

**Result (stored in `submission.template_data`):**
```json
{
  "ho_ten_con": "Nguyễn Văn Minh",
  "ngay_sinh": "15/03/2024",
  "gioi_tinh": "Nam",
  "ho_ten_me": "Trần Thị Lan",
  "ho_ten_cha": "Nguyễn Văn An",
  "cccd_me": "001204012345",
  "_classification_method": "ensemble_agree",
  "_classification_confidence": 0.95,
  "_classification_reasoning": "[Hình ảnh] Biểu mẫu A4... | [Nội dung] Từ khóa...",
  "_citizen_identified": true
}
```

### 7. CCCD Detection & Citizen Linking

#### Single-page scan
If the classified type is `ID_CCCD`, the CCCD number from template fill is used
to auto-link/create a `Citizen` record.

#### Multi-page scan (e.g., birth form + CCCD)
1. `_detect_cccd_page()` identifies which page is the CCCD by counting keyword
   matches (≥3 of: "căn cước công dân", "citizen identity card", "số / no", etc.)
2. The CCCD page is excluded from classification candidates (the main document
   is classified instead)
3. A separate `fill_template` call runs on the CCCD page with the `ID_CCCD`
   schema to extract `so_cccd`, `ho_ten`, `ngay_sinh`, etc.
4. The citizen is auto-linked to both the submission and its dossier.

If no CCCD data is found, the system sets `_missing_cccd_warning` to prompt
staff to scan a CCCD separately.

---

## Concrete Example: Birth Registration

**Scenario:** Staff scans a 2-page document: page 1 = birth registration form,
page 2 = mother's CCCD.

```
Step 1: OCR Worker
  ├── Page 1 OCR: "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM... TỜ KHAI ĐĂNG KÝ
  │                KHAI SINH... Họ tên: Nguyễn Văn Minh... Ngày sinh: 15/03/2024..."
  └── Page 2 OCR: "CĂN CƯỚC CÔNG DÂN... Số: 001204012345... Họ và tên: TRẦN THỊ LAN..."

Step 2: OCR Quality Gate
  └── estimate_ocr_confidence = 0.85 → PASS ✓

Step 3: CCCD Detection (cached)
  └── Page 2 has 5 CCCD keywords → cccd_page = Page 2, cccd_number = "001204012345"

Step 4: Text Classification (excludes ID_CCCD from candidates)
  └── Input: combined OCR text (both pages)
  └── Output: {"document_type_code": "BIRTH_REG_FORM", "confidence": 0.92}

Step 5: Vision Classification
  └── Input: Page 1 image (Page 2 excluded as CCCD page)
  └── Output: {"document_type_code": "BIRTH_REG_FORM", "confidence": 0.88}

Step 6: Ensemble
  └── Both agree → confidence = (0.92 + 0.88) / 2 + 0.10 = 1.0
  └── method = "ensemble_agree"

Step 7: Template Fill (BIRTH_REG_FORM schema)
  └── {"ho_ten_con": "Nguyễn Văn Minh", "ngay_sinh": "15/03/2024", ...}

Step 8: CCCD Template Fill (ID_CCCD schema, from cached cccd_page)
  └── {"so_cccd": "001204012345", "ho_ten": "Trần Thị Lan", ...}
  └── Promoted to submission.template_data["so_cccd"]

Step 9: Citizen Linking
  └── Look up Citizen where id_number = "001204012345"
  └── Not found → auto-create Citizen(full_name="Trần Thị Lan")
  └── Link submission + dossier to this citizen

Step 10: Chain to Summarization Worker
```

---

## Key Files

| File | Purpose |
|------|---------|
| `src/workers/classification_worker.py` | Main classification pipeline (Celery task) |
| `src/services/ai_client.py` | AI model wrappers (OCR, classify, fill, validate) |
| `src/models/document_type.py` | Document type definitions with `template_schema` and `classification_prompt` |
| `src/models/submission.py` | Stores classification result, confidence, and extracted data |
| `src/config.py` | `classification_confidence_threshold` (default 0.7) |
| `src/seeds/seed_data.py` | All document type definitions with schemas |

## Key Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `run_classification` | classification_worker.py | Main Celery task entry point |
| `_ensemble_classification` | classification_worker.py | Merges text + vision results |
| `_detect_cccd_page` | classification_worker.py | Finds CCCD page by keyword matching |
| `_parse_ai_json` | classification_worker.py | Robust JSON parsing from AI output |
| `_try_auto_link_citizen` | classification_worker.py | Links citizen via CCCD in template_data |
| `validate_document_slot` | classification_worker.py | Validates dossier document vs expected slot |
| `estimate_ocr_confidence` | ai_client.py | Scores OCR text quality (0.0–1.0) |

## Supported Document Types (as of seed data)

| Code | Name | Category |
|------|------|----------|
| `ID_CCCD` | Căn cước công dân | Identity |
| `PASSPORT_VN` | Hộ chiếu Việt Nam | Identity |
| `BIRTH_REG_FORM` | Tờ khai đăng ký khai sinh | Civil registration |
| `BIRTH_CERTIFICATE_MEDICAL` | Giấy chứng sinh | Medical |
| `MARRIAGE_CERT` | Giấy chứng nhận kết hôn | Civil registration |
| `MARITAL_STATUS_FORM` | Tờ khai xác nhận tình trạng hôn nhân | Civil registration |
| `RESIDENCE_FORM_CT01` | Tờ khai thay đổi cư trú | Residence |
| `RESIDENCE_PROOF` | Giấy tờ chứng minh chỗ ở | Residence |
| `RESIDENCE_CONFIRM` | Giấy xác nhận cư trú | Residence |
| `BIZ_REG_FORM` | Đơn đăng ký hộ kinh doanh | Business |
| `COMPANY_REG_FORM` | Đơn đăng ký doanh nghiệp | Business |
| `COMPANY_CHARTER` | Điều lệ công ty | Business |
| `MEMBER_LIST` | Danh sách thành viên/cổ đông | Business |
| `COMPLAINT` | Đơn khiếu nại/tố cáo | Complaints |
| `CLASSIFIED_RPT` | Báo cáo nội bộ có độ mật | Internal |
