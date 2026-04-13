# ──────────────────────────────────────────────
# ECS Instance — Backend API + Celery Workers
# ──────────────────────────────────────────────
data "alicloud_images" "ubuntu" {
  name_regex   = "^ubuntu_22_04_x64_20G"
  most_recent  = true
  owners       = "system"
  architecture = "x86_64"
}

resource "alicloud_instance" "backend" {
  instance_name        = "${var.project_name}-${var.environment}-backend"
  instance_type        = var.ecs_instance_type
  image_id             = data.alicloud_images.ubuntu.images[0].id
  security_groups      = [alicloud_security_group.backend.id]
  vswitch_id           = alicloud_vswitch.main.id
  internet_max_bandwidth_out = 10 # Mbps — for API traffic
  system_disk_category = "cloud_efficiency"
  system_disk_size     = 40
  password             = var.ecs_password

  # Cloud-init: install Docker
  user_data = base64encode(templatefile("${path.module}/cloud-init.yaml", {
    db_host             = alicloud_db_instance.postgres.connection_string
    db_port             = "3432"
    db_name             = var.db_name
    db_username         = var.db_username
    db_password         = var.db_password
    redis_host          = alicloud_kvstore_instance.redis.connection_domain
    redis_password      = var.redis_password
    jwt_secret_key      = var.jwt_secret_key
    dashscope_key       = var.dashscope_api_key
    vneid_jwt_secret    = var.vneid_jwt_secret
    vneid_client_id     = var.vneid_client_id
    vneid_client_secret = var.vneid_client_secret
  }))

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Role        = "backend"
  }
}
