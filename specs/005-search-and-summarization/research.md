# Research: Search & AI Summarization

**Feature**: 005-search-and-summarization
**Date**: 2026-04-15
**Purpose**: Resolve technical design decisions for full-text search, AI summarization, entity extraction, and SLA analytics.

---

## R-001: PostgreSQL Full-Text Search Strategy for Vietnamese

**Question**: How should full-text search be implemented for Vietnamese text using PostgreSQL?

**Decision**: Use `simple` text search configuration + `unaccent` extension + `pg_trgm` trigram index. Create a computed `tsvector` column on `ScannedPage` and a search helper view/function.

**Rationale**:
- PostgreSQL has no built-in Vietnamese stemmer. The `simple` config tokenizes by whitespace/punctuation without stemming — acceptable for Vietnamese (an isolating language with minimal inflection).
- `unaccent` normalizes diacritics so searching "Nguyen" matches "Nguyễn". This is critical for Vietnamese where users may omit diacritics in search queries.
- `pg_trgm` provides trigram-based similarity matching for fuzzy search (typo-tolerant), complementing exact `tsvector` matching.
- GIN index on `tsvector` column for ranked full-text search; GiST index on `pg_trgm` for fuzzy `%LIKE%` fallback.
- At < 100K documents, PostgreSQL FTS performs well without external infrastructure.

**Implementation**:
```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create immutable unaccent wrapper (required for index expressions)
CREATE OR REPLACE FUNCTION immutable_unaccent(text) RETURNS text AS $$
  SELECT unaccent($1);
$$ LANGUAGE sql IMMUTABLE STRICT;

-- Add tsvector column to scanned_page
ALTER TABLE scanned_page ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (
    to_tsvector('simple', COALESCE(immutable_unaccent(ocr_corrected_text), '') || ' ' || COALESCE(immutable_unaccent(ocr_raw_text), ''))
  ) STORED;

-- GIN index for full-text search
CREATE INDEX idx_scanned_page_search ON scanned_page USING GIN (search_vector);

-- Trigram index for fuzzy matching
CREATE INDEX idx_scanned_page_trgm ON scanned_page USING GiST (
  immutable_unaccent(COALESCE(ocr_corrected_text, ocr_raw_text, '')) gist_trgm_ops
);
```

**Alternatives considered**:
- **Elasticsearch**: Full-featured Vietnamese analyzer (ICU plugin), but adds infrastructure complexity and ops burden for demo scale. Rejected — overkill.
- **Vietnamese word segmentation (VnCoreNLP/underthesea)**: Pre-segment text before indexing. Adds Python dependency and preprocessing step. Rejected — `simple` tokenizer + trigram is sufficient for exact/fuzzy match (no need for semantic word boundaries in search).
- **ParadeDB (pg_search)**: PostgreSQL extension with BM25 ranking. More advanced but non-standard for Alibaba Cloud RDS. Rejected — portability risk.

---

## R-002: Summarization Prompt Design

**Question**: What prompt structure should be used for AI summarization via `qwen3.5-flash`?

**Decision**: Single system+user prompt generating a Vietnamese summary in structured JSON format. Same approach for submission-level and dossier-level summaries.

**Rationale**:
- `qwen3.5-flash` already handles Vietnamese text well (proven in classification task).
- Structured JSON output (`{"summary": "...", "key_points": [...]}`) is parseable and consistent.
- Submission summary: extract document type, subject name, key facts from OCR text.
- Dossier summary: aggregate purpose from all document summaries + case type context.

**Prompt template (submission)**:
```
System: Bạn là trợ lý hành chính chuyên tóm tắt tài liệu hành chính Việt Nam.
Trả lời bằng JSON hợp lệ, KHÔNG thêm markdown.

User: Tóm tắt tài liệu sau trong 2-3 câu ngắn gọn bằng tiếng Việt.
Nêu rõ: (1) loại tài liệu, (2) tên người liên quan, (3) thông tin chính.

Loại tài liệu: {document_type_name}
Nội dung OCR:
{ocr_text[:8000]}

Trả về JSON:
{
  "summary": "Tóm tắt 2-3 câu",
  "key_points": ["điểm chính 1", "điểm chính 2"]
}
```

**Prompt template (dossier)**:
```
System: Bạn là trợ lý hành chính chuyên tóm tắt hồ sơ hành chính Việt Nam.
Trả lời bằng JSON hợp lệ, KHÔNG thêm markdown.

User: Tóm tắt hồ sơ sau trong 2-3 câu ngắn gọn bằng tiếng Việt.
Nêu rõ: (1) mục đích hồ sơ, (2) danh sách tài liệu, (3) thông tin chính.

Loại hồ sơ: {case_type_name}
Mã tham chiếu: {reference_number}
Tài liệu đính kèm:
{document_summaries}

Trả về JSON:
{
  "summary": "Tóm tắt 2-3 câu",
  "key_points": ["điểm chính 1", "điểm chính 2"]
}
```

**Alternatives considered**:
- **Free-form text summary (no JSON)**: Simpler but unpredictable format. Harder to extract preview substring. Rejected.
- **Two-step prompt (summarize + extract separately)**: More accurate per-step but doubles API calls. Rejected — single combined prompt is efficient and qwen3.5-flash handles complex instructions well.

---

## R-003: Entity Extraction Approach

**Question**: Should entity extraction use a separate NER model or prompt-based extraction via the same LLM?

**Decision**: Prompt-based extraction via `qwen3.5-flash` in the same API call as summarization.

**Rationale**:
- Combining summarization + entity extraction in one prompt reduces API calls by 50%.
- Vietnamese NER models (e.g., PhoBERT NER) require additional Python dependencies and a separate model endpoint. Overkill for structured entity types we target: person names, ID numbers (regex-matchable), dates, addresses, amounts.
- ID numbers (CCCD: 12 digits, CMND: 9 digits) can be validated with regex post-extraction.
- The prompt asks the model to return entities alongside the summary in a single JSON response.

**Combined prompt (appended to R-002 templates)**:
```
Ngoài tóm tắt, trích xuất các thực thể chính:

Trả về JSON:
{
  "summary": "...",
  "key_points": [...],
  "entities": {
    "persons": ["Tên người 1"],
    "id_numbers": ["012345678901"],
    "dates": ["15/03/1990"],
    "addresses": ["123 Đường ABC, Quận 1, TP.HCM"],
    "amounts": ["1.000.000 VNĐ"]
  }
}
```

**Alternatives considered**:
- **Separate NER model (PhoBERT, underthesea)**: Higher accuracy for edge cases but adds dependencies, GPU requirements, and operational complexity. Rejected — prompt-based is good enough.
- **Regex-only extraction**: Works for ID numbers and dates but fails for names and addresses. Rejected — partial solution only.
- **Separate API call for entities**: Cleaner separation but doubles cost. Rejected.

---

## R-004: Summarization Task Chaining

**Question**: How should the summarization Celery task integrate into the existing OCR → Classification pipeline?

**Decision**: Chain `summarization.generate` after `classification.run` completes successfully. Dossier summarization triggers separately on dossier submit.

**Rationale**:
- Current chain: `ocr.run_pipeline` → `classification.run` (via `delay()`)
- Extended chain: `ocr.run_pipeline` → `classification.run` → `summarization.generate`
- Summarization needs the classified document type name for context — so it must run after classification.
- Dossier-level summary triggers when all documents are classified (on dossier submit), not per-document.
- Retry policy: 3 retries with exponential backoff (10s, 30s, 90s). On final failure: `ai_summary = null`, log error, do NOT block workflow.

**Implementation**:
- `classification_worker.py`: After successful classification, call `generate_summary.delay(submission_id)`
- `summarization_worker.py`: New task `summarization.generate(submission_id)` — loads OCR text + document type name, calls AI, stores summary + entities
- `dossier_service.py`: On dossier submit, call `summarize_dossier.delay(dossier_id)` — aggregates document summaries

**Alternatives considered**:
- **Single combined classification + summarization task**: Simpler chain but mixed responsibilities. If summarization fails, classification result is lost. Rejected — separation of concerns.
- **Celery chord/group**: Over-engineering for a sequential dependency. Rejected.
- **Synchronous summarization in API handler**: Blocks response for 5-15 seconds. Rejected — async is critical.

---

## R-005: Search Query Architecture

**Question**: How should the search query combine full-text and structured filters while enforcing clearance?

**Decision**: Two-phase query — full-text match (tsvector) → join to parent entities → apply clearance + structured filters.

**Rationale**:
- Primary search targets: `scanned_page.search_vector` (OCR text), `citizen.full_name` + `citizen.id_number`, `dossier.reference_number`.
- Search hits on `scanned_page` need JOIN to `submission` (via `submission_id`) or `dossier_document` (via `dossier_document_id`) → `dossier`.
- Clearance filter applies on `submission.security_classification` and `dossier.security_classification`.
- Structured filters (status, date range, department) apply on `submission`/`dossier` columns.
- Result type is a union: `SearchResult` with discriminated type (`submission` or `dossier`).

**Query flow**:
```sql
-- Phase 1: Full-text search on scanned_page
WITH ocr_hits AS (
  SELECT sp.submission_id, sp.dossier_document_id,
         ts_rank(sp.search_vector, query) AS rank
  FROM scanned_page sp,
       plainto_tsquery('simple', immutable_unaccent(:query)) query
  WHERE sp.search_vector @@ query
),
-- Phase 2: Join to submission/dossier + clearance filter
submission_results AS (
  SELECT s.id, s.status, s.submitted_at, MAX(oh.rank) AS rank
  FROM ocr_hits oh
  JOIN submission s ON s.id = oh.submission_id
  WHERE s.security_classification <= :clearance_level
    AND oh.submission_id IS NOT NULL
  GROUP BY s.id
),
dossier_results AS (
  SELECT d.id, d.status, d.submitted_at, MAX(oh.rank) AS rank
  FROM ocr_hits oh
  JOIN dossier_document dd ON dd.id = oh.dossier_document_id
  JOIN dossier d ON d.id = dd.dossier_id
  WHERE d.security_classification <= :clearance_level
    AND oh.dossier_document_id IS NOT NULL
  GROUP BY d.id
)
-- Phase 3: Union + sort + paginate
SELECT * FROM submission_results
UNION ALL
SELECT * FROM dossier_results
ORDER BY rank DESC
LIMIT :limit OFFSET :offset;
```

**Alternatives considered**:
- **Materialized search view**: Pre-computed join of scanned_page + submission/dossier. Faster queries but stale data (needs refresh). Rejected — real-time accuracy preferred.
- **Separate search per entity**: Three endpoints for submissions, dossiers, pages. Rejected — contradicts "centralized indexing" requirement.
- **Application-level UNION**: Two separate queries merged in Python. Rejected — less efficient, harder to paginate correctly.

---

## R-006: SLA Analytics Query Design

**Question**: How should SLA analytics be computed — ad-hoc query or pre-aggregated materialized view?

**Decision**: Ad-hoc aggregate query with date-range parameters.

**Rationale**:
- At demo scale (< 10K workflow steps), aggregate queries complete in milliseconds.
- No need for background aggregation jobs or materialized views.
- The query groups `workflow_step` by `department_id` and computes: avg processing time, completion count, delay count, pending count.
- A step is "delayed" if `completed_at > expected_complete_by` OR (still pending AND `now() > expected_complete_by`).

**Alternatives considered**:
- **Celery Beat periodic aggregation into analytics table**: Needed at scale but premature for demo. Rejected.
- **Database materialized view with pg_cron refresh**: Adds infrastructure dependency. Rejected.

---

## R-007: Backfill Strategy for Existing Data

**Question**: How should existing classified submissions get AI summaries after the feature ships?

**Decision**: One-time management command (`python -m src.workers.backfill_summaries`) that queues individual Celery tasks with rate limiting.

**Rationale**:
- Existing data may have hundreds of classified submissions without summaries.
- Running summarization synchronously would be too slow; queuing Celery tasks re-uses the existing async pipeline.
- Rate-limit: 5 tasks/second to avoid overwhelming dashscope API quota.
- The command is idempotent: skips submissions where `ai_summary IS NOT NULL`.
- Does NOT run automatically during migration — admin triggers manually when ready.

**Alternatives considered**:
- **Alembic data migration**: Automatically runs during `alembic upgrade head`. Risk of timeout on large datasets, blocks deployment. Rejected.
- **Background job on first search**: Lazy summmarization on access. Adds latency to first search and complicates search result display. Rejected.
