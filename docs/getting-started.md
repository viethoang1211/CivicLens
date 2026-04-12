# Getting Started

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Backend API and workers |
| Flutter | 3.24+ | Staff and citizen mobile apps |
| Docker & Docker Compose | Latest | Local PostgreSQL, Redis, RocketMQ |
| Alibaba Cloud Account | — | Model Studio API key (for AI features) |

## 1. Start Infrastructure

```bash
cd infra
docker compose up -d
```

This starts:
- **PostgreSQL 16** on port `5432` (user: `postgres`, password: `postgres`, db: `public_sector`)
- **Redis 7** on port `6379`
- **RocketMQ 5.3** nameserver on port `9876`, broker on port `10911`

Verify all services are healthy:

```bash
docker compose ps
```

## 2. Backend Setup

### Install Dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Configure Environment

Create a `.env` file in `backend/` or export these variables:

```bash
# Required
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/public_sector"
export REDIS_URL="redis://localhost:6379/0"
export DASHSCOPE_API_KEY="sk-your-model-studio-key"

# Alibaba Cloud OSS
export OSS_ACCESS_KEY_ID="your-access-key"
export OSS_ACCESS_KEY_SECRET="your-secret"
export OSS_BUCKET_NAME="public-sector-docs"
export OSS_ENDPOINT="https://oss-ap-southeast-1.aliyuncs.com"

# Celery
export CELERY_BROKER_URL="rocketmq://localhost:9876"
export CELERY_RESULT_BACKEND="redis://localhost:6379/1"

# JWT (change in production!)
export JWT_SECRET_KEY="change-me-in-production"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRE_MINUTES="480"

# Thresholds
export IMAGE_QUALITY_THRESHOLD="0.5"
export CLASSIFICATION_CONFIDENCE_THRESHOLD="0.7"
```

### Run Database Migrations

```bash
alembic upgrade head
```

### Seed Initial Data

Populates departments, document types, routing rules, case types (with requirement groups and routing steps) for common Vietnamese government documents:

```bash
python -m src.seeds.seed_data
```

This seeds 5 case types: `HOUSEHOLD_BIZ_REG`, `COMPANY_REG`, `BIRTH_CERT`, `HOUSEHOLD_REG`, `MARITAL_STATUS` — each with their required document groups and department routing steps. The seeding is idempotent (safe to run multiple times).

### Start the API Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API documentation is available at: **http://localhost:8000/docs** (Swagger UI)

### Start Celery Workers

In a separate terminal:

```bash
cd backend
source .venv/bin/activate
celery -A src.workers.celery_app worker --loglevel=info
```

## 3. Staff App Setup

```bash
cd staff_app
flutter pub get
flutter run
```

The staff app requires:
- A physical device or emulator with camera access (for document scanning)
- Network connectivity to the backend API (configure the API base URL in the app)

## 4. Citizen App Setup

```bash
cd citizen_app
flutter pub get
flutter run
```

The citizen app will connect to the backend API for authentication and submission tracking.

## 5. Verify the Setup

### Quick Smoke Test

1. Open the Swagger UI at http://localhost:8000/docs
2. **Create a staff login** — use the seed data or create via direct DB insert
3. **Authenticate** via `POST /v1/staff/auth/login` with employee_id and password
4. **Create a submission** via `POST /v1/staff/submissions` with the JWT token
5. **Upload a page** via `POST /v1/staff/submissions/{id}/pages` with an image
6. **Finalize scan** via `POST /v1/staff/submissions/{id}/finalize-scan`
7. Watch Celery logs — OCR and classification tasks should execute automatically
8. **Check classification** via `GET /v1/staff/submissions/{id}/classification`

### Running Tests

```bash
cd backend
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### Linting

```bash
cd backend
ruff check src/
```

## Project Layout Reference

```
public_sector/
├── backend/
│   ├── src/                  # Application source code
│   │   ├── api/              # HTTP endpoints (staff + citizen)
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── services/         # Business logic
│   │   ├── security/         # Auth, ABAC, audit
│   │   ├── workers/          # Celery async tasks
│   │   └── seeds/            # Initial data seeding
│   ├── alembic/              # Database migrations
│   ├── Dockerfile            # Production container
│   └── pyproject.toml        # Dependencies
├── staff_app/                # Flutter — staff mobile app
├── citizen_app/              # Flutter — citizen mobile app
├── shared_dart/              # Shared Dart DTOs & API clients
├── infra/
│   └── docker-compose.yml    # Local dev services
├── specs/                    # Specifications & design docs
└── docs/                     # Project documentation
```

## Common Issues

### Database connection refused

Ensure PostgreSQL is running: `docker compose -f infra/docker-compose.yml ps`. The database takes a few seconds to initialize on first start.

### Celery worker not picking up tasks

Verify RocketMQ is running and healthy. Check that `CELERY_BROKER_URL` matches the RocketMQ nameserver address.

### OSS/Model Studio errors

These require valid Alibaba Cloud credentials. For local development without cloud access, the OCR and classification features will fail gracefully — manual classification can still be used.

### Flutter build errors

Ensure Flutter 3.24+ is installed (`flutter --version`). Run `flutter doctor` to check for missing dependencies.
