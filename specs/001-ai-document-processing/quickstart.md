# Quickstart: AI-Powered Public Sector Document Processing

**Feature Branch**: `001-ai-document-processing`

## Prerequisites

- Python 3.12+
- Flutter 3.24+ (for mobile apps)
- PostgreSQL 16+ (local dev) or ApsaraDB RDS connection
- Alibaba Cloud account with Model Studio (百炼) enabled
- Redis 7+ (local dev) or Tair connection
- Docker & Docker Compose (for local infrastructure)

## Repository Structure

```
public_sector/
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI routes
│   │   │   ├── staff/        # Staff app endpoints
│   │   │   └── citizen/      # Citizen app endpoints
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── services/         # Business logic
│   │   │   ├── ocr.py        # Qwen OCR integration
│   │   │   ├── classifier.py # Document classification
│   │   │   ├── router.py     # Workflow routing engine
│   │   │   └── notifier.py   # Push notification dispatch
│   │   ├── workers/          # Celery async task workers
│   │   ├── security/         # ABAC middleware, RLS setup
│   │   └── config.py         # Environment configuration
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/
│   ├── alembic/              # Database migrations
│   ├── pyproject.toml
│   └── Dockerfile
├── staff_app/                # Flutter staff application
│   ├── lib/
│   │   ├── features/
│   │   │   ├── scan/         # Camera capture & offline queue
│   │   │   ├── classify/     # Classification review
│   │   │   ├── review/       # Department review queue
│   │   │   └── auth/         # Staff authentication
│   │   ├── core/
│   │   │   ├── api/          # API client
│   │   │   ├── sync/         # Offline sync engine
│   │   │   └── storage/      # Local encrypted storage
│   │   └── main.dart
│   └── pubspec.yaml
├── citizen_app/              # Flutter citizen application
│   ├── lib/
│   │   ├── features/
│   │   │   ├── submissions/  # Submission list & detail
│   │   │   ├── workflow/     # Visual workflow tracker
│   │   │   ├── notifications/
│   │   │   └── auth/         # VNeID authentication
│   │   ├── core/
│   │   │   └── api/          # API client
│   │   └── main.dart
│   └── pubspec.yaml
├── shared_dart/              # Shared Dart package (API models, DTOs)
│   ├── lib/
│   └── pubspec.yaml
├── infra/                    # Infrastructure-as-code
│   ├── docker-compose.yml    # Local dev environment
│   └── terraform/            # Alibaba Cloud provisioning
├── specs/                    # Feature specifications
└── requirements/             # Requirements images
```

## Local Development Setup

### 1. Start infrastructure

```bash
cd infra
docker-compose up -d  # PostgreSQL, Redis, RocketMQ
```

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Set environment variables
export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-key>
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-secret>
export DASHSCOPE_API_KEY=<your-model-studio-key>
export DATABASE_URL=postgresql://dev:dev@localhost:5432/public_sector
export REDIS_URL=redis://localhost:6379/0

# Run migrations
alembic upgrade head

# Start API server
uvicorn src.main:app --reload --port 8000

# Start Celery worker (separate terminal)
celery -A src.workers.app worker --loglevel=info
```

### 3. Staff App

```bash
cd staff_app
flutter pub get
flutter run  # Connect device or emulator
```

### 4. Citizen App

```bash
cd citizen_app
flutter pub get
flutter run
```

## Key Environment Variables

| Variable | Description |
|---|---|
| `DASHSCOPE_API_KEY` | Alibaba Cloud Model Studio API key |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis/Tair connection string |
| `OSS_BUCKET_NAME` | Alibaba Cloud OSS bucket for document images |
| `OSS_ENDPOINT` | OSS endpoint |
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | Alibaba Cloud credentials |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | Alibaba Cloud credentials |
| `VNEID_CLIENT_ID` | VNeID OAuth client ID |
| `VNEID_CLIENT_SECRET` | VNeID OAuth client secret |
| `EMAS_APP_KEY` | Alibaba Cloud Push (EMAS) app key |

## Running Tests

```bash
cd backend
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/contract/ -v
```

## API Documentation

After starting the backend, OpenAPI docs are available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
