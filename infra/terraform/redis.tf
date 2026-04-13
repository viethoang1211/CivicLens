# ──────────────────────────────────────────────
# Redis (Tair-compatible)
# ──────────────────────────────────────────────
resource "alicloud_kvstore_instance" "redis" {
  db_instance_name = "${var.project_name}-${var.environment}-redis"
  instance_class   = var.redis_instance_class
  instance_type    = "Redis"
  engine_version   = "7.0"
  vswitch_id       = alicloud_vswitch.main.id
  security_ips     = [var.vpc_cidr]
  password         = var.redis_password
  payment_type     = "PostPaid"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}
