# 🚀 VPS Deployment Guide - Arise Bot

Complete guide to deploy your Arise Solo Leveling Discord bot to your Contabo VPS with automatic startup and database transfer.

## 📋 Prerequisites

- Contabo VPS with Ubuntu/Debian
- SSH access to your VPS
- Your Discord bot token
- Local database files you want to transfer

## 🎯 Quick Deployment (Recommended)

### Step 1: Clone Repository on VPS

```bash
# SSH into your VPS
ssh your_username@your_vps_ip

# Clone the repository
git clone https://github.com/LostmyChicken/Arise.git
cd Arise
```

### Step 2: Run Setup Script

```bash
# Make setup script executable and run it
chmod +x setup-vps.sh
./setup-vps.sh
```

This will automatically:
- Install Python dependencies
- Create virtual environment
- Set up systemd service
- Create necessary directories

### Step 3: Configure Environment

```bash
# Edit the environment file with your bot token
nano .env
```

Add your Discord credentials:
```
DISCORD_TOKEN=your_actual_bot_token_here
CLIENT_ID=your_client_id_here
```

### Step 4: Test the Bot

```bash
# Test the bot manually first
./start-bot.sh
```

If it starts successfully (you'll see "🤖 Arise is ready to rock and roll!"), press `Ctrl+C` to stop it.

### Step 5: Start the Service

```bash
# Start the systemd service
sudo systemctl start arise-bot

# Check status
sudo systemctl status arise-bot
```

### Step 6: Transfer Database (Optional)

If you have existing database files:

```bash
# On your local machine, create backup
./database-backup.sh

# Upload to VPS
scp arise_databases_*.tar.gz your_username@your_vps_ip:~/Arise/

# On VPS, restore database
cd ~/Arise
./database-restore.sh arise_databases_*.tar.gz
```

## 🔧 Manual Deployment (Alternative)

If you prefer to do it step by step:

### 1. System Setup

```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3 python3-pip python3-venv git curl wget htop

# Create bot directory
mkdir -p /opt/Arise
cd /opt/Arise
```

### 2. Clone Repository

```bash
# Clone your private repository (you'll need to authenticate)
git clone https://github.com/LostmyChicken/Arise.git .
```

### 3. Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

### 5. Install Systemd Service

```bash
# Copy service file
cp arise-bot.service /etc/systemd/system/

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable arise-bot
```

### 6. Database Setup

```bash
# Create data directory
mkdir -p data database_backups

# Upload and extract your database backup
# (upload arise_databases_*.tar.gz to /opt/Arise first)
tar -xzf arise_databases_*.tar.gz
cp -r database_export/* ./
```

### 7. Start Service

```bash
systemctl start arise-bot
```

## 📊 Service Management

### Check Status
```bash
systemctl status arise-bot
```

### View Logs
```bash
# Real-time logs
journalctl -u arise-bot -f

# Recent logs
journalctl -u arise-bot --since "1 hour ago"
```

### Control Service
```bash
# Start
systemctl start arise-bot

# Stop
systemctl stop arise-bot

# Restart
systemctl restart arise-bot

# Reload (if you change code)
systemctl reload arise-bot
```

## 🔄 Updates and Maintenance

### Update Bot Code
```bash
cd /opt/Arise
git pull origin main
pip install -r requirements.txt --upgrade
systemctl restart arise-bot
```

### Backup Database
```bash
cd /opt/Arise
./database-backup.sh
```

### Monitor Resources
```bash
# Check memory usage
free -h

# Check disk space
df -h

# Monitor processes
htop
```

## 🛡️ Security Features

The systemd service includes security hardening:
- ✅ Runs with minimal privileges
- ✅ Private temporary directory
- ✅ Protected system directories
- ✅ No new privileges allowed

## 🔥 Firewall Setup

```bash
# Enable firewall
ufw enable

# Allow SSH
ufw allow ssh

# Allow HTTP/HTTPS (if needed)
ufw allow 80
ufw allow 443
```

## 📝 Log Rotation

Automatic log rotation is configured to:
- Rotate logs daily
- Keep 7 days of logs
- Compress old logs
- Handle missing log files gracefully

## 🎉 Benefits

✅ **Auto-start on reboot** - Bot automatically starts when VPS restarts  
✅ **Automatic restart** - Bot restarts if it crashes  
✅ **Proper logging** - All logs go to systemd journal  
✅ **Security hardened** - Runs with minimal system access  
✅ **Easy management** - Simple systemctl commands  
✅ **Database backup/restore** - Easy database migration  

## 🆘 Troubleshooting

### Bot Won't Start
```bash
# Check service status
systemctl status arise-bot

# Check logs for errors
journalctl -u arise-bot --since "10 minutes ago"

# Check if .env file has correct token
cat /opt/Arise/.env
```

### Database Issues
```bash
# Check if database files exist
ls -la /opt/Arise/data/

# Check file permissions
ls -la /opt/Arise/*.db
```

### Memory Issues
```bash
# Check memory usage
free -h

# Check bot memory usage
ps aux | grep python
```

Your bot is now production-ready with automatic startup! 🚀
