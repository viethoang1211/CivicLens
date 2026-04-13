#!/usr/bin/env bash
# deploy.sh — Build, push Docker image, and restart backend on ECS
#
# Usage:
#   ./deploy.sh                  # Push :latest and restart
#   ./deploy.sh v1.2.3           # Push with version tag
#
set -euo pipefail

TAG="${1:-latest}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../../backend"
TF_DIR="$SCRIPT_DIR"

# Read outputs from Terraform
cd "$TF_DIR"
ACR_REGISTRY=$(terraform output -raw acr_registry)
ECS_IP=$(terraform output -raw ecs_public_ip)

echo "==> Building backend Docker image..."
cd "$BACKEND_DIR"
docker build -t "$ACR_REGISTRY:$TAG" .

echo "==> Pushing to ACR: $ACR_REGISTRY:$TAG"
docker push "$ACR_REGISTRY:$TAG"

if [ "$TAG" != "latest" ]; then
  docker tag "$ACR_REGISTRY:$TAG" "$ACR_REGISTRY:latest"
  docker push "$ACR_REGISTRY:latest"
fi

echo "==> Restarting backend on ECS ($ECS_IP)..."
ssh -o StrictHostKeyChecking=no "root@$ECS_IP" \
  "cd /opt/public-sector && docker compose pull && docker compose up -d"

echo ""
echo "==> Deploy complete!"
echo "    API: http://$ECS_IP:8000/docs"
cd "$TF_DIR"
echo "    SLB: $(terraform output -raw api_base_url)/docs"
