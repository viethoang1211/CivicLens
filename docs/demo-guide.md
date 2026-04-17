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

## Kịch bản D: Demo Quét nhanh (Quick Scan) — 5 phút

> Demo luồng quét nhanh: NV chụp tài liệu → AI tự động OCR + phân loại → NV xác nhận → hồ sơ được route.

### Chuẩn bị

- [ ] In file `02_to_khai_khai_sinh.pdf` từ `docs/sample-docs/` ra giấy A4
- [ ] Chuẩn bị ảnh chụp CCCD thật của Giàng Thị Pà (in A4 hoặc hiển thị trên màn hình)
- [ ] Cài Staff App APK mới nhất trên điện thoại NV001

### Giấy tờ mẫu có sẵn

| Giấy tờ | Nguồn | Mã hệ thống |
|---------|-------|-------------|
| Căn cước công dân (CCCD) | **Ảnh chụp CCCD thật** của Giàng Thị Pà | `ID_CCCD` |
| Tờ khai đăng ký khai sinh | `02_to_khai_khai_sinh.pdf` (in A4) | `BIRTH_REG_FORM` |
| Tờ khai xác nhận tình trạng hôn nhân | `01_to_khai_hon_nhan.pdf` (in A4) | `MARITAL_STATUS_FORM` |
| Giấy đề nghị đăng ký hộ kinh doanh | `03_dang_ky_ho_kinh_doanh.pdf` (in A4) | `BIZ_REG_FORM` |
| Đơn khiếu nại | `04_don_khieu_nai.pdf` (in A4) | `COMPLAINT` |
| Giấy đề nghị đăng ký doanh nghiệp | `05_dang_ky_doanh_nghiep.pdf` (in A4) | `COMPANY_REG_FORM` |

> 📌 **CCCD dùng ảnh chụp thật** (không cần PDF). AI model `qwen-vl-ocr` xử lý trực tiếp ảnh chụp. Các tài liệu khác in từ PDF mẫu trong `docs/sample-docs/`.

### Kịch bản đề xuất: Đăng ký khai sinh (2 giấy tờ)

> Quét 2 giấy tờ liên quan: **CCCD của mẹ** (ảnh chụp thật) + **Tờ khai đăng ký khai sinh** (PDF in A4).
> AI sẽ nhận diện từng loại giấy tờ và trích xuất thông tin.

**Chuẩn bị:**
- Ảnh chụp CCCD thật của Giàng Thị Pà (in ra A4 hoặc hiển thị trên màn hình)
- In file `02_to_khai_khai_sinh.pdf` ra A4 (người yêu cầu & mẹ = Giàng Thị Pà, CCCD 011167000556)

### Bước 1: NV Tiếp nhận quét CCCD (Staff App — NV001)

1. Mở **Staff App** → Đăng nhập NV001
2. Nhấn **"Quét nhanh"** trên trang chủ
3. Chọn mức bảo mật: **"Công khai"**
4. Nhấn **"Tạo & Bắt đầu quét"**
5. **Camera mở** → hướng camera vào **ảnh CCCD Giàng Thị Pà**
6. Chụp ảnh → nhấn **"Hoàn tất"**

### Bước 2: Theo dõi AI xử lý CCCD

1. ✅ Màn hình **"Trạng thái xử lý"** hiện ra:
   - 🔄 **"Đang trích xuất văn bản (OCR)..."** — thanh tiến trình chạy
   - App tự động poll mỗi 3 giây
2. Sau 10–30 giây, chuyển sang:
   - 🔄 **"Đang phân loại tài liệu..."**
3. Khi AI hoàn tất:
   - ✅ Hiện **Kết quả AI**: "Căn cước công dân / CMND" — Độ tin cậy: ~95%
   - Hiện tóm tắt AI: trích xuất **số CCCD 011167000556**, họ tên **GIÀNG THỊ PÀ**, ngày sinh **01/01/1967**

> ℹ️ **Lưu ý**: Hồ sơ CCCD (1 trang) sẽ phân loại là **"Căn cước công dân / CMND"**. Thông tin số CCCD tự động liên kết tài khoản công dân Giàng Thị Pà.

**Giải thích**: _"AI sử dụng model Qwen-VL-OCR để đọc trực tiếp ảnh chụp CCCD thật — không cần scan hay PDF. Thông tin quan trọng được trích xuất tự động."_

### Bước 3: NV xác nhận phân loại CCCD

- **Nếu AI đúng** (Căn cước công dân): Nhấn **"Xác nhận phân loại"**
- **Nếu AI sai**: Chọn loại đúng trong **"Gợi ý khác"**
- ✅ Hồ sơ CCCD chuyển trạng thái "classified" — route tới hàng đợi RECEPTION

### Bước 4: Quét tờ khai khai sinh (lặp lại Quick Scan)

1. Quay về trang chủ → nhấn **"Quét nhanh"** lần nữa
2. Chụp **Tờ khai đăng ký khai sinh** (bản in A4)
3. Nhấn **"Hoàn tất"** → theo dõi AI xử lý
4. AI nhận diện: **"Tờ khai đăng ký khai sinh"** — Độ tin cậy: ~90%

> ✅ **Điểm quan trọng**: Khi quét **nhiều trang** (CCCD + Tờ khai), AI ưu tiên phân loại theo **văn bản chính** — kết quả sẽ là **"Tờ khai đăng ký khai sinh"** (không phải CCCD). CCCD chỉ được dùng để trích xuất số CCCD liên kết công dân.

5. Tóm tắt AI: trích xuất tên trẻ **SÙNG THỊ MỶ**, mẹ **GIÀNG THỊ PÀ**, ngày sinh **10/03/2026**
6. Nhấn **"Xác nhận phân loại"**

**Giải thích**: _"Cùng một luồng Quick Scan cho mọi loại giấy tờ. AI tự phân biệt CCCD với tờ khai, trích xuất đúng thông tin theo từng loại."_

### Bước 5: Kiểm tra kết quả

1. Mỗi lần quét tạo 1 hồ sơ riêng với mã tham chiếu (VD: `HS-20260416-00003`)
2. Hồ sơ được route đến phòng Tiếp nhận (RECEPTION) — **NV001** thấy trong hàng đợi
3. Sau khi NV001 phê duyệt → route tiếp tới phòng Tư pháp — **NV003 (Lê Văn Cường)** xử lý bước tiếp theo
4. Nếu CCCD công dân trùng khớp → tự động liên kết với tài khoản công dân

### Bước 6: Công dân xem hồ sơ (Citizen App — Giàng Thị Pà)

1. Mở **Citizen App**
2. Nhấn **"Đăng nhập bằng VNeID"** → chọn **"Giàng Thị Pà — CCCD: 011167000556"**
3. Xác thực OAuth → nhấn "Copy mã" → dán vào app → **"Xác thực"**
4. ✅ Màn hình chủ: "Xin chào, Giàng Thị Pà"
5. Nhấn **"Hồ sơ Quick Scan"** ← nút mới, hiện badge số hồ sơ
6. ✅ Thấy hồ sơ "Tờ khai đăng ký khai sinh" — trạng thái **"Đang xử lý"**
7. Thấy phòng ban hiện tại đang xử lý

> 💡 **Lưu ý**: "Hồ sơ của tôi" hiển thị hồ sơ case-based; **"Hồ sơ Quick Scan"** hiển thị hồ sơ từ luồng quét nhanh.

### Lưu ý khi demo Quick Scan

- **Chất lượng ảnh quan trọng**: Chụp thẳng, đủ sáng, không bị mờ. Ảnh lệch/tối sẽ làm OCR sai
- **In PDF trên A4**: Cho kết quả tốt nhất. Chụp từ màn hình laptop cũng được nhưng dễ bị phản chiếu
- **Thời gian xử lý**: Thường 10–30 giây. Nếu server bận có thể lâu hơn
- **Loại tài liệu hỗ trợ**: Hệ thống hỗ trợ 15 loại (xem bảng dưới)

### Danh sách 15 loại tài liệu AI hỗ trợ

| # | Loại tài liệu | Mã | Phòng ban route |
|---|---------------|-----|----------------|
| 1 | Căn cước công dân / CMND | `ID_CCCD` | Tiếp nhận |
| 2 | Hộ chiếu Việt Nam | `PASSPORT_VN` | Tiếp nhận |
| 3 | Tờ khai đăng ký khai sinh | `BIRTH_REG_FORM` | Tiếp nhận → Tư pháp |
| 4 | Giấy chứng sinh | `BIRTH_CERTIFICATE_MEDICAL` | Tiếp nhận → Tư pháp |
| 5 | Giấy chứng nhận kết hôn | `MARRIAGE_CERT` | Tiếp nhận → Tư pháp |
| 6 | Tờ khai xác nhận tình trạng hôn nhân | `MARITAL_STATUS_FORM` | Tiếp nhận → Tư pháp |
| 7 | Tờ khai thay đổi cư trú (CT01) | `RESIDENCE_FORM_CT01` | Tiếp nhận → Công an |
| 8 | Giấy tờ chứng minh chỗ ở hợp pháp | `RESIDENCE_PROOF` | Tiếp nhận → Hành chính |
| 9 | Giấy đề nghị đăng ký hộ kinh doanh | `BIZ_REG_FORM` | Tiếp nhận → Tài chính |
| 10 | Giấy đề nghị đăng ký doanh nghiệp | `COMPANY_REG_FORM` | Tiếp nhận → Tài chính → Tư pháp |
| 11 | Điều lệ công ty | `COMPANY_CHARTER` | Tiếp nhận → Tư pháp |
| 12 | Danh sách thành viên / cổ đông | `MEMBER_LIST` | Tiếp nhận → Tài chính |
| 13 | Đơn khiếu nại / tố cáo | `COMPLAINT` | Tiếp nhận → Hành chính → Lãnh đạo |
| 14 | Báo cáo mật | `CLASSIFIED_RPT` | Tiếp nhận → Nội vụ → Lãnh đạo |
| 15 | Giấy xác nhận thông tin cư trú | `RESIDENCE_CONFIRM` | Tiếp nhận |

---

## Demo tính năng bổ sung khác (nếu còn thời gian)

### Tìm kiếm (Search)

1. NV bất kỳ → **"Tìm kiếm"** → nhập từ khóa (VD: "Trần Văn Hùng")
2. Hệ thống tìm full-text trên OCR text + thông tin hồ sơ
3. Hiển thị kết quả với highlight

### Demo từ chối

1. Tại bước duyệt, NV chọn **"Từ chối"** thay vì "Phê duyệt"
2. Ghi lý do: _"Thiếu giấy tờ bổ sung"_
3. Công dân mở app → trạng thái **"Bị từ chối"** + lý do hiển thị trong phần "Ghi chú từ phòng ban"

### Demo mức độ bảo mật (Security Classification)

> Demo hệ thống kiểm soát truy cập dựa trên mức bảo mật (ABAC — Attribute-Based Access Control).

**Bối cảnh**: Mỗi hồ sơ khi tạo được gán mức bảo mật (0–3). Nhân viên chỉ xem được hồ sơ có mức ≤ clearance level của mình.

| Mức | Nhãn | Ý nghĩa |
|-----|------|---------|
| 0 | Công khai | Mọi nhân viên đều xem được |
| 1 | Mật | Chỉ NV có clearance ≥ 1 |
| 2 | Tối mật | Chỉ NV có clearance ≥ 2 |
| 3 | Tuyệt mật | Chỉ NV có clearance ≥ 3 (Lãnh đạo) |

**Các bước demo:**

1. Đăng nhập **NV001** (Tiếp nhận, clearance = 0)
2. Nhấn **"Quét nhanh"** → ở bước chọn mức bảo mật:
   - Chọn **"Công khai"** (mức 0) → Tạo thành công
3. Quay lại → **"Quét nhanh"** lần nữa:
   - Chọn **"Mật"** (mức 1) → ⚠️ Cảnh báo: _"Mức bảo mật vượt quyền truy cập của bạn"_
   - NV001 (clearance=0) không thể tạo hồ sơ mức 1
4. Đăng nhập **NV007** (Lãnh đạo, clearance = 3):
   - Tạo hồ sơ mức **"Tối mật"** → Thành công
   - Hồ sơ này chỉ hiện trong hàng đợi của NV có clearance ≥ 2

**Giải thích**: _"Hệ thống kiểm soát truy cập theo thuộc tính (ABAC) đảm bảo hồ sơ nhạy cảm chỉ được truy cập bởi nhân viên có đủ thẩm quyền. Mọi truy cập (kể cả bị từ chối) đều được ghi audit log."_

### Demo Audit Trail (Nhật ký kiểm toán)

> Demo khả năng truy vết toàn bộ vòng đời hồ sơ.

**Bối cảnh**: Mọi thao tác trên hồ sơ (quét, phân loại, duyệt, từ chối, sửa OCR) đều được ghi lại trong audit log với: ai làm, làm gì, lúc nào.

**Các bước demo:**

1. Mở Swagger: http://43.98.196.158/docs
2. Đăng nhập lấy token (dùng NV007 — manager)
3. Gọi `GET /v1/staff/audit/submissions/{submission_id}/trail`
4. ✅ Hiển thị timeline đầy đủ:
   - `scan` — NV001 quét tài liệu lúc 14:30
   - `finalize_scan` — NV001 hoàn tất lúc 14:31
   - `confirm_classification` — NV001 xác nhận phân loại lúc 14:32
   - `review_approved` — NV004 phê duyệt (phòng Tài chính) lúc 14:45
   - `annotation_approved` — NV004 ghi chú "Vốn điều lệ hợp lệ"
   - `review_approved` — NV003 phê duyệt (phòng Tư pháp) lúc 15:00

5. Gọi `GET /v1/staff/audit/logs` để xem toàn bộ nhật ký hệ thống

**Giải thích**: _"Toàn bộ thao tác được ghi nhật ký kiểm toán (audit trail), đảm bảo truy vết được ai đã xử lý hồ sơ, quyết định gì, lúc nào. Đây là yêu cầu bắt buộc cho hệ thống hành chính công — phục vụ thanh tra, kiểm toán, và giải quyết khiếu nại."_

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
