# ──────────────────────────────────────────────
# OSS Bucket — Document Storage
# ──────────────────────────────────────────────
resource "alicloud_oss_bucket" "documents" {
  bucket = "${var.oss_bucket_name}-${var.environment}"
  acl    = "private"

  server_side_encryption_rule {
    sse_algorithm = "AES256"
  }

  lifecycle_rule {
    id      = "archive-old-documents"
    enabled = true

    transition {
      days          = 180
      storage_class = "IA" # Infrequent Access after 6 months
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Block all public access
resource "alicloud_oss_bucket_public_access_block" "documents" {
  bucket                            = alicloud_oss_bucket.documents.bucket
  block_public_access               = true
}
