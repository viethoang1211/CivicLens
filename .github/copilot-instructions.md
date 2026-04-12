# public_sector Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-11

## Active Technologies
- Python 3.12 (backend), Dart/Flutter 3.24+ (staff & citizen apps) + FastAPI, SQLAlchemy 2 (async), Alembic, Celery, dashscope (Alibaba Cloud AI), OSS client (002-case-based-submission)
- PostgreSQL with JSONB columns; Alibaba Cloud OSS for scanned images (002-case-based-submission)

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
- 002-case-based-submission: Added Python 3.12 (backend), Dart/Flutter 3.24+ (staff & citizen apps) + FastAPI, SQLAlchemy 2 (async), Alembic, Celery, dashscope (Alibaba Cloud AI), OSS client

- 001-ai-document-processing: Added Python 3.12 (backend), Dart/Flutter 3.24+ (mobile apps) + FastAPI, Celery, SQLAlchemy, Alembic, Alibaba Cloud SDK (dashscope), Flutter

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
