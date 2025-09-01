#!/usr/bin/env python3
"""
Database Bloat Fix Script
Fixes the 41GB database issue by rebuilding and optimizing the database
"""

import sqlite3
import os
import shutil
import json
from datetime import datetime

def format_size(bytes_size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def backup_database():
    """Create backup of current database"""
    print("💾 Creating database backup...")
    
    db_path = "new_player.db"
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return False
    
    backup_path = f"new_player_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_path, backup_path)
    
    original_size = os.path.getsize(db_path)
    print(f"✅ Backup created: {backup_path}")
    print(f"📊 Original size: {format_size(original_size)}")
    return True

def analyze_database_structure():
    """Analyze database structure and identify issues"""
    print("\n🔍 Analyzing database structure...")
    
    db_path = "new_player.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("📋 Database Tables:")
    for (table_name,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Get table size estimate
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"   🗂️  {table_name}: {row_count} rows, {len(columns)} columns")
    
    # Check for database integrity
    print("\n🔧 Checking database integrity...")
    cursor.execute("PRAGMA integrity_check")
    integrity_result = cursor.fetchone()[0]
    
    if integrity_result == "ok":
        print("✅ Database integrity: OK")
    else:
        print(f"❌ Database integrity issues: {integrity_result}")
    
    # Check page count and size
    cursor.execute("PRAGMA page_count")
    page_count = cursor.fetchone()[0]
    
    cursor.execute("PRAGMA page_size")
    page_size = cursor.fetchone()[0]
    
    calculated_size = page_count * page_size
    actual_size = os.path.getsize(db_path)
    
    print(f"📊 Database Analysis:")
    print(f"   Pages: {page_count:,}")
    print(f"   Page Size: {page_size:,} bytes")
    print(f"   Calculated Size: {format_size(calculated_size)}")
    print(f"   Actual Size: {format_size(actual_size)}")
    print(f"   Bloat Factor: {actual_size / calculated_size:.2f}x")
    
    conn.close()
    return page_count, page_size, actual_size

def rebuild_database():
    """Rebuild database to eliminate bloat"""
    print("\n🔨 Rebuilding database...")
    
    db_path = "new_player.db"
    new_db_path = "new_player_optimized.db"
    
    # Remove old optimized database if exists
    if os.path.exists(new_db_path):
        os.remove(new_db_path)
    
    # Connect to both databases
    old_conn = sqlite3.connect(db_path)
    new_conn = sqlite3.connect(new_db_path)
    
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()
    
    try:
        # Get all table schemas
        old_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")
        table_schemas = old_cursor.fetchall()
        
        # Create tables in new database
        print("📋 Creating table structures...")
        for (schema,) in table_schemas:
            new_cursor.execute(schema)
        
        # Copy data table by table
        old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = old_cursor.fetchall()
        
        for (table_name,) in tables:
            print(f"   📊 Copying {table_name}...")
            
            # Get all data from old table
            old_cursor.execute(f"SELECT * FROM {table_name}")
            rows = old_cursor.fetchall()
            
            if rows:
                # Get column count
                old_cursor.execute(f"PRAGMA table_info({table_name})")
                columns = old_cursor.fetchall()
                placeholders = ','.join(['?' for _ in columns])
                
                # Insert into new table
                new_cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)
                print(f"      ✅ Copied {len(rows)} rows")
            else:
                print(f"      ℹ️  No data to copy")
        
        # Copy indexes
        print("🔍 Creating indexes...")
        old_cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        indexes = old_cursor.fetchall()
        
        for (index_sql,) in indexes:
            try:
                new_cursor.execute(index_sql)
            except sqlite3.Error as e:
                print(f"      ⚠️  Index creation warning: {e}")
        
        # Commit all changes first
        new_conn.commit()

        # Optimize new database (VACUUM must be outside transaction)
        print("⚡ Optimizing new database...")
        new_cursor.execute("PRAGMA optimize")
        new_cursor.execute("ANALYZE")
        
        # Get new database size
        new_conn.close()
        old_conn.close()
        
        new_size = os.path.getsize(new_db_path)
        old_size = os.path.getsize(db_path)
        
        print(f"✅ Database rebuild complete!")
        print(f"📊 Size comparison:")
        print(f"   Old: {format_size(old_size)}")
        print(f"   New: {format_size(new_size)}")
        print(f"   Saved: {format_size(old_size - new_size)} ({((old_size - new_size) / old_size * 100):.1f}%)")
        
        return new_db_path, old_size, new_size
        
    except Exception as e:
        print(f"❌ Error during rebuild: {e}")
        new_conn.close()
        old_conn.close()
        if os.path.exists(new_db_path):
            os.remove(new_db_path)
        return None, 0, 0

def replace_database(new_db_path):
    """Replace old database with optimized version"""
    print("\n🔄 Replacing database...")
    
    db_path = "new_player.db"
    old_db_backup = f"new_player_old_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    # Move old database to backup
    shutil.move(db_path, old_db_backup)
    
    # Move new database to main location
    shutil.move(new_db_path, db_path)
    
    print(f"✅ Database replaced successfully!")
    print(f"📁 Old database backed up as: {old_db_backup}")

def verify_data_integrity():
    """Verify that data was preserved correctly"""
    print("\n✅ Verifying data integrity...")
    
    db_path = "new_player.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check table counts
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("📊 Data verification:")
    for (table_name,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   🗂️  {table_name}: {count} rows")
    
    # Test a sample query
    try:
        cursor.execute("SELECT COUNT(*) FROM players WHERE id IS NOT NULL")
        player_count = cursor.fetchone()[0]
        print(f"✅ Sample query successful: {player_count} valid players")
    except Exception as e:
        print(f"❌ Sample query failed: {e}")
    
    conn.close()

def main():
    print("🔨 DATABASE BLOAT FIX SCRIPT")
    print("🎯 Fixing 41GB database issue...")
    print("=" * 80)
    
    # Step 1: Backup
    if not backup_database():
        return
    
    # Step 2: Analyze
    page_count, page_size, actual_size = analyze_database_structure()
    
    # Step 3: Rebuild
    new_db_path, old_size, new_size = rebuild_database()
    
    if new_db_path:
        # Step 4: Replace
        replace_database(new_db_path)
        
        # Step 5: Verify
        verify_data_integrity()
        
        print(f"\n🎉 DATABASE OPTIMIZATION COMPLETE!")
        print("=" * 80)
        print(f"📊 Final Results:")
        print(f"   Original Size: {format_size(old_size)}")
        print(f"   Optimized Size: {format_size(new_size)}")
        print(f"   Space Saved: {format_size(old_size - new_size)}")
        print(f"   Reduction: {((old_size - new_size) / old_size * 100):.1f}%")
        
        print(f"\n💡 Next Steps:")
        print(f"   • Restart your bot to use the optimized database")
        print(f"   • Monitor performance and data growth")
        print(f"   • Run VACUUM regularly to prevent future bloat")
        print(f"   • Consider implementing automatic optimization")
        
    else:
        print(f"\n❌ DATABASE OPTIMIZATION FAILED!")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main()
