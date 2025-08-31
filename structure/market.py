import json
import logging
import sqlite3
import aiosqlite
from typing import List, Dict, Optional

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("player", "data/player.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "data/player.db"

DATABASE_PATH = get_database_path()

class Market:
    def __init__(self, id: int, sid: int, i_id: str, i_t: str, q: int, p: int, i_n: str):
        self.id = id        # Listing ID
        self.sid = sid      # Seller ID
        self.i_id = i_id   # Item ID
        self.i_t = i_t     # Item Type ("hunter" or "weapon")
        self.q = q         # Quantity
        self.p = p         # Price
        self.i_n = i_n     # Item Name

    @staticmethod
    async def get(market_id: int) -> Optional['Market']:
        """Get listing by ID"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT * FROM market WHERE id = ?", (market_id,)) as cursor:
                row = await cursor.fetchone()
                return Market(*row) if row else None

    @staticmethod
    async def get_all() -> List['Market']:
        """Get all listings"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT * FROM market") as cursor:
                return [Market(*row) for row in await cursor.fetchall()]

    @staticmethod
    async def get_by_seller(seller_id: int) -> List['Market']:
        """Get seller's listings"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT * FROM market WHERE sid = ?", (seller_id,)) as cursor:
                return [Market(*row) for row in await cursor.fetchall()]

    @staticmethod
    async def search(name: str = None, i_t: str = None, max_p: int = None) -> List['Market']:
        """Search listings with filters"""
        query = "SELECT * FROM market WHERE 1=1"
        params = []
        
        if name:
            query += " AND i_n LIKE ?"
            params.append(f"%{name}%")
        if i_t:
            query += " AND i_t = ?"
            params.append(i_t)
        if max_p:
            query += " AND p <= ?"
            params.append(max_p)
            
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute(query, params) as cursor:
                return [Market(*row) for row in await cursor.fetchall()]

    async def save(self):
        """Save/update listing"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            if await Market.get(self.id):
                await db.execute("""
                    UPDATE market SET 
                    sid=?, i_id=?, i_t=?, q=?, p=?, i_n=?
                    WHERE id=?
                """, (self.sid, self.i_id, self.i_t, self.q, self.p, self.i_n, self.id))
            else:
                # Get the next ID from counter table
                async with db.execute("SELECT value FROM counters WHERE name = 'market'") as cursor:
                    counter = (await cursor.fetchone())[0]
                
                new_id = counter + 1
                
                await db.execute("""
                    INSERT INTO market (id, sid, i_id, i_t, q, p, i_n)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (new_id, self.sid, self.i_id, self.i_t, self.q, self.p, self.i_n))
                
                # Update the counter
                await db.execute("UPDATE counters SET value = ? WHERE name = 'market'", (new_id,))
                self.id = new_id
            await db.commit()

    @staticmethod
    async def get_next_id():
        """Get the next available ID for a new listing"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT value FROM counters WHERE name = 'market'") as cursor:
                counter = (await cursor.fetchone())[0]
                return counter + 1

    @staticmethod
    async def create(sid: int, i_id: str, i_t: str, q: int, p: int, i_n: str) -> 'Market':
        """Create new listing with proper ID handling"""
        listing = Market(
            id=None,
            sid=sid,
            i_id=i_id,
            i_t=i_t,
            q=q,
            p=p,
            i_n=i_n
        )
        await listing.save()
        return listing

    async def delete(self):
        """Delete listing"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("DELETE FROM market WHERE id = ?", (self.id,))
            await db.commit()

    @staticmethod
    def initialize():
        """Create market table and counter table"""
        with sqlite3.connect(DATABASE_PATH) as db:
            # Create market table
            db.execute("""
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
            
            # Create counters table if it doesn't exist
            db.execute("""
                CREATE TABLE IF NOT EXISTS counters (
                    name TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                )
            """)
            
            # Initialize market counter if it doesn't exist
            db.execute("""
                INSERT OR IGNORE INTO counters (name, value)
                VALUES ('market', 0)
            """)
            
            db.commit()