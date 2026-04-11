# Implementation Plan: AI-Powered Public Sector Document Processing

**Branch**: `001-ai-document-processing` | **Date**: 2026-04-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ai-document-processing/spec.md`

## Summary

Build an AI-powered document processing system for Vietnamese public sector organizations. Staff use a mobile app to scan physical documents; the system performs OCR (Qwen VL OCR) on handwritten Vietnamese text, classifies documents into types (Qwen3.5-Flash with prompt-based classification), auto-fills standardized templates, and routes submissions through sequential department workflows. Citizens track processing status in real-time via a separate mobile app with visual workflow nodes. All on Alibaba Cloud infrastructure.

## Technical Context

**Language/Version**: Python 3.12 (backend), Dart/Flutter 3.24+ (mobile apps)
**Primary Dependencies**: FastAPI, Celery, SQLAlchemy, Alembic, Alibaba Cloud SDK (dashscope), Flutter
**Storage**: PostgreSQL 16 (ApsaraDB RDS), Alibaba Cloud OSS (documents), Redis/Tair (cache)
**Testing**: pytest (backend), flutter_test (mobile)
**Target Platform**: Linux server (Alibaba Cloud ECS), iOS 15+ / Android 8+ (mobile apps)
**Project Type**: Mobile apps + API backend + AI processing pipeline
**Performance Goals**: OCR + classification < 30s per document, API responses < 500ms p95, push notifications < 60s
**Constraints**: Offline-capable staff app, multi-level security classification (0-3), 99.5% uptime, 5-year minimum data retention
**Scale/Scope**: Multiple government departments, district/commune level deployment, 2 mobile apps, ~20 screens total

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No project constitution has been defined (template is still blank). Gate passes by default — no constraints to violate. Recommend defining a constitution before implementation begins.

**Post-Phase 1 re-check**: Design is consistent with no constitution violations (no constitution defined).

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-document-processing/
├── plan.md              # This file
├── research.md          # Phase 0: Technology decisions
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Dev environment setup
├── contracts/           # Phase 1: API contracts
│   ├── staff-api.md     # Staff app backend API
│   └── citizen-api.md   # Citizen app backend API
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── staff/           # Staff app API routes
│   │   └── citizen/         # Citizen app API routes
│   ├── models/              # SQLAlchemy ORM models
│   ├── services/            # Business logic (OCR, classifier, router, notifier)
│   ├── workers/             # Celery async task workers
│   ├── security/            # ABAC middleware, RLS policies
│   └── config.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── alembic/                 # Database migrations
├── pyproject.toml
└── Dockerfile

staff_app/                   # Flutter staff application
├── lib/
│   ├── features/
│   │   ├── scan/            # Camera capture & offline queue
│   │   ├── classify/        # Classification review UI
│   │   ├── review/          # Department review queue
│   │   └── auth/            # Staff authentication
│   └── core/
│       ├── api/             # API client
│       ├── sync/            # Offline sync engine
│       └── storage/         # Local encrypted storage
└── pubspec.yaml

citizen_app/                 # Flutter citizen application
├── lib/
│   ├── features/
│   │   ├── submissions/     # Submission list & detail
│   │   ├── workflow/        # Visual workflow tracker
│   │   ├── notifications/
│   │   └── auth/            # VNeID authentication
│   └── core/
│       └── api/             # API client
└── pubspec.yaml

shared_dart/                 # Shared Dart package (DTOs, API models)
├── lib/
└── pubspec.yaml

infra/
├── docker-compose.yml       # Local dev (PostgreSQL, Redis, RocketMQ)
└── terraform/               # Alibaba Cloud provisioning
```

**Structure Decision**: Mobile + API pattern with two separate Flutter apps (staff and citizen) sharing a common Dart package, and a Python backend with async AI workers. Four top-level projects justified by: (1) backend and mobile are different runtimes, (2) two mobile apps serve fundamentally different user personas, (3) shared_dart avoids DTO duplication.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 4 top-level projects (backend, staff_app, citizen_app, shared_dart) | Two distinct user personas (staff vs citizen) with different security models and features | Single app with role switching increases attack surface and UX complexity |
| Celery workers separate from API | OCR/classification takes 5-30s, cannot block API responses | Sync processing would cause request timeouts and poor UX |
