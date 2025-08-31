#!/bin/bash

# Database Restore Script for Arise Bot VPS
# Restores database files from backup archive

set -e

echo "🗄️ Arise Bot Database Restore"
echo "============================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if backup file is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Please provide the backup file name${NC}"
    echo -e "${YELLOW}Usage: $0 <backup_file.tar.gz>${NC}"
    exit 1
fi

BACKUP_FILE="$1"
BOT_DIR="/opt/Arise"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Backup file '$BACKUP_FILE' not found${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Extracting backup file...${NC}"
tar -xzf "$BACKUP_FILE"

echo -e "${BLUE}🛑 Stopping bot service...${NC}"
systemctl stop arise-bot || echo -e "${YELLOW}⚠️  Service not running${NC}"

echo -e "${BLUE}💾 Backing up current databases...${NC}"
if [ -d "$BOT_DIR/data" ]; then
    mv "$BOT_DIR/data" "$BOT_DIR/data.backup.$(date +%Y%m%d_%H%M%S)"
fi

echo -e "${BLUE}📁 Restoring database files...${NC}"
if [ -d "database_export" ]; then
    # Copy all files from the export
    cp -r database_export/* "$BOT_DIR/"
    
    # Ensure proper permissions
    chown -R root:root "$BOT_DIR/data" 2>/dev/null || true
    chmod -R 644 "$BOT_DIR"/*.db 2>/dev/null || true
    chmod -R 644 "$BOT_DIR"/*.json 2>/dev/null || true
    
    echo -e "${GREEN}✅ Database files restored${NC}"
else
    echo -e "${RED}❌ No database_export directory found in backup${NC}"
    exit 1
fi

echo -e "${BLUE}🧹 Cleaning up extraction...${NC}"
rm -rf database_export

echo -e "${BLUE}🚀 Starting bot service...${NC}"
systemctl start arise-bot

echo -e "${BLUE}📊 Checking service status...${NC}"
sleep 3
systemctl status arise-bot --no-pager

echo -e "${GREEN}✅ Database restore complete!${NC}"
echo -e "${YELLOW}📋 Check logs with: journalctl -u arise-bot -f${NC}"
