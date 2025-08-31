#!/usr/bin/env python3
"""
Quick fix script to update the raids database table with missing columns.
Run this script to fix existing databases that are missing the required columns.
"""

import asyncio
import aiosqlite
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_database_path():
    """Get the database path from db.json"""
    try:
        with open("db.json", "r") as f:
            return json.load(f).get("player", "data/player.db")
    except Exception:
        return "data/player.db"

async def fix_raids_table():
    """Fix the raids table by adding missing columns"""
    DATABASE_PATH = get_database_path()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        print(f"Connected to database: {DATABASE_PATH}")

        # First, check if the table exists at all
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='raids'")
        table_exists = await cursor.fetchone()

        if not table_exists:
            print("⚠️  Raids table doesn't exist, creating it...")
            # Create the table with all required columns
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
            print("✅ Created complete raids table")
            await db.commit()
            return

        # Table exists, check current structure
        cursor = await db.execute("PRAGMA table_info(raids)")
        columns = await cursor.fetchall()
        column_names = [column[1] for column in columns]

        print(f"Current columns: {column_names}")

        # List of ALL required columns with their types (in case some basic ones are missing too)
        required_columns = {
            'channel': 'INTEGER PRIMARY KEY',
            'level': 'INTEGER',
            'shadow': 'TEXT',
            'raid_class': 'TEXT',
            'health': 'INTEGER',
            'image': 'TEXT',
            'attack': 'INTEGER',
            'defense': 'INTEGER',
            'max_health': 'INTEGER',
            'members': 'TEXT',
            'started': 'INTEGER',
            'message_id': 'INTEGER'
        }

        # Add missing columns (skip PRIMARY KEY ones as they can't be added)
        added_columns = []
        for column_name, column_type in required_columns.items():
            if column_name not in column_names and 'PRIMARY KEY' not in column_type:
                try:
                    await db.execute(f'ALTER TABLE raids ADD COLUMN {column_name} {column_type}')
                    added_columns.append(f"{column_name} ({column_type})")
                    print(f"✅ Added missing '{column_name}' column")
                except Exception as e:
                    print(f"⚠️  Could not add column '{column_name}': {e}")

        if added_columns:
            print(f"✅ Successfully added columns: {', '.join(added_columns)}")
        else:
            print("✅ All required columns already exist")

        await db.commit()
        print("✅ Database changes committed")

        # Verify the fix
        cursor = await db.execute("PRAGMA table_info(raids)")
        columns = await cursor.fetchall()
        final_columns = [column[1] for column in columns]
        print(f"Final table structure: {final_columns}")

        # Clear any existing raids to prevent issues with old data
        try:
            await db.execute("DELETE FROM raids")
            await db.commit()
            print("✅ Cleared existing raids to prevent conflicts")
        except Exception as e:
            print(f"⚠️  Could not clear existing raids: {e}")

async def main():
    """Main function"""
    print("🔧 Fixing raids database table...")
    try:
        await fix_raids_table()
        print("🎉 Raids database fix completed successfully!")
        print("You can now restart your bot - raids should work properly.")
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        logging.error(f"Database fix failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
