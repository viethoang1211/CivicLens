# ──────────────────────────────────────────────
# VPC + VSwitch
# ──────────────────────────────────────────────
resource "alicloud_vpc" "main" {
  vpc_name   = "${var.project_name}-${var.environment}-vpc"
  cidr_block = var.vpc_cidr
}

resource "alicloud_vswitch" "main" {
  vswitch_name  = "${var.project_name}-${var.environment}-vsw"
  vpc_id        = alicloud_vpc.main.id
  cidr_block    = var.vswitch_cidr
  zone_id       = var.availability_zone
}
