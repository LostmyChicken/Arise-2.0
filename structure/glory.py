import json
import logging
import sqlite3
import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("player", "data/player.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "data/player.db"

DATABASE_PATH = get_database_path()

class Glory:
    def __init__(self, user_id: int, name: str = None, points: int = 0, rank: int = 0, 
                 hs: int = 0, current_streak: int = 0, logs: str = None):
        self.user_id = user_id
        self.name = name
        self.points = points
        self.rank = rank
        self.hs = hs  # highest streak
        self.current_streak = current_streak
        self._logs = logs  # JSON string of defense logs
        
    @property
    def logs(self) -> List[Dict[str, Any]]:
        """Get the defense logs as a list of dictionaries"""
        if self._logs:
            return json.loads(self._logs)
        return []
    
    @logs.setter
    def logs(self, value: List[Dict[str, Any]]):
        """Set the defense logs from a list of dictionaries"""
        self._logs = json.dumps(value) if value else None
        
    async def save(self):
        """Save or update the glory record in the database"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT 1 FROM glory WHERE user_id = ?", (self.user_id,)) as cursor:
                if await cursor.fetchone():
                    await db.execute("""
                        UPDATE glory 
                        SET name = ?, points = ?, rank = ?, hs = ?, current_streak = ?, logs = ?
                        WHERE user_id = ?
                    """, (self.name, self.points, self.rank, self.hs, self.current_streak, self._logs, self.user_id))
                else:
                    await db.execute("""
                        INSERT INTO glory (user_id, name, points, rank, hs, current_streak, logs)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (self.user_id, self.name, self.points, self.rank, self.hs, self.current_streak, self._logs))
            await db.commit()
    
    @staticmethod
    async def get(user_id: int) -> Optional['Glory']:
        """Get a glory record by user ID"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT * FROM glory WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Glory(*row)
                return None
    
    @staticmethod
    async def get_top(n: int = 10) -> List['Glory']:
        """Get top n glory records by points"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("""
                SELECT * FROM glory 
                ORDER BY points DESC 
                LIMIT ?
            """, (n,)) as cursor:
                rows = await cursor.fetchall()
                return [Glory(*row) for row in rows]
    
    @staticmethod
    async def get_ranked_list(n: int = None) -> List['Glory']:
        """Get all glory records ordered by rank/points"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            query = "SELECT * FROM glory ORDER BY points DESC"
            if n is not None:
                query += f" LIMIT {n}"
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [Glory(*row) for row in rows]
    
    async def add_points(self, amount: int, log_entry: Dict[str, Any] = None):
        """Add points to the user's glory, optionally with a log entry"""
        self.points += amount
        self.current_streak += 1
        
        # Update highest streak if current streak is higher
        if self.current_streak > self.hs:
            self.hs = self.current_streak
            
        # Add log entry if provided
        if log_entry:
            logs = self.logs
            log_entry['timestamp'] = datetime.now().isoformat()
            logs.append(log_entry)
            self.logs = logs
            
        await self.save()
    
    async def add_log_entry(self, log_entry: Dict[str, Any]):
        """Add a defense log entry"""
        logs = self.logs
        log_entry['timestamp'] = datetime.now().isoformat()
        logs.append(log_entry)
        self.logs = logs
        await self.save()
    
    async def reset_streak(self):
        """Reset the current streak to 0"""
        self.current_streak = 0
        await self.save()
    
    async def update_rank(self):
        """Update the rank based on the current points"""
        ranked_list = await Glory.get_ranked_list()
        for index, glory in enumerate(ranked_list, start=1):
            if glory.user_id == self.user_id:
                self.rank = index
                await self.save()
                break
    
    @staticmethod
    def initialize():
        """Initialize the glory table in the database"""
        with sqlite3.connect(DATABASE_PATH) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS glory (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    points INTEGER DEFAULT 0,
                    rank INTEGER DEFAULT 0,
                    hs INTEGER DEFAULT 0,  -- highest streak
                    current_streak INTEGER DEFAULT 0,
                    logs TEXT,           -- JSON string of defense logs
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            db.commit()
            
            # Check for and add missing columns
            cursor = db.execute("PRAGMA table_info(glory)")
            columns = [column[1] for column in cursor.fetchall()]  # column name is at index 1
            if 'logs' not in columns:
                db.execute("ALTER TABLE glory ADD COLUMN logs TEXT")
                db.commit()
    
    @staticmethod
    async def clear():
        """Clear the glory table (for testing/reset purposes)"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("DROP TABLE IF EXISTS glory")
            await db.commit()
    
    @staticmethod
    async def update_name(user_id: int, name: str):
        """Update the name for a glory record"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                UPDATE glory 
                SET name = ?
                WHERE user_id = ?
            """, (name, user_id))
            await db.commit()