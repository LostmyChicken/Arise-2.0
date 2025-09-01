#!/usr/bin/env python3
"""
Fix existing players who don't have story_progress data.
"""

import aiosqlite
import asyncio
import logging

DATABASE_PATH = "data/player.db"

async def fix_existing_players():
    """Fix existing players without story_progress data"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as conn:
            await conn.execute("PRAGMA journal_mode=WAL;")
            await conn.execute("PRAGMA busy_timeout = 5000;")
            
            # Count players without story_progress
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM players 
                WHERE story_progress IS NULL OR story_progress = ''
            """)
            null_count = await cursor.fetchone()
            await cursor.close()
            
            print(f"🔍 Found {null_count[0]} players without story_progress data")
            
            if null_count[0] > 0:
                # Update players with NULL or empty story_progress
                print("🔧 Fixing players with missing story_progress...")
                await conn.execute("""
                    UPDATE players 
                    SET story_progress = '{}' 
                    WHERE story_progress IS NULL OR story_progress = ''
                """)
                await conn.commit()
                
                # Verify the fix
                cursor = await conn.execute("""
                    SELECT COUNT(*) FROM players 
                    WHERE story_progress IS NULL OR story_progress = ''
                """)
                remaining_null = await cursor.fetchone()
                await cursor.close()
                
                fixed_count = null_count[0] - remaining_null[0]
                print(f"✅ Fixed {fixed_count} players!")
                
                if remaining_null[0] > 0:
                    print(f"⚠️ {remaining_null[0]} players still have issues")
                else:
                    print("🎉 All players now have story_progress data!")
            else:
                print("✅ All players already have story_progress data!")
            
            # Show total player count
            cursor = await conn.execute("SELECT COUNT(*) FROM players")
            total_count = await cursor.fetchone()
            await cursor.close()
            
            print(f"📊 Total players in database: {total_count[0]}")
            
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        logging.error(f"Fix existing players failed: {e}")

async def main():
    """Main fix function"""
    print("🔄 Starting fix for existing players...")
    await fix_existing_players()
    print("🎉 Fix completed!")

if __name__ == "__main__":
    asyncio.run(main())
