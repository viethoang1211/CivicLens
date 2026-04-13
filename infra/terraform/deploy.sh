#!/usr/bin/env bash
# deploy.sh — Build Docker images locally, transfer to ECS via SCP, restart
#
# Usage:
#   ./deploy.sh                  # Full deploy (build + transfer + restart)
#   ./deploy.sh --restart-only   # Just restart containers on ECS
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../../backend"
MOCK_VNEID_DIR="$SCRIPT_DIR/../../mock_vneid"
TF_DIR="$SCRIPT_DIR"

# Read ECS IP from Terraform
cd "$TF_DIR"
ECS_IP=$(terraform output -raw ecs_public_ip)
SSH_CMD="ssh -o StrictHostKeyChecking=no root@$ECS_IP"

if [ "${1:-}" = "--restart-only" ]; then
  echo "==> Restarting containers on ECS ($ECS_IP)..."
  $SSH_CMD "cd /opt/public-sector && docker compose up -d"
  echo "==> Done! API: http://$ECS_IP:8000/docs"
  exit 0
fi

echo "==> Building backend Docker image..."
cd "$BACKEND_DIR"
docker build -t ps-backend:latest .

echo "==> Building mock VNeID Docker image..."
cd "$MOCK_VNEID_DIR"
docker build -t ps-mock-vneid:latest .

echo "==> Saving images to tar..."
cd /tmp
docker save ps-backend:latest ps-mock-vneid:latest | gzip > ps-images.tar.gz
IMAGE_SIZE=$(du -h /tmp/ps-images.tar.gz | cut -f1)
echo "    Image archive: $IMAGE_SIZE"

echo "==> Transferring to ECS ($ECS_IP)..."
scp -o StrictHostKeyChecking=no /tmp/ps-images.tar.gz "root@$ECS_IP:/tmp/"

echo "==> Loading images on ECS..."
$SSH_CMD "gunzip -c /tmp/ps-images.tar.gz | docker load && rm /tmp/ps-images.tar.gz"

echo "==> Restarting services..."
$SSH_CMD "cd /opt/public-sector && docker compose up -d"

# Cleanup local tar
rm -f /tmp/ps-images.tar.gz

echo ""
echo "==> Deploy complete!"
echo "    API:   http://$ECS_IP:8000/docs"
echo "    VNeID: http://$ECS_IP:9000/health"
cd "$TF_DIR"
echo "    SLB:   $(terraform output -raw api_base_url)/docs"
