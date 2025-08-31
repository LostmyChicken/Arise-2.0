#!/usr/bin/env python3
"""
Automated Database Backup and Maintenance System
- Daily backups at noon UTC (keeps last 4 backups)
- Weekly database vacuum on Sundays at noon UTC
- Persistent through bot restarts using file-based scheduling
"""

import asyncio
import os
import shutil
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

class AutomatedMaintenance:
    """Handles automated database backup and maintenance"""
    
    def __init__(self):
        self.db_path = "new_player.db"
        self.backup_dir = Path("database_backups")
        self.schedule_file = "maintenance_schedule.json"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Schedule settings
        self.backup_hour = 12  # Noon UTC
        self.vacuum_day = 6    # Sunday (0=Monday, 6=Sunday)
        self.max_backups = 4   # Keep last 4 backups
        
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for maintenance operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('maintenance.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def format_size(self, bytes_size):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"
    
    def load_schedule(self):
        """Load maintenance schedule from file"""
        try:
            if os.path.exists(self.schedule_file):
                with open(self.schedule_file, 'r') as f:
                    return json.load(f)
            return {
                "last_backup": None,
                "last_vacuum": None,
                "next_backup": None,
                "next_vacuum": None
            }
        except Exception as e:
            self.logger.error(f"Error loading schedule: {e}")
            return {
                "last_backup": None,
                "last_vacuum": None,
                "next_backup": None,
                "next_vacuum": None
            }
    
    def save_schedule(self, schedule):
        """Save maintenance schedule to file"""
        try:
            with open(self.schedule_file, 'w') as f:
                json.dump(schedule, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving schedule: {e}")
    
    def calculate_next_backup(self):
        """Calculate next backup time (daily at noon UTC)"""
        now = datetime.utcnow()
        next_backup = now.replace(hour=self.backup_hour, minute=0, second=0, microsecond=0)
        
        # If we've passed today's backup time, schedule for tomorrow
        if now >= next_backup:
            next_backup += timedelta(days=1)
        
        return next_backup.isoformat()
    
    def calculate_next_vacuum(self):
        """Calculate next vacuum time (weekly on Sunday at noon UTC)"""
        now = datetime.utcnow()
        days_until_sunday = (self.vacuum_day - now.weekday()) % 7
        
        next_vacuum = now.replace(hour=self.backup_hour, minute=0, second=0, microsecond=0)
        next_vacuum += timedelta(days=days_until_sunday)
        
        # If it's Sunday but we've passed the vacuum time, schedule for next Sunday
        if days_until_sunday == 0 and now >= next_vacuum:
            next_vacuum += timedelta(days=7)
        
        return next_vacuum.isoformat()
    
    def create_backup(self):
        """Create database backup"""
        try:
            if not os.path.exists(self.db_path):
                self.logger.error("Database not found for backup")
                return False
            
            # Create backup filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"new_player_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            # Create backup
            shutil.copy2(self.db_path, backup_path)
            
            # Get sizes
            original_size = os.path.getsize(self.db_path)
            backup_size = os.path.getsize(backup_path)
            
            self.logger.info(f"✅ Database backup created: {backup_filename}")
            self.logger.info(f"📊 Backup size: {self.format_size(backup_size)}")
            
            # Clean old backups
            self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Backup failed: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Keep only the last N backups"""
        try:
            # Get all backup files
            backup_files = list(self.backup_dir.glob("new_player_backup_*.db"))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old backups beyond the limit
            removed_count = 0
            for backup_file in backup_files[self.max_backups:]:
                size = backup_file.stat().st_size
                backup_file.unlink()
                removed_count += 1
                self.logger.info(f"🗑️  Removed old backup: {backup_file.name} ({self.format_size(size)})")
            
            if removed_count > 0:
                self.logger.info(f"📊 Cleaned up {removed_count} old backups")
            
            # Log current backup status
            remaining_backups = len(backup_files[:self.max_backups])
            self.logger.info(f"📁 Current backups: {remaining_backups}/{self.max_backups}")
            
        except Exception as e:
            self.logger.error(f"❌ Backup cleanup failed: {e}")
    
    def vacuum_database(self):
        """Perform database vacuum operation"""
        try:
            if not os.path.exists(self.db_path):
                self.logger.error("Database not found for vacuum")
                return False
            
            # Get size before vacuum
            size_before = os.path.getsize(self.db_path)
            
            # Perform vacuum
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA optimize")
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
            conn.close()
            
            # Get size after vacuum
            size_after = os.path.getsize(self.db_path)
            saved = size_before - size_after
            
            self.logger.info(f"✅ Database vacuum completed")
            self.logger.info(f"📊 Size before: {self.format_size(size_before)}")
            self.logger.info(f"📊 Size after: {self.format_size(size_after)}")
            self.logger.info(f"💾 Space saved: {self.format_size(saved)} ({(saved/size_before*100):.1f}%)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Database vacuum failed: {e}")
            return False
    
    def should_backup(self, schedule):
        """Check if backup is due"""
        if not schedule.get("next_backup"):
            return True
        
        next_backup = datetime.fromisoformat(schedule["next_backup"])
        return datetime.utcnow() >= next_backup
    
    def should_vacuum(self, schedule):
        """Check if vacuum is due"""
        if not schedule.get("next_vacuum"):
            return True
        
        next_vacuum = datetime.fromisoformat(schedule["next_vacuum"])
        return datetime.utcnow() >= next_vacuum
    
    async def run_maintenance_cycle(self):
        """Run one maintenance cycle"""
        self.logger.info("🔧 Starting maintenance cycle...")
        
        schedule = self.load_schedule()
        
        # Check for backup
        if self.should_backup(schedule):
            self.logger.info("📅 Daily backup is due")
            if self.create_backup():
                schedule["last_backup"] = datetime.utcnow().isoformat()
                schedule["next_backup"] = self.calculate_next_backup()
                self.logger.info(f"📅 Next backup scheduled: {schedule['next_backup']}")
        
        # Check for vacuum
        if self.should_vacuum(schedule):
            self.logger.info("📅 Weekly vacuum is due")
            if self.vacuum_database():
                schedule["last_vacuum"] = datetime.utcnow().isoformat()
                schedule["next_vacuum"] = self.calculate_next_vacuum()
                self.logger.info(f"📅 Next vacuum scheduled: {schedule['next_vacuum']}")
        
        # Update schedule
        if not schedule.get("next_backup"):
            schedule["next_backup"] = self.calculate_next_backup()
        if not schedule.get("next_vacuum"):
            schedule["next_vacuum"] = self.calculate_next_vacuum()
        
        self.save_schedule(schedule)
        self.logger.info("✅ Maintenance cycle completed")
    
    async def start_maintenance_loop(self):
        """Start the maintenance loop"""
        self.logger.info("🚀 Starting automated maintenance system...")
        self.logger.info(f"📅 Daily backups at {self.backup_hour:02d}:00 UTC (keeps last {self.max_backups} backups)")
        self.logger.info(f"📅 Weekly vacuum on Sundays at {self.backup_hour:02d}:00 UTC")
        
        while True:
            try:
                await self.run_maintenance_cycle()
                
                # Wait 1 hour before next check
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                self.logger.error(f"❌ Maintenance loop error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def get_status(self):
        """Get current maintenance status"""
        schedule = self.load_schedule()
        
        status = {
            "last_backup": schedule.get("last_backup"),
            "next_backup": schedule.get("next_backup"),
            "last_vacuum": schedule.get("last_vacuum"),
            "next_vacuum": schedule.get("next_vacuum"),
            "backup_count": len(list(self.backup_dir.glob("new_player_backup_*.db")))
        }
        
        return status

# Standalone script functionality
async def main():
    """Run maintenance system as standalone script"""
    maintenance = AutomatedMaintenance()
    await maintenance.start_maintenance_loop()

if __name__ == "__main__":
    asyncio.run(main())
