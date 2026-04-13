# ──────────────────────────────────────────────
# Server Load Balancer (SLB) — Public HTTPS endpoint
# ──────────────────────────────────────────────
resource "alicloud_slb_load_balancer" "api" {
  load_balancer_name = "${var.project_name}-${var.environment}-slb"
  address_type       = "internet"
  load_balancer_spec = "slb.s1.small"
  vswitch_id         = alicloud_vswitch.main.id

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# HTTP listener (upgrade to HTTPS with certificate in production)
resource "alicloud_slb_listener" "http" {
  load_balancer_id = alicloud_slb_load_balancer.api.id
  frontend_port    = 80
  backend_port     = 8000
  protocol         = "http"
  bandwidth        = 10
  health_check     = "on"
  health_check_uri = "/docs"
}

# Attach backend ECS to SLB
resource "alicloud_slb_backend_server" "backend" {
  load_balancer_id = alicloud_slb_load_balancer.api.id

  backend_servers {
    server_id = alicloud_instance.backend.id
    weight    = 100
  }
}
