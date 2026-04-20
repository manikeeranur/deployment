#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# SMC Deploy Bot — One-time EC2 setup script
# Run this ONCE on the EC2 server after uploading the deploy/ folder.
# Usage:  bash /home/ubuntu/deploy/setup_ec2.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

DEPLOY_DIR="/home/ubuntu/deploy"
SERVICE_NAME="telegram-deploy-bot"

echo "======================================================"
echo "  SMC Deploy Bot — EC2 Setup"
echo "======================================================"

# ── 1. System packages ──────────────────────────────────────────────────────
echo ""
echo "[1/6] Installing system packages..."
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv git

# ── 2. Python virtualenv ─────────────────────────────────────────────────────
echo ""
echo "[2/6] Creating Python virtual environment..."
cd "$DEPLOY_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# ── 3. .env file ─────────────────────────────────────────────────────────────
echo ""
echo "[3/6] Setting up .env config..."
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
    echo ""
    echo "  ⚠️  IMPORTANT: Edit your config now:"
    echo "      nano $DEPLOY_DIR/.env"
    echo ""
    echo "  Fill in:"
    echo "    BOT_TOKEN=<from @BotFather>"
    echo "    ALLOWED_CHAT_IDS=<your Telegram chat ID from @userinfobot>"
    echo ""
    read -p "  Press ENTER after editing .env to continue..." _
else
    echo "  .env already exists, skipping."
fi

# ── 4. Script permissions ────────────────────────────────────────────────────
echo ""
echo "[4/6] Setting script permissions..."
chmod +x "$DEPLOY_DIR/scripts/"*.sh

# ── 5. Systemd service ───────────────────────────────────────────────────────
echo ""
echo "[5/6] Installing systemd service..."

# Patch service file to use venv python
sed "s|/usr/bin/python3|$DEPLOY_DIR/venv/bin/python3|g" \
    "$DEPLOY_DIR/telegram-deploy-bot.service" \
    | sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start  "$SERVICE_NAME"

# ── 6. Verify ────────────────────────────────────────────────────────────────
echo ""
echo "[6/6] Verifying service..."
sleep 2
sudo systemctl status "$SERVICE_NAME" --no-pager

echo ""
echo "======================================================"
echo "✅ Setup complete!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "  sudo systemctl restart $SERVICE_NAME"
echo "  sudo journalctl -u $SERVICE_NAME -f"
echo "======================================================"
