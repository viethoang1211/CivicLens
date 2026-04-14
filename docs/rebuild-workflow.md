# Quy trình Rebuild sau khi sửa code

Hướng dẫn nhanh để rebuild và deploy sau khi sửa code cho từng thành phần.

---

## Thông tin kết nối

| Thông tin | Giá trị |
|-----------|---------|
| **SLB (API endpoint)** | `http://43.98.196.158` |
| **ECS (SSH)** | `root@47.236.130.178` |
| **SSH Key** | `~/.ssh/id_ed25519` (đã cài) |

---

## 1. Sửa Staff App (Flutter)

### Đang chạy debug (hot reload)

Nếu đang chạy `flutter run`, chỉ cần:
- Nhấn **`r`** trong terminal → Hot reload (giữ state, cập nhật UI)
- Nhấn **`R`** → Hot restart (reset state, load lại từ đầu)
- Nhấn **`q`** → Thoát app

### Build APK mới

```powershell
$env:PATH = "C:\flutter\bin;" + $env:PATH
cd staff_app
flutter build apk --dart-define=API_BASE_URL=http://43.98.196.158
```

File APK tại: `staff_app/build/app/outputs/flutter-apk/app-release.apk`

### Chạy trực tiếp trên thiết bị đã kết nối

```powershell
$env:PATH = "C:\flutter\bin;" + $env:PATH
cd staff_app

# Xem danh sách thiết bị
flutter devices

# Chạy trên thiết bị cụ thể
flutter run -d <device-id> --dart-define=API_BASE_URL=http://43.98.196.158
```

---

## 2. Sửa Citizen App (Flutter)

### Hot reload (giống Staff App)

```powershell
# Nhấn r / R / q trong terminal đang chạy flutter run
```

### Build APK

```powershell
$env:PATH = "C:\flutter\bin;" + $env:PATH
cd citizen_app
flutter build apk --dart-define=API_BASE_URL=http://43.98.196.158
```

File APK tại: `citizen_app/build/app/outputs/flutter-apk/app-release.apk`

### Chạy trên thiết bị

```powershell
$env:PATH = "C:\flutter\bin;" + $env:PATH
cd citizen_app
flutter run -d <device-id> --dart-define=API_BASE_URL=http://43.98.196.158
```

---

## 3. Sửa shared_dart (Shared Dart package)

`shared_dart` được import bằng `path: ../shared_dart` trong cả 2 app. Sau khi sửa:

```powershell
$env:PATH = "C:\flutter\bin;" + $env:PATH

# Chạy lại pub get ở app cần update
cd staff_app && flutter pub get
cd ../citizen_app && flutter pub get

# Nếu đang chạy debug → nhấn R (Hot restart) hoặc chạy lại flutter run
```

---

## 4. Sửa Backend (Python) → Deploy lên Cloud

### Bước 1: Build Docker image

```powershell
cd backend
docker build -t ps-backend:latest .
```

### Bước 2: Transfer image lên ECS

```powershell
# Lưu image ra file tạm, SCP lên server, rồi load
docker save ps-backend:latest -o "$env:TEMP\ps-backend.tar"
scp "$env:TEMP\ps-backend.tar" root@47.236.130.178:/tmp/
ssh root@47.236.130.178 "docker load < /tmp/ps-backend.tar; rm /tmp/ps-backend.tar"
```

### Bước 3: Restart container

```powershell
ssh root@47.236.130.178 "cd /opt/public-sector; docker-compose up -d --force-recreate backend"
```

### Bước 4 (nếu đổi DB schema): Chạy migration

```powershell
ssh root@47.236.130.178 "cd /opt/public-sector; docker-compose exec backend alembic upgrade head"
```

### Bước 5 (nếu thêm seed data): Seed lại

```powershell
ssh root@47.236.130.178 "cd /opt/public-sector; docker-compose exec backend python -m src.seeds.seed_data"
```

### Xem logs backend

```powershell
ssh root@47.236.130.178 "cd /opt/public-sector; docker-compose logs -f --tail=50 backend"
```

---

## 5. Sửa Mock VNeID → Deploy lên Cloud

```powershell
# Build
cd mock_vneid
docker build -t ps-mock-vneid:latest .

# Transfer
docker save ps-mock-vneid:latest -o "$env:TEMP\ps-mock-vneid.tar"
scp "$env:TEMP\ps-mock-vneid.tar" root@47.236.130.178:/tmp/
ssh root@47.236.130.178 "docker load < /tmp/ps-mock-vneid.tar; rm /tmp/ps-mock-vneid.tar"

# Restart
ssh root@47.236.130.178 "cd /opt/public-sector; docker-compose up -d --force-recreate mock-vneid"
```

---

## 6. Sửa cả Backend + Mock VNeID cùng lúc

```powershell
# Build cả 2
cd backend && docker build -t ps-backend:latest .
cd ../mock_vneid && docker build -t ps-mock-vneid:latest .

# Transfer cả 2
docker save ps-backend:latest -o "$env:TEMP\ps-backend.tar"
docker save ps-mock-vneid:latest -o "$env:TEMP\ps-mock-vneid.tar"
scp "$env:TEMP\ps-backend.tar" "$env:TEMP\ps-mock-vneid.tar" root@47.236.130.178:/tmp/
ssh root@47.236.130.178 "docker load < /tmp/ps-backend.tar; docker load < /tmp/ps-mock-vneid.tar; rm /tmp/ps-backend.tar /tmp/ps-mock-vneid.tar"

# Restart cả 2
ssh root@47.236.130.178 "cd /opt/public-sector; docker-compose up -d --force-recreate backend mock-vneid"
```

---

## Lệnh hữu ích

```powershell
# Xem trạng thái container trên server
ssh root@47.236.130.178 "cd /opt/public-sector; docker-compose ps"

# Restart tất cả container
ssh root@47.236.130.178 "cd /opt/public-sector; docker-compose restart"

# Xem logs realtime (Ctrl+C để thoát)
ssh root@47.236.130.178 "cd /opt/public-sector; docker-compose logs -f"

# Test API
Invoke-RestMethod -Uri "http://43.98.196.158/docs"
Invoke-RestMethod -Uri "http://43.98.196.158/vneid/health"

# Flutter: thêm Flutter vào PATH (mỗi terminal mới cần chạy lại)
$env:PATH = "C:\flutter\bin;" + $env:PATH
```

---

## Lưu ý quan trọng

1. **Flutter PATH**: Mỗi terminal PowerShell mới cần chạy `$env:PATH = "C:\flutter\bin;" + $env:PATH` trước khi dùng lệnh flutter. Hoặc thêm `C:\flutter\bin` vào System PATH vĩnh viễn.

2. **`--dart-define` là bắt buộc**: Nếu không truyền `API_BASE_URL`, app sẽ kết nối `localhost` và không hoạt động.

3. **SSH không cần mật khẩu**: SSH key đã được cài, kết nối trực tiếp bằng `ssh root@47.236.130.178`.

4. **SLB vs ECS**: API endpoint (cho app) dùng SLB IP `43.98.196.158`. SSH dùng ECS IP `47.236.130.178`.

5. **docker-compose** (có dấu gạch ngang): Server cài bản cũ, dùng `docker-compose` thay vì `docker compose`.
