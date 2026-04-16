# ──────────────────────────────────────────────
# Default values — EDIT THESE for your environment
# ──────────────────────────────────────────────

# General
cli_profile       = "default"
region            = "ap-southeast-1"
environment       = "dev"
project_name      = "public-sector"
availability_zone = "ap-southeast-1c"

# Networking
vpc_cidr     = "10.0.0.0/16"
vswitch_cidr = "10.0.1.0/24"

# RDS PostgreSQL
rds_instance_type = "pg.n2.2c.1m"
rds_storage_gb    = 20
db_name           = "public_sector"
db_username       = "ps_admin"
db_password       = "ChangeMe_Pg_2026!"

# Redis
redis_instance_class = "redis.master.micro.default"
redis_password       = "ChangeMe_Redis_2026!"

# ECS
ecs_instance_type = "ecs.t5-lc1m2.large"
ecs_password      = "ChangeMe_Ecs_2026!"

# OSS
oss_bucket_name = "public-sector-docs"

# Application
jwt_secret_key    = "change-me-to-a-long-random-string-in-production"
dashscope_api_key = "sk-305573b4c89a4a47bdb360c98ed7ae29"

# VNeID Mock OAuth (dev/demo only — remove when using real VNeID)
vneid_jwt_secret    = "mock-vneid-secret-key"
vneid_client_id     = "citizen-app"
vneid_client_secret = "mock-secret"
