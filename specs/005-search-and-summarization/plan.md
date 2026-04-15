# Implementation Plan: Search & AI Summarization

**Branch**: `005-search-and-summarization` | **Date**: 2026-04-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-search-and-summarization/spec.md`

## Summary

Add full-text search across all OCR text, template data, and citizen information (the missing "Centralized Indexing" capability) and AI-powered document/dossier summarization with entity extraction (the partial "AI Summarization" capability). Uses PostgreSQL `tsvector`/GIN indexes with `unaccent` + `pg_trgm` for Vietnamese-aware search, and chains a new Celery summarization task after classification using the existing `qwen3.5-flash` model. Includes a P3 SLA analytics endpoint for department management.

## Technical Context

**Language/Version**: Python 3.12 (backend), Dart/Flutter 3.24+ (staff_app, shared_dart)
**Primary Dependencies**: FastAPI, SQLAlchemy 2 (async), Alembic, Celery, dashscope (Alibaba Cloud AI), Dio (Flutter HTTP)
**Storage**: PostgreSQL 16 (JSONB, tsvector + GIN, pg_trgm + unaccent extensions)
**Testing**: pytest (backend unit/integration/contract), flutter test (widget + unit)
**Target Platform**: Android (staff app), Linux server (backend)
**Project Type**: Full-stack mobile + API
**Performance Goals**: Search p95 < 3s, summarization < 15s per document (async)
**Constraints**: Online-first, < 100K documents (PostgreSQL FTS sufficient), qwen3.5-flash context window limit (~50K chars)
**Scale/Scope**: 7 departments, 15 document types, 6 case types, < 100K documents

## Constitution Check

*GATE: Constitution is unpopulated (template placeholders only). No violations to check. Proceeding.*

## Project Structure

### Documentation (this feature)

```text
specs/005-search-and-summarization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── staff-api.md     # New search + analytics endpoints
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── alembic/versions/
│   └── 0004_search_and_summarization.py    # NEW: ai_summary columns, tsvector, GIN indexes, extensions
├── src/
│   ├── api/staff/
│   │   ├── search.py                       # NEW: GET /v1/staff/search
│   │   ├── analytics.py                    # NEW: GET /v1/staff/analytics/sla
│   │   └── departments.py                  # MODIFY: add summary_preview to queue response
│   ├── models/
│   │   ├── submission.py                   # MODIFY: add ai_summary, ai_summary_generated_at
│   │   ├── dossier.py                      # MODIFY: add ai_summary, ai_summary_generated_at
│   │   └── scanned_page.py                 # MODIFY: add search_vector (tsvector)
│   ├── services/
│   │   ├── search_service.py               # NEW: full-text search with clearance filtering
│   │   ├── summarization_service.py        # NEW: AI summary + entity extraction logic
│   │   ├── analytics_service.py            # NEW: SLA aggregate queries
│   │   └── ai_client.py                    # MODIFY: add summarize_document(), extract_entities()
│   └── workers/
│       ├── summarization_worker.py         # NEW: Celery task for summarization + entity extraction
│       └── classification_worker.py        # MODIFY: chain to summarization after classification
└── tests/
    ├── unit/
    │   ├── test_search_service.py          # NEW
    │   ├── test_summarization_service.py   # NEW
    │   └── test_analytics_service.py       # NEW
    ├── integration/
    │   ├── test_search_api.py              # NEW
    │   └── test_analytics_api.py           # NEW
    └── contract/
        └── test_search_contract.py         # NEW

staff_app/
├── lib/features/
│   ├── search/                             # NEW: search screen + results
│   └── queue/                              # MODIFY: add summary_preview display
└── test/

shared_dart/
├── lib/src/
│   ├── models/search_result.dart           # NEW: SearchResult DTO
│   └── api/search_api_client.dart          # NEW: search API client
└── test/
```

**Structure Decision**: Existing mobile + API structure. Backend-heavy feature — 3 new services, 1 new worker, 2 new API routers. Flutter changes limited to staff_app search screen and queue preview enhancement.
