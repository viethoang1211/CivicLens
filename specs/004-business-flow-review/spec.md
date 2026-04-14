# Feature Specification: Business Flow Review & Recommendations

**Feature Branch**: `004-business-flow-review`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "Review toàn bộ business flow, tình trạng data, template, etc và đưa ra recommendation. Bỏ qua security concerns (demo repo), nhưng implement đàng hoàng about logic classification, OCR. Data pháp luật phải chuẩn xác, chỉ user data và data không quan trọng là mock được."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hoàn thiện Classification Logic & OCR Pipeline (Priority: P1)

Staff reception quét tài liệu, hệ thống AI phải nhận diện chính xác loại giấy tờ và trích xuất dữ liệu có cấu trúc với độ chính xác cao cho tài liệu hành chính Việt Nam.

**Why this priority**: Classification & OCR là nền tảng của toàn bộ hệ thống. Nếu AI nhận dạng sai loại giấy tờ hoặc trích xuất sai dữ liệu, toàn bộ workflow phía sau đều bị ảnh hưởng — sai routing, sai template, sai thông tin phục vụ công dân.

**Independent Test**: Có thể test độc lập bằng cách chạy OCR + classification pipeline trên bộ ảnh mẫu (test images) của 15+ loại giấy tờ đã seed, so sánh kết quả với ground truth.

**Acceptance Scenarios**:

1. **Given** ảnh CCCD rõ nét được upload, **When** OCR pipeline chạy xong, **Then** trích xuất chính xác các trường: số CCCD (12 chữ số), họ tên, ngày sinh, giới tính, quê quán, nơi thường trú, ngày cấp, ngày hết hạn
2. **Given** ảnh Giấy chứng sinh (Giấy chứng sinh y tế), **When** classification chạy, **Then** hệ thống nhận diện đúng mã `BIRTH_CERTIFICATE_MEDICAL` với confidence ≥ 0.7
3. **Given** ảnh tài liệu mờ (quality score < 0.5), **When** OCR primary model trả kết quả confidence thấp, **Then** hệ thống tự động chuyển sang fallback model (qwen3-vl-plus) và lưu kết quả từ model tốt hơn
4. **Given** classification confidence < 0.7, **When** kết quả trả về cho staff, **Then** hiển thị danh sách alternatives kèm confidence để staff chọn thủ công
5. **Given** OCR pipeline hoàn thành trên tất cả pages của submission, **When** classification chạy, **Then** template_data được fill với giá trị chính xác theo template_schema của document type tương ứng

---

### User Story 2 - Case-Based Dossier Flow (Guided Capture) Hoàn chỉnh (Priority: P1)

Staff tạo hồ sơ mới theo thủ tục hành chính (case type), hệ thống hướng dẫn từng bước quét tài liệu theo yêu cầu, validate bằng AI, và nộp hồ sơ hoàn chỉnh.

**Why this priority**: Đây là workflow chính của hệ thống (Mode B: Guided Document Capture). Quick Scan (Mode A) chỉ là fallback cho tài liệu đơn lẻ. Phần lớn công dân đến UBND là để làm thủ tục hành chính có cấu trúc.

**Independent Test**: Có thể test end-to-end bằng cách tạo dossier cho case type "Đăng ký khai sinh" (BIRTH_REG), upload tài liệu cho từng requirement group, kiểm tra AI validation, submit, và verify workflow được tạo.

**Acceptance Scenarios**:

1. **Given** staff chọn case type "Đăng ký khai sinh", **When** dossier được tạo, **Then** hệ thống tạo requirement_snapshot chính xác 4 groups (tờ khai, giấy chứng sinh, CCCD, giấy kết hôn optional)
2. **Given** staff quét CCCD cho group 3 (CCCD/CMND cha hoặc mẹ), **When** ảnh upload xong, **Then** AI slot validation xác nhận match/mismatch trong ≤ 30 giây
3. **Given** tất cả mandatory groups đã được fulfill, **When** staff nhấn submit, **Then** reference number được tạo (HS-YYYYMMDD-NNNNN), workflow tạo theo routing steps, citizen nhận notification
4. **Given** staff override AI mismatch warning, **When** tài liệu được chấp nhận, **Then** `ai_match_overridden = true` được ghi nhận cho audit
5. **Given** dossier đang ở trạng thái draft, **When** staff quay lại từ "Hồ sơ đang xử lý", **Then** dossier resume đúng trạng thái với progress indicator cho mỗi group

---

### User Story 3 - Seed Data Pháp Luật Chuẩn Xác & Đầy Đủ (Priority: P1)

Hệ thống phải có dữ liệu gốc (seed data) chuẩn xác về mặt pháp luật Việt Nam cho tất cả loại giấy tờ, thủ tục hành chính, template schema, classification prompts, và routing rules.

**Why this priority**: Dữ liệu pháp luật không thể mock. Sai căn cứ luật, sai mẫu biểu, sai thời hạn lưu trữ đều không chấp nhận được — ngay cả trong demo. Đây là nền tảng cho AI classification, template filling, và toàn bộ business logic.

**Independent Test**: So sánh seed data với văn bản pháp luật gốc (Luật Hộ tịch 2014, Luật Cư trú 2020, NĐ 01/2021/NĐ-CP, etc.) để verify căn cứ pháp lý, trường dữ liệu, thời hạn lưu trữ.

**Acceptance Scenarios**:

1. **Given** 15+ document types đã seed, **When** so sánh với văn bản luật tham chiếu, **Then** mỗi document type có: tên chính xác, mã code nhất quán, legal reference đúng, retention policy theo Luật Lưu trữ
2. **Given** 6 case types đã seed, **When** kiểm tra requirement groups, **Then** mỗi thủ tục có danh sách giấy tờ đúng theo quy định (mandatory/optional đúng)
3. **Given** template_schema cho mỗi document type, **When** so sánh với mẫu biểu chính thức, **Then** các trường bắt buộc đều có mặt, tên trường thống nhất với biểu mẫu (tiếng Việt, snake_case)
4. **Given** classification_prompt cho mỗi document type, **When** AI nhận ảnh tương ứng, **Then** prompt mô tả đúng đặc điểm nhận dạng vật lý (kích thước, logo, dấu, màu sắc)

---

### User Story 4 - Citizen Tracking & Workflow Transparency (Priority: P2)

Công dân có thể theo dõi tình trạng hồ sơ qua app, tra cứu bằng mã tham chiếu, và nhận thông báo khi có thay đổi.

**Why this priority**: Tính minh bạch là yêu cầu bắt buộc trong thủ tục hành chính. Tuy nhiên, đây là luồng đọc (read-only), logic đơn giản hơn intake + classification, nên đặt P2.

**Independent Test**: Tạo dossier hoàn chỉnh, submit, advance workflow qua các bước, kiểm tra citizen app hiển thị đúng trạng thái, timeline, và reference number lookup.

**Acceptance Scenarios**:

1. **Given** dossier đã submit với reference number HS-20260414-00001, **When** citizen tra cứu bằng reference number (không cần đăng nhập), **Then** thấy trạng thái, case type, tiến độ (không lộ UUID)
2. **Given** workflow step chuyển sang department mới, **When** step advance, **Then** citizen nhận push notification bằng tiếng Việt
3. **Given** active workflow step quá deadline (expected_complete_by), **When** delay detection chạy, **Then** step được đánh dấu `delayed`, citizen được thông báo

---

### User Story 5 - Department Review & Workflow Advancement (Priority: P2)

Cán bộ các phòng ban xem xét hồ sơ theo thứ tự, phê duyệt/từ chối, và hệ thống tự động chuyển bước tiếp theo.

**Why this priority**: Review workflow đã implement cơ bản trong Feature 001. Cần đảm bảo hoạt động mượt mà cho cả Legacy (submission) lẫn Case-based (dossier) mode.

**Independent Test**: Tạo submission + dossier, route, review approve → verify next step activated, review reject → verify submission/dossier rejected + citizen notified.

**Acceptance Scenarios**:

1. **Given** workflow step đang active cho department JUDICIAL, **When** reviewer approve, **Then** next step activated, previous step marked completed, citizen notified
2. **Given** reviewer reject tại bất kỳ step nào, **When** rejection recorded, **Then** submission/dossier status = rejected, citizen nhận notification kèm lý do
3. **Given** reviewer request info, **When** request recorded, **Then** step pause, citizen nhận thông báo cần bổ sung, annotation visible cho citizen

---

### User Story 6 - Mock Data Cho User & Non-Critical Data (Priority: P3)

Hệ thống cần mock data hợp lý cho demo: citizens, staff, notifications. Mock data phải đủ realistic để demo nhưng rõ ràng không phải dữ liệu thật.

**Why this priority**: Mock data chỉ phục vụ demo, không ảnh hưởng business logic. Tuy nhiên cần đủ data để demo các flow end-to-end.

**Independent Test**: Chạy seed, verify mock citizens/staff tồn tại với dữ liệu hợp lý, verify có thể demo full flow từ scan → classify → route → review → complete.

**Acceptance Scenarios**:

1. **Given** seed data chạy, **When** kiểm tra mock citizens, **Then** có ≥ 3 citizens với tên tiếng Việt realistic, số CCCD đúng format (12 chữ số)
2. **Given** seed data chạy, **When** kiểm tra mock staff, **Then** có staff cho mỗi department với clearance level phù hợp
3. **Given** mock data loaded, **When** chạy full demo flow (scan → classify → route → review → complete), **Then** flow hoàn thành end-to-end không lỗi

---

### Edge Cases

- Khi classification trả về confidence thấp cho tất cả document types (< 0.3), hệ thống phải yêu cầu staff classify thủ công thay vì chọn classification sai
- Khi OCR trả về text rỗng (ảnh trắng, ảnh không phải tài liệu), hệ thống ghi nhận lỗi và cho phép staff thử lại
- Khi case type có requirement group dùng OR-logic (multiple slots), staff chỉ cần fulfill 1 slot — completeness check phải xử lý đúng
- Khi 2 dossier được submit cùng ngày cùng lúc, reference number phải unique (concurrent generation safe)
- Khi dossier đang ở draft, case type bị admin sửa, requirement_snapshot đã freeze phải không bị ảnh hưởng
- Khi fallback OCR model cũng trả confidence thấp, hệ thống vẫn lưu kết quả và để staff review/correct

## Requirements *(mandatory)*

### Functional Requirements

#### Classification & OCR Logic

- **FR-001**: Classification pipeline PHẢI sử dụng classification_confidence_threshold (config: 0.7) để quyết định hiển thị kết quả tự tin hay danh sách alternatives cho staff
- **FR-002**: OCR pipeline PHẢI tự động switch sang fallback model khi confidence < 0.6, và lưu kết quả từ model nào cho kết quả tốt hơn
- **FR-003**: Template filling PHẢI validate output theo JSON Schema của document type (type checking, required fields), không chỉ passthrough
- **FR-004**: Classification prompt cho mỗi document type PHẢI mô tả đặc điểm nhận dạng vật lý bằng tiếng Việt (kích thước, logo, dấu, format) — đây là input chính để AI phân biệt
- **FR-005**: AI slot validation (guided capture) PHẢI trả kết quả binary (match/mismatch) với confidence và reason, không phải open-ended classification
- **FR-006**: OCR confidence score PHẢI được parse từ model response thực tế, không hardcode 0.85

#### Data Quality & Legal Accuracy

- **FR-007**: Template schema cho mỗi document type PHẢI bao gồm ĐẦY ĐỦ các trường theo mẫu biểu chính thức của văn bản pháp luật tương ứng
- **FR-008**: Classification prompt PHẢI phân biệt được các loại giấy tờ tương tự (ví dụ: Tờ khai khai sinh vs Giấy khai sinh đã cấp)
- **FR-009**: Retention policy PHẢI tuân theo Luật Lưu trữ 2011 và quy định lưu trữ hồ sơ hộ tịch (NĐ 123/2015)
- **FR-010**: Routing rules PHẢI phản ánh đúng quy trình thực tế: thủ tục tư pháp qua Phòng Tư pháp, cư trú qua Công an, kinh doanh qua Phòng TC-KH
- **FR-011**: Tất cả reference pháp luật trong seed data PHẢI chính xác (đúng số Luật/NĐ/TT, đúng Điều khoản, đúng năm ban hành)
- **FR-012**: Case type requirement groups PHẢI phản ánh đúng hồ sơ pháp lý yêu cầu (mandatory vs optional đúng theo quy định)

#### Workflow & Business Logic

- **FR-013**: Dual-owner pattern (submission_id XOR dossier_id) PHẢI được enforce qua CHECK constraint trên WorkflowStep và ScannedPage
- **FR-014**: Requirement snapshot PHẢI freeze toàn bộ case type requirements tại thời điểm dossier creation, immune với admin changes sau đó
- **FR-015**: Completeness check PHẢI xử lý OR-logic đúng: group fulfilled khi BẤT KỲ slot nào có DossierDocument tương ứng
- **FR-016**: Reference number generation PHẢI đảm bảo unique trong ngày (HS-YYYYMMDD-NNNNN format), safe với concurrent requests
- **FR-017**: Workflow advancement PHẢI xử lý đúng 3 outcomes: approve (next step), reject (terminate), needs_info (pause)
- **FR-018**: Delay detection PHẢI chạy định kỳ, so sánh NOW() với expected_complete_by cho mỗi active step

#### Mock Data

- **FR-019**: Mock citizens PHẢI có tên tiếng Việt realistic, số CCCD đúng format 12 chữ số, nhưng KHÔNG dùng số CCCD thật
- **FR-020**: Mock staff PHẢI cover mỗi department với ≥ 1 member, clearance level phù hợp với min_clearance_level của department
- **FR-021**: Image quality assessment có thể mock bằng size-based heuristic cho demo, nhưng PHẢI có interface rõ ràng để swap implementation sau

#### Citizen-Facing

- **FR-022**: Public reference number lookup PHẢI chỉ trả thông tin an toàn (status, case type, progress) — không lộ IDs nội bộ
- **FR-023**: Notifications PHẢI bằng tiếng Việt, mapping đúng event → message template
- **FR-024**: Citizen tracking view PHẢI hiển thị visual timeline với trạng thái từng step (completed/active/pending/delayed)

### Key Entities

- **DocumentType**: Loại giấy tờ hành chính — có template_schema (JSON Schema), classification_prompt, retention policy, legal reference
- **CaseType**: Thủ tục hành chính — nhóm các document requirements thành groups với OR-logic, có routing steps
- **DocumentRequirementGroup/Slot**: Hai tầng requirement hierarchy — Group (mandatory/optional) chứa Slots (OR-logic alternatives)
- **Submission**: Hồ sơ đơn lẻ (Quick Scan mode) — qua OCR → Classification → Routing pipeline
- **Dossier**: Hồ sơ case-based (Guided Capture mode) — chứa nhiều DossierDocuments, freeze requirements, tạo workflow từ case type routing
- **WorkflowStep**: Bước xử lý tại phòng ban — dual-owner (submission XOR dossier), sequential processing
- **ScannedPage**: Trang ảnh quét — dual-owner, mang OCR text + confidence
- **StepAnnotation**: Nhận xét/quyết định trên workflow step — approve/reject/needs_info/consultation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AI classification đạt accuracy ≥ 80% trên bộ test 15+ document types khi chạy với ảnh chất lượng trung bình (resolution ≥ 720p, không quá mờ)
- **SC-002**: Template filling extract đúng ≥ 70% trường dữ liệu trên tài liệu in rõ nét (so sánh với ground truth)
- **SC-003**: 100% legal references trong seed data khớp với văn bản pháp luật gốc (Luật, NĐ, TT đúng số, đúng Điều, đúng năm)
- **SC-004**: Staff có thể tạo dossier, quét tài liệu cho tất cả requirement groups, submit, và nhận reference number trong ≤ 10 phút cho case type "Đăng ký khai sinh"
- **SC-005**: Citizen có thể tra cứu hồ sơ bằng reference number và thấy progress chính xác trong ≤ 5 giây
- **SC-006**: Full workflow cycle (scan → classify → route → review → complete) hoàn thành end-to-end cho cả Legacy và Case-based mode
- **SC-007**: Delay detection phát hiện chính xác 100% steps quá hạn và trigger notification
- **SC-008**: OR-logic completeness check xử lý đúng trong mọi trường hợp: 1 slot fulfilled trong group multi-slot

## Assumptions

- **Demo scope**: Bỏ qua security hardening (JWT secret rotation, rate limiting, HTTPS enforcement) — repo là demo. Tuy nhiên ABAC clearance check VẪN hoạt động vì nó ảnh hưởng business logic
- **AI models**: Sử dụng base Qwen models (qwen-vl-ocr, qwen3.5-flash, qwen3-vl-plus) không fine-tune. Accuracy có thể thấp hơn production, nhưng logic pipeline phải đúng
- **Storage**: Dùng local storage cho demo (storage_backend = "local"), không cần Alibaba Cloud OSS thật
- **Notifications**: Push notification qua EMAS có thể mock (log ra console), nhưng database notification record phải được tạo đúng
- **Concurrent users**: Demo với ≤ 10 concurrent users, reference number generation dùng COUNT query là đủ
- **VNeID**: Dùng mock VNeID server (pre-loaded 3 citizens), không cần kết nối VNeID thật
- **Celery**: Dùng Redis làm broker thay RocketMQ cho đơn giản lúc demo

---

## Appendix: Detailed Recommendations

Phần này tổng hợp toàn bộ findings từ review codebase và đưa ra recommendations cụ thể.

### A. Classification & OCR Logic — CRITICAL FIXES

| # | Issue | Current State | Recommendation | Impact |
|---|-------|--------------|----------------|--------|
| A1 | OCR confidence hardcoded | `ocr_confidence = 0.85` hardcoded trong ocr_worker.py | Parse actual confidence từ dashscope API response. Nếu API không trả confidence riêng, tính từ tỷ lệ recognized text vs expected fields | Ảnh hưởng fallback logic — model không bao giờ switch sang fallback |
| A2 | Classification threshold không được dùng | `classification_confidence_threshold: 0.7` trong config nhưng code không check | Thêm logic: nếu `confidence < threshold` → set `classification_method = "manual_required"`, trả alternatives cho staff | Low-confidence classifications slip through |
| A3 | Template validation quá basic | `template_service.validate_template_data()` chỉ passthrough | Validate type (string/number/date), check required fields theo schema, sanitize values | Dữ liệu trích xuất có thể sai type hoặc thiếu field |
| A4 | Image quality chỉ dựa vào file size | `quality_service.assess_image_quality()` dùng size-based heuristic | Chấp nhận cho demo, nhưng thêm TODO rõ ràng + interface cho OpenCV/PIL implementation sau | Ảnh mờ/nghiêng không bị reject |

### B. Seed Data & Legal Accuracy — MOSTLY GOOD, NEEDS REFINEMENT

| # | Issue | Current State | Recommendation | Impact |
|---|-------|--------------|----------------|--------|
| B1 | Document types comprehensive | 15+ types, legal references correct | Verify: `RESIDENCE_CONFIRM` và `RESIDENCE_PROOF` — đây không phải mẫu biểu chính thức, cần xác nhận có tồn tại trong hệ thống pháp luật không | Có thể tạo document type không có thực |
| B2 | Template schema detailed | Các trường khớp mẫu biểu BTP, BYT, BCA | Cross-check `COMPANY_REG_FORM`, `COMPANY_CHARTER`, `MEMBER_LIST` — đây là document types riêng nhưng template schema có thể chưa được seed | Schema có thể empty cho một số types |
| B3 | Classification prompts bằng tiếng Việt | Mô tả đặc điểm vật lý (kích thước, màu, logo) | Thêm đặc điểm phân biệt giữa tờ khai (form trống do công dân điền) vs giấy chứng nhận (do cơ quan cấp, có dấu đỏ) | AI có thể nhầm form vs certificate |
| B4 | Routing rules đúng quy trình | Tư pháp qua JUDICIAL, cư trú qua POLICE, KD qua FINANCE | OK — đúng thực tế. Khiếu nại qua ADMIN→LEADERSHIP cũng hợp lý | Không cần sửa |
| B5 | Case types 6 nhưng thiếu một số thủ tục phổ biến | Có BIRTH_REG, MARITAL_STATUS, RESIDENCE, BIZ, COMPANY, COMPLAINT | Xem xét thêm: Cấp lại bản sao giấy khai sinh (Đ.63 Luật Hộ tịch), Đăng ký khai tử (Đ.32), Chứng thực bản sao (NĐ 23/2015) | Demo coverage |

### C. Workflow & Business Logic — SOLID, MINOR FIXES

| # | Issue | Current State | Recommendation | Impact |
|---|-------|--------------|----------------|--------|
| C1 | Dual-owner pattern enforced | CHECK constraint: exactly one of (submission_id, dossier_id) non-null | OK — đúng. Verify constraint tồn tại trong Alembic migrations | DB integrity |
| C2 | Requirement snapshot works | `build_requirement_snapshot()` freeze full case type structure | OK — implementation tốt. Verify snapshot includes `classification_prompt` cho AI slot validation | AI validation sau submit cần prompt |
| C3 | Completeness check OR-logic | `check_completeness()` kiểm tra ANY slot in group has document | Verify: test case group có 2 slots, fulfill 1, check returns complete. Test case mandatory group unfulfilled, check returns incomplete | Logic có thể sai edge case |
| C4 | Reference number concurrent safety | COUNT-based, OK cho < 1000/day | OK cho demo. Production cần SEQUENCE hoặc ADVISORY LOCK | Concurrent collision possible |
| C5 | Workflow advancement for dossier | `advance_workflow()` works for submission | Verify dossier-mode advancement sử dụng đúng `dossier_id` thay vì `submission_id`, và retention_expires_at tính từ CaseType.retention_years | Dossier workflow có thể bị stuck |

### D. Data — WHAT CAN BE MOCKED, WHAT CANNOT

| Category | Can Mock? | Notes |
|----------|-----------|-------|
| Citizen names, CCCD numbers | ✅ YES | Dùng tên tiếng Việt realistic (Phạm Văn Dũng, etc.), CCCD 12 chữ số nhưng fake |
| Staff members | ✅ YES | Tên + employee_id fake, nhưng department assignment phải hợp lý |
| AI model responses | ✅ YES (for testing) | Mock dashscope responses cho unit tests |
| Push notification delivery | ✅ YES | Log to console thay vì gọi EMAS |
| OSS storage | ✅ YES | Dùng local filesystem |
| VNeID OAuth | ✅ YES | Mock server đã có |
| Document type names/codes | ❌ NO | Phải đúng tên chính thức theo pháp luật VN |
| Template schema fields | ❌ NO | Phải khớp mẫu biểu BTP/BYT/BCA |
| Legal references (Luật/NĐ/TT) | ❌ NO | Phải chính xác: đúng số, đúng Điều, đúng năm |
| Retention policy | ❌ NO | Phải theo Luật Lưu trữ 2011 + NĐ chuyên ngành |
| Routing rules (dept flow) | ❌ NO | Phải phản ánh đúng quy trình thực tế |
| Case type requirements | ❌ NO | Danh sách hồ sơ phải đúng theo quy định |
| Classification prompts | ⚠️ PARTIAL | Mô tả vật lý phải đúng, nhưng wording có thể tùy chỉnh cho AI performance |

### E. Flutter Apps — STATUS ASSESSMENT

| Component | Status | Notes |
|-----------|--------|-------|
| Staff auth | ✅ Done | Login functional |
| Staff Quick Scan | ✅ Done | Scan → OCR → Classify flow |
| Staff Guided Capture UI | ⚠️ Not started | Feature 003 spec ready, backend ready, UI chưa có |
| Staff Review | ✅ Done | Approve/Reject/Request Info |
| Citizen VNeID Login | ✅ Done | Mock VNeID integration |
| Citizen Submission List | ✅ Done | Feature 001 |
| Citizen Dossier Tracking | ⚠️ Partial | Backend endpoints ready, UI may be incomplete |
| Citizen Reference Lookup | ⚠️ Partial | API exists, UI unknown |
| Shared Dart DTOs | ✅ Done | CaseType, Dossier, DossierTracking models |

### F. Prioritized Action Items

1. **[CRITICAL]** Fix OCR confidence hardcode → parse actual model response
2. **[CRITICAL]** Enforce classification_confidence_threshold in classification worker
3. **[HIGH]** Enhance template_service validation (type checking, required field validation)
4. **[HIGH]** Verify all document type template_schema fields are complete (especially COMPANY_* types)
5. **[HIGH]** Verify dossier workflow advancement path (advance_workflow with dossier_id)
6. **[MEDIUM]** Add distinguishing features in classification_prompt (form vs certificate)
7. **[MEDIUM]** Verify RESIDENCE_CONFIRM and RESIDENCE_PROOF as valid document types
8. **[MEDIUM]** Add more case types for demo coverage (cấp lại bản sao, khai tử, chứng thực)
9. **[LOW]** Image quality: document the interface clearly for future OpenCV implementation
10. **[LOW]** Add test images for each document type to verify classification pipeline
