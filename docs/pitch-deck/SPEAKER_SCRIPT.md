# Speaker Script — AI Document Intelligence Pitch

> **Total time: 4 minutes** (3 min presentation + 1 min demo video)
> Suggested pacing: ~25-30 seconds per slide, 60 seconds for video

---

## Slide 1: Title (15 seconds)

> Good morning/afternoon. Today I'm going to show you how we turned a manual, paper-heavy document processing workflow into an intelligent, AI-powered platform — built specifically for public sector organizations with strict security and multi-department coordination requirements.

**[Click to next slide]**

---

## Slide 2: The Challenge Today (35 seconds)

> Let's start with the problem we all recognize.

> On the left — three pain points your teams face every day. First, **processing delays**: officers manually read, classify, and route every document — and that takes 5 to 7 days on average. Second, **fragmented flow**: each department works in its own silo — duplicating effort, inconsistent interpretations, no shared visibility. Third, **security constraints**: with four classification levels from Unclassified to Top Secret, access control can't be an afterthought — it has to be built into every layer.

> On the right you see the impact — high manual workload, multiple departments touching the same case, and citizens waiting with no visibility into where their documents are.

> So the question is: can we do better? Yes.

**[Click to next slide]**

---

## Slide 3: Our Solution (40 seconds)

> We built an end-to-end platform with three core engines.

> First, the **AI Engine** — this handles OCR, document classification, and summarization. An officer scans a document with their phone camera, and within 10 to 30 seconds, the AI extracts all the text, identifies the document type, and generates a summary with key entities — names, ID numbers, dates — all extracted automatically.

> Second, the **Workflow Engine** — once documents are classified, the system automatically routes them to the right departments in the right order. Each step has an SLA deadline. No more paper memos or physical file transfers.

> Third, the **Citizen Portal** — a mobile app where citizens can track their case in real-time. They see every step: which department has their case, what's been approved, what's pending. No phone calls, no waiting at the counter.

> At the bottom you see the digitized workflow: Scan, OCR, Classify, Route, Review, Complete — six steps, all automated or AI-assisted.

**[Click to next slide]**

---

## Slide 4: 8 Capabilities Delivered (30 seconds)

> Now here's the important part — these aren't future plans. Every single one of the eight capabilities from the Innovation Challenge requirements is **fully implemented and demo-ready**.

> *(Point across the grid)*

> Automated Ingestion — camera scan on any phone. Intelligent Classification — ensemble AI with 85 to 95 percent accuracy across 15 document types. Auto-Routing with SLA deadlines. AI Summarization with entity extraction. Cross-department collaboration with shared annotations. Real-time citizen tracking. Centralized full-text search across all documents — with Vietnamese diacritics support. And four-level access control with database-level row-level security and a complete audit trail.

> All running on live AI models, not mocks.

**[Click to next slide]**

---

## Slide 5: Challenges Solved (30 seconds)

> Let me map this directly to your three operational challenges.

> **Manual identification** — before, officers spent 5 to 10 minutes per document reading and classifying. Now? Under one minute. The AI does the heavy lifting, the officer confirms with one tap.

> **Cross-department consolidation** — before, every department re-read the same document independently. Now there's a single shared dossier. One scan, one index — every department sees the same OCR text, the same AI summary, the same extracted entities.

> **Extended approval cycles** — before, physical file transfers with no visibility. Now, instant auto-routing with SLA tracking. The citizen sees the progress on their phone in real-time.

**[Click to next slide]**

---

## Slide 6: See It in Action (60 seconds — play video)

> Don't just take my word for it — let me show you.

> *(Play the 1-minute demo video)*

> *(While video plays or right after, highlight:)*

> What you just saw: an officer scanning a real Citizen ID card and a Birth Registration Form. The AI recognized both document types, extracted the key information — name, ID number, date of birth — and created searchable, indexed records in seconds.

> On the right side — the key numbers: 10 to 30 seconds per document, 15 document types supported, 85 to 95 percent classification accuracy, and 100 percent audit trail coverage — every action logged, every access checked.

**[Click to next slide]**

---

## Slide 7: Thank You / Q&A (10 seconds)

> To wrap up — we directly answered the Innovation Challenge. We **classify** with ensemble AI. We **summarize** with entity extraction. We **route** automatically. We **track** in real-time. And we **secure** everything with four-level classification and a complete audit trail.

> Thank you. I'm happy to take questions.

---

## Q&A Preparation (3 minutes)

### Likely questions and suggested answers:

**Q: Is the AI real or mocked?**
> Completely real. We use Alibaba Cloud DashScope — Qwen-VL-OCR for text extraction and Qwen-Plus for classification and summarization. The only mock is VNeID authentication, which requires government approval to connect.

**Q: How do you handle security classification?**
> Four levels: Unclassified, Confidential, Secret, Top Secret. Enforced at three layers — application-level ABAC checks, PostgreSQL Row-Level Security policies, and a complete audit log. A level-1 officer cannot see Secret documents even through search.

**Q: What happens when the AI is wrong?**
> AI is always advisory. Officers confirm or override every classification. We track override rates to continuously improve the prompts. The human is always in control.

**Q: Does it handle Vietnamese text and diacritics?**
> Yes. We built a custom unaccent function for PostgreSQL so searching "nguyen" finds "Nguyễn". The OCR model is specifically chosen for Vietnamese language quality.

**Q: Can it scale?**
> Current architecture handles up to 100K documents on PostgreSQL full-text search. Beyond that, we can migrate to Elasticsearch without changing the API. The search service is a clean abstraction.

**Q: What about offline use?**
> Currently requires internet connectivity for both the API and AI processing. Offline document capture with deferred processing is a feasible future enhancement.

**Q: How long did this take to build?**
> Six feature sprints, built incrementally. Each capability is modular and can be enhanced independently.

**Q: Can it be deployed on-premises?**
> Yes. Everything runs in Docker containers with PostgreSQL. The only cloud dependency is DashScope for AI models — which could be replaced with self-hosted Qwen models for air-gapped environments.
