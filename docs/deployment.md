# Hướng dẫn Deploy lên Alibaba Cloud

Hướng dẫn cài đặt Alibaba Cloud CLI, xác thực, và deploy hạ tầng bằng Terraform.

## Tổng quan kiến trúc deploy

```
┌─ Alibaba Cloud (ap-southeast-1) ──────────────────────┐
│                                                        │
│  SLB (Internet) ──► ECS Instance ──► Docker            │
│       :80              │              ├── FastAPI :8000 │
│                        │              │   ├── /v1/*     │
│                        │              │   ├── /vneid/*  │
│                        │              │   └── /files/*  │
│                        │              ├── Mock VNeID    │
│                        │              │   :9000         │
│                        │              └── Celery Worker │
│                        │                  (optional)    │
│                        │                               │
│                        ▼                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │  RDS PostgreSQL 16   │  Redis 5.0                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  File storage: /data/uploads trên ECS                  │
│  (hoặc Alibaba Cloud OSS nếu STORAGE_BACKEND=oss)     │
└────────────────────────────────────────────────────────┘

Flutter apps (staff_app, citizen_app) chạy trên thiết bị người dùng,
kết nối tới SLB endpoint qua HTTP/HTTPS.
```

> **Lưu ý:** Deploy hiện tại dùng `docker save/scp/load` thay vì ACR (Container Registry), và local filesystem thay vì OSS. Phù hợp cho demo/dev.

## Bước 0: Cài đặt công cụ

### Terraform

```bash
# Ubuntu/Debian
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# macOS
brew tap hashicorp/tap && brew install hashicorp/tap/terraform

# Kiểm tra
terraform version
```

### Alibaba Cloud CLI (`aliyun`)

```bash
# Linux
curl -fsSL https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.tgz | tar xz
sudo mv aliyun /usr/local/bin/

# macOS
brew install aliyun-cli

# Kiểm tra
aliyun version
```

### Docker (để build image)

```bash
docker --version
```

## Bước 1: Đăng nhập Alibaba Cloud CLI

Tạo Access Key tại: https://ram.console.aliyun.com/manage/ak

```bash
aliyun configure
```

Nhập:
- **Access Key ID**: `LTAI5t...` (từ RAM console)
- **Access Key Secret**: `xxxxx` (từ RAM console)
- **Region Id**: `ap-southeast-1` (Singapore)
- **Output Format**: `json`

Kiểm tra kết nối:

```bash
aliyun ecs DescribeRegions --output cols=RegionId,LocalName rows=Regions.Region[]
```

> **Lưu ý**: CLI lưu credentials tại `~/.aliyun/config.json`. Terraform đọc file này qua tham số `profile = "default"`.

## Bước 2: Cấu hình Terraform

### Sửa `terraform.tfvars`

Mở file `infra/terraform/terraform.tfvars` và thay đổi mật khẩu + API key:

```hcl
# Bắt buộc thay đổi:
db_password       = "MatKhau_PostgreSQL_Manh!"
redis_password    = "MatKhau_Redis_Manh!"
ecs_password      = "MatKhau_ECS_Manh!"
jwt_secret_key    = "chuoi-ngau-nhien-dai-64-ky-tu-o-day"
dashscope_api_key = "sk-your-model-studio-key"

# VNeID mock server:
vneid_jwt_secret    = "mock-vneid-secret-key"
vneid_client_id     = "citizen-app"
vneid_client_secret = "mock-secret"

# Tùy chọn:
environment       = "dev"       # dev | staging | prod
region            = "ap-southeast-1"
availability_zone = "ap-southeast-1c"
```

### Yêu cầu mật khẩu ECS

Mật khẩu ECS yêu cầu: 8–30 ký tự, ít nhất 3 trong 4 loại (chữ hoa, chữ thường, số, ký tự đặc biệt).

### RDS Service Linked Role

Trước khi tạo RDS, cần tạo Service Linked Role (chỉ cần 1 lần):

```bash
aliyun rds CreateServiceLinkedRole --ServiceLinkedRole AliyunServiceRoleForRdsPgsqlOnEcs --RegionId ap-southeast-1
```

## Bước 3: Khởi tạo & Deploy hạ tầng

```bash
cd infra/terraform

# Tải provider alicloud
terraform init

# Xem trước thay đổi
terraform plan

# Tạo hạ tầng (nhập "yes" để xác nhận)
terraform apply
```

Quá trình mất ~5–10 phút. Sau khi xong, Terraform hiển thị outputs:

```
api_base_url         = "http://43.xx.xx.xx"
ecs_public_ip        = "47.xx.xx.xx"
slb_public_ip        = "43.xx.xx.xx"
database_url         = "postgresql+psycopg://..."
redis_url            = "redis://...:6379/0"
vneid_base_url       = "http://mock-vneid:9000"
```

## Bước 4: Setup SSH key

```bash
ECS_IP=$(cd infra/terraform && terraform output -raw ecs_public_ip)

# Copy SSH key lên ECS (sử dụng mật khẩu ECS)
ssh-copy-id root@$ECS_IP

# Test SSH (không cần mật khẩu)
ssh root@$ECS_IP "echo OK"
```

## Bước 5: Build & Deploy Docker images

Không cần Container Registry — build image trên máy local, transfer qua SSH:

### Build images

```bash
# Backend
cd backend
docker build -t ps-backend:latest .

# Mock VNeID
cd ../mock_vneid
docker build -t ps-mock-vneid:latest .
```

### Transfer images tới ECS

```bash
ECS_IP=$(cd infra/terraform && terraform output -raw ecs_public_ip)

# Export & transfer (nén pipeline, không cần file tạm)
docker save ps-backend:latest | gzip | ssh root@$ECS_IP "gunzip | docker load"
docker save ps-mock-vneid:latest | gzip | ssh root@$ECS_IP "gunzip | docker load"
```

### Tạo file .env trên ECS

```bash
cd infra/terraform

# Generate .env từ terraform outputs
python3 -c "
import json, subprocess
def tf(key):
    return subprocess.check_output(['terraform','output','-raw',key]).decode().strip()

lines = [
    f'DATABASE_URL={tf(\"database_url\")}',
    f'REDIS_URL={tf(\"redis_url\")}',
    f'DASHSCOPE_API_KEY={tf(\"dashscope_api_key\")}',
    f'JWT_SECRET_KEY={tf(\"jwt_secret_key\")}',
    f'VNEID_BASE_URL=http://mock-vneid:9000',
    f'VNEID_JWT_SECRET={tf(\"vneid_jwt_secret\")}',
    'STORAGE_BACKEND=local',
    'LOCAL_STORAGE_PATH=/data/uploads',
    'CELERY_BROKER_URL=redis://localhost:6379/1',
    'CELERY_RESULT_BACKEND=redis://localhost:6379/2',
]
print(chr(10).join(lines))
" > /tmp/ps-env

scp /tmp/ps-env root@$ECS_IP:/opt/public-sector/.env
```

### Tạo docker-compose.yml trên ECS

```bash
ssh root@$ECS_IP "cat > /opt/public-sector/docker-compose.yml" << 'COMPOSE'
services:
  backend:
    image: ps-backend:latest
    restart: always
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - uploads:/data/uploads
    depends_on:
      - mock-vneid

  mock-vneid:
    image: ps-mock-vneid:latest
    restart: always
    environment:
      VNEID_JWT_SECRET: ${VNEID_JWT_SECRET:-mock-vneid-secret-key}

volumes:
  uploads:
COMPOSE
```

### Start containers

```bash
ssh root@$ECS_IP "cd /opt/public-sector && docker compose up -d"
```

## Bước 6: Chạy migration & seed data

```bash
ECS_IP=$(cd infra/terraform && terraform output -raw ecs_public_ip)

# RDS cần GRANT quyền trước (chỉ lần đầu)
# Kết nối RDS qua psql và chạy:
#   GRANT ALL ON SCHEMA public TO ps_admin;

# Chạy Alembic migration
ssh root@$ECS_IP "cd /opt/public-sector && docker compose exec backend alembic upgrade head"

# Seed data (idempotent — chạy bao nhiêu lần cũng được)
ssh root@$ECS_IP "cd /opt/public-sector && docker compose exec backend python -m src.seeds.seed_data"
```

## Bước 7: Kiểm tra

```bash
SLB_IP=$(cd infra/terraform && terraform output -raw slb_public_ip)

# Swagger UI
echo "Swagger UI: http://$SLB_IP/docs"

# Backend API
curl -s "http://$SLB_IP/docs" | head -1

# VNeID health
curl -s "http://$SLB_IP/vneid/health"
# → {"status":"ok","service":"mock-vneid"}

# VNeID login page (mở trong browser)
echo "VNeID login: http://$SLB_IP/vneid/authorize"

# Auth URL endpoint
curl -s "http://$SLB_IP/v1/citizen/auth/vneid/authorize-url?redirect_uri=citizen-app://callback"
```

## Bước 8: Build Flutter apps với API URL

`API_BASE_URL` trong cả hai Flutter app là **compile-time constant** (dùng `String.fromEnvironment`), nên phải truyền URL vào lúc `flutter build` qua `--dart-define`.

```bash
# Lấy SLB URL từ Terraform output
cd infra/terraform
SLB_IP=$(terraform output -raw slb_public_ip)

# Build citizen app
cd ../../citizen_app
flutter build apk --dart-define=API_BASE_URL=http://$SLB_IP

# Build staff app
cd ../staff_app
flutter build apk --dart-define=API_BASE_URL=http://$SLB_IP
```

> **Lưu ý**: Nếu không truyền `--dart-define`, app sẽ dùng `defaultValue: 'http://localhost:8000'` — không kết nối được server thật.

Trong production, nên:
1. Mua domain và trỏ DNS A record tới `slb_public_ip`
2. Cấu hình HTTPS certificate trên SLB
3. Đổi SLB listener từ HTTP sang HTTPS
4. Dùng `https://your-domain.vn` thay cho IP thô trong `--dart-define`

## Cập nhật code (re-deploy)

Sau khi sửa code, deploy lại bằng:

```bash
ECS_IP=$(cd infra/terraform && terraform output -raw ecs_public_ip)

# Rebuild image
cd backend && docker build -t ps-backend:latest .

# Transfer & restart
docker save ps-backend:latest | gzip | ssh root@$ECS_IP "gunzip | docker load"
ssh root@$ECS_IP "cd /opt/public-sector && docker compose up -d --force-recreate backend"
```

## Các lệnh hữu ích

```bash
# Xem tất cả outputs
cd infra/terraform && terraform output

# Xem output nhạy cảm (database URL, redis URL)
terraform output -raw database_url
terraform output -raw redis_url

# Xem trạng thái hạ tầng
terraform show

# Cập nhật hạ tầng sau khi sửa .tf files
terraform plan && terraform apply

# Xem logs trên ECS
ssh root@$ECS_IP "cd /opt/public-sector && docker compose logs -f backend"
ssh root@$ECS_IP "cd /opt/public-sector && docker compose logs -f mock-vneid"

# Hủy toàn bộ hạ tầng (CẨN THẬN!)
terraform destroy
```

## Xử lý sự cố

### Không kết nối được RDS

- Kiểm tra security group cho phép port PostgreSQL (5432)
- Kiểm tra `security_ips` của RDS chứa VPC CIDR
- Chạy: `GRANT ALL ON SCHEMA public TO ps_admin;` nếu lần đầu

### Alembic: ModuleNotFoundError

Đảm bảo `ENV PYTHONPATH=/app` có trong `backend/Dockerfile`.

### Alembic kết nối localhost thay vì RDS

Đảm bảo `backend/alembic/env.py` đọc `DATABASE_URL` từ env var (đã có sẵn).

### bcrypt lỗi ValueError

Đảm bảo `bcrypt==4.0.1` trong `pyproject.toml` (passlib compatibility).

### SLB port khác 80 không accessible

SLB spec `slb.s1.small` có thể chỉ hỗ trợ port 80/443. Sử dụng reverse proxy `/vneid/*` trên backend thay vì expose port riêng.

### Terraform state bị lỗi

```bash
# Import resource đã tồn tại
terraform import alicloud_vpc.main vpc-xxxxxxxxxx

# Xóa resource khỏi state (không xóa thật)
terraform state rm alicloud_instance.backend
```

## Chi phí ước tính (dev tier)

| Resource | Spec | ~USD/tháng |
|----------|------|-----------|
| ECS | ecs.t5-lc1m1.small (1C/1G) | ~10 |
| RDS PostgreSQL | pg.n2.2c.1m (2C/1G, 20GB cloud_essd) | ~20 |
| Redis | redis.master.micro.default (1GB, v5.0) | ~15 |
| SLB | slb.s1.small | ~5 |
| **Tổng** | | **~$50/tháng** |

> Chi phí thực tế phụ thuộc vào traffic và dung lượng lưu trữ.
