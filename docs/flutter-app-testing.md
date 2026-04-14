# Hướng dẫn chạy Flutter Apps kết nối Backend đã deploy

Tài liệu hướng dẫn các developer mở và chạy **Staff App** + **Citizen App** bằng Android Studio, kết nối tới backend đang chạy trên Alibaba Cloud.

---

## Thông tin Backend đã deploy

| Thông tin | Giá trị |
|-----------|---------|
| **Backend API** | `http://43.98.196.158` |
| **Swagger UI** | http://43.98.196.158/docs |
| **VNeID Login (browser)** | http://43.98.196.158/vneid/authorize |

### Tài khoản test (Seed Data)

**Staff App** — đăng nhập bằng Employee ID + Password:

| Employee ID | Mật khẩu | Tên | Phòng ban | Clearance |
|-------------|----------|-----|-----------|-----------|
| `NV001` | `password123` | Nguyễn Văn An | Tiếp nhận (Reception) | 1 |
| `NV002` | `password123` | Trần Thị Bình | Hành chính (Admin) | 2 |
| `NV003` | `password123` | Lê Văn Cường | Tư pháp (Judicial) | 1 |

**Citizen App** — đăng nhập qua VNeID (chọn từ danh sách):

| Tên | Số CCCD |
|-----|---------|
| Phạm Văn Dũng | 012345678901 |
| Nguyễn Thị Mai | 012345678902 |
| Trần Văn Hùng | 012345678903 |

---

## Yêu cầu cài đặt

### 1. Flutter SDK

Cần Flutter **3.24+** trở lên.

```bash
# Kiểm tra phiên bản
flutter --version

# Nếu chưa cài, tải tại:
# https://docs.flutter.dev/get-started/install
```

### 2. Android Studio

Tải tại: https://developer.android.com/studio

Phiên bản khuyến nghị: **Android Studio Hedgehog (2023.1)** trở lên.

### 3. Java JDK 17

```bash
# Kiểm tra
java -version

# Ubuntu
sudo apt install openjdk-17-jdk

# macOS
brew install openjdk@17
```

### 4. Kiểm tra môi trường

```bash
flutter doctor
```

Đảm bảo các mục sau đều ✅:
- Flutter
- Android toolchain
- Android Studio

---

## Bước 1: Clone repository

```bash
git clone <repo-url>
cd public_sector
```

> Nếu đã clone rồi thì `git pull` để lấy code mới nhất.

---

## Bước 2: Mở project trong Android Studio

### 2.1. Cài Flutter plugin cho Android Studio

1. Mở Android Studio
2. Vào **File → Settings** (Windows/Linux) hoặc **Android Studio → Preferences** (macOS)
3. Chọn **Plugins** ở menu bên trái
4. Tìm kiếm **"Flutter"** trong tab Marketplace
5. Nhấn **Install** (plugin Dart sẽ được cài cùng tự động)
6. Nhấn **Restart IDE**

### 2.2. Mở Staff App

1. Mở Android Studio
2. Chọn **File → Open...**
3. Duyệt tới thư mục `public_sector/staff_app`
4. Nhấn **OK**
5. Đợi Android Studio index xong (thanh progress bar ở dưới cùng chạy hết)

### 2.3. Mở Citizen App

Tương tự, mở thêm 1 cửa sổ Android Studio mới:

1. **File → Open...**
2. Duyệt tới thư mục `public_sector/citizen_app`
3. Nhấn **OK**

> **Lưu ý:** Mỗi app nên mở trong 1 cửa sổ Android Studio riêng. Nếu Android Studio hỏi "Open in New Window?", chọn **New Window**.

---

## Bước 3: Cài dependencies

Khi mở project lần đầu, Android Studio thường tự chạy `flutter pub get`. Nếu không, chạy thủ công:

**Cách 1:** Trong Android Studio, mở **Terminal** (tab ở dưới cùng) và chạy:

```bash
flutter pub get
```

**Cách 2:** Qua terminal bên ngoài:

```bash
# Staff App
cd public_sector/staff_app
flutter pub get

# Citizen App
cd public_sector/citizen_app
flutter pub get
```

> `shared_dart` package được tham chiếu qua `path: ../shared_dart` trong `pubspec.yaml`, nên không cần cài riêng.

---

## Bước 4: Cấu hình thiết bị chạy app

Có 3 cách chạy app: **Android Emulator**, **điện thoại thật qua USB**, hoặc **Chrome (web)**.

### Cách A: Android Emulator (khuyến nghị cho test nhanh)

#### Tạo Emulator:

1. Trong Android Studio, mở **Device Manager**:
   - Nhấn biểu tượng 📱 trên thanh toolbar (hoặc **Tools → Device Manager**)
2. Nhấn **Create Virtual Device**
3. Chọn thiết bị: **Pixel 7** (hoặc bất kỳ thiết bị nào)
4. Nhấn **Next**
5. Chọn system image: **API 34** (Android 14) — nhấn **Download** nếu chưa tải
6. Nhấn **Next → Finish**

#### Khởi động Emulator:

1. Trong **Device Manager**, nhấn nút ▶️ (Play) bên cạnh emulator vừa tạo
2. Đợi emulator boot xong (hiện màn hình chính Android)
3. Kiểm tra Android Studio đã nhận thiết bị: dropdown thiết bị trên toolbar hiện tên emulator

### Cách B: Điện thoại Android thật qua USB

1. Trên điện thoại: **Cài đặt → Giới thiệu về điện thoại → nhấn "Build number" 7 lần** để bật Developer Mode
2. **Cài đặt → Tùy chọn nhà phát triển → Bật "USB debugging"**
3. Cắm USB vào máy tính
4. Nhấn **"Cho phép gỡ lỗi USB"** trên điện thoại khi popup xuất hiện
5. Kiểm tra trong terminal:
   ```bash
   adb devices
   # Kết quả: <serial>  device
   ```
6. Android Studio sẽ tự nhận thiết bị trong dropdown

### Cách C: Chrome (Web) — chỉ dùng để test UI nhanh

```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://43.98.196.158
```

> ⚠️ Một số tính năng native (camera, secure storage) không hoạt động trên web.

---

## Bước 5: Chạy app kết nối Backend đã deploy

### ⚡ Điểm quan trọng nhất

Cả hai app đều đọc `API_BASE_URL` qua `--dart-define` lúc build/run. **Nếu không truyền, app sẽ kết nối localhost và không hoạt động.**

### Cách 1: Chạy qua Android Studio (giao diện)

#### Bước 5.1: Cấu hình Run Configuration

1. Trên thanh toolbar của Android Studio, tìm dropdown **Run Configuration** (thường hiện tên `main.dart`)
2. Nhấn vào dropdown → chọn **Edit Configurations...**
3. Trong cửa sổ Run/Debug Configurations:
   - Chọn configuration hiện có (hoặc tạo mới bằng nút **+** → **Flutter**)
   - Tìm mục **Additional run args** (hoặc **Additional arguments**)
   - Thêm vào ô đó:
     ```
     --dart-define=API_BASE_URL=http://43.98.196.158
     ```
4. Nhấn **Apply → OK**

> **Hình minh họa vị trí cấu hình:**
> ```
> ┌─ Run/Debug Configurations ──────────────────────────────┐
> │                                                          │
> │  Name: main.dart                                         │
> │  Dart entrypoint: lib/main.dart                          │
> │  Additional run args: --dart-define=API_BASE_URL=http://43.98.196.158
> │                                                          │
> │  [Apply]  [OK]  [Cancel]                                 │
> └──────────────────────────────────────────────────────────┘
> ```

#### Bước 5.2: Chọn thiết bị

Trên toolbar, chọn thiết bị từ dropdown thiết bị (emulator hoặc điện thoại thật đã kết nối).

#### Bước 5.3: Nhấn Run

Nhấn nút **▶️ Run** (hoặc `Shift+F10`). App sẽ build và mở trên thiết bị.

### Cách 2: Chạy qua Terminal (nhanh hơn)

Mở Terminal trong Android Studio (hoặc terminal bên ngoài):

```bash
# ═══════════════════════════════════════
#  STAFF APP
# ═══════════════════════════════════════
cd staff_app
flutter run --dart-define=API_BASE_URL=http://43.98.196.158

# ═══════════════════════════════════════
#  CITIZEN APP
# ═══════════════════════════════════════
cd citizen_app
flutter run --dart-define=API_BASE_URL=http://43.98.196.158
```

Nếu có nhiều thiết bị kết nối, Flutter sẽ hỏi chọn. Hoặc chỉ định thiết bị:

```bash
# Xem danh sách thiết bị
flutter devices

# Chạy trên thiết bị cụ thể
flutter run -d <device-id> --dart-define=API_BASE_URL=http://43.98.196.158
```

---

## Bước 6: Test từng app

### 6.1. Test Staff App

1. Chạy Staff App theo Bước 5
2. Màn hình **Staff Login** hiện ra
3. Nhập:
   - **Employee ID:** `NV001`
   - **Password:** `password123`
4. Nhấn **Login**
5. Nếu thành công → chuyển sang màn hình chính **Hệ thống Quản lý Hồ sơ**
6. Tại đây có thể:
   - Tạo hồ sơ mới (chọn loại thủ tục)
   - Xem danh sách hồ sơ
   - Xem hàng đợi xử lý của phòng ban

### 6.2. Test Citizen App

1. Chạy Citizen App theo Bước 5
2. Màn hình **Đăng nhập bằng VNeID** hiện ra
3. Nhấn nút **"Đăng nhập bằng VNeID"**
4. App sẽ mở trình duyệt → trang đăng nhập VNeID (mock) hiện ra
5. Chọn công dân từ dropdown (ví dụ: **Phạm Văn Dũng**)
6. Nhấn **Xác nhận đăng nhập**
7. Trình duyệt redirect về app với mã code
8. Nhập mã code vào dialog trong app → nhấn **Xác nhận**
9. Nếu thành công → chuyển sang màn hình **Dịch vụ công trực tuyến**

> **Lưu ý VNeID trên Emulator:** Trên emulator, deep link (`citizen-app://auth/callback`) có thể không tự động chuyển về app. Trong trường hợp đó, copy mã `code` từ URL trên trình duyệt và paste vào dialog trong app.

---

## Xử lý lỗi thường gặp

### ❌ `Connection refused` hoặc `SocketException`

**Nguyên nhân:** App không kết nối được tới backend.

**Kiểm tra:**
1. Mở browser trên **máy tính** → vào http://43.98.196.158/docs → xác nhận Swagger UI hiện ra
2. Đảm bảo đã truyền `--dart-define=API_BASE_URL=http://43.98.196.158` khi chạy
3. Nếu dùng emulator, kiểm tra emulator có internet (mở Chrome trong emulator → vào google.com)

### ❌ `flutter pub get` thất bại

**Nguyên nhân:** `shared_dart` package không tìm thấy.

**Cách fix:** Đảm bảo đang ở đúng thư mục (`staff_app/` hoặc `citizen_app/`), và thư mục `shared_dart/` tồn tại cùng cấp:

```
public_sector/
├── staff_app/        ← bạn đang ở đây
├── citizen_app/
└── shared_dart/      ← package này phải tồn tại
```

### ❌ `Gradle build failed` hoặc `JAVA_HOME not set`

**Cách fix:**

```bash
# Kiểm tra Java
java -version   # Cần JDK 17

# Set JAVA_HOME
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64   # Linux
export JAVA_HOME=$(/usr/libexec/java_home -v 17)       # macOS
```

Hoặc trong Android Studio: **File → Settings → Build → Gradle → Gradle JDK** → chọn JDK 17.

### ❌ `SDK not found` hoặc `Android SDK not installed`

1. Mở **Android Studio → Settings → Languages & Frameworks → Android SDK**
2. Tab **SDK Platforms**: tick **Android 14 (API 34)**
3. Tab **SDK Tools**: tick **Android SDK Build-Tools**, **Android SDK Command-line Tools**
4. Nhấn **Apply** → tải về

### ❌ Staff login trả về `Login failed`

- Kiểm tra Employee ID: `NV001`, `NV002`, hoặc `NV003`
- Mật khẩu là `password123` (chữ thường, không có khoảng trắng)
- Kiểm tra backend có đang chạy: `curl http://43.98.196.158/docs`

### ❌ VNeID trả về lỗi hoặc trang trắng

- Kiểm tra: `curl http://43.98.196.158/vneid/health` → phải trả về `{"status":"ok"}`
- Mở trực tiếp http://43.98.196.158/vneid/authorize trên browser máy tính để verify

### ❌ Emulator quá chậm

- Bật **Hardware Acceleration**: Android Studio → Settings → search "hardware" → enable KVM/HAXM
- Dùng **x86_64 system image** (không dùng ARM) cho emulator
- Tăng RAM cho emulator: Device Manager → Edit → Show Advanced → Memory: 4096 MB

---

## Build APK để cài trên điện thoại (không cần Android Studio)

Nếu muốn chia sẻ APK cho người khác test mà không cần cài Android Studio:

```bash
# Build Staff App APK
cd staff_app
flutter build apk --dart-define=API_BASE_URL=http://43.98.196.158

# Build Citizen App APK
cd citizen_app
flutter build apk --dart-define=API_BASE_URL=http://43.98.196.158
```

File APK nằm tại:
- `staff_app/build/app/outputs/flutter-apk/app-release.apk`
- `citizen_app/build/app/outputs/flutter-apk/app-release.apk`

Gửi file APK qua Zalo/Telegram/email → người nhận mở file → **Cài đặt** (cần bật "Cài từ nguồn không xác định" trên điện thoại).

---

## Tóm tắt nhanh (TL;DR)

```bash
# 1. Cài Flutter 3.24+
flutter --version

# 2. Lấy code
git pull

# 3. Chạy Staff App
cd staff_app && flutter run --dart-define=API_BASE_URL=http://43.98.196.158
# Login: NV001 / password123

# 4. Chạy Citizen App (cửa sổ terminal khác)
cd citizen_app && flutter run --dart-define=API_BASE_URL=http://43.98.196.158
# Chọn "Phạm Văn Dũng" từ VNeID login page
```
