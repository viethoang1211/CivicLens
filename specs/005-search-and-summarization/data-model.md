# Data Model: Search & AI Summarization

**Feature**: 005-search-and-summarization
**Date**: 2026-04-15
**References**: [research.md](research.md) (R-001, R-002, R-003)

---

## Schema Changes

### Modified Tables

#### `submission` — Add AI Summary

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `ai_summary` | `Text` | YES | `NULL` | AI-generated 2-3 sentence Vietnamese summary |
| `ai_summary_generated_at` | `DateTime(timezone=True)` | YES | `NULL` | When summary was last generated |

- Summary is populated async by Celery task after classification completes.
- Set to `NULL` when OCR text is empty or OCR confidence < 0.3.
- Regenerated when OCR text is corrected by staff.

#### `dossier` — Add AI Summary

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `ai_summary` | `Text` | YES | `NULL` | AI-generated 2-3 sentence Vietnamese summary (aggregated from document summaries) |
| `ai_summary_generated_at` | `DateTime(timezone=True)` | YES | `NULL` | When summary was last generated |

- Summary is populated async by Celery task when dossier is submitted.
- Aggregates summaries from all constituent DossierDocument submissions.

#### `scanned_page` — Add Search Vector

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `search_vector` | `TSVector` | YES | Generated | PostgreSQL full-text search vector, auto-computed from `ocr_corrected_text` (preferred) or `ocr_raw_text` |

- Generated column: `to_tsvector('simple', COALESCE(immutable_unaccent(ocr_corrected_text), '') || ' ' || COALESCE(immutable_unaccent(ocr_raw_text), ''))`
- GIN index: `idx_scanned_page_search`
- GiST trigram index for fuzzy matching: `idx_scanned_page_trgm`

### New Database Extensions

| Extension | Purpose |
|-----------|---------|
| `unaccent` | Normalize Vietnamese diacritics (Nguyễn → Nguyen) for search |
| `pg_trgm` | Trigram similarity for fuzzy matching / typo tolerance |

### New Database Functions

| Function | Purpose |
|----------|---------|
| `immutable_unaccent(text)` | Immutable wrapper around `unaccent()` — required for use in generated columns and index expressions |

---

## Entity Relationships (Search Context)

```
SearchResult (union type, not a table)
├── SubmissionResult
│   ├── submission.id, status, submitted_at, ai_summary
│   ├── citizen.full_name, citizen.id_number
│   ├── document_type.name, document_type.code
│   └── scanned_page[].search_vector (match source)
│
└── DossierResult
    ├── dossier.id, status, submitted_at, reference_number, ai_summary
    ├── citizen.full_name, citizen.id_number
    ├── case_type.name, case_type.code
    └── dossier_document[].scanned_page[].search_vector (match source)
```

---

## Entity Extraction Storage

Entities extracted by AI are stored in the existing `template_data` JSONB column on `submission` under the `_entities` key:

```json
{
  "_classification_alternatives": [...],
  "_entities": {
    "persons": ["Nguyễn Văn An", "Trần Thị Bình"],
    "id_numbers": ["012345678901"],
    "dates": ["15/03/1990", "01/01/2026"],
    "addresses": ["123 Đường ABC, Quận 1, TP.HCM"],
    "amounts": ["1.000.000 VNĐ"]
  },
  "ho_ten": "Nguyễn Văn An",
  ...
}
```

- No schema change needed — JSONB is flexible.
- Entity values are indexed via the `search_vector` on `scanned_page` (derived from OCR text that contains these entities).
- For direct entity search (e.g., by CCCD number), the search service also queries `citizen.id_number` directly.

---

## Indexes (New)

| Index Name | Table | Column(s) | Type | Purpose |
|------------|-------|-----------|------|---------|
| `idx_scanned_page_search` | `scanned_page` | `search_vector` | GIN | Full-text search ranking |
| `idx_scanned_page_trgm` | `scanned_page` | `immutable_unaccent(COALESCE(ocr_corrected_text, ocr_raw_text, ''))` | GiST (gist_trgm_ops) | Fuzzy trigram matching |
| `idx_submission_ai_summary` | `submission` | `ai_summary_generated_at` | BTREE | Filter submissions needing summary backfill |
| `idx_citizen_fullname_trgm` | `citizen` | `immutable_unaccent(full_name)` | GiST (gist_trgm_ops) | Fuzzy citizen name search |
| `idx_citizen_id_number` | `citizen` | `id_number` | BTREE | Exact ID number lookup (may already exist) |
| `idx_dossier_reference` | `dossier` | `reference_number` | BTREE | Exact reference number lookup (already exists — unique constraint) |

---

## Migration: `0004_search_and_summarization.py`

**Operations** (in order):
1. `CREATE EXTENSION IF NOT EXISTS unaccent`
2. `CREATE EXTENSION IF NOT EXISTS pg_trgm`
3. `CREATE FUNCTION immutable_unaccent(text)`
4. `ADD COLUMN submission.ai_summary Text`
5. `ADD COLUMN submission.ai_summary_generated_at DateTime`
6. `ADD COLUMN dossier.ai_summary Text`
7. `ADD COLUMN dossier.ai_summary_generated_at DateTime`
8. `ADD COLUMN scanned_page.search_vector TSVector (GENERATED)`
9. `CREATE INDEX idx_scanned_page_search (GIN)`
10. `CREATE INDEX idx_scanned_page_trgm (GiST)`
11. `CREATE INDEX idx_submission_ai_summary (BTREE)`
12. `CREATE INDEX idx_citizen_fullname_trgm (GiST)`

**Downgrade**: Drop indexes, drop columns, drop function, drop extensions (in reverse order).

**Note**: Step 8 (generated column) will compute `search_vector` for all existing `scanned_page` rows automatically. This may take a few minutes on large datasets.

---

## State Transitions

### AI Summary Lifecycle (Submission)

```
[No summary] ──(classification completes)──> [Generating] ──(AI success)──> [Generated]
                                                         ──(AI failure 3x)──> [No summary, error logged]

[Generated] ──(OCR text corrected)──> [Generating] ──(AI success)──> [Generated (updated)]
```

- States are implicit (no status column): `ai_summary IS NULL` = no summary, `ai_summary IS NOT NULL` = generated.
- `ai_summary_generated_at` tracks freshness.

### AI Summary Lifecycle (Dossier)

```
[No summary] ──(dossier submitted)──> [Generating] ──(AI success)──> [Generated]
                                                    ──(AI failure 3x)──> [No summary, error logged]
```
