#!/usr/bin/env python3
"""
Database table fix script - Creates all missing tables that are causing errors
"""

import asyncio
import aiosqlite
import sqlite3
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_database_path():
    """Get the database path from configuration"""
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("database", "players.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "players.db"

DATABASE_PATH = get_database_path()

async def create_missing_tables():
    """Create all missing database tables"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            logging.info(f"Connected to database: {DATABASE_PATH}")
            
            # Create leaderboard table (for old ranking system compatibility)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS leaderboard (
                    id INTEGER PRIMARY KEY,
                    rank TEXT NOT NULL,
                    rank_ INTEGER NOT NULL,
                    power INTEGER NOT NULL
                )
            """)
            logging.info("Created/verified leaderboard table")
            
            # Create player_ranks table (for ranking system compatibility)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS player_ranks (
                    player_id TEXT PRIMARY KEY,
                    current_rank TEXT NOT NULL DEFAULT 'E',
                    progress INTEGER DEFAULT 0,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logging.info("Created/verified player_ranks table")
            
            # Create hunter_rankings table (new ranking system)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS hunter_rankings (
                    player_id TEXT PRIMARY KEY,
                    current_rank TEXT NOT NULL DEFAULT 'E',
                    rank_points INTEGER DEFAULT 0,
                    last_evaluation TEXT,
                    rank_history TEXT DEFAULT '[]',
                    total_evaluations INTEGER DEFAULT 0
                )
            """)
            logging.info("Created/verified hunter_rankings table")
            
            # Create srank_hunters table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS srank_hunters (
                    id INTEGER PRIMARY KEY
                )
            """)
            logging.info("Created/verified srank_hunters table")
            
            # Create glory table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS glory (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    points INTEGER DEFAULT 0,
                    rank INTEGER DEFAULT 0,
                    hs INTEGER DEFAULT 0,
                    current_streak INTEGER DEFAULT 0,
                    logs TEXT,
                    FOREIGN KEY(user_id) REFERENCES players(id)
                )
            """)
            logging.info("Created/verified glory table")
            
            # Create market table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS market (
                    id INTEGER PRIMARY KEY,
                    sid INTEGER NOT NULL,
                    i_id TEXT NOT NULL,
                    i_t TEXT NOT NULL,
                    q INTEGER NOT NULL,
                    p INTEGER NOT NULL,
                    i_n TEXT NOT NULL,
                    FOREIGN KEY (sid) REFERENCES players(id)
                )
            """)
            logging.info("Created/verified market table")
            
            # Create counters table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS counters (
                    name TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                )
            """)
            logging.info("Created/verified counters table")
            
            # Initialize market counter if it doesn't exist
            await db.execute("""
                INSERT OR IGNORE INTO counters (name, value)
                VALUES ('market', 0)
            """)
            
            # Create server_tracking table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS server_tracking (
                    guild_id TEXT PRIMARY KEY,
                    guild_name TEXT NOT NULL,
                    owner_name TEXT,
                    member_count INTEGER DEFAULT 0,
                    joined_at TEXT NOT NULL,
                    left_at TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    invite_source TEXT
                )
            """)
            logging.info("Created/verified server_tracking table")
            
            await db.commit()
            logging.info("All database tables created/verified successfully!")
            
    except Exception as e:
        logging.error(f"Error creating database tables: {e}")
        raise

def create_missing_tables_sync():
    """Synchronous version for compatibility"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Create all the same tables synchronously
        tables = [
            """CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY,
                rank TEXT NOT NULL,
                rank_ INTEGER NOT NULL,
                power INTEGER NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS player_ranks (
                player_id TEXT PRIMARY KEY,
                current_rank TEXT NOT NULL DEFAULT 'E',
                progress INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS hunter_rankings (
                player_id TEXT PRIMARY KEY,
                current_rank TEXT NOT NULL DEFAULT 'E',
                rank_points INTEGER DEFAULT 0,
                last_evaluation TEXT,
                rank_history TEXT DEFAULT '[]',
                total_evaluations INTEGER DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS srank_hunters (
                id INTEGER PRIMARY KEY
            )""",
            """CREATE TABLE IF NOT EXISTS glory (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                points INTEGER DEFAULT 0,
                rank INTEGER DEFAULT 0,
                hs INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                logs TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS market (
                id INTEGER PRIMARY KEY,
                sid INTEGER NOT NULL,
                i_id TEXT NOT NULL,
                i_t TEXT NOT NULL,
                q INTEGER NOT NULL,
                p INTEGER NOT NULL,
                i_n TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS counters (
                name TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS server_tracking (
                guild_id TEXT PRIMARY KEY,
                guild_name TEXT NOT NULL,
                owner_name TEXT,
                member_count INTEGER DEFAULT 0,
                joined_at TEXT NOT NULL,
                left_at TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                invite_source TEXT
            )"""
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        # Initialize market counter
        cursor.execute("INSERT OR IGNORE INTO counters (name, value) VALUES ('market', 0)")
        
        conn.commit()
        conn.close()
        logging.info("Synchronous database table creation completed!")
        
    except Exception as e:
        logging.error(f"Error in synchronous table creation: {e}")
        raise

async def main():
    """Main function to run the database fix"""
    logging.info("Starting database table fix...")
    await create_missing_tables()
    logging.info("Database fix completed!")

if __name__ == "__main__":
    # Run the async version
    asyncio.run(main())
