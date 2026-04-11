# Research: AI-Powered Public Sector Document Processing

**Feature Branch**: `001-ai-document-processing`
**Date**: 2026-04-10

## R1: OCR for Handwritten Vietnamese Text

**Task**: Research best model/approach for OCR on handwritten Vietnamese documents via Alibaba Cloud

**Decision**: Use `qwen-vl-ocr` as the primary OCR model, with `qwen3-vl-plus` as fallback for complex layouts

**Rationale**:
- `qwen-vl-ocr` is Alibaba's dedicated OCR model specifically designed for documents, tables, and handwritten text extraction
- Very cost-effective at 0.3元/M input tokens, 0.5元/M output tokens
- Supports multi-language including Vietnamese character recognition
- For complex layouts (mixed print + handwriting, tables), `qwen3-vl-plus` provides deeper reasoning at higher cost (1元/M input)
- Both available on Model Studio (百炼) — no self-hosting required

**Alternatives Considered**:
- Self-hosted open-source OCR (Tesseract, PaddleOCR): Rejected — requires GPU infrastructure management, weaker on Vietnamese handwriting
- Third-party OCR services (Google Vision, Azure OCR): Rejected — data sovereignty concerns for government documents, additional vendor dependency
- `qwen3-vl-flash` for all OCR: Less accurate than dedicated OCR model for text extraction tasks

## R2: Document Classification Approach

**Task**: Research whether to fine-tune or use prompt-based classification for Vietnamese administrative documents

**Decision**: Two-phase approach — start with prompt-based classification using `qwen3.5-flash`, migrate to fine-tuned model as training data accumulates

**Rationale**:
- Phase 1 (MVP): Use `qwen3.5-flash` with structured prompts describing each document type template. At 0.2元/M input tokens, this is cost-effective for initial deployment. Supports 1M token context which can hold many template descriptions
- Phase 2 (post-launch): Fine-tune a smaller Qwen model on classified document images via Model Studio's fine-tuning pipeline. This improves accuracy and reduces per-inference cost
- Model Studio supports SFT (supervised fine-tuning) on Qwen VL models through 百炼
- Staff corrections on misclassifications naturally generate training data for fine-tuning

**Alternatives Considered**:
- Fine-tune from day one: Rejected — requires labeled training dataset that doesn't exist yet; cold-start problem
- Traditional ML classifier (SVM, Random Forest on features): Rejected — can't handle visual layout analysis needed for Vietnamese forms
- `qwen3-max` for classification: Overkill for classification; `qwen3.5-flash` provides adequate accuracy at 12x lower cost

## R3: Mobile App Framework

**Task**: Research cross-platform mobile framework for staff and citizen apps

**Decision**: Flutter for both apps (separate codebases sharing a common Dart package for API client and models)

**Rationale**:
- Cross-platform (iOS + Android) from single codebase per app
- Strong camera/image processing plugins for document scanning
- Offline-first architecture support via built-in SQLite (sqflite) and Hive for local storage
- Flutter's rendering engine ensures consistent workflow visualization across platforms
- Large ecosystem of plugins for push notifications, biometric auth (VNeID integration)
- Good performance for image-heavy workflows

**Alternatives Considered**:
- React Native: Viable but weaker camera/offline support, bridge performance overhead for image processing
- Native (Kotlin + Swift): Best performance, but doubles development effort for 2 platforms × 2 apps = 4 codebases
- Web-based PWA: Rejected — insufficient camera access, offline capability, and push notification reliability for government use

## R4: Backend Framework & Architecture

**Task**: Research backend architecture for document processing pipeline

**Decision**: Python 3.12 + FastAPI, with Celery workers for async AI processing

**Rationale**:
- FastAPI: High-performance async API framework, excellent OpenAPI docs generation, strong type safety with Pydantic
- Celery (with RocketMQ as broker): Handles long-running AI tasks (OCR, classification) asynchronously — scanned document processing takes 5-30 seconds per page
- Alibaba Cloud SDK (alibabacloud-sdk) has first-class Python support for Model Studio, OSS, RDS, and all services
- Aligns with AI/ML ecosystem (model fine-tuning scripts, data pipelines)

**Alternatives Considered**:
- Node.js/Express: Weaker Alibaba Cloud SDK support, less natural fit for AI pipeline integration
- Go: Excellent performance but weaker AI ecosystem, no first-class Model Studio SDK
- Java/Spring: Viable but heavier framework overhead, slower development velocity for this team size

## R5: Alibaba Cloud Infrastructure Services

**Task**: Map feature requirements to specific Alibaba Cloud services

**Decision**: The following service mapping:

| Requirement | Service | Justification |
|---|---|---|
| Document image storage | OSS (Object Storage Service) | 12 nines durability, WORM for compliance, lifecycle policies for retention |
| Relational data | ApsaraDB RDS for PostgreSQL | Managed PostgreSQL, supports JSONB for flexible document metadata |
| AI inference | Model Studio (百炼) | Managed Qwen model hosting, fine-tuning pipeline, pay-per-token |
| Async task processing | RocketMQ | Managed message queue for OCR/classification job dispatch |
| Cache & sessions | Tair (Redis-compatible) | Staff/citizen session management, department queue caching |
| Push notifications | Alibaba Cloud Push (EMAS) | Mobile push for citizen status updates |
| Audit logs | SLS (Simple Log Service) | Managed log ingestion, search, and retention for compliance |
| CDN | Alibaba Cloud CDN | Static assets delivery for mobile app updates |
| VNeID integration | API Gateway | Rate limiting and security for citizen identity verification |

**Rationale**: All services are within Alibaba Cloud ecosystem, ensuring data sovereignty within China/Vietnam compliance requirements. Managed services reduce operational burden.

## R6: Offline Sync Strategy for Staff App

**Task**: Research offline-first architecture for document scanning at offices with intermittent connectivity

**Decision**: Local-first capture with background sync queue

**Rationale**:
- Staff app stores scanned images locally (device storage) immediately upon capture
- A background sync queue (implemented in Dart using workmanager plugin) syncs captured images to OSS when connectivity is available
- Each scan creates a local `PendingScan` record with status: `captured` → `uploading` → `synced`
- OCR, classification, and routing are triggered server-side only after sync completes
- Conflict resolution: server-side timestamp wins; staff can re-upload if sync fails
- Local storage is encrypted at rest using Flutter's flutter_secure_storage for document confidentiality

**Alternatives Considered**:
- No offline support: Rejected — commune/district offices confirmed to have intermittent connectivity
- Full offline AI processing (on-device classification): Rejected — model size too large for mobile devices, and classification accuracy would suffer
- Periodic batch sync: Rejected — real-time sync when connectivity is available provides faster processing times

## R7: Security Classification Implementation

**Task**: Research implementing multi-level security (Unclassified → Top Secret) in document processing

**Decision**: Row-Level Security (RLS) in PostgreSQL + ABAC (Attribute-Based Access Control) middleware

**Rationale**:
- PostgreSQL RLS enforces security classifications at the database level — even direct DB access respects clearance levels
- ABAC middleware in FastAPI checks `user.clearance_level >= document.classification_level` on every request
- Four levels mapped to integer values: Unclassified(0), Confidential(1), Secret(2), Top Secret(3)
- All access events written to SLS audit log with user identity, document ID, action, timestamp, and clearance check result
- Department routing validates receiving department has personnel with adequate clearance before transfer

**Alternatives Considered**:
- Application-level only (no RLS): Rejected — a bug in application logic could expose classified documents
- External authorization service (OPA/Cedar): Over-engineering for this scope; RLS + middleware is sufficient
- Separate databases per classification level: Rejected — vastly increases operational complexity
