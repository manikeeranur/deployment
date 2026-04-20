#!/bin/bash
# Deploy SMC Backend (Express.js — port 4000)
set -e

APP_DIR="/var/www/html/SMC-Backend"
APP_NAME="SMC-Backend"

echo "[1/4] Pulling latest code..."
cd "$APP_DIR"
git pull origin main 2>&1

echo "[2/4] Installing dependencies..."
npm install 2>&1

echo "[3/4] Restarting PM2 process..."
if pm2 list | grep -q "$APP_NAME"; then
    pm2 restart "$APP_NAME" 2>&1
else
    pm2 start index.js --name "$APP_NAME" 2>&1
fi

echo "[4/4] Saving PM2 process list..."
pm2 save 2>&1

echo ""
echo "✅ Backend deployed successfully!"
pm2 show "$APP_NAME" 2>&1 | grep -E "status|restarts|uptime"
