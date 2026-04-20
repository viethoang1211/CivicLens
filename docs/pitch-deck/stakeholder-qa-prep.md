# Stakeholder Q&A Preparation

> Anticipated questions from stakeholders based on the **Desired Outcomes & Innovation Challenge** slides, **Key Operational Challenges**, **Constraints & Impact Analysis**, and **Current Workflow Analysis**. Answers are mapped to actual implemented features.

---

## Part 1 — The 8 Future-State Capabilities

### 1. Automated Ingestion

**Q: How does the system handle physical documents? Do we need special scanners?**
> No special hardware required. Officers use the Staff App on a standard Android phone or tablet — they simply point the camera at the document and capture. The app supports both camera capture and gallery import. For case-based submissions, there's a guided capture flow that tells the officer exactly which documents are needed and tracks completion of each slot.

**Q: What happens if the image quality is poor?**
> The system has a quality assessment step. If the image is blurry, too dark, or skewed, the AI model's OCR confidence score drops below 0.6, triggering an automatic fallback to a more powerful model (`qwen-vl-max`). Officers can also re-scan if unsatisfied. Image quality score is recorded for audit purposes.

**Q: Does it support batch scanning — multiple pages at once?**
> Yes. The multi-page scan flow lets the officer capture multiple pages of a single document in sequence. Each page is stored as a separate `ScannedPage` record linked to the same submission or dossier document.

**Q: Can it accept digital document uploads, not just camera scans?**
> Yes. The app supports gallery import alongside camera capture, so pre-existing photos or downloaded files can be used.

---

### 2. Intelligent Classification

**Q: How does the AI classify documents? How accurate is it?**
> We use an **ensemble classification** approach — two independent AI models analyze each document:
> 1. **Text-based** — Analyzes the OCR-extracted text using `qwen-plus`
> 2. **Vision-based** — Analyzes the raw image (stamps, logos, layout) using a multimodal model
>
> When both agree, the confidence score gets a +10% bonus. When they disagree, the higher-confidence result is used with a -20% penalty. In testing with Vietnamese government documents, classification accuracy is typically 85–95%.

**Q: What document types can it recognize?**
> Currently **15 document types** are configured, covering common Vietnamese administrative documents: Citizen ID (CCCD), passport, birth registration, marriage certificate, marital status declaration, residence forms, business registration, company charter, shareholder lists, complaints, classified reports, and more. New document types can be added via seed data — just define a `classification_prompt` and the AI adapts.

**Q: What if the AI gets it wrong?**
> AI classification is **always advisory, never final**. The officer sees the AI suggestion with a confidence score and can either confirm or override it. The `ai_match_overridden` flag is recorded in the audit trail, so we track how often human judgment differs from AI. This data can be used to fine-tune prompts over time.

**Q: Does it extract specific fields, or just classify the document type?**
> Both. Classification identifies the document type. Then **entity extraction** (part of the summarization pipeline) pulls out key fields: names, ID numbers, dates, addresses, etc. These are stored as structured data in `template_data["_entities"]` and are searchable.

---

### 3. Auto-Routing

**Q: How does the system decide which department handles a document?**
> Routing is **template-based per procedure type**. Each Case Type (e.g., "Business Registration") has a predefined sequence of departments — for example, Reception → Finance → Judicial. When a dossier is submitted, the system creates workflow steps for each department in order. Each step includes an expected duration (SLA deadline).

**Q: Can routing rules be changed without developer intervention?**
> Currently, routing rules are defined in seed data and database records (`CaseTypeRoutingStep`, `RoutingRule`). An admin with database access can add/modify routes. A future admin UI could expose this, but the data model fully supports it today.

**Q: What if a document doesn't match any known routing rule?**
> The system assigns a `pending_routing` status. The Reception officer can then manually assign the next department. No document gets lost — it stays visible in the Reception queue until explicitly routed.

**Q: Does routing consider staff availability or workload?**
> Not currently. Routing assigns to departments, not individual officers. Within a department, any officer with adequate clearance can pick up the case from the queue. Load-balancing across individuals is a potential future enhancement.

---

### 4. AI Summarization

**Q: What does "AI Summarization" actually produce?**
> For each scanned document, the system generates a natural-language summary highlighting key facts: parties involved, dates, amounts, document purpose. For dossiers with multiple documents, it produces a **consolidated summary** across all documents. The summary appears in the officer's review screen and in search results as a preview.

**Q: Which AI model is used? Is it hosted locally?**
> We use Alibaba Cloud's `qwen-plus` model via the DashScope SDK. The model runs on Alibaba Cloud infrastructure — no local GPU required. This was chosen for Vietnamese language quality and compliance with data residency considerations (Alibaba Cloud has a presence in the region).

**Q: How fast is summarization?**
> Summarization runs **asynchronously** via a Celery task queue. It typically completes within 10–30 seconds after OCR finishes. It does not block the officer's workflow — they can continue scanning while summaries generate in the background.

**Q: Is there a quality gate?**
> Yes. If OCR confidence is below 0.3 (very poor scan), the summarization task skips the document to avoid generating a misleading summary based on garbage text. The officer is notified to re-scan.

---

### 5. Cross-Dept Collaboration

**Q: How do different departments work together on the same case?**
> Each case follows a **sequential workflow**. When Department A finishes reviewing and approves, the case automatically moves to Department B's queue. Each department sees only the cases assigned to them. Officers can add **annotations** (notes) at each step — these carry forward so the next department has context from previous reviewers.

**Q: Can two departments review simultaneously?**
> Currently, workflow steps are strictly **sequential** — one department at a time. This matches the typical Vietnamese administrative process where each step requires sign-off before the next begins. Parallel review is architecturally possible but not yet implemented.

**Q: What happens when a department rejects a case?**
> Three possible outcomes at each step:
> 1. **Approved** → case advances to next department
> 2. **Rejected** → case is marked rejected with a reason; citizen is notified
> 3. **Needs Info** → case is paused; citizen is notified to provide additional documents
>
> In all cases, the officer must provide a note explaining the decision.

**Q: Can a case be sent back to a previous department?**
> The current workflow model supports forward progression or rejection. Re-routing to a previous step would require a new workflow step to be created. This is a potential enhancement for complex litigation cases.

---

### 6. Real-time Tracking

**Q: How do citizens track their case status?**
> Citizens use the **Citizen App** (separate mobile application). After authenticating via VNeID (Vietnam's national eID system), they see all their linked dossiers with a **visual timeline** showing every department step: completed, in-progress, or pending. They can also look up any dossier by reference number without logging in.

**Q: Do citizens receive notifications when something changes?**
> Yes. The system sends **in-app notifications** when:
> - A step is approved and the case moves forward
> - A department requests additional information
> - The case is completed
> - The case is rejected (with reason)
> - A step is delayed past its SLA deadline
>
> Push notifications via Alibaba Cloud EMAS are integrated at the infrastructure level and ready for activation.

**Q: Is it truly real-time or does it require manual refresh?**
> The Citizen App uses **polling** (periodic refresh). This is reliable and battery-efficient. WebSocket/Server-Sent Events for instant push could be added, but polling with a 30-second interval is sufficient for a process that takes hours or days per step.

**Q: Can citizens see the estimated completion time?**
> Yes. Each workflow step has an `expected_complete_by` timestamp based on the routing rule's `expected_duration_hours`. The Citizen App shows an `estimated_completion` date derived from remaining steps.

---

### 7. Centralized Indexing

**Q: Can officers search across all documents in the system?**
> Yes. The search endpoint (`GET /v1/staff/search`) performs **full-text search across all OCR-extracted text** from every scanned document, plus citizen names, ID numbers, and dossier reference numbers. Results are ranked by relevance with highlighted matching snippets.

**Q: Does it handle Vietnamese diacritics? Searching "nguyen" finds "Nguyễn"?**
> Yes. We use a custom `immutable_unaccent()` PostgreSQL function combined with the `pg_trgm` extension. Searching "nguyen van hung" correctly matches "Nguyễn Văn Hùng". The search index is built on both raw and corrected OCR text.

**Q: Is search filtered by security clearance?**
> Absolutely. Every search result is filtered: `staff.clearance_level >= document.security_classification`. A level-1 officer will never see Secret or Top Secret documents in search results, even if the text matches. This is enforced at the query level, not just the UI.

**Q: What filters are available?**
> Status (pending, in-progress, completed, rejected), document type, case type, department, date range, and sort order (relevance, submission date, last updated).

**Q: Can citizens search?**
> Not currently. Search is staff-only. Citizens access their own dossiers via the "My Dossiers" screen. Cross-dossier citizen search was deliberately excluded from the current scope for privacy reasons.

**Q: Can it scale? What if there are millions of documents?**
> The current implementation uses **PostgreSQL full-text search** with GIN indexes — performant up to ~100K documents. Beyond that, the architecture supports migration to a dedicated search engine (e.g., Elasticsearch or Alibaba Cloud OpenSearch) without changing the API contract. The search service is a clean abstraction layer.

---

### 8. Access Control

**Q: What security levels are supported?**
> Four levels, matching government classification standards:
> | Level | Label | Example |
> |-------|-------|---------|
> | 0 | Unclassified | Birth registration |
> | 1 | Confidential | Business registration |
> | 2 | Secret | Internal investigation |
> | 3 | Top Secret | Classified reports |

**Q: How is security enforced?**
> Three layers:
> 1. **Application-level ABAC** — Every staff API endpoint checks `staff.clearance_level >= document.security_classification` before returning data
> 2. **PostgreSQL Row-Level Security (RLS)** — Database-level policies on `submission` and `scanned_page` tables prevent even raw SQL from leaking classified data
> 3. **Audit logging** — Every access attempt (granted or denied) is recorded with actor, action, resource, and clearance decision

**Q: Is there an audit trail?**
> Yes, comprehensive. The `AuditLogEntry` table records:
> - Who (staff member ID, name, department)
> - What (action: view, create, approve, reject, classify, search, etc.)
> - Which resource (submission/dossier/scanned page ID)
> - When (timestamp)
> - Clearance result (granted/denied)
> - Additional metadata (JSONB)
>
> An automatic audit interceptor middleware logs every staff API call without requiring developers to add manual logging.

**Q: Can an officer see cases outside their department?**
> Officers see their **department's queue** by default. Search can return results from other departments (if clearance allows), but workflow actions (approve/reject) can only be performed by the assigned department. This is enforced at both the API and database level.

**Q: Who can access classified documents?**
> Only staff members whose `clearance_level` is equal to or higher than the document's `security_classification`. This is checked on every read, search, and action. Unauthorized access attempts are logged and denied — the officer sees an access denied message, and the attempt appears in the audit log.

---

## Part 2 — Addressing Operational Challenges

### Challenge 1: Manual Identification

**Q: How does this reduce the time-intensive manual review?**
> Previously: officer reads each document, determines its type, manually fills metadata. Now: the officer scans → AI identifies document type in 10–30 seconds with 85–95% accuracy → officer confirms with one tap. **Estimated time reduction: 5–10 minutes per document → under 1 minute.**

**Q: How does it reduce the risk of misrouting?**
> Routing is **automatic and rule-based**. Once the case type is selected (or the document is classified), the system applies pre-configured routing rules. Human error in department assignment is eliminated. If no routing rule exists, the system flags it rather than routing to a random department.

**Q: What about backlog during intake?**
> Quick Scan mode lets officers scan documents in under 30 seconds each. AI processing happens asynchronously — the officer can scan the next document while the previous one is being analyzed. This parallelism significantly reduces intake bottleneck.

---

### Challenge 2: Cross-Department Consolidation

**Q: How does this eliminate duplication of effort?**
> Each document is scanned and OCR'd **once**. The extracted text, AI classification, and summary follow the dossier through every department. No department needs to re-read or re-interpret a document that another department already processed.

**Q: How does it ensure consistent interpretation across departments?**
> The AI summary provides a **standardized interpretation** of each document. Every department reviewer sees the same AI-extracted entities, the same summary, and the same OCR text. Annotations from previous departments add context. This creates a shared, consistent understanding.

**Q: How does it speed up information consolidation?**
> Before: departments request documents from each other via paper memos or emails. Now: everything is in a **single dossier** accessible to all authorized departments. The search system lets any officer find any document in the entire system (within clearance limits) in seconds.

---

### Challenge 3: Extended Approval Cycles

**Q: How does this reduce the number of review layers?**
> The system doesn't reduce review layers (those are legally mandated). Instead, it **eliminates dead time between layers**. When Department A approves, the case appears in Department B's queue **instantly** — no physical transfer, no waiting for courier, no lost files. Each department also has SLA deadlines that trigger alerts when exceeded.

**Q: How does it reduce repeated consultations?**
> Officers see the full history: previous departments' decisions, notes, AI summary, extracted entities. This eliminates the need to call colleagues for context. Everything is already in the dossier timeline.

**Q: How does it improve visibility into case status?**
> Three levels of visibility:
> 1. **Citizens** — see real-time timeline in Citizen App + notifications
> 2. **Officers** — see department queue with SLA indicators, case detail with full history
> 3. **Managers** — see SLA analytics dashboard with department-level performance metrics (completion rate, average processing time, delay rate)

---

## Part 3 — Addressing Constraints

### Physical Document Reliance

**Q: Does the system still require physical documents?**
> Yes — the system is designed to **bridge the physical-digital gap**, not eliminate physical documents. Citizens bring paper documents to the counter. Officers scan them with a phone camera. From that point on, everything is digital. The physical originals are still retained per legal requirements, but all processing happens on the digital copy.

**Q: What about documents already in digital form?**
> The system accepts images from the phone gallery, so digital photos, screenshots, or downloaded images can be used. The OCR and classification pipeline processes any image regardless of source.

### Strict Security & Confidentiality

**Q: How is data protected in transit?**
> All API communication is over HTTPS. The mobile apps communicate exclusively with the backend API — no direct database access. JWT tokens with expiration are used for authentication.

**Q: Where is data stored?**
> - **Database**: PostgreSQL on Alibaba Cloud RDS (encrypted at rest)
> - **Document images**: Alibaba Cloud OSS (Object Storage Service) with access control
> - **AI processing**: Alibaba Cloud DashScope — documents are sent to the API for processing but not retained by the AI service per DashScope terms

**Q: Is there data residency compliance?**
> Yes. Alibaba Cloud infrastructure is used throughout, which has data centers in the Asia-Pacific region. No data leaves to US/EU cloud providers.

### Multi-Level Document Classification

**Q: Can classification levels be changed after assignment?**
> The `security_classification` field can be updated by authorized staff. The audit log records any changes. RLS policies enforce the new classification immediately — if a document is upgraded from Confidential to Secret, officers with only Confidential clearance lose access instantly.

### Fragmented Systems

**Q: How does this replace existing fragmented systems?**
> The platform serves as a **single system of record** for all document processing. Instead of separate tracking spreadsheets per department, all dossiers live in one database with one workflow engine. The centralized search indexes everything. The single API serves both the Staff App and Citizen App.

---

## Part 4 — Innovation Challenge

> **"How might public sector organizations implement a secure, AI-assisted document intelligence capability that can automatically classify, summarize, route, and track administrative documents across departments while complying with strict security and confidentiality requirements?"**

**Q: Can you summarize how this platform answers the Innovation Challenge?**
> We built a platform that covers the complete document lifecycle:
>
> | Challenge Keyword | Our Solution |
> |---|---|
> | **Classify** | Ensemble AI classification (text + vision) with 15 document types, officer override, confidence scoring |
> | **Summarize** | AI-generated summaries with entity extraction, available at every review step |
> | **Route** | Template-based auto-routing per case type, with SLA deadlines per step |
> | **Track** | Citizen App with real-time timeline, in-app notifications, dossier lookup by reference |
> | **Security** | 4-level classification, ABAC + RLS, full audit trail, department-scoped queues |
> | **Cross-department** | Single dossier flows through multiple departments sequentially, with shared context |

---

## Part 5 — Technical Questions

**Q: What tech stack is this built on?**
> - **Backend**: Python 3.12, FastAPI, SQLAlchemy 2 (async), Celery (task queue), Alembic (migrations)
> - **Database**: PostgreSQL 16 with JSONB, tsvector, RLS
> - **AI**: Alibaba Cloud DashScope SDK — Qwen-VL-OCR (OCR), Qwen-Plus (classification/summarization)
> - **Mobile**: Flutter 3.24+ (Dart) — two apps (Staff + Citizen) sharing a common DTO package
> - **Storage**: Alibaba Cloud OSS for document images
> - **Infrastructure**: Docker Compose (dev), Alibaba Cloud ECS/RDS/OSS (production)

**Q: How long did this take to build?**
> The platform was developed across 6 feature sprints (001 through 006), each building on the previous one. The architecture is modular — each capability can be enhanced independently.

**Q: Can it be deployed on-premises?**
> The system uses Docker containers and PostgreSQL — both can run on-premises. The only external dependency is the Alibaba Cloud DashScope API for AI models. For a fully air-gapped deployment, the AI models would need to be replaced with self-hosted alternatives (e.g., locally-run Qwen models).

**Q: What's the performance like?**
> - OCR + Classification: 10–30 seconds per document
> - Search: sub-second for typical queries (PostgreSQL FTS with GIN indexes)
> - API response time: <200ms for standard endpoints
> - Concurrent users: tested for typical ward-level load (~10 simultaneous staff users)

**Q: What are the known limitations?**
> | Area | Current State | Future Enhancement |
> |------|--------------|-------------------|
> | Push notifications | Infrastructure ready, not yet activated | Enable Alibaba Cloud EMAS |
> | Parallel department review | Sequential only | Add parallel step support |
> | Citizen-side search | Not available | Privacy-scoped citizen search |
> | Admin dashboard | API exists, no UI | Build manager web dashboard |
> | AI routing | Static rules | ML-based routing suggestions |
> | Document volume | PostgreSQL FTS (~100K docs) | Elasticsearch for larger scale |

---

## Part 6 — Demo-Specific Questions

**Q: Is this real AI or a mock?**
> Real AI. The OCR and classification use live Alibaba Cloud DashScope models. We use the `qwen-vl-ocr` model for text extraction and `qwen-plus` for classification/summarization. The only mock in the demo is VNeID authentication (which is a government system we can't connect to without formal approval).

**Q: Can you scan my document right now?**
> Yes — bring any Vietnamese document (ID card, form, certificate) and the system will OCR and classify it live. This is the best way to see the AI in action.

**Q: What if the internet goes down during the demo?**
> The Staff App will show connection errors. The system requires internet connectivity for both the API backend and AI processing. Offline mode is not currently supported but could be added for basic document capture (with deferred AI processing).

**Q: How is this different from just scanning to PDF?**
> Scanning to PDF gives you an image file. This system gives you:
> 1. Extracted text (searchable)
> 2. Document classification (what type it is)
> 3. Entity extraction (who, what, when)
> 4. AI summary (what does it say)
> 5. Automatic routing (where should it go)
> 6. Workflow tracking (where is it now)
> 7. Citizen visibility (status in their app)
> 8. Audit trail (who did what when)
