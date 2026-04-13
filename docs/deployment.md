# Hướng dẫn Deploy lên Alibaba Cloud

Hướng dẫn cài đặt Alibaba Cloud CLI, xác thực, và deploy hạ tầng bằng Terraform.

## Tổng quan kiến trúc deploy

```
┌─ Alibaba Cloud (ap-southeast-1) ──────────────────────┐
│                                                        │
│  SLB (Internet) ──► ECS Instance ──► Docker            │
│       :80              │              ├── FastAPI :8000 │
│                        │              └── Celery Worker │
│                        │                               │
│                        ▼                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │  RDS PostgreSQL 16   │  Redis 7   │  OSS Bucket  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ACR (Container Registry) — lưu Docker image backend   │
└────────────────────────────────────────────────────────┘

Flutter apps (staff_app, citizen_app) chạy trên thiết bị người dùng,
kết nối tới SLB endpoint qua HTTPS.
```

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

### Docker (để build & push image)

```bash
# Kiểm tra Docker đã cài
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

# Tùy chọn:
environment       = "dev"       # dev | staging | prod
region            = "ap-southeast-1"
availability_zone = "ap-southeast-1a"
```

### Yêu cầu mật khẩu ECS

Mật khẩu ECS yêu cầu: 8–30 ký tự, ít nhất 3 trong 4 loại (chữ hoa, chữ thường, số, ký tự đặc biệt).

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
api_base_url         = "http://47.xx.xx.xx"
acr_registry         = "registry.ap-southeast-1.aliyuncs.com/publicsector/backend"
ecs_public_ip        = "47.xx.xx.xx"
rds_connection_string = "rm-xxxxxxxxxx.pg.rds.aliyuncs.com"
slb_public_ip        = "47.xx.xx.xx"
```

## Bước 4: Đăng nhập Container Registry

```bash
# Lấy registry URL từ Terraform output
ACR_REGISTRY=$(terraform output -raw acr_registry)

# Đăng nhập ACR (dùng Access Key làm password)
docker login registry.ap-southeast-1.aliyuncs.com
# Username: Access Key ID (LTAI5t...)
# Password: Access Key Secret
```

## Bước 5: Build & Deploy backend

### Cách 1: Dùng deploy script (khuyến nghị)

```bash
cd infra/terraform
./deploy.sh           # Deploy tag :latest
./deploy.sh v1.0.0    # Deploy version cụ thể
```

Script tự động:
1. Build Docker image từ `backend/`
2. Push lên ACR
3. SSH vào ECS và restart containers

### Cách 2: Thủ công

```bash
# Build
cd backend
docker build -t "$ACR_REGISTRY:latest" .

# Push
docker push "$ACR_REGISTRY:latest"

# SSH vào ECS và deploy
ECS_IP=$(cd ../infra/terraform && terraform output -raw ecs_public_ip)
ssh root@$ECS_IP "cd /opt/public-sector && docker compose pull && docker compose up -d"
```

## Bước 6: Chạy migration & seed data

```bash
ECS_IP=$(terraform output -raw ecs_public_ip)

# Chạy Alembic migration
ssh root@$ECS_IP "docker compose -f /opt/public-sector/docker-compose.yml exec backend alembic upgrade head"

# Seed data
ssh root@$ECS_IP "docker compose -f /opt/public-sector/docker-compose.yml exec backend python -m src.seeds.seed_data"
```

## Bước 7: Kiểm tra

```bash
# Lấy API URL
SLB_URL=$(terraform output -raw api_base_url)

# Health check
curl "$SLB_URL/docs"

# Hoặc truy cập trực tiếp
echo "Swagger UI: $SLB_URL/docs"
```

## Bước 8: Build Flutter apps với API URL

`API_BASE_URL` trong cả hai Flutter app là **compile-time constant** (dùng `String.fromEnvironment`), nên phải truyền URL vào lúc `flutter build` qua `--dart-define`.

```bash
# Lấy SLB URL từ Terraform output
cd infra/terraform
SLB_URL=$(terraform output -raw api_base_url)
# Ví dụ: http://47.xx.xx.xx

# Build citizen app
cd ../../citizen_app
flutter build apk --dart-define=API_BASE_URL=$SLB_URL
# hoặc iOS:
flutter build ipa --dart-define=API_BASE_URL=$SLB_URL

# Build staff app
cd ../staff_app
flutter build apk --dart-define=API_BASE_URL=$SLB_URL
```

> **Lưu ý**: Nếu không truyền `--dart-define`, app sẽ dùng `defaultValue: 'http://10.0.2.2:8000'` (Android emulator localhost) — không kết nối được server thật.

Trong production, nên:
1. Mua domain và trỏ DNS A record tới `slb_public_ip`
2. Cấu hình HTTPS certificate trên SLB
3. Đổi SLB listener từ HTTP sang HTTPS
4. Dùng `https://your-domain.vn` thay cho IP thô trong `--dart-define`

## Các lệnh hữu ích

```bash
# Xem tất cả outputs
terraform output

# Xem output nhạy cảm (database URL, redis URL)
terraform output -raw database_url
terraform output -raw redis_url

# Xem trạng thái hạ tầng
terraform show

# Cập nhật hạ tầng sau khi sửa .tf files
terraform plan && terraform apply

# Hủy toàn bộ hạ tầng (CẨN THẬN!)
terraform destroy
```

## Xử lý sự cố

### Không kết nối được RDS

- Kiểm tra security group cho phép port PostgreSQL
- Kiểm tra `security_ips` của RDS chứa VPC CIDR
- `aliyun rds DescribeDBInstanceNetInfo --DBInstanceId <id>`

### Docker pull thất bại trên ECS

- Kiểm tra ECS có internet access (`internet_max_bandwidth_out > 0`)
- Kiểm tra ACR login: `docker login registry.ap-southeast-1.aliyuncs.com`

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
| ECS | t6-c1m1.large (2C/2G) | ~15 |
| RDS PostgreSQL | pg.n2e.small.1 (1C/1G, 20GB) | ~20 |
| Redis | micro (1GB) | ~15 |
| SLB | s1.small | ~5 |
| OSS | Pay-per-use | ~1 |
| **Tổng** | | **~$56/tháng** |

> Chi phí thực tế phụ thuộc vào traffic và dung lượng lưu trữ. Xem [Alibaba Cloud Pricing Calculator](https://www.alibabacloud.com/pricing-calculator) để ước tính chính xác.
