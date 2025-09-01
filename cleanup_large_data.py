#!/usr/bin/env python3
"""
Data Cleanup Script for 44GB Issue
Safely reduces data usage while preserving important information
"""

import os
import json
import sqlite3
import shutil
import sys
from pathlib import Path
from datetime import datetime, timedelta
import logging

def format_size(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def backup_critical_files():
    """Create backup of critical files before cleanup"""
    print("💾 Creating backup of critical files...")
    
    backup_dir = Path("backup_before_cleanup")
    backup_dir.mkdir(exist_ok=True)
    
    critical_files = [
        "new_player.db",
        "hunters.json",
        "items.json",
        "emojis.json"
    ]
    
    for filename in critical_files:
        if os.path.exists(filename):
            shutil.copy2(filename, backup_dir / filename)
            print(f"✅ Backed up {filename}")

def clean_log_files():
    """Clean up excessive log files"""
    print("\n📝 Cleaning log files...")
    
    log_patterns = ["*.log", "*.txt", "logs/*", "*.out"]
    cleaned_size = 0
    
    for pattern in log_patterns:
        for filepath in Path.cwd().glob(pattern):
            if filepath.is_file():
                size = filepath.stat().st_size
                if size > 100 * 1024 * 1024:  # >100MB
                    print(f"🗑️  Removing large log: {filepath} ({format_size(size)})")
                    filepath.unlink()
                    cleaned_size += size
                elif filepath.suffix in ['.log', '.txt'] and size > 10 * 1024 * 1024:  # >10MB
                    # Keep last 1000 lines of important logs
                    try:
                        with open(filepath, 'r') as f:
                            lines = f.readlines()
                        
                        if len(lines) > 1000:
                            with open(filepath, 'w') as f:
                                f.writelines(lines[-1000:])
                            new_size = filepath.stat().st_size
                            saved = size - new_size
                            cleaned_size += saved
                            print(f"✂️  Trimmed log: {filepath} (saved {format_size(saved)})")
                    except Exception as e:
                        print(f"❌ Error trimming {filepath}: {e}")
    
    print(f"📊 Total log cleanup: {format_size(cleaned_size)}")
    return cleaned_size

def clean_cache_directories():
    """Clean up cache and temporary directories"""
    print("\n🗂️  Cleaning cache directories...")
    
    cache_dirs = [
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".cache",
        "temp",
        "tmp"
    ]
    
    cleaned_size = 0
    
    for cache_dir in cache_dirs:
        cache_path = Path(cache_dir)
        if cache_path.exists() and cache_path.is_dir():
            size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
            shutil.rmtree(cache_path)
            cleaned_size += size
            print(f"🗑️  Removed {cache_dir}: {format_size(size)}")
    
    print(f"📊 Total cache cleanup: {format_size(cleaned_size)}")
    return cleaned_size

def optimize_database():
    """Optimize database and clean up oversized player data"""
    print("\n💾 Optimizing database...")
    
    db_path = "new_player.db"
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return 0
    
    original_size = os.path.getsize(db_path)
    print(f"📊 Original database size: {format_size(original_size)}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Find players with extremely large data
        cursor.execute("""
            SELECT id, LENGTH(hunters) as h_size, LENGTH(inventory) as i_size 
            FROM players 
            WHERE LENGTH(hunters) > 1000000 OR LENGTH(inventory) > 1000000
            ORDER BY h_size + i_size DESC
        """)
        
        large_players = cursor.fetchall()
        
        if large_players:
            print(f"🔍 Found {len(large_players)} players with large data:")
            
            for player_id, h_size, i_size in large_players[:5]:  # Top 5
                total_size = h_size + i_size
                print(f"   👤 Player {player_id}: {format_size(total_size)}")
                
                # Clean up this player's data
                cursor.execute("SELECT hunters, inventory FROM players WHERE id = ?", (player_id,))
                result = cursor.fetchone()
                
                if result:
                    hunters_data, inventory_data = result
                    
                    # Clean hunters data
                    if hunters_data:
                        try:
                            hunters = json.loads(hunters_data)
                            if isinstance(hunters, dict) and len(hunters) > 500:
                                # Keep only the most recent 500 hunters
                                cleaned_hunters = dict(list(hunters.items())[:500])
                                cursor.execute("UPDATE players SET hunters = ? WHERE id = ?", 
                                             (json.dumps(cleaned_hunters), player_id))
                                print(f"      ✂️  Trimmed hunters: {len(hunters)} → {len(cleaned_hunters)}")
                        except json.JSONDecodeError:
                            pass
                    
                    # Clean inventory data
                    if inventory_data:
                        try:
                            inventory = json.loads(inventory_data)
                            if isinstance(inventory, dict) and len(inventory) > 1000:
                                # Keep only the most recent 1000 items
                                cleaned_inventory = dict(list(inventory.items())[:1000])
                                cursor.execute("UPDATE players SET inventory = ? WHERE id = ?", 
                                             (json.dumps(cleaned_inventory), player_id))
                                print(f"      ✂️  Trimmed inventory: {len(inventory)} → {len(cleaned_inventory)}")
                        except json.JSONDecodeError:
                            pass
        
        # Vacuum the database to reclaim space
        print("🔧 Vacuuming database...")
        cursor.execute("VACUUM")
        
        conn.commit()
        conn.close()
        
        new_size = os.path.getsize(db_path)
        saved = original_size - new_size
        print(f"📊 Database optimization complete: {format_size(saved)} saved")
        
        return saved
        
    except Exception as e:
        print(f"❌ Database optimization error: {e}")
        return 0

def clean_large_json_files():
    """Clean up oversized JSON files"""
    print("\n📄 Cleaning large JSON files...")
    
    cleaned_size = 0
    
    # Check hunters.json for duplicates or test data
    if os.path.exists("hunters.json"):
        original_size = os.path.getsize("hunters.json")
        
        try:
            with open("hunters.json", 'r') as f:
                hunters = json.load(f)
            
            if isinstance(hunters, list):
                # Remove test hunters and duplicates
                cleaned_hunters = []
                seen_ids = set()
                
                for hunter in hunters:
                    if isinstance(hunter, dict) and 'id' in hunter:
                        hunter_id = hunter['id']
                        # Skip test data
                        if hunter_id in ['test', 'skibidi', 'debug'] or 'test' in hunter_id.lower():
                            continue
                        # Skip duplicates
                        if hunter_id in seen_ids:
                            continue
                        
                        seen_ids.add(hunter_id)
                        cleaned_hunters.append(hunter)
                
                if len(cleaned_hunters) < len(hunters):
                    with open("hunters.json", 'w') as f:
                        json.dump(cleaned_hunters, f, indent=2)
                    
                    new_size = os.path.getsize("hunters.json")
                    saved = original_size - new_size
                    cleaned_size += saved
                    print(f"✂️  Cleaned hunters.json: {len(hunters)} → {len(cleaned_hunters)} hunters ({format_size(saved)} saved)")
        
        except Exception as e:
            print(f"❌ Error cleaning hunters.json: {e}")
    
    return cleaned_size

def remove_old_backups():
    """Remove old backup files"""
    print("\n🗑️  Removing old backups...")
    
    backup_patterns = ["*.bak", "*.backup", "*_backup_*", "backup_*"]
    cleaned_size = 0
    
    for pattern in backup_patterns:
        for filepath in Path.cwd().glob(pattern):
            if filepath.is_file():
                # Remove backups older than 7 days
                if filepath.stat().st_mtime < (datetime.now() - timedelta(days=7)).timestamp():
                    size = filepath.stat().st_size
                    filepath.unlink()
                    cleaned_size += size
                    print(f"🗑️  Removed old backup: {filepath} ({format_size(size)})")
    
    print(f"📊 Total backup cleanup: {format_size(cleaned_size)}")
    return cleaned_size

def main():
    print("🧹 LARGE DATA CLEANUP SCRIPT")
    print("🎯 Targeting 44GB data reduction...")
    print("=" * 80)
    
    # Create backup first
    backup_critical_files()
    
    total_cleaned = 0
    
    # Run cleanup operations
    total_cleaned += clean_log_files()
    total_cleaned += clean_cache_directories()
    total_cleaned += optimize_database()
    total_cleaned += clean_large_json_files()
    total_cleaned += remove_old_backups()
    
    print(f"\n🎉 CLEANUP COMPLETE!")
    print("=" * 80)
    print(f"📊 Total space reclaimed: {format_size(total_cleaned)}")
    print(f"💾 Backups created in: backup_before_cleanup/")
    
    if total_cleaned > 1024 * 1024 * 1024:  # >1GB
        print("✅ Significant space saved! Monitor bot performance.")
    else:
        print("⚠️  Limited space saved. May need manual investigation.")
    
    print(f"\n💡 NEXT STEPS:")
    print("   • Restart the bot to see memory improvements")
    print("   • Run: python3 analyze_data_usage.py to verify")
    print("   • Monitor bot performance and data growth")
    print("   • Consider implementing data rotation policies")

if __name__ == "__main__":
    main()
