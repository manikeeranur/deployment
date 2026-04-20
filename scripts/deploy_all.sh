#!/bin/bash
# Deploy both SMC Backend and Frontend sequentially
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "================================================"
echo "  DEPLOYING BACKEND + FRONTEND"
echo "================================================"
echo ""

echo ">>> STEP 1: Backend"
bash "$SCRIPT_DIR/deploy_backend.sh"

echo ""
echo ">>> STEP 2: Frontend"
bash "$SCRIPT_DIR/deploy_frontend.sh"

echo ""
echo "================================================"
echo "✅ All services deployed!"
echo "================================================"
pm2 list
