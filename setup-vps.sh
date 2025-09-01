#!/bin/bash

# Arise Bot VPS Setup Script
# Run this script after cloning the repository to set up the bot on your VPS

set -e  # Exit on any error

echo "🗡️ Arise Bot VPS Setup"
echo "====================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}📁 Working in: $(pwd)${NC}"

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py not found. Make sure you're in the Arise bot directory.${NC}"
    exit 1
fi

echo -e "${BLUE}🐍 Setting up Python virtual environment...${NC}"

# Install system dependencies if needed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Python3...${NC}"
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv python3-full
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${BLUE}🔧 Creating virtual environment...${NC}"
    python3 -m venv venv
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Set up environment file
if [ ! -f ".env" ]; then
    echo -e "${BLUE}📄 Setting up environment file...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your Discord bot token:${NC}"
    echo -e "${YELLOW}   nano .env${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists${NC}"
fi

# Create data directories
echo -e "${BLUE}🗄️ Creating data directories...${NC}"
mkdir -p data
mkdir -p database_backups

# Make startup script executable
echo -e "${BLUE}🔧 Making startup script executable...${NC}"
chmod +x start-bot.sh

# Set up systemd service
echo -e "${BLUE}⚙️ Setting up systemd service...${NC}"

# Update service file with current user and path
USER_NAME=$(whoami)
CURRENT_PATH=$(pwd)

# Create a temporary service file with correct paths
cat > arise-bot-temp.service << EOF
[Unit]
Description=Arise Solo Leveling Discord Bot
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$CURRENT_PATH
ExecStart=$CURRENT_PATH/start-bot.sh
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=arise-bot

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Install the service
sudo cp arise-bot-temp.service /etc/systemd/system/arise-bot.service
rm arise-bot-temp.service

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable arise-bot

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Next steps:${NC}"
echo -e "1. Edit your .env file: ${BLUE}nano .env${NC}"
echo -e "2. Add your Discord bot token and client ID"
echo -e "3. Test the bot: ${BLUE}./start-bot.sh${NC}"
echo -e "4. Start the service: ${BLUE}sudo systemctl start arise-bot${NC}"
echo ""
echo -e "${YELLOW}🔧 Useful commands:${NC}"
echo -e "• Check status: ${BLUE}sudo systemctl status arise-bot${NC}"
echo -e "• View logs: ${BLUE}sudo journalctl -u arise-bot -f${NC}"
echo -e "• Restart bot: ${BLUE}sudo systemctl restart arise-bot${NC}"
echo -e "• Stop bot: ${BLUE}sudo systemctl stop arise-bot${NC}"
echo ""
echo -e "${GREEN}🎉 Your bot will automatically start on server reboot!${NC}"
