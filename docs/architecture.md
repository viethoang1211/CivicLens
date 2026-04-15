# Architecture

## High-Level Overview

The system consists of four deployable components connected through a shared PostgreSQL database, Redis cache, and optionally a RocketMQ message broker.

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
│   - Routing            /vneid/*                   │
│   - Review             - Reverse proxy → Mock     │
│   - Admin CRUD           VNeID OAuth server       │
└──────┬──────────┬──────────┬──────────┬──────────┘
       │          │          │          │
       ▼          ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌────────────┐ ┌──────────────┐
│PostgreSQL│ │ Redis  │ │Mock VNeID  │ │ Alibaba Cloud│
│   16     │ │  5/7   │ │(OAuth 2.0) │ │              │
│          │ │        │ │            │ │ - Model      │
│ - Models │ │ - Cache│ │ - Authorize│ │   Studio     │
│ - RLS    │ │ - Rate │ │ - Token    │ │ - EMAS Push  │
│ - Audit  │ │   Limit│ │ - Userinfo │ │ - SLS Logs   │
│          │ │        │ │            │ │              │
└──────────┘ └────────┘ └────────────┘ └──────────────┘
```

> **Note:** File storage supports two backends: Alibaba Cloud OSS (production) or local filesystem (demo/dev, configured via `STORAGE_BACKEND=local`). In local mode, uploaded files are stored on the ECS disk at `/data/uploads` and served via a `/files` static mount.

> **Note:** The Celery task broker (RocketMQ) is optional for demo deployments where async AI tasks are not needed.

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
│   │   ├── vneid_proxy.py   # Reverse proxy /vneid/* → mock-vneid container
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
│   │       ├── auth.py            # VNeID OAuth2 code exchange → JWT
│   │       ├── submissions.py     # Read-only status + workflow view
│   │       ├── dossier.py         # Dossier tracking + reference lookup
│   │       └── notifications.py   # Push notification history
│   ├── models/              # SQLAlchemy ORM models (17 entities)
│   ├── services/            # Business logic layer
│   │   ├── ai_client.py          # Qwen VL OCR + classification + slot validation + summarization + entity extraction
│   │   ├── oss_client.py         # Storage abstraction (OSS or local filesystem)
│   │   ├── local_storage.py      # Local filesystem storage backend
│   │   ├── dossier_service.py    # Dossier completeness, reference numbers, workflow
│   │   ├── routing_service.py    # Workflow creation from rules
│   │   ├── workflow_service.py   # Step advancement (dual-owner: submission + dossier) + retention
│   │   ├── review_service.py     # Review validation + processing
│   │   ├── notification_service.py  # Push notification triggers
│   │   ├── audit_service.py      # Immutable audit logging + SLS
│   │   ├── quality_service.py    # Image quality assessment
│   │   ├── template_service.py   # Template schema validation
│   │   ├── submission_service.py # Duplicate detection
│   │   ├── search_service.py     # Cross-department full-text search (FTS + trigram)
│   │   ├── summarization_service.py  # AI summarization + entity extraction
│   │   └── analytics_service.py  # SLA metrics aggregation
│   ├── security/
│   │   ├── auth.py               # JWT encode/decode, identity deps
│   │   ├── abac.py               # Clearance-based access control
│   │   └── audit_interceptor.py  # Automatic API audit logging
│   └── workers/
│       ├── celery_app.py         # Celery configuration
│       ├── ocr_worker.py         # Async OCR pipeline
│       ├── classification_worker.py  # Async classification → chains to summarization
│       ├── summarization_worker.py   # Async AI summarization (submission + dossier)
│       └── backfill_summaries.py     # Management command for backfilling existing data
├── alembic/                 # Database migrations
├── Dockerfile               # Production container (ENV PYTHONPATH=/app)
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
- **Guided document capture** (003) — step-by-step capture wizard driven by `requirement_snapshot` JSONB, including `GuidedCaptureScreen`, `CaptureStepWidget`, `DossierSummaryScreen`, `AiValidationBadge`, and `PagePreviewWidget`

### Mock VNeID OAuth Server (`mock_vneid/`)

A lightweight FastAPI server that simulates Vietnam's national digital identity (VNeID) OAuth 2.0 flow for development and demo purposes. In production, this would be replaced by the real VNeID integration.

Endpoints:
- `GET /authorize` — Login page (citizen selection dropdown in demo mode)
- `POST /authorize` — Validates selection, redirects with `?code=...`
- `POST /oauth/token` — Exchanges authorization code for JWT access token
- `GET /oauth/userinfo` — Returns citizen profile from Bearer token
- `GET /health` — Health check
- `GET /.well-known/openid-configuration` — OpenID Connect discovery document

Pre-loaded with 3 demo citizens. The backend accesses this server internally (container-to-container), and the login page is exposed to browsers via a reverse proxy at `/vneid/*`.

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
- **OSS** — Document image storage with presigned URLs (production); local filesystem storage available for demo/dev
- **EMAS** — Push notification delivery to citizen devices
- **SLS** — Long-term audit log retention for compliance
- **RDS** — Managed PostgreSQL with automated backups

### Storage Backends

The storage layer supports two backends, selected via the `STORAGE_BACKEND` environment variable:

| Backend | Config | Use Case |
|---------|--------|----------|
| `oss` | `STORAGE_BACKEND=oss` + OSS credentials | Production — Alibaba Cloud Object Storage |
| `local` | `STORAGE_BACKEND=local` + `LOCAL_STORAGE_PATH=/data/uploads` | Demo/dev — local filesystem with `/files` static serving |

Both backends implement the same interface: `upload()`, `download()`, `delete()`, `generate_key()`, `get_presigned_url()`. The `oss_client.py` module auto-selects the backend at startup.

### Why Qwen Models?

- **qwen-vl-ocr** — Purpose-built for document OCR, handles Vietnamese handwriting well
- **qwen3.5-flash** — 1M token context, cost-effective for prompt-based classification
- **qwen3-vl-plus** — Fallback for complex document layouts
- All available through Model Studio API (dashscope SDK), no GPU infrastructure needed

## Deployment Topology

```
┌─ Alibaba Cloud Region (ap-southeast-1) ─────────────────┐
│                                                          │
│  ┌─ ECS Instance (Docker) ────────────────────────────┐  │
│  │  FastAPI Backend (:8000)                           │  │
│  │    ├── /v1/staff/*     ← Staff API                 │  │
│  │    ├── /v1/citizen/*   ← Citizen API                │  │
│  │    ├── /vneid/*        ← Reverse proxy → Mock VNeID │  │
│  │    └── /files/*        ← Static file serving (local)│  │
│  │  Mock VNeID OAuth (:9000)                          │  │
│  │  Celery Worker (optional)                          │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─ Managed Services ────────────────────────────────┐   │
│  │  RDS PostgreSQL 16  (single instance or replica)  │   │
│  │  Redis 5.0 (cache + sessions)                     │   │
│  │  Model Studio (AI inference)                      │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
│  SLB → :80 → ECS :8000 (all traffic through backend)    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

> **Demo deployment:** Uses local filesystem instead of OSS, and `docker save/scp/load` instead of ACR for image delivery. RocketMQ is optional when Celery async tasks are not needed.

## Communication Patterns

| Pattern | Components | Protocol |
|---------|-----------|----------|
| Sync request/response | Mobile apps → Backend API | HTTPS + JWT |
| Async task execution | API → Celery Workers | RocketMQ |
| Task chaining | OCR Worker → Classification Worker → Summarization Worker | Celery chain |
| Push notifications | Backend → Citizen app | EMAS Push |
| Background sync | Staff app → Backend API | Workmanager + HTTPS |
| Audit shipping | Backend → SLS | Alibaba Log SDK |
