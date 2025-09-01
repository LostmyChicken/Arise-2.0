#!/usr/bin/env python3
"""
Database migration script to add story_progress column to existing players table.
Run this script to update your database for the story campaign system.
"""

import aiosqlite
import asyncio
import logging

DATABASE_PATH = "data/player.db"

async def migrate_story_progress():
    """Add story_progress column to existing players table"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as conn:
            await conn.execute("PRAGMA journal_mode=WAL;")
            await conn.execute("PRAGMA busy_timeout = 5000;")
            
            # Check if column already exists
            cursor = await conn.execute("PRAGMA table_info(players)")
            columns = await cursor.fetchall()
            await cursor.close()
            
            column_names = [column[1] for column in columns]
            
            if 'story_progress' not in column_names:
                print("Adding story_progress column to players table...")
                await conn.execute("ALTER TABLE players ADD COLUMN story_progress TEXT DEFAULT '{}'")
                await conn.commit()
                print("✅ Successfully added story_progress column!")
                
                # Update existing players with empty story progress
                await conn.execute("UPDATE players SET story_progress = '{}' WHERE story_progress IS NULL")
                await conn.commit()
                print("✅ Updated existing players with empty story progress!")
                
            else:
                print("✅ story_progress column already exists!")
                
            # Verify the column was added
            cursor = await conn.execute("SELECT COUNT(*) FROM players WHERE story_progress IS NOT NULL")
            count = await cursor.fetchone()
            await cursor.close()
            
            print(f"✅ Migration complete! {count[0]} players have story progress data.")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        logging.error(f"Story progress migration failed: {e}")

async def main():
    """Main migration function"""
    print("🔄 Starting story progress database migration...")
    await migrate_story_progress()
    print("🎉 Migration completed!")

if __name__ == "__main__":
    asyncio.run(main())
