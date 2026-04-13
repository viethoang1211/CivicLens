# ──────────────────────────────────────────────
# RDS PostgreSQL 16
# ──────────────────────────────────────────────
resource "alicloud_db_instance" "postgres" {
  engine               = "PostgreSQL"
  engine_version       = "16.0"
  instance_type        = var.rds_instance_type
  instance_storage     = var.rds_storage_gb
  db_instance_storage_type = "cloud_essd"
  instance_name        = "${var.project_name}-${var.environment}-pg"
  vswitch_id           = alicloud_vswitch.main.id
  security_ips         = [var.vpc_cidr]
  instance_charge_type = "Postpaid"
  category             = "Basic"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "alicloud_rds_account" "admin" {
  db_instance_id   = alicloud_db_instance.postgres.id
  account_name     = var.db_username
  account_password = var.db_password
  account_type     = "Super"
}

resource "alicloud_db_database" "main" {
  instance_id    = alicloud_db_instance.postgres.id
  data_base_name = var.db_name
  depends_on     = [alicloud_rds_account.admin]
}

# Allow ECS security group to access RDS
resource "alicloud_db_connection" "main" {
  instance_id       = alicloud_db_instance.postgres.id
  connection_prefix = "${var.project_name}-${var.environment}"
}
