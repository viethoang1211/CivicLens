# ──────────────────────────────────────────────
# General
# ──────────────────────────────────────────────
variable "cli_profile" {
  description = "Alibaba Cloud CLI profile name (from `aliyun configure`)"
  type        = string
  default     = "default"
}

variable "region" {
  description = "Alibaba Cloud region"
  type        = string
  default     = "ap-southeast-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project prefix for resource naming"
  type        = string
  default     = "public-sector"
}

# ──────────────────────────────────────────────
# Networking
# ──────────────────────────────────────────────
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "vswitch_cidr" {
  description = "VSwitch CIDR block"
  type        = string
  default     = "10.0.1.0/24"
}

variable "availability_zone" {
  description = "Availability zone for resources"
  type        = string
  default     = "ap-southeast-1a"
}

# ──────────────────────────────────────────────
# RDS PostgreSQL
# ──────────────────────────────────────────────
variable "rds_instance_type" {
  description = "RDS instance class"
  type        = string
  default     = "pg.n2e.small.1" # 1 vCPU, 1 GB — dev tier
}

variable "rds_storage_gb" {
  description = "RDS storage in GB"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "public_sector"
}

variable "db_username" {
  description = "Database superuser name"
  type        = string
  default     = "ps_admin"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# ──────────────────────────────────────────────
# Redis / Tair
# ──────────────────────────────────────────────
variable "redis_instance_class" {
  description = "Redis instance class"
  type        = string
  default     = "redis.master.micro.default" # 1 GB — dev tier
}

variable "redis_password" {
  description = "Redis password"
  type        = string
  sensitive   = true
}

# ──────────────────────────────────────────────
# ECS (Backend Server)
# ──────────────────────────────────────────────
variable "ecs_instance_type" {
  description = "ECS instance type"
  type        = string
  default     = "ecs.t6-c1m1.large" # 2 vCPU, 2 GB — dev tier
}

variable "ecs_password" {
  description = "ECS root password"
  type        = string
  sensitive   = true
}

# ──────────────────────────────────────────────
# OSS
# ──────────────────────────────────────────────
variable "oss_bucket_name" {
  description = "OSS bucket name for document storage"
  type        = string
  default     = "public-sector-docs"
}

# ──────────────────────────────────────────────
# VNeID Mock OAuth (dev/demo only)
# ──────────────────────────────────────────────
variable "vneid_jwt_secret" {
  description = "JWT signing secret for mock VNeID OAuth server"
  type        = string
  sensitive   = true
  default     = "mock-vneid-secret-key"
}

variable "vneid_client_id" {
  description = "OAuth client_id for VNeID integration"
  type        = string
  default     = "citizen-app"
}

variable "vneid_client_secret" {
  description = "OAuth client_secret for VNeID integration"
  type        = string
  sensitive   = true
  default     = "mock-secret"
}

# ──────────────────────────────────────────────
# Application
# ──────────────────────────────────────────────
variable "jwt_secret_key" {
  description = "JWT signing key for the backend"
  type        = string
  sensitive   = true
}

variable "dashscope_api_key" {
  description = "Alibaba Cloud Model Studio (dashscope) API key"
  type        = string
  sensitive   = true
  default     = ""
}
