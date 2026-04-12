# Architecture

## High-Level Overview

The system consists of four deployable components connected through a shared PostgreSQL database, Redis cache, and RocketMQ message broker.

```
┌─────────────────────┐     ┌─────────────────────┐
│    Staff App         │     │   Citizen App        │
│  (Flutter 3.24+)    │     │  (Flutter 3.24+)     │
│                     │     │                     │
│  - Camera scanning  │     │  - VNeID login       │
│  - OCR review       │     │  - Status tracking   │
│  - Classification   │     │  - Notifications     │
│  - Workflow review   │     │                     │
│  - Offline queue    │     │                     │
└────────┬────────────┘     └────────┬────────────┘
         │ HTTPS                      │ HTTPS
         ▼                            ▼
┌──────────────────────────────────────────────────┐
│                  Backend API                      │
│              (FastAPI + Uvicorn)                  │
│                                                  │
│   /v1/staff/*          /v1/citizen/*              │
│   - Auth (JWT)         - Auth (VNeID → JWT)      │
│   - Submissions        - Submissions (read-only) │
│   - Classification     - Notifications           │
│   - Routing                                      │
│   - Review                                       │
│   - Admin CRUD                                   │
└──────┬──────────┬──────────┬──────────┬──────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐
│PostgreSQL│ │ Redis  │ │RocketMQ│ │ Alibaba Cloud│
│   16     │ │   7    │ │  5.3   │ │              │
│          │ │        │ │        │ │ - OSS        │
│ - Models │ │ - Cache│ │ - Task │ │ - Model      │
│ - RLS    │ │ - Rate │ │   Queue│ │   Studio     │
│ - Audit  │ │   Limit│ │        │ │ - EMAS Push  │
│          │ │        │ │        │ │ - SLS Logs   │
└──────────┘ └────────┘ └────────┘ └──────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Celery Workers   │
                    │                  │
                    │  - OCR pipeline  │
                    │  - Classification│
                    │  - Template fill │
                    │  - Slot validate │
                    └──────────────────┘
```

## Component Architecture

### Backend API (`backend/`)

A FastAPI application serving both staff and citizen endpoints behind a single deployment. The API is stateless — all state lives in PostgreSQL, Redis, or OSS.

```
backend/
├── src/
│   ├── main.py              # FastAPI app factory, router registration
│   ├── config.py            # Pydantic Settings (env-driven config)
│   ├── dependencies.py      # DB session factory, clearance-aware sessions
│   ├── api/
│   │   ├── staff/           # Staff-facing endpoints
│   │   │   ├── auth.py            # POST /auth/login → JWT
│   │   │   ├── submissions.py     # Scan, upload pages, OCR review
│   │   │   ├── dossier.py         # Case-based dossier CRUD, upload, submit
│   │   │   ├── classification.py  # AI classification + confirm
│   │   │   ├── routing.py         # Trigger workflow creation
│   │   │   ├── departments.py     # Department work queues
│   │   │   ├── workflow_steps.py  # Review, approve, consult
│   │   │   ├── admin_document_types.py   # CRUD doc types
│   │   │   ├── admin_routing_rules.py    # CRUD routing rules
│   │   │   └── admin_case_types.py       # CRUD case types + requirement groups
│   │   └── citizen/         # Citizen-facing endpoints
│   │       ├── auth.py            # VNeID code exchange → JWT
│   │       ├── submissions.py     # Read-only status + workflow view
│   │       ├── dossier.py         # Dossier tracking + reference lookup
│   │       └── notifications.py   # Push notification history
│   ├── models/              # SQLAlchemy ORM models (17 entities)
│   ├── services/            # Business logic layer
│   │   ├── ai_client.py          # Qwen VL OCR + classification + slot validation
│   │   ├── oss_client.py         # Alibaba OSS operations
│   │   ├── dossier_service.py    # Dossier completeness, reference numbers, workflow
│   │   ├── routing_service.py    # Workflow creation from rules
│   │   ├── workflow_service.py   # Step advancement + retention
│   │   ├── review_service.py     # Review validation + processing
│   │   ├── notification_service.py  # Push notification triggers
│   │   ├── audit_service.py      # Immutable audit logging + SLS
│   │   ├── quality_service.py    # Image quality assessment
│   │   ├── template_service.py   # Template schema validation
│   │   └── submission_service.py # Duplicate detection
│   ├── security/
│   │   ├── auth.py               # JWT encode/decode, identity deps
│   │   ├── abac.py               # Clearance-based access control
│   │   └── audit_interceptor.py  # Automatic API audit logging
│   └── workers/
│       ├── celery_app.py         # Celery configuration
│       ├── ocr_worker.py         # Async OCR pipeline
│       └── classification_worker.py  # Async classification
├── alembic/                 # Database migrations
├── Dockerfile               # Production container
└── pyproject.toml           # Dependencies + tooling config
```

### Staff Mobile App (`staff_app/`)

Flutter app for government staff to scan documents, review OCR results, confirm classifications, and process workflow review queues.

Key capabilities:
- **Camera scanning** with multi-page support and image quality assessment
- **Case-based dossier workflow** — select a case type, see required document checklist, upload documents per slot
- **Offline-first** — scans are queued locally and synced via background `workmanager` tasks
- **Clearance enforcement** — UI filters documents above staff clearance level
- **Review workflow** — approve/reject/request-info with annotations
- **AI badge display** — shows AI slot validation results with override capability

### Citizen Mobile App (`citizen_app/`)

Flutter app for citizens to track their submissions and receive push notifications.

Key capabilities:
- **VNeID authentication** — national digital identity integration
- **Visual workflow tracker** — sequential node display showing completed/active/pending steps
- **Reference number lookup** — citizens can check dossier status with HS-YYYYMMDD-NNNNN reference number without logging in
- **Push notifications** — real-time updates via Alibaba Cloud EMAS when dossiers advance

### Shared Dart Package (`shared_dart/`)

Contains DTOs, API client base class, and feature-specific API clients shared between both Flutter apps. Avoids duplicating model definitions and network logic.

## Technology Decisions

### Why Two Separate Mobile Apps?

A single app with role-switching was considered and rejected:
- **Attack surface** — citizen users would have staff API client code in their binary
- **UX complexity** — staff need camera/scanning/offline features; citizens need simple read-only tracking
- **Deployment** — different release cycles and distribution channels (staff via MDM, citizens via app stores)

The `shared_dart` package extracts common code (DTOs, API clients) to avoid duplication.

### Why FastAPI + Celery?

- FastAPI provides async-first HTTP handling with automatic OpenAPI docs
- OCR and classification are **long-running AI tasks** (5–15 seconds) — they cannot block API request threads
- Celery with RocketMQ provides reliable async task execution with retry semantics
- RocketMQ is Alibaba Cloud-native, avoids introducing RabbitMQ/Kafka

### Why PostgreSQL Row-Level Security?

Documents have four security classification levels (0–3). Rather than relying solely on application-level checks:
- RLS policies enforce `app.clearance_level >= security_classification` at the database level
- Even a compromised API endpoint cannot leak classified documents past the DB layer
- This satisfies government compliance requirements for defense-in-depth

### Why Alibaba Cloud?

All infrastructure is on Alibaba Cloud for **data sovereignty** — Vietnamese government data must remain within approved cloud providers. Specific choices:
- **Model Studio** — Qwen models with Vietnamese language support, no self-hosted GPU
- **OSS** — Document image storage with presigned URLs
- **EMAS** — Push notification delivery to citizen devices
- **SLS** — Long-term audit log retention for compliance
- **RDS** — Managed PostgreSQL with automated backups

### Why Qwen Models?

- **qwen-vl-ocr** — Purpose-built for document OCR, handles Vietnamese handwriting well
- **qwen3.5-flash** — 1M token context, cost-effective for prompt-based classification
- **qwen3-vl-plus** — Fallback for complex document layouts
- All available through Model Studio API (dashscope SDK), no GPU infrastructure needed

## Deployment Topology

```
┌─ Alibaba Cloud Region (ap-southeast-1) ─────────────────┐
│                                                          │
│  ┌─ ECS / Container Service ──────────────────────────┐  │
│  │  FastAPI (N replicas behind SLB)                   │  │
│  │  Celery Workers (M replicas, autoscaled by queue)  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─ Managed Services ────────────────────────────────┐   │
│  │  RDS PostgreSQL 16  (primary + read replica)      │   │
│  │  Tair (Redis-compatible, for cache + sessions)    │   │
│  │  RocketMQ 5.3 (task broker)                       │   │
│  │  OSS (document storage)                           │   │
│  │  Model Studio (AI inference)                      │   │
│  │  EMAS (push notifications)                        │   │
│  │  SLS (audit log storage)                          │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Communication Patterns

| Pattern | Components | Protocol |
|---------|-----------|----------|
| Sync request/response | Mobile apps → Backend API | HTTPS + JWT |
| Async task execution | API → Celery Workers | RocketMQ |
| Task chaining | OCR Worker → Classification Worker | Celery chain |
| Push notifications | Backend → Citizen app | EMAS Push |
| Background sync | Staff app → Backend API | Workmanager + HTTPS |
| Audit shipping | Backend → SLS | Alibaba Log SDK |
