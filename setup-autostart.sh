#!/bin/bash
# Setup script for Whale Tracker Discord Bot on Ubuntu Server

echo "🐋 Setting up Whale Tracker Bot for auto-start..."

# Define paths
PROJECT_DIR="/home/ubuntu/whale-fishing"
SERVICE_FILE="whale-tracker.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_FILE"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)"
   exit 1
fi

echo "📁 Copying service file to systemd..."
cp "$PROJECT_DIR/$SERVICE_FILE" "$SERVICE_PATH"
chmod 644 "$SERVICE_PATH"

echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

echo "✅ Enabling auto-start on boot..."
systemctl enable whale-tracker.service

echo "🚀 Starting Whale Tracker Bot..."
systemctl start whale-tracker.service

echo ""
echo "════════════════════════════════════════"
echo "✅ Setup complete!"
echo "════════════════════════════════════════"
echo ""
echo "📋 Useful commands:"
echo "   • View status:    sudo systemctl status whale-tracker"
echo "   • View logs:      sudo journalctl -u whale-tracker -f"
echo "   • Stop service:   sudo systemctl stop whale-tracker"
echo "   • Restart:        sudo systemctl restart whale-tracker"
echo "   • Disable at boot: sudo systemctl disable whale-tracker"
echo ""
echo "🌐 Access bot at: http://localhost:8000"
echo "📖 API docs:     http://localhost:8000/docs"
echo ""
