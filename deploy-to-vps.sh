#!/bin/bash

# Arise Bot VPS Deployment Script
# This script sets up the bot on your Contabo VPS with systemd service

set -e  # Exit on any error

echo "🗡️ Arise Bot VPS Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BOT_DIR="/opt/Arise"
SERVICE_NAME="arise-bot"
GITHUB_REPO="https://github.com/LostmyChicken/Arise.git"

echo -e "${BLUE}📦 Installing system dependencies...${NC}"
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git curl wget htop

echo -e "${BLUE}📁 Setting up bot directory...${NC}"
if [ -d "$BOT_DIR" ]; then
    echo -e "${YELLOW}⚠️  Directory $BOT_DIR already exists. Backing up...${NC}"
    mv "$BOT_DIR" "${BOT_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p "$BOT_DIR"
cd "$BOT_DIR"

echo -e "${BLUE}📥 Cloning repository...${NC}"
git clone "$GITHUB_REPO" .

echo -e "${BLUE}🐍 Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${BLUE}📄 Setting up environment file...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your Discord bot token:${NC}"
    echo -e "${YELLOW}   nano $BOT_DIR/.env${NC}"
fi

echo -e "${BLUE}🗄️ Setting up database directories...${NC}"
mkdir -p data
mkdir -p database_backups

echo -e "${BLUE}⚙️ Installing systemd service...${NC}"
cp arise-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo -e "${BLUE}🔧 Setting up log rotation...${NC}"
cat > /etc/logrotate.d/arise-bot << EOF
$BOT_DIR/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF

echo -e "${BLUE}🔥 Setting up firewall...${NC}"
if command -v ufw &> /dev/null; then
    ufw --force enable
    ufw allow ssh
    ufw allow 80
    ufw allow 443
fi

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo -e "1. Edit your .env file: ${BLUE}nano $BOT_DIR/.env${NC}"
echo -e "2. Add your Discord bot token and client ID"
echo -e "3. Upload your database files to: ${BLUE}$BOT_DIR/data/${NC}"
echo -e "4. Start the bot: ${BLUE}systemctl start $SERVICE_NAME${NC}"
echo ""
echo -e "${YELLOW}🔧 Useful commands:${NC}"
echo -e "• Check status: ${BLUE}systemctl status $SERVICE_NAME${NC}"
echo -e "• View logs: ${BLUE}journalctl -u $SERVICE_NAME -f${NC}"
echo -e "• Restart bot: ${BLUE}systemctl restart $SERVICE_NAME${NC}"
echo -e "• Stop bot: ${BLUE}systemctl stop $SERVICE_NAME${NC}"
echo ""
echo -e "${GREEN}🎉 Your bot will now automatically start on server reboot!${NC}"
