#!/usr/bin/env python3
"""
Add story_progress column to the database.
"""

import aiosqlite
import asyncio

async def add_story_column():
    """Add story_progress column to players table"""
    # Check both possible database locations
    databases = ['new_player.db', 'data/player.db']

    for db_path in databases:
        try:
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute('ALTER TABLE players ADD COLUMN story_progress TEXT DEFAULT "{}"')
                await conn.commit()
                print(f'✅ Added story_progress column to {db_path}!')
        except Exception as e:
            if 'duplicate column name' in str(e):
                print(f'✅ Column already exists in {db_path}!')
            elif 'no such table' in str(e):
                print(f'⚠️ No players table in {db_path}')
            else:
                print(f'❌ Error with {db_path}: {e}')

if __name__ == "__main__":
    asyncio.run(add_story_column())
