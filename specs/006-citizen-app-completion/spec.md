# Feature Specification: Citizen App Completion

**Feature Branch**: `006-citizen-app-completion`  
**Created**: 2026-04-16  
**Status**: Draft  
**Input**: User description: "Hoàn thiện citizen app: màn hình 'Hồ sơ của tôi' hiển thị dossier gắn với CCCD, kết nối thông báo, và làm rõ flow quick scan → dossier"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Công dân xem danh sách hồ sơ của mình (Priority: P1)

Sau khi đăng nhập qua VNeID, công dân mở app và thấy ngay danh sách tất cả hồ sơ (dossier) mà nhân viên đã tạo cho họ, dựa trên CCCD. Mỗi hồ sơ hiển thị loại hồ sơ, trạng thái, ngày nộp, và tiến độ xử lý. Công dân không cần biết mã tham chiếu — chỉ cần đăng nhập là thấy.

**Why this priority**: Đây là tính năng cốt lõi bị thiếu. Hiện tại công dân phải biết mã tham chiếu (do nhân viên đưa offline) mới tra cứu được. Tính năng này biến citizen app từ "tra cứu thủ công" thành "ứng dụng cá nhân tự động".

**Independent Test**: Nhân viên tạo dossier cho CCCD X → Công dân đăng nhập bằng VNeID (CCCD X) → Thấy dossier trong danh sách.

**Acceptance Scenarios**:

1. **Given** công dân đã đăng nhập qua VNeID, **When** mở Home Screen, **Then** thấy mục "Hồ sơ của tôi" với badge hiển thị số hồ sơ đang xử lý
2. **Given** công dân nhấn vào "Hồ sơ của tôi", **When** danh sách tải xong, **Then** thấy tất cả dossier gắn với CCCD đó, hiển thị: loại hồ sơ, trạng thái (Nháp/Đang xử lý/Hoàn thành/Từ chối), ngày nộp, tiến độ (X/Y bước)
3. **Given** công dân đang xem danh sách, **When** kéo xuống để làm mới (pull-to-refresh), **Then** danh sách cập nhật từ server
4. **Given** công dân nhấn vào một hồ sơ, **When** mở chi tiết, **Then** thấy màn hình DossierStatusScreen với tracking workflow đầy đủ
5. **Given** công dân chưa có hồ sơ nào, **When** mở danh sách, **Then** thấy thông báo "Bạn chưa có hồ sơ nào. Vui lòng liên hệ bộ phận tiếp nhận."

---

### User Story 2 - Công dân lọc hồ sơ theo trạng thái (Priority: P1)

Công dân có thể lọc danh sách hồ sơ theo trạng thái (Tất cả / Đang xử lý / Hoàn thành / Từ chối) để nhanh chóng tìm hồ sơ quan tâm.

**Why this priority**: Khi có nhiều hồ sơ, lọc giúp tìm nhanh hồ sơ đang chờ hoặc đã hoàn thành. Cùng một màn hình với User Story 1.

**Independent Test**: Công dân có 3 hồ sơ (1 đang xử lý, 1 hoàn thành, 1 từ chối) → Nhấn filter "Đang xử lý" → Chỉ thấy 1 hồ sơ.

**Acceptance Scenarios**:

1. **Given** công dân có nhiều hồ sơ, **When** nhấn chip "Đang xử lý", **Then** chỉ hiển thị hồ sơ có status in_progress hoặc submitted
2. **Given** đang lọc "Hoàn thành", **When** nhấn "Tất cả", **Then** hiển thị lại toàn bộ hồ sơ

---

### User Story 3 - Công dân nhận và xem thông báo (Priority: P2)

Công dân nhận thông báo khi hồ sơ có cập nhật (chuyển bước, hoàn thành, từ chối, yêu cầu bổ sung). Thông báo hiển thị trong app với badge đếm chưa đọc.

**Why this priority**: Giúp công dân biết cập nhật mà không cần mở app kiểm tra liên tục. Backend API đã sẵn, chỉ cần kết nối UI.

**Independent Test**: Backend tạo notification cho citizen → Citizen mở app → Thấy badge thông báo trên Home → Nhấn vào thấy danh sách.

**Acceptance Scenarios**:

1. **Given** công dân đăng nhập, **When** có thông báo chưa đọc, **Then** icon chuông trên Home Screen hiển thị badge đỏ với số thông báo chưa đọc
2. **Given** nhấn vào icon chuông, **When** mở NotificationsScreen, **Then** thấy danh sách thông báo sắp xếp theo thời gian mới nhất, thông báo chưa đọc in đậm
3. **Given** nhấn vào 1 thông báo liên quan đến hồ sơ, **When** mở, **Then** đánh dấu đã đọc và điều hướng đến DossierStatusScreen tương ứng
4. **Given** có nhiều thông báo chưa đọc, **When** nhấn "Đánh dấu tất cả đã đọc", **Then** tất cả thông báo chuyển thành đã đọc

---

### User Story 4 - Home Screen hiển thị tổng quan sau khi đăng nhập (Priority: P2)

Sau khi đăng nhập, Home Screen hiển thị lời chào cá nhân ("Xin chào, [Tên]"), các mục menu chính (Hồ sơ của tôi, Tra cứu hồ sơ, Thông báo), và thông tin tổng quan (số hồ sơ đang xử lý).

**Why this priority**: Home screen hiện tại quá đơn giản (chỉ có "Tra cứu hồ sơ"). Cần trở thành dashboard cá nhân.

**Independent Test**: Đăng nhập → Thấy tên, thấy 3 menu cards, thấy badge hồ sơ đang xử lý.

**Acceptance Scenarios**:

1. **Given** công dân đăng nhập thành công, **When** vào Home Screen, **Then** thấy "Xin chào, [Tên công dân]" ở header
2. **Given** đang ở Home Screen, **When** nhìn các mục menu, **Then** thấy: "Hồ sơ của tôi" (với badge số hồ sơ), "Tra cứu hồ sơ", "Thông báo" (với badge chưa đọc)
3. **Given** nhấn nút đăng xuất, **When** xác nhận, **Then** xoá token, quay về màn hình đăng nhập

---

### User Story 5 - Quick Scan tự động tạo dossier (Priority: P3)

Hiện tại quick scan chỉ tạo Submission (mô hình cũ từ feature 001). Cần xác định rõ: quick scan có nên tự động tạo dossier (mô hình mới) hay không, và nếu có thì flow như thế nào.

**Why this priority**: Đây là vấn đề kiến trúc — hai mô hình song song (Submission vs Dossier). Quick scan hiện tại tạo Submission, không hiển thị trong "Hồ sơ của tôi" (dùng Dossier). Cần bridge hoặc thống nhất.

**Independent Test**: Staff quick scan cho CCCD X → CCCD X đăng nhập citizen app → Thấy hồ sơ tương ứng.

**Acceptance Scenarios**:

1. **Given** nhân viên thực hiện quick scan cho CCCD, **When** scan hoàn tất, **Then** hệ thống tự tạo 1 dossier liên kết với citizen tương ứng
2. **Given** dossier được tạo từ quick scan, **When** OCR hoàn tất, **Then** kết quả OCR gắn vào dossier document tương ứng
3. **Given** công dân đăng nhập citizen app, **When** mở "Hồ sơ của tôi", **Then** thấy dossier được tạo từ quick scan với trạng thái phù hợp

---

### Edge Cases

- Công dân đăng nhập nhưng VNeID trả về CCCD chưa tồn tại trong DB → Tạo citizen mới, danh sách hồ sơ rỗng
- Token hết hạn khi đang xem danh sách → Hiển thị lỗi, gợi ý đăng nhập lại
- Nhiều hồ sơ (>20) → Phân trang (pagination) với cuộn vô hạn
- Quick scan cho CCCD chưa có trong citizen table → Vẫn phải tạo submission nhưng cảnh báo "Citizen chưa tồn tại" cho staff
- Thông báo đến khi app đang đóng → Khi mở lại app, badge cập nhật số chưa đọc

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Citizen app PHẢI hiển thị danh sách dossier gắn với CCCD của công dân đang đăng nhập, sử dụng API `GET /v1/citizen/dossiers` đã có sẵn
- **FR-002**: Danh sách dossier PHẢI hỗ trợ lọc theo trạng thái (tất cả, đang xử lý, hoàn thành, từ chối) và pull-to-refresh
- **FR-003**: Khi nhấn vào 1 dossier trong danh sách, app PHẢI mở DossierStatusScreen hiển thị tracking workflow chi tiết
- **FR-004**: Home Screen PHẢI hiển thị tên công dân, menu cards cho các tính năng chính, và badges đếm hồ sơ/thông báo
- **FR-005**: Home Screen PHẢI có nút đăng xuất, xoá token khỏi secure storage
- **FR-006**: Màn hình Thông báo PHẢI kết nối với API `GET /v1/citizen/notifications` và hiển thị danh sách thông báo với trạng thái đọc/chưa đọc
- **FR-007**: Nhấn vào thông báo liên quan đến hồ sơ PHẢI điều hướng đến DossierStatusScreen tương ứng
- **FR-008**: Khi staff thực hiện quick scan, hệ thống PHẢI tạo 1 dossier liên kết với citizen (ngoài submission hiện tại), để công dân thấy trong "Hồ sơ của tôi"
- **FR-009**: Toàn bộ UI citizen app PHẢI hiển thị bằng tiếng Việt

### Key Entities

- **Dossier**: Hồ sơ hành chính gắn với citizen qua FK citizen_id. Có reference_number, status, case_type, workflow_steps. Đây là entity chính hiển thị trong "Hồ sơ của tôi".
- **Submission**: Mô hình cũ (feature 001) — document scan + OCR. Quick scan hiện tạo entity này. Cần bridge sang Dossier.
- **Notification**: Thông báo cho citizen, có type (step_advanced, completed, info_requested, delayed), liên kết đến dossier_id.
- **Citizen**: Công dân, xác thực qua VNeID, nhận diện bằng CCCD (id_number). Sở hữu dossiers và notifications.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Công dân đăng nhập và xem được danh sách hồ sơ trong dưới 3 giây
- **SC-002**: 100% dossier tạo bởi staff (kể cả từ quick scan) hiển thị trong citizen app cho đúng công dân
- **SC-003**: Thông báo chưa đọc hiển thị chính xác badge count trên Home Screen
- **SC-004**: Công dân tìm được hồ sơ cần thiết trong dưới 2 lần nhấn từ Home Screen (Home → Hồ sơ của tôi → Nhấn hồ sơ)
- **SC-005**: Toàn bộ text trong citizen app hiển thị tiếng Việt, không còn text tiếng Anh

## Assumptions

- Công dân đã có tài khoản VNeID và có thể đăng nhập thành công
- Backend API (`GET /v1/citizen/dossiers`, `GET /v1/citizen/notifications`) hoạt động đúng và không cần sửa đổi (trừ FR-008)
- `CitizenDossierApi` trong shared_dart đã implement `listMyDossiers()` và `getDossier()` đúng
- Quick scan bridge (FR-008) sẽ tạo dossier với case_type mặc định "Hồ sơ quét nhanh" hoặc case_type phù hợp nhất
- Pagination backend dùng offset/limit, frontend dùng infinite scroll
- Token VNeID được lưu trong Flutter secure storage và tự động gửi qua Authorization header
