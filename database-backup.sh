#!/bin/bash

# Database Backup Script for Arise Bot
# Creates a compressed backup of all database files

set -e

echo "🗄️ Arise Bot Database Backup"
echo "============================"

# Configuration
BACKUP_DIR="database_export"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="arise_databases_${TIMESTAMP}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}📁 Creating backup directory...${NC}"
mkdir -p "$BACKUP_DIR"

echo -e "${BLUE}📦 Collecting database files...${NC}"

# Copy all database files
if [ -d "data" ]; then
    echo -e "${YELLOW}• Copying data/ directory...${NC}"
    cp -r data "$BACKUP_DIR/"
fi

# Copy individual database files from root
for db_file in *.db; do
    if [ -f "$db_file" ]; then
        echo -e "${YELLOW}• Copying $db_file...${NC}"
        cp "$db_file" "$BACKUP_DIR/"
    fi
done

# Copy JSON data files
for json_file in *.json; do
    if [ -f "$json_file" ] && [ "$json_file" != "package.json" ] && [ "$json_file" != "package-lock.json" ]; then
        echo -e "${YELLOW}• Copying $json_file...${NC}"
        cp "$json_file" "$BACKUP_DIR/"
    fi
done

# Copy emojis.json specifically
if [ -f "emojis.json" ]; then
    echo -e "${YELLOW}• Copying emojis.json...${NC}"
    cp "emojis.json" "$BACKUP_DIR/"
fi

# Copy images.json specifically  
if [ -f "images.json" ]; then
    echo -e "${YELLOW}• Copying images.json...${NC}"
    cp "images.json" "$BACKUP_DIR/"
fi

echo -e "${BLUE}🗜️ Creating compressed archive...${NC}"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_DIR"

echo -e "${BLUE}🧹 Cleaning up temporary directory...${NC}"
rm -rf "$BACKUP_DIR"

echo -e "${GREEN}✅ Backup created: ${BACKUP_NAME}.tar.gz${NC}"
echo -e "${YELLOW}📤 Upload this file to your VPS and extract it in the bot directory${NC}"
echo ""
echo -e "${YELLOW}📋 To extract on VPS:${NC}"
echo -e "${BLUE}tar -xzf ${BACKUP_NAME}.tar.gz${NC}"
echo -e "${BLUE}cp -r database_export/* /opt/Arise/${NC}"
