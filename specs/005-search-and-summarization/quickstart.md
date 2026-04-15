# Quickstart: Search & AI Summarization

**Feature**: 005-search-and-summarization
**Date**: 2026-04-15

---

## Prerequisites

- Backend running (`uvicorn src.main:app --reload --port 8000`)
- PostgreSQL 16 with superuser access (needed for `CREATE EXTENSION`)
- Celery worker running (`celery -A src.workers worker -l info`)
- Seed data populated (`python -m src.seeds.seed_data`)
- `DASHSCOPE_API_KEY` set in environment

---

## Setup Steps

### 1. Apply Migration

```bash
cd backend
alembic upgrade head
```

This will:
- Install `unaccent` and `pg_trgm` PostgreSQL extensions
- Add `ai_summary` + `ai_summary_generated_at` to `submission` and `dossier`
- Add `search_vector` (generated tsvector column) to `scanned_page`
- Create GIN + GiST indexes for full-text and fuzzy search

> **Note**: The `search_vector` generated column backfills automatically for existing rows. May take a few minutes on large datasets.

### 2. Verify Extensions

```sql
SELECT extname FROM pg_extension WHERE extname IN ('unaccent', 'pg_trgm');
-- Expected: 2 rows
```

### 3. Backfill AI Summaries (Optional)

For existing classified submissions that don't have summaries yet:

```bash
cd backend
python -m src.workers.backfill_summaries
```

This queues Celery tasks at 5/second. Monitor progress in Celery logs.

---

## Testing the Feature

### Search

```bash
# Search for a citizen name
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/staff/search?q=Nguyễn+Văn+An"

# Search with filters
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/staff/search?q=khai+sinh&status=completed&date_from=2026-04-01"

# Search by CCCD number
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/staff/search?q=012345678901"

# Search by reference number
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/staff/search?q=HS-20260415"
```

### AI Summary

Summaries are generated automatically after classification. To trigger manually:

```bash
# Check a submission's summary
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/staff/submissions/{id}/classification"
# Look for: ai_summary, entities fields
```

### SLA Analytics

```bash
# Get department analytics (requires manager/admin role)
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/staff/analytics/sla?date_from=2026-03-01"
```

### Queue Preview

```bash
# Check department queue — now includes summary_preview
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/staff/departments/{dept_id}/queue"
# Look for: summary_preview field on each item
```

---

## Running Tests

```bash
cd backend

# All tests
pytest tests/ -v

# Search-specific tests
pytest tests/unit/test_search_service.py -v
pytest tests/unit/test_summarization_service.py -v
pytest tests/unit/test_analytics_service.py -v
pytest tests/integration/test_search_api.py -v
pytest tests/integration/test_analytics_api.py -v
pytest tests/contract/test_search_contract.py -v

# Lint
ruff check src/
```

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/src/api/staff/search.py` | Search API endpoint |
| `backend/src/api/staff/analytics.py` | SLA analytics API endpoint |
| `backend/src/services/search_service.py` | Full-text search with clearance filtering |
| `backend/src/services/summarization_service.py` | AI summary + entity extraction logic |
| `backend/src/services/analytics_service.py` | SLA aggregate queries |
| `backend/src/services/ai_client.py` | New: `summarize_document()`, `extract_entities()` |
| `backend/src/workers/summarization_worker.py` | Celery task for async summarization |
| `backend/src/workers/backfill_summaries.py` | One-time backfill command |
| `backend/alembic/versions/0004_search_and_summarization.py` | Migration |
