#!/usr/bin/env python3
"""
Critical Data Usage Analysis Script
Analyzes what's taking up 44GB of space in the bot
"""

import os
import json
import sqlite3
import sys
from pathlib import Path
import logging

def get_directory_size(path):
    """Get total size of directory in bytes"""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    pass
    except (OSError, PermissionError):
        pass
    return total

def format_size(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def analyze_file_sizes():
    """Analyze individual file sizes"""
    print("🔍 ANALYZING FILE SIZES...")
    print("=" * 60)
    
    # Get current directory
    current_dir = Path.cwd()
    
    # Analyze major files and directories
    items_to_check = [
        "new_player.db",
        "leaderboard.json", 
        "hunters.json",
        "items.json",
        "enemy.json",
        "emojis.json",
        "shadows.json",
        "__pycache__",
        "venv",
        "data",
        "logs",
        "backups",
        ".git"
    ]
    
    file_sizes = []
    
    for item in items_to_check:
        item_path = current_dir / item
        if item_path.exists():
            if item_path.is_file():
                size = item_path.stat().st_size
            else:
                size = get_directory_size(item_path)
            
            file_sizes.append((item, size))
            print(f"📁 {item:<20} {format_size(size):>15}")
    
    # Find all large files (>100MB)
    print(f"\n🚨 LARGE FILES (>100MB):")
    print("-" * 40)
    
    large_files = []
    for root, dirs, files in os.walk(current_dir):
        for file in files:
            filepath = Path(root) / file
            try:
                size = filepath.stat().st_size
                if size > 100 * 1024 * 1024:  # >100MB
                    large_files.append((str(filepath.relative_to(current_dir)), size))
            except (OSError, PermissionError):
                pass
    
    large_files.sort(key=lambda x: x[1], reverse=True)
    for filepath, size in large_files[:20]:  # Top 20 largest
        print(f"📄 {filepath:<50} {format_size(size):>15}")
    
    return file_sizes, large_files

def analyze_database():
    """Analyze database size and content"""
    print(f"\n💾 DATABASE ANALYSIS:")
    print("=" * 60)
    
    db_path = "new_player.db"
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return
    
    db_size = os.path.getsize(db_path)
    print(f"📊 Database Size: {format_size(db_size)}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table sizes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📋 TABLE ANALYSIS:")
        print("-" * 40)
        
        for (table_name,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Get approximate size by checking a sample
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
            sample = cursor.fetchone()
            if sample:
                sample_size = len(str(sample))
                estimated_size = sample_size * row_count
                print(f"🗂️  {table_name:<15} {row_count:>8} rows  ~{format_size(estimated_size):>10}")
        
        # Check for extremely large player data
        print(f"\n🔍 LARGE PLAYER DATA:")
        print("-" * 40)
        
        cursor.execute("SELECT id, LENGTH(hunters), LENGTH(inventory) FROM players ORDER BY LENGTH(hunters) + LENGTH(inventory) DESC LIMIT 10")
        large_players = cursor.fetchall()
        
        for player_id, hunters_size, inventory_size in large_players:
            total_size = (hunters_size or 0) + (inventory_size or 0)
            print(f"👤 Player {player_id}: Hunters={format_size(hunters_size or 0)}, Inventory={format_size(inventory_size or 0)}, Total={format_size(total_size)}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database analysis error: {e}")

def analyze_json_files():
    """Analyze JSON file sizes and content"""
    print(f"\n📄 JSON FILES ANALYSIS:")
    print("=" * 60)
    
    json_files = [
        "hunters.json",
        "items.json", 
        "enemy.json",
        "emojis.json",
        "shadows.json",
        "leaderboard.json"
    ]
    
    for filename in json_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"📋 {filename:<20} {format_size(size):>15}")
            
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        print(f"   └─ {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"   └─ {len(data)} keys")
            except Exception as e:
                print(f"   └─ Error reading: {e}")

def check_log_files():
    """Check for excessive log files"""
    print(f"\n📝 LOG FILES ANALYSIS:")
    print("=" * 60)
    
    log_patterns = ["*.log", "*.txt", "logs/*", "*.out"]
    log_files = []
    
    for pattern in log_patterns:
        for filepath in Path.cwd().glob(pattern):
            if filepath.is_file():
                size = filepath.stat().st_size
                log_files.append((str(filepath), size))
    
    log_files.sort(key=lambda x: x[1], reverse=True)
    
    total_log_size = sum(size for _, size in log_files)
    print(f"📊 Total Log Size: {format_size(total_log_size)}")
    
    for filepath, size in log_files[:10]:  # Top 10 largest logs
        print(f"📄 {filepath:<50} {format_size(size):>15}")

def main():
    print("🚨 CRITICAL DATA USAGE ANALYSIS")
    print("🔍 Investigating 44GB data usage...")
    print("=" * 80)
    
    # Get total directory size
    total_size = get_directory_size(".")
    print(f"📊 TOTAL DIRECTORY SIZE: {format_size(total_size)}")
    print()
    
    # Analyze different components
    file_sizes, large_files = analyze_file_sizes()
    analyze_database()
    analyze_json_files()
    check_log_files()
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print("=" * 60)
    
    # Generate recommendations based on findings
    if total_size > 10 * 1024 * 1024 * 1024:  # >10GB
        print("🚨 CRITICAL: Data usage is extremely high!")
        print("📋 Immediate actions needed:")
        print("   1. Check for large log files and rotate/delete them")
        print("   2. Analyze database for oversized player data")
        print("   3. Look for backup files or temporary data")
        print("   4. Check for large media files or downloads")
        print("   5. Consider database optimization and cleanup")
    
    print(f"\n💡 NEXT STEPS:")
    print("   • Run: python3 cleanup_large_data.py")
    print("   • Use: sl analyzeplayerdata <large_player_id>")
    print("   • Check: disk usage with 'du -sh *' command")

if __name__ == "__main__":
    main()
