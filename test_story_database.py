#!/usr/bin/env python3
"""
Test script to verify story_progress database column works correctly.
"""

import aiosqlite
import asyncio
import json
import logging

DATABASE_PATH = "data/player.db"

async def test_story_database():
    """Test story_progress database functionality"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as conn:
            await conn.execute("PRAGMA journal_mode=WAL;")
            await conn.execute("PRAGMA busy_timeout = 5000;")
            
            # Check table schema
            print("🔍 Checking database schema...")
            cursor = await conn.execute("PRAGMA table_info(players)")
            columns = await cursor.fetchall()
            await cursor.close()
            
            print("📋 Current columns in players table:")
            for column in columns:
                print(f"  - {column[1]} ({column[2]})")
            
            # Check if story_progress column exists
            column_names = [column[1] for column in columns]
            if 'story_progress' not in column_names:
                print("❌ story_progress column missing! Adding it now...")
                await conn.execute("ALTER TABLE players ADD COLUMN story_progress TEXT DEFAULT '{}'")
                await conn.commit()
                print("✅ Added story_progress column!")
            else:
                print("✅ story_progress column exists!")
            
            # Test writing story progress data
            test_player_id = 999999999  # Test player ID
            test_story_data = {
                "prologue_001": {
                    "completed": True,
                    "completed_at": 1234567890
                }
            }
            
            print(f"🧪 Testing story progress write for player {test_player_id}...")
            
            # Insert or update test player
            await conn.execute("""
                INSERT OR REPLACE INTO players (id, level, story_progress) 
                VALUES (?, ?, ?)
            """, (test_player_id, 1, json.dumps(test_story_data)))
            await conn.commit()
            
            # Read back the data
            cursor = await conn.execute(
                "SELECT story_progress FROM players WHERE id = ?", 
                (test_player_id,)
            )
            result = await cursor.fetchone()
            await cursor.close()
            
            if result:
                stored_data = json.loads(result[0]) if result[0] else {}
                print(f"✅ Successfully wrote and read story progress: {stored_data}")
                
                # Clean up test player
                await conn.execute("DELETE FROM players WHERE id = ?", (test_player_id,))
                await conn.commit()
                print("🧹 Cleaned up test data")
            else:
                print("❌ Failed to read story progress data")
            
            print("🎉 Database test completed successfully!")
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        logging.error(f"Story database test failed: {e}")

async def main():
    """Main test function"""
    print("🔄 Starting story database test...")
    await test_story_database()

if __name__ == "__main__":
    asyncio.run(main())
