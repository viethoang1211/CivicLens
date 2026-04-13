# ──────────────────────────────────────────────
# OSS Bucket — Document Storage
# Currently disabled for demo (using ECS local storage).
# Uncomment when OSS service is activated on the account.
# ──────────────────────────────────────────────
# resource "alicloud_oss_bucket" "documents" {
#   bucket = "${var.oss_bucket_name}-${var.environment}"
#   acl    = "private"
#
#   server_side_encryption_rule {
#     sse_algorithm = "AES256"
#   }
#
#   lifecycle_rule {
#     id      = "archive-old-documents"
#     enabled = true
#     transitions {
#       days          = 180
#       storage_class = "IA"
#     }
#   }
#
#   tags = {
#     Environment = var.environment
#     Project     = var.project_name
#   }
# }
#
# resource "alicloud_oss_bucket_public_access_block" "documents" {
#   bucket              = alicloud_oss_bucket.documents.bucket
#   block_public_access = true
# }
