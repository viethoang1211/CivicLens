# ──────────────────────────────────────────────
# Container Registry (ACR) — Push Docker images
# ──────────────────────────────────────────────
resource "alicloud_cr_namespace" "main" {
  name               = replace(var.project_name, "-", "")
  auto_create        = false
  default_visibility = "PRIVATE"
}

resource "alicloud_cr_repo" "backend" {
  namespace = alicloud_cr_namespace.main.name
  name      = "backend"
  repo_type = "PRIVATE"
  summary   = "Public Sector Backend API"
}

# ──────────────────────────────────────────────
# ECS Instance — Backend API + Celery Workers
# ──────────────────────────────────────────────
data "alicloud_images" "ubuntu" {
  name_regex  = "^ubuntu_22"
  most_recent = true
  owners      = "system"
}

resource "alicloud_instance" "backend" {
  instance_name        = "${var.project_name}-${var.environment}-backend"
  instance_type        = var.ecs_instance_type
  image_id             = data.alicloud_images.ubuntu.images[0].id
  security_groups      = [alicloud_security_group.backend.id]
  vswitch_id           = alicloud_vswitch.main.id
  internet_max_bandwidth_out = 10 # Mbps — for pulling images + API traffic
  system_disk_category = "cloud_efficiency"
  system_disk_size     = 40
  password             = var.ecs_password

  # Cloud-init: install Docker + deploy backend
  user_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
    region          = var.region
    acr_namespace   = alicloud_cr_namespace.main.name
    acr_registry    = "registry.${var.region}.aliyuncs.com"
    db_host         = alicloud_db_instance.postgres.connection_string
    db_port         = "3432"
    db_name         = var.db_name
    db_username     = var.db_username
    db_password     = var.db_password
    redis_host      = alicloud_kvstore_instance.redis.connection_domain
    redis_password  = var.redis_password
    oss_bucket      = alicloud_oss_bucket.documents.bucket
    oss_endpoint    = "https://oss-${var.region}.aliyuncs.com"
    jwt_secret_key  = var.jwt_secret_key
    dashscope_key   = var.dashscope_api_key
  }))

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Role        = "backend"
  }
}
