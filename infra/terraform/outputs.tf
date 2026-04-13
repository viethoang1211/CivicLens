# ──────────────────────────────────────────────
# Outputs
# ──────────────────────────────────────────────

output "vpc_id" {
  value = alicloud_vpc.main.id
}

# ── Database ──
output "rds_connection_string" {
  description = "RDS PostgreSQL internal endpoint"
  value       = alicloud_db_instance.postgres.connection_string
}

output "rds_port" {
  description = "RDS PostgreSQL port"
  value       = alicloud_db_instance.postgres.port
}

output "database_url" {
  description = "Full DATABASE_URL for backend .env"
  value       = "postgresql+psycopg://${var.db_username}:${var.db_password}@${alicloud_db_instance.postgres.connection_string}:${alicloud_db_instance.postgres.port}/${var.db_name}"
  sensitive   = true
}

# ── Redis ──
output "redis_connection_domain" {
  description = "Redis internal endpoint"
  value       = alicloud_kvstore_instance.redis.connection_domain
}

output "redis_url" {
  description = "Full REDIS_URL for backend .env"
  value       = "redis://:${var.redis_password}@${alicloud_kvstore_instance.redis.connection_domain}:6379/0"
  sensitive   = true
}

# ── ECS ──
output "ecs_public_ip" {
  description = "Backend ECS public IP"
  value       = alicloud_instance.backend.public_ip
}

# ── SLB ──
output "slb_public_ip" {
  description = "SLB public IP — point your domain here"
  value       = alicloud_slb_load_balancer.api.address
}

output "api_base_url" {
  description = "API base URL via SLB"
  value       = "http://${alicloud_slb_load_balancer.api.address}"
}

output "vneid_base_url" {
  description = "Mock VNeID OAuth base URL (via SLB)"
  value       = "http://${alicloud_slb_load_balancer.api.address}:9000"
}
