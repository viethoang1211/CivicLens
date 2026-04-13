terraform {
  required_version = ">= 1.5"

  required_providers {
    alicloud = {
      source  = "aliyun/alicloud"
      version = "~> 1.235"
    }
  }
}

# Uses Alibaba Cloud CLI profile for authentication.
# Run `aliyun configure` first — Terraform reads ~/.aliyun/config.json
provider "alicloud" {
  region  = var.region
  profile = var.cli_profile
}
