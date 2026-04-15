# Feature Specification: Tìm Kiếm & Tóm Tắt Tài Liệu AI (Search & AI Summarization)

**Feature Branch**: `005-search-and-summarization`  
**Created**: 2026-04-15  
**Status**: Draft  
**Input**: User description: "Gap analysis against Innovation Challenge — address missing Centralized Indexing (document retrieval) and AI Summarization (key information extraction) capabilities"

## Context: Innovation Challenge Gap Analysis

The platform was evaluated against the **Innovation Challenge** defined in the "Desired Outcomes & Innovation Challenge — Future State Vision" framework for AI-Assisted Document Intelligence. Of the 8 Future-State Capabilities:

| # | Capability | Status |
|---|---|---|
| 1 | Automated Ingestion | ✅ Implemented |
| 2 | Intelligent Classification | ✅ Implemented |
| 3 | Auto-Routing | ✅ Implemented |
| 4 | **AI Summarization** | ⚠️ Partial — template field extraction exists, but no document/dossier summarization |
| 5 | Cross-Dept Collaboration | ✅ Implemented |
| 6 | Real-time Tracking | ✅ Implemented |
| 7 | **Centralized Indexing** | ❌ Missing — no full-text search or document retrieval |
| 8 | Access Control | ✅ Implemented |

This feature addresses the **two remaining gaps**: Centralized Indexing (capability #7) and AI Summarization (capability #4).

## Out of Scope

- Citizen-facing search (citizen_app không thay đổi trong feature này)
- Migration sang Elasticsearch (PostgreSQL FTS đủ cho quy mô demo <100K documents)
- Real-time push (WebSocket/SSE) cho search results hoặc summary notifications
- Search history, saved searches, hoặc advanced boolean query syntax
- Pre-computed analytics aggregation (ad-hoc query đủ cho quy mô demo)

## Clarifications

### Session 2026-04-15

- Q: Search scope — cross-department hay chỉ own-department? → A: Cross-department — bất kỳ cán bộ nào đều search được toàn hệ thống, chỉ filter theo clearance level (phù hợp với yêu cầu "centralized indexing" của Innovation Challenge)
- Q: Vietnamese full-text search approach? → A: PostgreSQL `unaccent` extension + `pg_trgm` trigram index cho fuzzy matching; `simple` text search config. Đủ cho tiếng Việt tại quy mô demo.
- Q: Ranh giới out-of-scope rõ ràng? → A: Không bao gồm citizen search, Elasticsearch, SSE/WebSocket, saved searches, advanced query syntax
- Q: Xử lý khi AI API (dashscope) lỗi trong quá trình summarization? → A: Retry 3 lần với exponential backoff; nếu vẫn lỗi thì đặt `ai_summary = null` và ghi log — không block workflow progression
- Q: Backfill summary cho dữ liệu cũ đã có? → A: Cung cấp management command (Celery task) để backfill theo yêu cầu, không tự động chạy khi migration

---

## User Scenarios & Testing

### User Story 1 — Tìm Kiếm Hồ Sơ & Tài Liệu (Full-Text Search) (Priority: P1)

Cán bộ tại bất kỳ phòng ban nào cần tìm kiếm nhanh hồ sơ/tài liệu theo nội dung, tên công dân, số CCCD, mã tham chiếu, loại tài liệu, hoặc ngày nộp — mà không cần nhớ chính xác ID hay trạng thái. Hiện tại cán bộ chỉ lọc được theo status/priority trong queue của phòng minh, không thể search xuyên suốt toàn hệ thống.

**Why this priority**: Đây là gap lớn nhất (❌ Not Implemented) và ảnh hưởng trực tiếp đến hiệu quả làm việc hàng ngày. Nếu mỗi phòng ban xử lý 50+ hồ sơ/ngày, việc tìm lại hồ sơ theo nội dung OCR hoặc tên công dân là nhu cầu cơ bản.

**Independent Test**: Tạo 10+ submission với nội dung OCR khác nhau, gọi API search với từ khóa → kết quả trả về chính xác, sắp xếp theo relevance, và chỉ bao gồm tài liệu trong phạm vi clearance của cán bộ.

**Acceptance Scenarios**:

1. **Given** hệ thống có 100 submission đã OCR, **When** cán bộ search "Nguyễn Văn An", **Then** kết quả trả về tất cả submission có "Nguyễn Văn An" trong OCR text hoặc template_data, sắp xếp theo relevance
2. **Given** cán bộ có clearance level 1, **When** search trả về submission có security_classification = 2, **Then** submission đó bị lọc ra khỏi kết quả
3. **Given** cán bộ nhập mã tham chiếu "HS-20260415", **When** search, **Then** kết quả khớp chính xác dossier có reference_number đó
4. **Given** cán bộ search "giấy khai sinh" kết hợp filter status="completed", **When** thực hiện, **Then** kết quả chỉ bao gồm submission đã completed và có nội dung liên quan đến giấy khai sinh
5. **Given** không có kết quả khớp, **When** search "xyzabc123", **Then** hiển thị thông báo "Không tìm thấy kết quả" với gợi ý mở rộng tìm kiếm

---

### User Story 2 — Tóm Tắt Tài Liệu AI (Document Summarization) (Priority: P1)

Khi cán bộ mở review một tài liệu trong queue, họ thấy ngay tóm tắt 2-3 câu do AI tạo ở đầu trang — thay vì phải đọc toàn bộ nội dung OCR. Tóm tắt giúp cán bộ nhanh chóng hiểu nội dung chính, ai nộp, loại giấy tờ gì, điểm cần chú ý.

**Why this priority**: Ngang hàng P1 với search vì giải quyết gap còn lại trong Innovation Challenge. Mỗi cán bộ phải review 20+ hồ sơ mỗi ngày — tiết kiệm 1-2 phút/hồ sơ tạo ra hiệu quả lớn.

**Independent Test**: Tạo submission có OCR text dạng "Tờ khai đăng ký khai sinh cho Nguyễn Văn An, sinh ngày 15/03/2026...", gọi API tóm tắt → nhận được tóm tắt ngắn gọn bằng tiếng Việt; kiểm tra tóm tắt xuất hiện trong review endpoint.

**Acceptance Scenarios**:

1. **Given** submission có OCR text từ giấy khai sinh, **When** AI tóm tắt được trigger (sau classification), **Then** `submission.ai_summary` chứa tóm tắt 2-3 câu bằng tiếng Việt nêu đúng loại tài liệu, tên người liên quan, và thông tin chính
2. **Given** dossier có 3 tài liệu (tờ khai + giấy chứng sinh + CCCD), **When** dossier được submit, **Then** `dossier.ai_summary` chứa tóm tắt tổng hợp nêu mục đích hồ sơ và danh sách tài liệu đính kèm
3. **Given** OCR text rỗng hoặc chất lượng thấp (confidence < 0.3), **When** AI tóm tắt chạy, **Then** hệ thống bỏ qua và đặt `ai_summary = null` thay vì sinh ra tóm tắt sai
4. **Given** submission đã có tóm tắt, **When** cán bộ sửa OCR text và lưu, **Then** tóm tắt được tạo lại tự động

---

### User Story 3 — Tóm Tắt Hồ Sơ Tổng Hợp cho Hàng Đợi (Queue Summary Preview) (Priority: P2)

Trong màn hình hàng đợi phòng ban, mỗi mục hiển thị tóm tắt ngắn 1 câu bên dưới tiêu đề — giúp cán bộ scan nhanh danh sách mà không cần mở từng hồ sơ.

**Why this priority**: Giá trị lớn nhưng phụ thuộc vào US2 (cần AI summary sẵn có). Nâng cao trải nghiệm sử dụng hàng ngày cho cán bộ.

**Independent Test**: Gọi API department queue → response bao gồm trường `summary_preview` (tóm tắt ngắn 1 câu hoặc null).

**Acceptance Scenarios**:

1. **Given** department queue có 5 submission đã được AI tóm tắt, **When** cán bộ mở queue, **Then** mỗi mục hiển thị dòng tóm tắt ngắn (tối đa 100 ký tự) bên dưới tiêu đề
2. **Given** submission chưa có tóm tắt (đang xử lý hoặc lỗi), **When** hiển thị queue, **Then** mục đó hiển thị "Đang tạo tóm tắt..." hoặc bỏ trống dòng tóm tắt

---

### User Story 4 — Trích Xuất Thực Thể Chính (Key Entity Extraction) (Priority: P2)

Ngoài tóm tắt, hệ thống tự động trích xuất các thực thể chính từ tài liệu: tên người, ngày tháng, số CCCD, địa chỉ, số tiền — và hiển thị dưới dạng metadata có cấu trúc. Các thực thể này cũng được index để phục vụ tìm kiếm.

**Why this priority**: Bổ sung giá trị cho cả search (tìm theo entity) và review (hiểu nhanh nội dung). Phụ thuộc vào US1 (search infrastructure) và US2 (AI pipeline).

**Independent Test**: Submission có OCR text chứa "Nguyễn Văn An, CCCD 012345678901, sinh 15/03/1990" → trả về entities: `{persons: ["Nguyễn Văn An"], ids: ["012345678901"], dates: ["15/03/1990"]}`.

**Acceptance Scenarios**:

1. **Given** submission có OCR text chứa tên người và số CCCD, **When** entity extraction chạy, **Then** `template_data["_entities"]` chứa danh sách entities theo loại (person, id_number, date, address, amount)
2. **Given** search query "012345678901", **When** tìm kiếm, **Then** kết quả bao gồm submission có CCCD đó trong entities
3. **Given** OCR text không chứa entity nhận dạng được, **When** extraction chạy, **Then** `_entities = {}` (dictionary rỗng, không lỗi)

---

### User Story 5 — SLA Analytics Dashboard (Priority: P3)

Lãnh đạo cần dashboard hiển thị thống kê xử lý: thời gian trung bình theo phòng ban, tỉ lệ trễ hạn, số lượng pending, top bottleneck. Giúp quản lý quyết định phân bổ nhân sự.

**Why this priority**: Giá trị cho management nhưng không phải gap trong Innovation Challenge. Sử dụng data đã tồn tại (workflow steps, completed_at, expected_complete_by).

**Independent Test**: Gọi API analytics → nhận số liệu thống kê aggregate, không expose dữ liệu cá nhân công dân.

**Acceptance Scenarios**:

1. **Given** hệ thống có 100+ workflow steps completed, **When** lãnh đạo gọi dashboard API, **Then** response chứa avg processing time, delay rate, pending count per department
2. **Given** cán bộ không có role "manager" hoặc "admin", **When** truy cập dashboard API, **Then** trả về 403 Forbidden

---

### Edge Cases

- Search query quá ngắn (< 2 ký tự): trả về lỗi yêu cầu query dài hơn
- Search query chứa ký tự đặc biệt hoặc SQL injection attempt: sanitize input, chỉ cho phép alphanumeric + Vietnamese + dấu cách
- OCR text quá dài (> 50,000 ký tự): truncate trước khi gửi đến AI summarization (giới hạn context window)
- Nhiều submission cùng lúc trigger summarization: Celery queue xử lý tuần tự, không overwhelm AI API
- Summary sinh ra nội dung sai fact (AI hallucination): tóm tắt đi kèm label "AI tạo — cần kiểm tra" và cán bộ có thể dismiss/flag
- AI API (dashscope) không khả dụng: retry 3 lần với exponential backoff, nếu vẫn lỗi thì `ai_summary = null` và log error — workflow progression không bị block
- Full-text index chưa build xong cho dữ liệu cũ: migration cần backfill index, có thể mất vài phút trên dữ liệu lớn
- Search trả về quá nhiều kết quả: giới hạn 50 kết quả/trang, phân trang cursor-based

---

## Requirements

### Functional Requirements

**Search (US1)**

- **FR-001**: System MUST cung cấp endpoint `GET /v1/staff/search` cho phép tìm kiếm cross-department xuyên suốt submissions, dossiers, và scanned pages (không giới hạn theo phòng ban của cán bộ)
- **FR-002**: Search MUST hỗ trợ tìm kiếm full-text trong OCR text (`ScannedPage.ocr_raw_text`, `ocr_corrected_text`), citizen name, reference number — sử dụng PostgreSQL `tsvector`/GIN index kết hợp `pg_trgm` trigram cho fuzzy matching. (Template data values are derived from OCR text and are covered by OCR full-text search.)
- **FR-003**: Search MUST filter kết quả theo clearance level của cán bộ (cross-department access controlled solely by `security_classification` vs staff `clearance_level`) — không trả về tài liệu có `security_classification` cao hơn clearance
- **FR-004**: Search MUST hỗ trợ filters kết hợp: `status`, `document_type_code`, `case_type_code`, `date_from`, `date_to`, `department_id`
- **FR-005**: Search results MUST sắp xếp theo relevance (full-text search ranking) với option sort by `submitted_at`, `updated_at`
- **FR-006**: Search results MUST trả về paginated (cursor hoặc offset-based), tối đa 50 items/page
- **FR-007**: System MUST reject queries < 2 ký tự với error message rõ ràng

**AI Summarization (US2)**

- **FR-008**: System MUST tạo tóm tắt AI 2-3 câu bằng tiếng Việt cho mỗi submission sau khi classification hoàn thành
- **FR-009**: System MUST tạo tóm tắt tổng hợp cho dossier khi dossier được submit (tổng hợp từ tất cả document summaries)
- **FR-010**: System MUST bỏ qua summarization nếu combined OCR text rỗng hoặc OCR confidence trung bình < 0.3
- **FR-011**: AI summary MUST được lưu trong field mới trên Submission (`ai_summary`) và Dossier (`ai_summary`)
- **FR-012**: System MUST tự động tạo lại summary khi OCR text được cán bộ sửa
- **FR-013**: Summary response MUST đi kèm label cho biết đây là nội dung AI tạo

**Queue Preview (US3)**

- **FR-014**: Department queue API response MUST bao gồm `summary_preview` (tối đa 100 ký tự, cắt từ `ai_summary`)

**Entity Extraction (US4)**

- **FR-015**: System MUST trích xuất entities sau summarization: person names, ID numbers (CCCD/CMND), dates, addresses, monetary amounts
- **FR-016**: Entities MUST lưu trong `template_data["_entities"]` dưới dạng `{"persons": [], "id_numbers": [], "dates": [], "addresses": [], "amounts": []}`
- **FR-017**: Extracted entities MUST được index để hỗ trợ search

**Analytics (US5)**

- **FR-018**: System MUST cung cấp endpoint `GET /v1/staff/analytics/sla` trả về aggregate statistics per department
- **FR-019**: Analytics MUST chỉ accessible cho staff có role "manager" hoặc "admin"
- **FR-020**: Analytics MUST KHÔNG expose thông tin cá nhân công dân

### Key Entities

- **Search Index**: Dữ liệu full-text search, aggregated từ OCR text + template data + citizen name + reference number. Clearance-filtered tại query time.
- **AI Summary**: Tóm tắt 2-3 câu do AI tạo, gắn vào Submission và Dossier. Được tạo async qua Celery sau classification/dossier submit.
- **Extracted Entities**: Metadata có cấu trúc (tên, số ID, ngày, địa chỉ, số tiền) trích xuất từ OCR text, lưu trong JSONB, indexed cho search.
- **SLA Metrics**: Aggregate statistics tính toán ad-hoc từ workflow step timestamps, không lưu pre-computed.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Cán bộ tìm thấy tài liệu theo nội dung OCR trong < 3 giây (search response time p95)
- **SC-002**: Search accuracy: 90%+ kết quả đầu tiên là kết quả mong muốn khi tìm theo tên công dân hoặc số CCCD
- **SC-003**: AI summary coverage: 95%+ submission được classified có `ai_summary` non-null
- **SC-004**: Thời gian review trung bình giảm 30% sau khi có AI summary (đo bằng thời gian từ open review đến decision)
- **SC-005**: 100% search results tuân thủ clearance filtering — không bao giờ trả về tài liệu vượt clearance level
- **SC-006**: Cán bộ đánh giá AI summary "hữu ích" hoặc "chính xác" > 80% trường hợp

---

## Assumptions

- PostgreSQL full-text search (`tsvector` + GIN index) đủ hiệu năng cho quy mô demo (< 100K documents). Nếu tăng quy mô, có thể chuyển sang Elasticsearch sau.
- AI summarization sử dụng `qwen3.5-flash` (đã có trong hệ thống) — không cần model mới.
- Entity extraction sử dụng prompt-based approach qua cùng model `qwen3.5-flash`, không cần NER model chuyên biệt.
- Vietnamese full-text search cần cấu hình `unaccent` extension hoặc custom text search configuration cho tiếng Việt (xử lý dấu).
- Summarization task chạy async qua Celery, chain sau classification task — không ảnh hưởng latency API.
- SLA analytics tính ad-hoc từ query, không cần pre-aggregation cho quy mô demo.
- Flutter app changes chỉ ảnh hưởng `staff_app` — `citizen_app` không cần thay đổi cho feature này.
- Backfill AI summary cho dữ liệu cũ (submissions đã classified trước feature này) được thực hiện qua management command tùy chọn, không tự động chạy khi migration.
- Vietnamese full-text search sử dụng `unaccent` extension + `pg_trgm` trigram index. `simple` text search configuration (không dùng language-specific stemmer vì PostgreSQL không có built-in Vietnamese stemmer).
