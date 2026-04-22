#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Run this from your LOCAL machine (Windows Git Bash / WSL / Mac Terminal)
# to upload the deploy/ folder to EC2 and trigger setup.
#
# Usage:  bash deploy/upload_to_ec2.sh
# ─────────────────────────────────────────────────────────────────────────────

EC2_HOST="13.61.175.6"
EC2_USER="ubuntu"
PEM_KEY="algo_server.pem"   # path to your .pem file (relative to project root)
REMOTE_DIR="/home/ubuntu/deploy"

echo "======================================================"
echo "  Uploading deploy/ to EC2"
echo "======================================================"

# ── 1. Upload deploy folder ──────────────────────────────────────────────────
echo ""
echo "[1/3] Copying deploy/ folder to EC2..."
scp -i "$PEM_KEY" -r "$(dirname "$0")" "${EC2_USER}@${EC2_HOST}:${REMOTE_DIR}"

# ── 2. Fix line endings & permissions on EC2 ─────────────────────────────────
echo ""
echo "[2/3] Fixing permissions on EC2..."
ssh -i "$PEM_KEY" "${EC2_USER}@${EC2_HOST}" \
    "find ${REMOTE_DIR} -name '*.sh' -exec chmod +x {} \; && \
     find ${REMOTE_DIR} -name '*.sh' -exec sed -i 's/\r//' {} \;"

# ── 3. Run setup ─────────────────────────────────────────────────────────────
echo ""
echo "[3/3] Running setup on EC2..."
ssh -i "$PEM_KEY" "${EC2_USER}@${EC2_HOST}" "bash ${REMOTE_DIR}/setup_ec2.sh"

echo ""
echo "======================================================"
echo "✅ Upload & setup complete!"
echo "======================================================"
