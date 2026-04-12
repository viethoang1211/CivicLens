# Public Sector AI Document Processing Platform

An AI-powered document processing system for Vietnamese government departments that replaces manual paper-based workflows with intelligent digitization, classification, and routing — while giving citizens real-time visibility into their submissions.

## The Problem

Vietnamese government departments currently process citizen-submitted documents through a **5–7 day manual pipeline**:

1. Citizens hand-deliver physical documents to a reception window
2. Staff manually registers each document in paper ledgers
3. Documents are physically carried between departments for review
4. Reviewers re-type handwritten content into internal forms
5. Citizens have **zero visibility** — they must call or visit in person to check status

This creates long processing times, high error rates from manual data entry, lost documents, and frustrated citizens.

## The Solution

This platform digitizes the entire flow with AI-assisted processing:

| Before | After |
|--------|-------|
| 5–7 days processing | < 2 days target |
| Manual handwriting transcription | AI-powered OCR (≥ 85% accuracy on Vietnamese handwriting) |
| Manual document classification | AI classification with ≥ 90% accuracy + slot validation |
| One document at a time | Case-based dossier (hồ sơ) bundles all required documents |
| Physical document routing | Automated sequential department routing per case type |
| Zero citizen visibility | Real-time mobile tracking + reference number lookup |
| No audit trail | 100% immutable audit logging |

## Key Capabilities

- **Case-Based Dossier Submission (Hồ Sơ)** — Staff select a case type (e.g., household business registration), see a checklist of required documents, scan and upload each one, and submit the entire dossier as a unit. Each case type defines its own required document bundle with OR-group flexibility.
- **Document Scanning & OCR** — Staff scan physical documents via mobile camera. AI extracts text from handwritten Vietnamese using Qwen VL models, with human-in-the-loop correction.
- **AI Classification & Slot Validation** — Documents are automatically classified by type (birth certificate, household registration, etc.) and structured fields are extracted into templates. AI also validates whether uploaded documents match their assigned slot in a dossier, with staff override capability.
- **Configurable Case Types** — Admins create and manage case types, document requirement groups (with OR-logic for alternative documents), and routing step templates — all through the API without code changes.
- **Automated Routing** — Dossiers and individual documents flow through configurable sequential department workflows, with clearance-level enforcement at every step.
- **Citizen Status Tracking** — Citizens authenticate via VNeID and track their dossier progress through a visual workflow timeline with push notifications. Citizens can also look up dossier status by reference number (HS-YYYYMMDD-NNNNN) without logging in.
- **Department Review & Collaboration** — Staff review queued documents, approve/reject/request info, and consult across departments without transferring ownership.
- **Security & Compliance** — Four-tier classification (Unclassified → Top Secret), attribute-based access control, PostgreSQL Row-Level Security, and immutable audit logs shipped to Alibaba Cloud SLS.

## Project Structure

```
backend/          Python 3.12 — FastAPI, Celery, SQLAlchemy
staff_app/        Flutter 3.24+ — Government staff mobile app
citizen_app/      Flutter 3.24+ — Citizen-facing mobile app
shared_dart/      Shared Dart — API client & DTOs
infra/            Docker Compose — Local development infrastructure
specs/            Speckit — Specifications, plans, tasks
docs/             Documentation (you are here)
```

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](getting-started.md) | Local development setup, prerequisites, running the system |
| [Architecture](architecture.md) | High-level architecture, tech stack decisions, component overview |
| [Business Flow](business-flow.md) | End-to-end document processing workflow, state machines |
| [API Reference](api-reference.md) | REST API endpoints for staff and citizen apps |
| [Data Model](data-model.md) | Database entities, relationships, and constraints |
| [Security](security.md) | Authentication, authorization, audit logging, data classification |

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend API | Python 3.12 + FastAPI | Async-first, auto-generated OpenAPI docs |
| Task Queue | Celery + RocketMQ | Long-running AI tasks (OCR, classification) |
| Database | PostgreSQL 16 | Row-Level Security for clearance enforcement |
| Cache | Redis 7 / Alibaba Cloud Tair | Session cache, rate limiting |
| AI Models | Qwen VL (OCR), Qwen3.5-Flash (classification) | Vietnamese language support, Alibaba Cloud-native |
| Object Storage | Alibaba Cloud OSS | Scanned document image storage |
| Mobile Apps | Flutter 3.24+ (Dart) | Cross-platform, strong camera/offline support |
| Push Notifications | Alibaba Cloud EMAS | Citizen status update delivery |
| Audit Storage | Alibaba Cloud SLS | Long-term compliance log retention |

## License

Internal — Vietnamese Public Sector.
