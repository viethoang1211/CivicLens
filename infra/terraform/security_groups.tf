# ──────────────────────────────────────────────
# Security Group — Backend ECS
# ──────────────────────────────────────────────
resource "alicloud_security_group" "backend" {
  security_group_name = "${var.project_name}-${var.environment}-backend-sg"
  vpc_id              = alicloud_vpc.main.id
}

# Allow inbound HTTP (demo: open to internet, production: VPC only)
resource "alicloud_security_group_rule" "backend_http" {
  type              = "ingress"
  ip_protocol       = "tcp"
  port_range        = "8000/8000"
  security_group_id = alicloud_security_group.backend.id
  cidr_ip           = "0.0.0.0/0"
}

# Allow mock VNeID (dev/demo only — remove in production)
resource "alicloud_security_group_rule" "backend_vneid" {
  type              = "ingress"
  ip_protocol       = "tcp"
  port_range        = "9000/9000"
  security_group_id = alicloud_security_group.backend.id
  cidr_ip           = "0.0.0.0/0"
}

# Allow SSH (restrict to your IP in production)
resource "alicloud_security_group_rule" "backend_ssh" {
  type              = "ingress"
  ip_protocol       = "tcp"
  port_range        = "22/22"
  security_group_id = alicloud_security_group.backend.id
  cidr_ip           = "0.0.0.0/0"
}

# Allow all outbound
resource "alicloud_security_group_rule" "backend_egress" {
  type              = "egress"
  ip_protocol       = "all"
  port_range        = "-1/-1"
  security_group_id = alicloud_security_group.backend.id
  cidr_ip           = "0.0.0.0/0"
}
