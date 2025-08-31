import json
import logging
import aiosqlite

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("boss", "data/bosses.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "data/bosses.db"

DATABASE_PATH = get_database_path()

class Boss:
    def __init__(
        self, 
        boss_id: str, 
        name: str, 
        description: str, 
        image: str, 
        attack: int, 
        defense: int, 
        health: int, 
        speed: int, 
        precision: int, 
        rarity: str, 
        boss_class: str, 
        weakness_class: str
    ):
        self.id = boss_id
        self.name = name
        self.description = description
        self.image = image
        self.attack = attack
        self.defense = defense
        self.health = health
        self.speed = speed
        self.precision = precision
        self.rarity = rarity
        self.boss_class = boss_class
        self.weakness_class = weakness_class

    @classmethod
    async def initialize(cls):
        """Initialize the database and create the bosses table if it doesn't exist."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bosses (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    image TEXT NOT NULL,
                    attack INTEGER NOT NULL,
                    defense INTEGER NOT NULL,
                    health INTEGER NOT NULL,
                    speed INTEGER NOT NULL,
                    precision INTEGER NOT NULL,
                    rarity TEXT NOT NULL,
                    class TEXT NOT NULL,
                    weaknessClass TEXT NOT NULL
                )
            """)
            await db.commit()

    @classmethod
    async def get(cls, boss_id: str):
        """Retrieve a single boss by its ID."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT * FROM bosses WHERE id = ?", (boss_id,))
            row = await cursor.fetchone()
            await cursor.close()
            if row:
                return cls(*row)
            return None

    @classmethod
    async def get_all(cls):
        """Retrieve all bosses from the database."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT * FROM bosses")
            rows = await cursor.fetchall()
            await cursor.close()
            return [cls(*row) for row in rows]

    async def save(self):
        """Save or update a boss in the database."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                INSERT OR REPLACE INTO bosses (
                    id, name, description, image, attack, defense, health, speed, precision, rarity, class, weaknessClass
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.id, self.name, self.description, self.image, self.attack, self.defense,
                self.health, self.speed, self.precision, self.rarity, self.boss_class, self.weakness_class
            ))
            await db.commit()

    @classmethod
    async def get_all_ids(cls):
        """Retrieve all boss IDs from the database."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT id FROM bosses")
            rows = await cursor.fetchall()
            await cursor.close()
            return [row[0] for row in rows]

    @classmethod
    async def delete(cls, boss_id: str):
        """Delete a boss from the database."""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                cursor = await db.execute("DELETE FROM bosses WHERE id = ?", (boss_id,))
                await db.commit()
                return cursor.rowcount > 0  # Returns True if boss was deleted
        except Exception as e:
            print(f"An error occurred while deleting boss {boss_id}: {e}")
            return False

    @classmethod
    async def delete(cls, boss_id: str):
        """Delete a boss from the database."""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                cursor = await db.execute("DELETE FROM bosses WHERE id = ?", (boss_id,))
                await db.commit()
                return cursor.rowcount > 0  # Returns True if boss was deleted
        except Exception as e:
            print(f"An error occurred while deleting boss {boss_id}: {e}")
            return False