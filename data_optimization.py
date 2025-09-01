#!/usr/bin/env python3
"""
Data Storage Optimization System
Implements better data storage practices to prevent 44GB issues
"""

import os
import json
import sqlite3
import gzip
import pickle
import logging
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import aiosqlite

class DataOptimizer:
    """Handles data storage optimization and cleanup"""
    
    def __init__(self):
        self.max_player_data_size = 5 * 1024 * 1024  # 5MB per player
        self.max_inventory_items = 1000
        self.max_hunters = 500
        self.backup_retention_days = 7
        self.log_retention_days = 30
        
    def format_size(self, bytes_size):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"
    
    async def optimize_player_data(self, player_id=None):
        """Optimize player data in database"""
        print(f"🔧 Optimizing player data...")
        
        db_path = "new_player.db"
        if not os.path.exists(db_path):
            print("❌ Database not found!")
            return
        
        try:
            async with aiosqlite.connect(db_path) as conn:
                if player_id:
                    # Optimize specific player
                    await self._optimize_single_player(conn, player_id)
                else:
                    # Find and optimize all large players
                    cursor = await conn.execute("""
                        SELECT id, LENGTH(hunters) + LENGTH(inventory) as total_size 
                        FROM players 
                        WHERE LENGTH(hunters) + LENGTH(inventory) > ?
                        ORDER BY total_size DESC
                    """, (self.max_player_data_size,))
                    
                    large_players = await cursor.fetchall()
                    
                    if large_players:
                        print(f"🔍 Found {len(large_players)} players with large data")
                        for player_id, size in large_players:
                            await self._optimize_single_player(conn, player_id)
                    else:
                        print("✅ No players with excessive data found")
                
                await conn.commit()
                
        except Exception as e:
            print(f"❌ Error optimizing player data: {e}")
    
    async def _optimize_single_player(self, conn, player_id):
        """Optimize a single player's data"""
        cursor = await conn.execute(
            "SELECT hunters, inventory FROM players WHERE id = ?", 
            (player_id,)
        )
        result = await cursor.fetchone()
        
        if not result:
            return
        
        hunters_data, inventory_data = result
        original_size = len(str(hunters_data)) + len(str(inventory_data))
        
        # Optimize hunters
        if hunters_data:
            try:
                hunters = json.loads(hunters_data)
                if isinstance(hunters, dict) and len(hunters) > self.max_hunters:
                    # Keep most recent hunters based on level/usage
                    sorted_hunters = sorted(
                        hunters.items(), 
                        key=lambda x: x[1].get('level', 0), 
                        reverse=True
                    )
                    optimized_hunters = dict(sorted_hunters[:self.max_hunters])
                    
                    await conn.execute(
                        "UPDATE players SET hunters = ? WHERE id = ?",
                        (json.dumps(optimized_hunters), player_id)
                    )
                    print(f"   👤 Player {player_id}: Hunters {len(hunters)} → {len(optimized_hunters)}")
            except json.JSONDecodeError:
                pass
        
        # Optimize inventory
        if inventory_data:
            try:
                inventory = json.loads(inventory_data)
                if isinstance(inventory, dict) and len(inventory) > self.max_inventory_items:
                    # Keep most valuable items
                    sorted_inventory = sorted(
                        inventory.items(),
                        key=lambda x: x[1].get('level', 0),
                        reverse=True
                    )
                    optimized_inventory = dict(sorted_inventory[:self.max_inventory_items])
                    
                    await conn.execute(
                        "UPDATE players SET inventory = ? WHERE id = ?",
                        (json.dumps(optimized_inventory), player_id)
                    )
                    print(f"   🎒 Player {player_id}: Inventory {len(inventory)} → {len(optimized_inventory)}")
            except json.JSONDecodeError:
                pass
        
        # Check final size
        cursor = await conn.execute(
            "SELECT LENGTH(hunters) + LENGTH(inventory) FROM players WHERE id = ?",
            (player_id,)
        )
        new_size = (await cursor.fetchone())[0]
        saved = original_size - new_size
        
        if saved > 0:
            print(f"   💾 Player {player_id}: Saved {self.format_size(saved)}")
    
    def compress_json_files(self):
        """Compress large JSON files"""
        print("🗜️  Compressing JSON files...")
        
        json_files = [
            "hunters.json",
            "items.json", 
            "shadows.json",
            "leaderboard.json"
        ]
        
        total_saved = 0
        
        for filename in json_files:
            if os.path.exists(filename):
                original_size = os.path.getsize(filename)
                
                # Only compress if file is large (>1MB)
                if original_size > 1024 * 1024:
                    compressed_filename = f"{filename}.gz"
                    
                    with open(filename, 'rb') as f_in:
                        with gzip.open(compressed_filename, 'wb') as f_out:
                            f_out.writelines(f_in)
                    
                    compressed_size = os.path.getsize(compressed_filename)
                    saved = original_size - compressed_size
                    total_saved += saved
                    
                    print(f"   📄 {filename}: {self.format_size(original_size)} → {self.format_size(compressed_size)} (saved {self.format_size(saved)})")
                    
                    # Keep original for now, can be removed after verification
                    # os.remove(filename)
        
        print(f"📊 Total compression savings: {self.format_size(total_saved)}")
        return total_saved
    
    def implement_log_rotation(self):
        """Implement log file rotation"""
        print("📝 Implementing log rotation...")
        
        log_files = list(Path.cwd().glob("*.log"))
        total_cleaned = 0
        
        for log_file in log_files:
            if log_file.stat().st_size > 100 * 1024 * 1024:  # >100MB
                # Archive large log files
                archive_name = f"{log_file.stem}_{datetime.now().strftime('%Y%m%d')}.log.gz"
                
                with open(log_file, 'rb') as f_in:
                    with gzip.open(archive_name, 'wb') as f_out:
                        f_out.writelines(f_in)
                
                # Clear the original log file
                with open(log_file, 'w') as f:
                    f.write(f"Log rotated on {datetime.now()}\n")
                
                saved = log_file.stat().st_size
                total_cleaned += saved
                print(f"   📄 Rotated {log_file.name}: {self.format_size(saved)}")
        
        # Clean old archived logs
        cutoff_date = datetime.now() - timedelta(days=self.log_retention_days)
        
        for archive in Path.cwd().glob("*.log.gz"):
            if archive.stat().st_mtime < cutoff_date.timestamp():
                size = archive.stat().st_size
                archive.unlink()
                total_cleaned += size
                print(f"   🗑️  Removed old archive: {archive.name}")
        
        print(f"📊 Total log cleanup: {self.format_size(total_cleaned)}")
        return total_cleaned
    
    def setup_data_monitoring(self):
        """Setup monitoring for data growth"""
        print("📊 Setting up data monitoring...")
        
        monitor_script = """#!/usr/bin/env python3
# Auto-generated data monitoring script
import os
import json
from datetime import datetime

def check_data_sizes():
    sizes = {}
    
    # Check database
    if os.path.exists('new_player.db'):
        sizes['database'] = os.path.getsize('new_player.db')
    
    # Check JSON files
    json_files = ['hunters.json', 'items.json', 'shadows.json', 'leaderboard.json']
    for filename in json_files:
        if os.path.exists(filename):
            sizes[filename] = os.path.getsize(filename)
    
    # Log sizes
    with open('data_size_log.json', 'a') as f:
        entry = {
            'timestamp': datetime.now().isoformat(),
            'sizes': sizes,
            'total': sum(sizes.values())
        }
        f.write(json.dumps(entry) + '\\n')
    
    # Alert if total > 1GB
    total_size = sum(sizes.values())
    if total_size > 1024 * 1024 * 1024:
        print(f"⚠️  WARNING: Total data size is {total_size / 1024 / 1024 / 1024:.2f} GB")

if __name__ == "__main__":
    check_data_sizes()
"""
        
        with open('monitor_data_sizes.py', 'w') as f:
            f.write(monitor_script)
        
        os.chmod('monitor_data_sizes.py', 0o755)
        print("✅ Created monitor_data_sizes.py script")
        print("   Run this script regularly to monitor data growth")
    
    async def full_optimization(self):
        """Run full data optimization"""
        print("🚀 STARTING FULL DATA OPTIMIZATION")
        print("=" * 80)
        
        total_saved = 0
        
        # 1. Optimize player data
        await self.optimize_player_data()
        
        # 2. Compress JSON files
        total_saved += self.compress_json_files()
        
        # 3. Implement log rotation
        total_saved += self.implement_log_rotation()
        
        # 4. Setup monitoring
        self.setup_data_monitoring()
        
        print(f"\n🎉 OPTIMIZATION COMPLETE!")
        print("=" * 80)
        print(f"📊 Total space saved: {self.format_size(total_saved)}")
        print(f"💡 Recommendations:")
        print(f"   • Run monitor_data_sizes.py daily")
        print(f"   • Set up automated cleanup scripts")
        print(f"   • Monitor player data growth")
        print(f"   • Consider database archiving for old data")

async def main():
    optimizer = DataOptimizer()
    await optimizer.full_optimization()

if __name__ == "__main__":
    asyncio.run(main())
