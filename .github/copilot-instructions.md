# public_sector Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-16

## Active Technologies
- Python 3.12 (backend), Dart/Flutter 3.24+ (staff & citizen apps) + FastAPI, SQLAlchemy 2 (async), Alembic, Celery, dashscope (Alibaba Cloud AI), OSS client (002-case-based-submission)
- PostgreSQL with JSONB columns; Alibaba Cloud OSS for scanned images (002-case-based-submission)
- Python 3.12 (backend), Dart/Flutter 3.24+ (staff_app, shared_dart) + FastAPI, SQLAlchemy 2 (async), Alembic, Celery, dashscope (Alibaba Cloud AI), Dio (Flutter HTTP) (003-guided-document-capture)
- PostgreSQL 16 (JSONB), Alibaba Cloud OSS / local filesystem (003-guided-document-capture)
- Python 3.12 (backend) + FastAPI, SQLAlchemy 2 (async), Celery, dashscope (Alibaba Cloud AI) (004-business-flow-review)
- PostgreSQL 16 (JSONB), local filesystem (004-business-flow-review)
- PostgreSQL 16 (JSONB, tsvector + GIN, pg_trgm + unaccent extensions) (005-search-and-summarization)
- Python 3.12 (backend), Dart/Flutter 3.24+ (citizen_app, shared_dart) + FastAPI, SQLAlchemy 2 (async), Alembic, Celery, Dio (Flutter HTTP) (006-citizen-app-completion)
- PostgreSQL 16 (JSONB, UUID PKs), Alibaba Cloud OSS (006-citizen-app-completion)

- Python 3.12 (backend), Dart/Flutter 3.24+ (mobile apps) + FastAPI, Celery, SQLAlchemy, Alembic, Alibaba Cloud SDK (dashscope), Flutter (001-ai-document-processing)

## Project Structure

```text
src/
tests/
```

## Commands

cd src && pytest && ruff check .

## Code Style

Python 3.12 (backend), Dart/Flutter 3.24+ (mobile apps): Follow standard conventions

## Recent Changes
- 006-citizen-app-completion: Added Python 3.12 (backend), Dart/Flutter 3.24+ (citizen_app, shared_dart) + FastAPI, SQLAlchemy 2 (async), Alembic, Celery, Dio (Flutter HTTP)
- 005-search-and-summarization: Added Python 3.12 (backend), Dart/Flutter 3.24+ (staff_app, shared_dart) + FastAPI, SQLAlchemy 2 (async), Alembic, Celery, dashscope (Alibaba Cloud AI), Dio (Flutter HTTP)
- 004-business-flow-review: Added Python 3.12 (backend) + FastAPI, SQLAlchemy 2 (async), Celery, dashscope (Alibaba Cloud AI)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
