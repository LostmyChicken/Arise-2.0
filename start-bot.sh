#!/bin/bash

# Arise Bot Startup Script
# This script activates the virtual environment and starts the bot

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Arise Bot..."
echo "📁 Working directory: $(pwd)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found"
    exit 1
fi

# Start the bot
echo "🤖 Starting bot..."
python main.py
