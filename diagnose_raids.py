#!/usr/bin/env python3
"""
Comprehensive diagnostic script for raids database issues.
This will show us exactly what's wrong with your database.
"""

import asyncio
import aiosqlite
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_database_path():
    """Get the database path from db.json"""
    try:
        with open("db.json", "r") as f:
            return json.load(f).get("player", "data/player.db")
    except Exception as e:
        print(f"⚠️  Could not read db.json: {e}")
        return "data/player.db"

async def diagnose_database():
    """Comprehensive database diagnosis"""
    DATABASE_PATH = get_database_path()
    
    print("🔍 RAIDS DATABASE DIAGNOSTIC")
    print("=" * 50)
    print(f"Database path: {DATABASE_PATH}")
    print(f"Database exists: {os.path.exists(DATABASE_PATH)}")
    
    if not os.path.exists(DATABASE_PATH):
        print("❌ Database file doesn't exist!")
        return
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            print("✅ Successfully connected to database")
            
            # Check if raids table exists
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='raids'")
            table_exists = await cursor.fetchone()
            
            if not table_exists:
                print("❌ Raids table doesn't exist at all!")
                print("🔧 Creating raids table...")
                await create_raids_table(db)
                return
            
            print("✅ Raids table exists")
            
            # Get current table structure
            cursor = await db.execute("PRAGMA table_info(raids)")
            columns = await cursor.fetchall()
            
            print(f"\n📋 Current table structure ({len(columns)} columns):")
            for i, col in enumerate(columns):
                print(f"  {i}: {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")
            
            column_names = [col[1] for col in columns]
            
            # Check for required columns
            required_columns = [
                'channel', 'level', 'shadow', 'raid_class', 'health', 
                'image', 'attack', 'defense', 'max_health', 'members', 
                'started', 'message_id'
            ]
            
            missing_columns = []
            for req_col in required_columns:
                if req_col not in column_names:
                    missing_columns.append(req_col)
            
            if missing_columns:
                print(f"\n❌ Missing columns: {missing_columns}")
                print("🔧 Adding missing columns...")
                await add_missing_columns(db, missing_columns)
            else:
                print("\n✅ All required columns present")
            
            # Check existing data
            cursor = await db.execute("SELECT COUNT(*) FROM raids")
            count = await cursor.fetchone()
            print(f"\n📊 Current raids in database: {count[0] if count else 0}")
            
            if count and count[0] > 0:
                print("🧹 Clearing old raids to prevent conflicts...")
                await db.execute("DELETE FROM raids")
                await db.commit()
                print("✅ Old raids cleared")
            
            # Test a basic insert/select
            print("\n🧪 Testing database operations...")
            test_data = (
                12345, 50, "Test Shadow", "Fire", 1000, "test.png", 
                200, 100, 1000, '{}', 0, 67890
            )
            
            await db.execute('''
                INSERT OR REPLACE INTO raids 
                (channel, level, shadow, raid_class, health, image, attack, defense, max_health, members, started, message_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', test_data)
            await db.commit()
            
            cursor = await db.execute("SELECT * FROM raids WHERE channel = ?", (12345,))
            result = await cursor.fetchone()
            
            if result:
                print("✅ Database operations working correctly")
                print(f"   Test data: {len(result)} columns retrieved")
                
                # Clean up test data
                await db.execute("DELETE FROM raids WHERE channel = ?", (12345,))
                await db.commit()
            else:
                print("❌ Database operations failed")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()

async def create_raids_table(db):
    """Create the complete raids table"""
    try:
        await db.execute('''
            CREATE TABLE raids (
                channel INTEGER PRIMARY KEY,
                level INTEGER,
                shadow TEXT,
                raid_class TEXT,
                health INTEGER,
                image TEXT,
                attack INTEGER,
                defense INTEGER,
                max_health INTEGER,
                members TEXT,
                started INTEGER,
                message_id INTEGER
            )
        ''')
        await db.commit()
        print("✅ Created complete raids table")
    except Exception as e:
        print(f"❌ Failed to create raids table: {e}")

async def add_missing_columns(db, missing_columns):
    """Add missing columns to existing table"""
    column_types = {
        'image': 'TEXT',
        'attack': 'INTEGER',
        'defense': 'INTEGER',
        'max_health': 'INTEGER',
        'message_id': 'INTEGER',
        'level': 'INTEGER',
        'shadow': 'TEXT',
        'raid_class': 'TEXT',
        'health': 'INTEGER',
        'members': 'TEXT',
        'started': 'INTEGER'
    }
    
    for column in missing_columns:
        if column in column_types:
            try:
                column_type = column_types[column]
                await db.execute(f'ALTER TABLE raids ADD COLUMN {column} {column_type}')
                print(f"✅ Added column: {column} ({column_type})")
            except Exception as e:
                print(f"❌ Failed to add column {column}: {e}")
    
    await db.commit()

async def main():
    """Main diagnostic function"""
    try:
        await diagnose_database()
        print("\n🎉 Diagnostic complete!")
        print("If you see ✅ for all checks, your raids should work now.")
        print("If you see ❌ errors, please share this output for further help.")
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
