# Whale Tracker Discord Bot - Ubuntu Server Setup Guide

## Auto-Start Setup on Ubuntu Server

### Prerequisites
- Ubuntu 20.04+ (or any systemd-based Linux)
- Python 3.11+
- Project cloned to `/home/ubuntu/whale-fishing`
- Virtual environment created: `python -m venv venv`
- Dependencies installed: `pip install -r requirements.txt`

### Installation Steps

#### 1. Upload Files to Server
Copy the project to your Ubuntu server:
```bash
scp -r "whale-fishing" ubuntu@your-server-ip:/home/ubuntu/
```

#### 2. Set Up Python Environment
```bash
cd /home/ubuntu/whale-fishing
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Configure Environment
```bash
# Copy and edit .env with your Discord webhook
cp .env.template .env
nano .env
# Add: DISCORD_WEBHOOK_URL=your_webhook_here
```

#### 4. Make Setup Script Executable
```bash
chmod +x setup-autostart.sh
```

#### 5. Run Setup (requires sudo)
```bash
sudo ./setup-autostart.sh
```

This will:
- Copy `whale-tracker.service` to systemd
- Enable auto-start on boot
- Start the service immediately

### Managing the Service

**Check service status:**
```bash
sudo systemctl status whale-tracker
```

**View live logs:**
```bash
sudo journalctl -u whale-tracker -f
```

**Stop the bot:**
```bash
sudo systemctl stop whale-tracker
```

**Start the bot:**
```bash
sudo systemctl start whale-tracker
```

**Restart the bot:**
```bash
sudo systemctl restart whale-tracker
```

**Disable auto-start (keep service stopped):**
```bash
sudo systemctl disable whale-tracker
```

**Re-enable auto-start:**
```bash
sudo systemctl enable whale-tracker
```

### Verify It's Running

**Check if listening on port 8000:**
```bash
netstat -tuln | grep 8000
# or
ss -tuln | grep 8000
```

**Test the health endpoint:**
```bash
curl http://localhost:8000/health
```

**View recent logs:**
```bash
sudo journalctl -u whale-tracker -n 50
```

### Troubleshooting

**Service won't start:**
```bash
# Check for errors
sudo journalctl -u whale-tracker -n 100
# Check if port is in use
sudo lsof -i :8000
```

**Permission issues:**
```bash
# Ensure proper ownership
sudo chown -R www-data:www-data /home/ubuntu/whale-fishing
```

**Service crashes on reboot:**
```bash
# Verify service file is correct
sudo systemctl status whale-tracker
# Check logs
sudo journalctl -u whale-tracker -f
```

### Auto-Start Persistence

After setup, the bot will:
- ✅ Start automatically on server boot
- ✅ Restart automatically if it crashes
- ✅ Run in background (won't need SSH session open)
- ✅ Log to systemd journal (viewable with `journalctl`)

### Optional: Set Restart Delay

To adjust crash restart delay, edit the service file:
```bash
sudo nano /etc/systemd/system/whale-tracker.service
```

Change `RestartSec=10` to desired seconds (e.g., 5, 30, 60)

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart whale-tracker
```

---

**Bot will now run 24/7 and persist across reboots!** 🚀
