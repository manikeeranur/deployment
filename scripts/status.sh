#!/bin/bash
# Server & App Status Report

echo "=== PM2 Processes ==="
pm2 list 2>&1

echo ""
echo "=== Disk Usage ==="
df -h / 2>&1

echo ""
echo "=== Memory Usage ==="
free -h 2>&1

echo ""
echo "=== CPU Load ==="
uptime 2>&1

echo ""
echo "=== Port Listeners ==="
ss -tlnp 2>&1 | grep -E "3000|4000|80|443" || echo "No matching ports found"
