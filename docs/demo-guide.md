# Hướng dẫn Demo End-to-End

> Demo luồng xử lý hồ sơ hoàn chỉnh: từ tiếp nhận → OCR/AI → route qua các phòng ban → công dân theo dõi trạng thái.

## Tổng quan luồng demo

```
Công dân nộp giấy tờ tại quầy
       ↓
[Staff App] NV Tiếp nhận (NV001) tạo hồ sơ, quét tài liệu → AI OCR + phân loại
       ↓
Hồ sơ được route tự động qua các phòng ban theo thủ tục
       ↓
[Staff App] NV từng phòng ban xem hàng đợi → duyệt/từ chối
       ↓
[Citizen App] Công dân mở app → xem trạng thái hồ sơ realtime
```

---

## Tài khoản demo

### Staff (Nhân viên) — Staff App

| Mã NV   | Họ tên          | Phòng ban               | Mật khẩu       | Vai trò  |
|---------|-----------------|-------------------------|-----------------|----------|
| NV001   | Nguyễn Văn An   | Tiếp nhận (RECEPTION)   | `password123`   | officer  |
| NV002   | Trần Thị Bình   | Hành chính (ADMIN)      | `password123`   | officer  |
| NV003   | Lê Văn Cường    | Tư pháp (JUDICIAL)      | `password123`   | officer  |
| NV004   | Phạm Thị Dung   | Tài chính (FINANCE)     | `password123`   | officer  |
| NV005   | Hoàng Văn Em    | Công an (POLICE)        | `password123`   | officer  |
| NV006   | Đỗ Thị Phương   | Nội vụ (INTERNAL)       | `password123`   | officer  |
| NV007   | Vũ Đức Giang    | Lãnh đạo (LEADERSHIP)   | `password123`   | manager  |

### Citizen (Công dân) — Citizen App

| CCCD          | Họ tên          | SĐT          |
|--------------|-----------------|--------------|
| 012345678901 | Phạm Văn Dũng   | 0901234567   |
| 012345678902 | Nguyễn Thị Mai   | 0912345678   |
| 012345678903 | Trần Văn Hùng    | 0923456789   |

---

## Kịch bản demo đề xuất

### Kịch bản A: "Xác nhận tình trạng hôn nhân" (2 phòng ban)

**Route: Tiếp nhận → Tư pháp**

Giấy tờ cần chuẩn bị (in ra giấy A4):
1. Tờ khai xác nhận tình trạng hôn nhân (điền tay hoặc in sẵn)
2. Bản photo CCCD/CMND

### Kịch bản B: "Đăng ký khai sinh" (2 phòng ban)

**Route: Tiếp nhận → Tư pháp**

Giấy tờ cần chuẩn bị:
1. Tờ khai đăng ký khai sinh (mẫu BTP)
2. Giấy chứng sinh (bản photo)
3. CCCD của cha hoặc mẹ

### Kịch bản C: "Đăng ký doanh nghiệp" (3 phòng ban) ⭐ Đề xuất cho demo

**Route: Tiếp nhận → Tài chính → Tư pháp**

Giấy tờ cần chuẩn bị:
1. Giấy đề nghị đăng ký doanh nghiệp (mẫu)
2. Điều lệ công ty
3. Danh sách thành viên/cổ đông
4. CCCD người đại diện pháp luật

> ⭐ Đề xuất Kịch bản C vì có 3 phòng ban, thể hiện rõ luồng route.

---

## Các bước demo chi tiết (Kịch bản C)

### Chuẩn bị trước demo

- [ ] Cài Staff App APK trên 3 điện thoại/máy tính bảng (NV001, NV004, NV003)
- [ ] Cài Citizen App APK trên 1 điện thoại riêng
- [ ] In giấy tờ vật lý: CCCD mẫu, Giấy đề nghị đăng ký DN, Điều lệ công ty
- [ ] Đảm bảo tất cả thiết bị kết nối được internet (truy cập http://43.98.196.158)

### Bước 1: Công dân đăng nhập (Citizen App) — 2 phút

1. Mở **Citizen App** trên điện thoại công dân
2. Nhấn **"Đăng nhập bằng VNeID"**
3. Trình duyệt mở trang VNeID mock → chọn tài khoản **"Trần Văn Hùng — CCCD: 012345678903"**
4. Nhấn **"Xác nhận đăng nhập"**
5. Ở trang thành công, nhấn **"Copy mã"** (hoặc nhấn vào mã → select all → copy)
6. Quay lại Citizen App → dán mã → nhấn **"Xác thực"**
7. ✅ Hiện trang chủ: "Xin chào, Trần Văn Hùng"

**Giải thích cho stakeholder**: _"Đây là luồng xác thực qua VNeID — hệ thống định danh điện tử quốc gia. Trong production, VNeID sẽ xác minh sinh trắc học (vân tay, khuôn mặt). Đây là bản demo nên dùng mock server."_

### Bước 2: NV Tiếp nhận tạo hồ sơ (Staff App — NV001) — 5 phút

1. Mở **Staff App** trên điện thoại NV001
2. Đăng nhập: Mã NV = `NV001`, Mật khẩu = `password123`
3. ✅ Hiện trang chủ: "Xin chào, Nguyễn Văn An" / "Tiếp nhận (Reception)"
4. Nhấn **"Tạo Hồ sơ mới"**
5. Chọn thủ tục: **"Đăng ký doanh nghiệp"**
6. Hệ thống hiển thị danh sách tài liệu cần thiết:
   - ✅ Giấy đề nghị đăng ký DN (bắt buộc)
   - ✅ Điều lệ công ty (bắt buộc)
   - ✅ Danh sách thành viên (bắt buộc)
   - ✅ CCCD người đại diện (bắt buộc)
7. Với mỗi tài liệu:
   - Nhấn slot → **camera mở** → quét giấy tờ vật lý
   - AI tự động chạy **OCR** (trích xuất text) + **phân loại** (nhận diện loại giấy tờ)
   - Hiển thị kết quả: loại giấy tờ, độ tin cậy, text trích xuất
8. Sau khi quét đủ, nhấn **"Nộp hồ sơ"**
9. ✅ Hồ sơ chuyển trạng thái **"Đã nộp"** → tự động route đến phòng Tài chính

**Giải thích**: _"AI sử dụng mô hình Qwen-VL để OCR tiếng Việt và phân loại tài liệu. Kết quả AI chỉ mang tính tham khảo — nhân viên luôn có quyền override."_

### Bước 3: Công dân xem trạng thái (Citizen App) — 1 phút

1. Quay lại **Citizen App** (Trần Văn Hùng)
2. Nhấn **"Hồ sơ của tôi"**
3. ✅ Thấy hồ sơ mới: "Đăng ký doanh nghiệp" — trạng thái **"Đang xử lý"**
4. Nhấn vào hồ sơ → thấy timeline:
   - ✅ Tiếp nhận — Hoàn thành
   - 🔄 Tài chính — **Đang xử lý**
   - ⏳ Tư pháp — Chờ

**Giải thích**: _"Công dân có thể theo dõi hồ sơ realtime. Mỗi khi hồ sơ được duyệt qua 1 bước, trạng thái cập nhật ngay."_

### Bước 4: NV Tài chính duyệt (Staff App — NV004) — 2 phút

1. Mở **Staff App** trên điện thoại NV004
2. Đăng nhập: Mã NV = `NV004`, Mật khẩu = `password123`
3. ✅ Trang chủ: "Xin chào, Phạm Thị Dung" / "Tài chính (Finance)"
4. Nhấn **"Hàng đợi"**
5. ✅ Thấy hồ sơ "Đăng ký doanh nghiệp" trong danh sách
6. Nhấn vào hồ sơ → xem chi tiết:
   - Xem ảnh scan các tài liệu
   - Xem kết quả OCR + AI phân loại
   - Xem tóm tắt AI (nếu đã tạo)
7. Nhấn **"Phê duyệt"** → thêm ghi chú: _"Vốn điều lệ hợp lệ, ngành nghề không thuộc danh mục cấm"_
8. ✅ Hồ sơ chuyển sang bước tiếp theo → Tư pháp

**Giải thích**: _"Mỗi phòng ban chỉ thấy hồ sơ thuộc phòng mình. Sau khi duyệt, hệ thống tự động route đến phòng tiếp theo."_

### Bước 5: Công dân nhận thông báo (Citizen App) — 30 giây

1. Quay lại **Citizen App**
2. Nhấn **"Thông báo"** (badge hiện số mới)
3. ✅ Thấy thông báo: "Hồ sơ đã được phòng Tài chính phê duyệt"
4. Nhấn vào → xem timeline cập nhật:
   - ✅ Tiếp nhận — Hoàn thành
   - ✅ Tài chính — **Hoàn thành**
   - 🔄 Tư pháp — **Đang xử lý**

### Bước 6: NV Tư pháp duyệt & hoàn tất (Staff App — NV003) — 2 phút

1. Mở **Staff App** trên điện thoại NV003
2. Đăng nhập: Mã NV = `NV003`, Mật khẩu = `password123`
3. ✅ Trang chủ: "Xin chào, Lê Văn Cường" / "Tư pháp (Judicial)"
4. Nhấn **"Hàng đợi"** → thấy hồ sơ
5. Xem chi tiết → nhấn **"Phê duyệt"**
6. ✅ Hồ sơ hoàn tất — trạng thái **"Hoàn thành"**

### Bước 7: Kết quả cuối (Citizen App) — 30 giây

1. Quay lại **Citizen App**
2. **"Hồ sơ của tôi"** → trạng thái **"Hoàn thành"** ✅
3. Timeline đầy đủ:
   - ✅ Tiếp nhận — Hoàn thành
   - ✅ Tài chính — Hoàn thành
   - ✅ Tư pháp — Hoàn thành

**Giải thích tổng kết**: _"Toàn bộ luồng từ tiếp nhận → xử lý qua 3 phòng ban → công dân theo dõi, được số hóa hoàn toàn. AI hỗ trợ OCR + phân loại tài liệu. Mỗi bước đều có audit trail đầy đủ."_

---

## Demo tính năng bổ sung (nếu còn thời gian)

### Quét nhanh (Quick Scan)

1. NV001 → **"Quét nhanh"** → chụp 1 tài liệu bất kỳ
2. AI tự động OCR + phân loại → hiển thị kết quả
3. Nhấn "Hoàn tất" → hồ sơ được tạo tự động
4. Công dân mở app → thấy hồ sơ quét nhanh

### Tìm kiếm (Search)

1. NV bất kỳ → **"Tìm kiếm"** → nhập từ khóa (VD: "Trần Văn Hùng")
2. Hệ thống tìm full-text trên OCR text + thông tin hồ sơ
3. Hiển thị kết quả với highlight

### Demo từ chối

1. Tại bước duyệt, NV chọn **"Từ chối"** thay vì "Phê duyệt"
2. Ghi lý do: _"Thiếu giấy tờ bổ sung"_
3. Công dân mở app → trạng thái **"Bị từ chối"** + lý do

---

## URL & Thông tin kỹ thuật

| Thành phần      | URL / Thông tin                        |
|-----------------|---------------------------------------|
| API Backend     | http://43.98.196.158                  |
| Swagger Docs    | http://43.98.196.158/docs             |
| VNeID Mock      | http://43.98.196.158/vneid/authorize  |
| Staff App APK   | `C:\flutter-builds\staff_app\build\app\outputs\flutter-apk\app-release.apk` |
| Citizen App APK | `C:\flutter-builds\citizen_app\build\app\outputs\flutter-apk\app-release.apk` |

## Troubleshooting

| Vấn đề | Giải pháp |
|--------|-----------|
| Copy mã VNeID không hoạt động | Nhấn vào ô mã → text tự động được chọn → dùng menu "Copy" của Android |
| "Không xác định được phòng ban" | Đăng xuất → đăng nhập lại |
| Hàng đợi trống | Hồ sơ chưa được route đến phòng ban này, hoặc chưa nộp |
| Thông báo trống | Chưa có hồ sơ nào → tạo hồ sơ trước |
| API trả về 500 | SSH vào server kiểm tra logs: `docker logs public-sector-backend-1` |
