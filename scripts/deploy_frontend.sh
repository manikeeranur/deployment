#!/bin/bash
# Deploy SMC Frontend (Next.js — port 3000)
set -e

APP_DIR="/var/www/html/SMC-Frontend"
APP_NAME="SMC-Frontend"

echo "[1/5] Pulling latest code..."
cd "$APP_DIR"
git pull origin main 2>&1

echo "[2/5] Installing dependencies..."
npm install 2>&1

echo "[3/5] Building Next.js app..."
npm run build 2>&1

echo "[4/5] Restarting PM2 process..."
if pm2 list | grep -q "$APP_NAME"; then
    pm2 restart "$APP_NAME" 2>&1
else
    pm2 start npm --name "$APP_NAME" -- start 2>&1
fi

echo "[5/5] Saving PM2 process list..."
pm2 save 2>&1

echo ""
echo "✅ Frontend deployed successfully!"
pm2 show "$APP_NAME" 2>&1 | grep -E "status|restarts|uptime"
