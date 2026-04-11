# Hướng dẫn Cài đặt & Kiểm thử (Testing Guide)

Tài liệu này hướng dẫn chi tiết cách chạy backend API và test 2 ứng dụng Flutter (Staff App, Citizen App) trên **điện thoại Android thật** và **Android Emulator** trên cả Ubuntu và Windows.

---

## Mục lục

1. [Yêu cầu chung](#1-yêu-cầu-chung)
2. [Khởi động Backend](#2-khởi-động-backend)
3. [Test trên điện thoại Android thật](#3-test-trên-điện-thoại-android-thật)
4. [Test bằng Android Emulator trên Ubuntu](#4-test-bằng-android-emulator-trên-ubuntu)
5. [Test bằng Android Emulator trên Windows](#5-test-bằng-android-emulator-trên-windows)
6. [Kịch bản test (Test Scenarios)](#6-kịch-bản-test)
7. [Khắc phục lỗi thường gặp](#7-khắc-phục-lỗi-thường-gặp)

---

## 1. Yêu cầu chung

### Backend
| Công cụ | Phiên bản | Mục đích |
|---------|-----------|----------|
| Python | 3.12+ | Backend API |
| Docker & Docker Compose | Latest | PostgreSQL, Redis, RocketMQ |
| Git | Latest | Clone source code |

### Flutter
| Công cụ | Phiên bản | Mục đích |
|---------|-----------|----------|
| Flutter SDK | 3.24+ | Build & chạy app |
| Android SDK | API 34 | Nền tảng Android |
| Java JDK | 17 | Gradle build |

### Cài Flutter SDK

```bash
# Linux / WSL
cd ~
git clone https://github.com/flutter/flutter.git -b stable --depth 1
echo 'export PATH="$HOME/flutter/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
flutter --version
```

**Windows:** Tải từ https://docs.flutter.dev/get-started/install/windows/mobile và giải nén vào `C:\flutter`, thêm `C:\flutter\bin` vào PATH.

### Cài Java JDK 17

```bash
# Ubuntu / WSL
sudo apt-get update && sudo apt-get install -y openjdk-17-jdk
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
```

**Windows:** Tải từ https://adoptium.net/temurin/releases/?version=17 và cài đặt. Đặt `JAVA_HOME = C:\Program Files\Eclipse Adoptium\jdk-17...`.

---

## 2. Khởi động Backend

Backend cần chạy để các ứng dụng Flutter có thể gọi API. Có **2 cách** expose backend:

### Cách A: Chạy trên cùng máy (Local)

```bash
cd infra
docker compose up -d          # PostgreSQL, Redis, RocketMQ

cd ../backend
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Chạy migration & seed data
alembic upgrade head
python -m src.seeds.seed_data

# Khởi động API server — lắng nghe trên tất cả interfaces
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

> **Quan trọng:** Dùng `--host 0.0.0.0` để điện thoại / emulator trong cùng mạng LAN có thể kết nối.

### Cách B: Expose ra internet bằng ngrok (để test từ điện thoại ở mạng khác)

Nếu điện thoại không cùng mạng WiFi với máy chạy backend, dùng [ngrok](https://ngrok.com):

```bash
# Cài ngrok
# Linux: snap install ngrok
# Windows: choco install ngrok hoặc tải từ https://ngrok.com/download

# Đăng ký tài khoản miễn phí tại ngrok.com, lấy auth token
ngrok config add-authtoken <your-token>

# Tạo tunnel tới backend
ngrok http 8000
```

ngrok sẽ cho URL dạng: `https://abc123.ngrok-free.app` — dùng URL này làm `API_BASE_URL` khi build app.

### Xác nhận backend hoạt động

Mở trình duyệt hoặc dùng curl:

```bash
curl http://localhost:8000/docs    # Swagger UI
curl http://localhost:8000/v1/staff/admin/case-types  # Danh sách loại thủ tục
```

---

## 3. Test trên điện thoại Android thật

### Bước 1: Bật Developer Options trên điện thoại

1. Vào **Cài đặt** → **Giới thiệu về điện thoại**
2. Nhấn **Build number** (Số hiệu bản dựng) **7 lần** liên tục
3. Quay lại **Cài đặt** → **Tùy chọn nhà phát triển** (Developer options)
4. Bật **USB debugging** (Gỡ lỗi USB)
5. Bật **Install via USB** (Cài đặt qua USB) nếu có

### Bước 2: Kết nối USB

1. Cắm điện thoại vào máy tính bằng cáp USB
2. Trên điện thoại, chọn **"Cho phép gỡ lỗi USB"** khi thông báo xuất hiện
3. Kiểm tra kết nối:

```bash
adb devices
# Kết quả mong đợi:
# List of devices attached
# XXXXXXX   device
```

> **WSL:** Nếu chạy Flutter trên WSL, cần cài thêm [usbipd-win](https://github.com/dorssel/usbipd-win) trên Windows để chuyển USB device vào WSL:
> ```powershell
> # PowerShell (Admin) trên Windows:
> winget install usbipd
> usbipd list                    # Tìm device Android
> usbipd bind --busid <busid>    # Bind device
> usbipd attach --wsl --busid <busid>  # Attach vào WSL
> ```
> Sau đó `adb devices` trong WSL sẽ thấy điện thoại.

### Bước 3: Xác định API_BASE_URL

Điện thoại cần gọi được tới backend. Có 3 trường hợp:

| Tình huống | API_BASE_URL |
|-----------|-------------|
| Điện thoại và máy tính cùng mạng WiFi | `http://<IP-máy-tính>:8000` |
| Khác mạng — dùng ngrok | `https://abc123.ngrok-free.app` |
| WSL — điện thoại qua USB | `http://<WSL-IP>:8000` |

Tìm IP máy tính:

```bash
# Linux / WSL
hostname -I | awk '{print $1}'

# Windows (PowerShell)
(Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi").IPAddress
```

### Bước 4: Build & chạy app

```bash
# Staff App
cd staff_app
flutter pub get
flutter run -d <device-id> --dart-define=API_BASE_URL=http://192.168.1.100:8000

# Citizen App
cd citizen_app
flutter pub get
flutter run -d <device-id> --dart-define=API_BASE_URL=http://192.168.1.100:8000
```

> **Thay `192.168.1.100` bằng IP thật** của máy chạy backend, hoặc URL ngrok.

> **Thay `<device-id>`** bằng ID từ `adb devices`, hoặc bỏ `-d` nếu chỉ có 1 thiết bị.

### Bước 5 (Tùy chọn): Kết nối qua WiFi (không cần cáp)

Sau khi đã kết nối USB thành công 1 lần:

```bash
# Đảm bảo điện thoại và máy tính cùng WiFi
adb tcpip 5555
adb connect <IP-điện-thoại>:5555
# Rút cáp USB — vẫn debug được qua WiFi
```

Tìm IP điện thoại: **Cài đặt** → **WiFi** → nhấn vào mạng đang kết nối → xem **Địa chỉ IP**.

---

## 4. Test bằng Android Emulator trên Ubuntu

### Bước 1: Kiểm tra KVM (bắt buộc cho emulator)

```bash
# Kiểm tra CPU hỗ trợ ảo hóa
egrep -c "(vmx|svm)" /proc/cpuinfo    # Kết quả > 0 là OK

# Kiểm tra KVM
ls -la /dev/kvm
# Nếu chưa có quyền:
sudo apt install -y qemu-kvm
sudo gpasswd -a $USER kvm
# Đăng xuất và đăng nhập lại (hoặc dùng lệnh tạm: sudo chmod 666 /dev/kvm)
```

> **WSL2:** KVM chỉ hoạt động trên Windows 11 Build 22000+ với WSL kernel 5.10.60+. Kiểm tra bằng `uname -r`.

### Bước 2: Cài Android SDK

```bash
# Tạo thư mục
mkdir -p ~/android-sdk/cmdline-tools

# Tải cmdline-tools
cd /tmp
wget https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip commandlinetools-linux-11076708_latest.zip
mv cmdline-tools ~/android-sdk/cmdline-tools/latest

# Đặt biến môi trường (thêm vào ~/.bashrc)
cat >> ~/.bashrc << 'EOF'
export ANDROID_HOME=$HOME/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/emulator
EOF
source ~/.bashrc

# Chấp nhận licenses
yes | sdkmanager --licenses

# Cài các package cần thiết
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0" \
           "system-images;android-34;google_apis;x86_64" "emulator"

# Cho Flutter biết đường dẫn SDK
flutter config --android-sdk ~/android-sdk
```

### Bước 3: Tạo và chạy Emulator

```bash
# Tạo AVD (Android Virtual Device)
echo "no" | avdmanager create avd \
  -n pixel_7 \
  -k "system-images;android-34;google_apis;x86_64" \
  -d "pixel_7"

# Chạy emulator
emulator -avd pixel_7 -gpu swiftshader_indirect -no-audio -no-snapshot &

# Đợi ~30 giây, kiểm tra
adb devices
# Mong đợi: emulator-5554   device
```

### Bước 4: Build & chạy app

```bash
cd staff_app
flutter pub get
flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

> **`10.0.2.2`** là alias đặc biệt của Android Emulator, trỏ tới `localhost` của máy host.

### Kiểm tra hệ thống

```bash
flutter doctor
# Mong đợi:
# [✓] Flutter
# [✓] Android toolchain
# [✓] Connected device (emulator-5554)
```

---

## 5. Test bằng Android Emulator trên Windows

### Cách A: Dùng Android Studio (Khuyến nghị)

1. **Tải Android Studio** từ https://developer.android.com/studio
2. Cài đặt — chọn **Standard** setup, sẽ tự cài Android SDK + Emulator
3. Mở **Android Studio** → **More Actions** → **Virtual Device Manager**
4. **Create Device** → chọn **Pixel 7** → **Next**
5. Chọn system image **API 34 (UpsideDownCake)** → **Download** → **Next** → **Finish**
6. Nhấn ▶️ để chạy emulator

```powershell
# Mở terminal (CMD hoặc PowerShell)
cd staff_app
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

### Cách B: Command-line (không cần Android Studio)

```powershell
# 1. Tải cmdline-tools
# Tải file: https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip
# Giải nén vào: C:\android-sdk\cmdline-tools\latest\

# 2. Đặt biến môi trường (System Environment Variables)
# ANDROID_HOME = C:\android-sdk
# PATH thêm:
#   C:\android-sdk\cmdline-tools\latest\bin
#   C:\android-sdk\platform-tools
#   C:\android-sdk\emulator

# 3. Cài packages (mở CMD as Administrator)
sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0" ^
           "system-images;android-34;google_apis;x86_64" "emulator"

# 4. Tạo AVD
echo no | avdmanager create avd -n pixel_7 ^
  -k "system-images;android-34;google_apis;x86_64" -d "pixel_7"

# 5. Chạy emulator
emulator -avd pixel_7

# 6. Chạy trên cửa sổ terminal khác
flutter config --android-sdk C:\android-sdk
cd staff_app
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

> **Lưu ý Windows:** Cần bật **Intel HAXM** hoặc **Windows Hypervisor Platform** (WHPx) trong BIOS/UEFI và Windows Features để emulator chạy nhanh. Kiểm tra: **Settings** → **Apps** → **Optional Features** → **More Windows Features** → bật **Windows Hypervisor Platform**.

---

## 6. Kịch bản test

### 6.1 Staff App — Tạo & nộp hồ sơ

> Đảm bảo backend đã seed data (`python -m src.seeds.seed_data`)

1. **Đăng nhập**: Mở app → Nhập mã nhân viên và mật khẩu (seed data tạo sẵn)
2. **Tạo hồ sơ**:
   - Nhấn "Tạo Hồ sơ mới"
   - Chọn loại thủ tục (ví dụ: "Đăng ký hộ kinh doanh")
   - Nhập thông tin công dân (CCCD, họ tên)
   - Nhấn "Tạo hồ sơ"
3. **Upload tài liệu**:
   - Trong checklist hồ sơ, nhấn vào từng slot
   - Chụp ảnh hoặc chọn file ảnh từ thư viện
   - Chờ AI validate (badge sẽ hiển thị kết quả)
4. **Nộp hồ sơ**:
   - Khi tất cả nhóm tài liệu đã hoàn thành (checkmark xanh)
   - Nhấn "Nộp hồ sơ"
   - Ghi nhận mã tham chiếu (HS-YYYYMMDD-NNNNN)

### 6.2 Staff App — Xử lý hồ sơ

1. Nhấn "Hàng đợi xử lý" từ màn hình chính
2. Chọn một hồ sơ trong danh sách
3. Xem chi tiết, phê duyệt hoặc yêu cầu bổ sung

### 6.3 Citizen App — Tra cứu hồ sơ

1. **Đăng nhập** bằng số CCCD (mô phỏng VNeID)
2. **Tra cứu hồ sơ**: Nhập mã tham chiếu từ bước Staff #4
3. Xem timeline tiến độ xử lý

### 6.4 API Smoke Test (không cần app)

Dùng Swagger UI tại `http://<backend-url>:8000/docs` hoặc curl:

```bash
API=http://localhost:8000

# 1. Đăng nhập staff
TOKEN=$(curl -s -X POST "$API/v1/staff/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"employee_id":"NV001","password":"password123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Xem danh sách Case Types  
curl -s "$API/v1/staff/admin/case-types" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 3. Tạo dossier
CASE_TYPE_ID="<id-từ-bước-2>"
curl -s -X POST "$API/v1/staff/dossiers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"case_type_id\":\"$CASE_TYPE_ID\",\"citizen_id_number\":\"012345678901\",\"citizen_name\":\"Nguyễn Văn A\"}" | python3 -m json.tool
```

---

## 7. Khắc phục lỗi thường gặp

### Điện thoại không thấy trong `adb devices`

| Triệu chứng | Giải pháp |
|-------------|-----------|
| Danh sách trống | Kiểm tra cáp USB, bật USB debugging, thử đổi cáp |
| `unauthorized` | Nhấn "Cho phép" trên popup điện thoại |
| WSL không thấy USB | Cài `usbipd-win` và attach (xem Bước 2 mục 3) |

### App không kết nối được Backend

| Triệu chứng | Giải pháp |
|-------------|-----------|
| Connection refused | Kiểm tra backend chạy với `--host 0.0.0.0` |
| Timeout trên điện thoại thật | Kiểm tra cùng WiFi, thử `ping <IP>` từ terminal app |
| Timeout trên emulator | Dùng `10.0.2.2` thay vì `localhost` |
| `CLEARTEXT not permitted` | Android 9+ chặn HTTP. Thêm vào `android/app/src/main/AndroidManifest.xml`: `android:usesCleartextTraffic="true"` trong tag `<application>` |

### Emulator không chạy

| Triệu chứng | Giải pháp |
|-------------|-----------|
| KVM permission denied (Linux) | `sudo gpasswd -a $USER kvm` + đăng xuất/đăng nhập |
| HAXM not installed (Windows) | Bật Intel VT-x trong BIOS + cài HAXM hoặc WHPx |
| Chậm / lag nặng | Dùng `-gpu swiftshader_indirect` hoặc tăng RAM: `-memory 4096` |
| Emulator đen màn hình | Thử `-gpu angle_indirect` hoặc `-gpu guest` |

### Gradle build lỗi

| Triệu chứng | Giải pháp |
|-------------|-----------|
| `JAVA_HOME not set` | `export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64` |
| Java version conflict | Cần JDK 17 (không phải 18 hay 21). Kiểm tra `java -version` |
| `minSdkVersion` lỗi | Đặt `minSdk = 21` trong `android/app/build.gradle` |
| `Could not resolve shared_dart` | Chạy `flutter pub get` trong thư mục `shared_dart/` trước |

### Flutter không tìm thấy thiết bị

```bash
# Kiểm tra tất cả
flutter doctor -v
flutter devices

# Sửa lỗi Android SDK
flutter config --android-sdk /path/to/android-sdk
yes | sdkmanager --licenses
```

---

## Tóm tắt nhanh

```
┌─────────────────────────────────────────────────────────┐
│                    MÁY TÍNH (HOST)                      │
│                                                         │
│   docker compose up -d     ← Infra (PG, Redis, RMQ)    │
│   uvicorn ... --host 0.0.0.0 --port 8000  ← Backend    │
│                                                         │
│   IP: 192.168.x.x (LAN) hoặc ngrok URL (internet)      │
└───────────────┬─────────────────────────┬───────────────┘
                │                         │
    ┌───────────▼──────────┐   ┌──────────▼───────────┐
    │  ĐIỆN THOẠI THẬT     │   │  ANDROID EMULATOR    │
    │                      │   │                      │
    │  API_BASE_URL =      │   │  API_BASE_URL =      │
    │  http://192.168.x.x  │   │  http://10.0.2.2     │
    │        :8000         │   │        :8000         │
    │                      │   │                      │
    │  Kết nối: USB hoặc   │   │  Ubuntu: KVM         │
    │  WiFi (adb tcpip)    │   │  Windows: HAXM/WHPx  │
    └──────────────────────┘   └──────────────────────┘
```

**Lệnh chạy nhanh:**

```bash
# Staff App
cd staff_app && flutter run --dart-define=API_BASE_URL=http://<IP>:8000

# Citizen App
cd citizen_app && flutter run --dart-define=API_BASE_URL=http://<IP>:8000
```
