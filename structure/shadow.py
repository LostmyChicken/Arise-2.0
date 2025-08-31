import json
import logging
import aiosqlite

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("shadow", "shadow.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "shadow.db"

DATABASE_PATH = get_database_path()

class Shadow:
    def __init__(self, shadow_id: str, name: str, description: str, image: str, price: int, attack: int, defense: int, required_boss: str = None, custom_emoji: str = "", emoji_name: str = "", rarity: str = "Common"):
        self.id = shadow_id
        self.name = name
        self.description = description
        self.image = image
        self.price = price
        self.attack = attack
        self.defense = defense
        self.required_boss = required_boss
        self.custom_emoji = custom_emoji
        self.emoji_name = emoji_name
        self.rarity = rarity  # Added rarity attribute

    @classmethod
    async def initialize(cls):
        """Initialize the database and create the shadows table if it doesn't exist."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS shadows (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    image TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    attack INTEGER NOT NULL,
                    defense INTEGER NOT NULL,
                    custom_emoji TEXT DEFAULT '',
                    emoji_name TEXT DEFAULT ''
                )
            """)

            # Add custom emoji columns to existing tables if they don't exist
            try:
                await db.execute("ALTER TABLE shadows ADD COLUMN custom_emoji TEXT DEFAULT ''")
            except:
                pass  # Column already exists
            try:
                await db.execute("ALTER TABLE shadows ADD COLUMN emoji_name TEXT DEFAULT ''")
            except:
                pass  # Column already exists
            try:
                await db.execute("ALTER TABLE shadows ADD COLUMN rarity TEXT DEFAULT 'Common'")
            except:
                pass  # Column already exists

            await db.commit()

    @classmethod
    async def get(cls, shadow_id: str):
        """Retrieve a single shadow by its ID."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT id, name, description, image, price, attack, defense, custom_emoji, emoji_name, rarity FROM shadows WHERE id = ?", (shadow_id,))
            row = await cursor.fetchone()
            await cursor.close()
            if row:
                # Handle missing rarity column gracefully
                if len(row) < 10:  # If rarity column is missing
                    row = row + ("Common",)  # Add default rarity
                return cls(*row)
            return None

    @classmethod
    async def get_all(cls):
        """Retrieve all shadows from the database."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT id, name, description, image, price, attack, defense, custom_emoji, emoji_name, rarity FROM shadows")
            rows = await cursor.fetchall()
            await cursor.close()
            shadows = []
            for row in rows:
                # Handle missing rarity column gracefully
                if len(row) < 10:  # If rarity column is missing
                    row = row + ("Common",)  # Add default rarity
                shadows.append(cls(*row))
            return shadows

    async def save(self):
        """Save or update a shadow in the database."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                INSERT OR REPLACE INTO shadows (id, name, description, image, price, attack, defense, custom_emoji, emoji_name, rarity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.id, self.name, self.description, self.image, self.price, self.attack, self.defense, self.custom_emoji, self.emoji_name, self.rarity))
            await db.commit()

    @classmethod
    async def get_all_ids(cls):
        """Retrieve all shadow IDs from the database."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("SELECT id FROM shadows")
            rows = await cursor.fetchall()
            await cursor.close()
            return [row[0] for row in rows]

    @classmethod
    async def delete(cls, shadow_id: str):
        """Delete a shadow from the database."""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                cursor = await db.execute("DELETE FROM shadows WHERE id = ?", (shadow_id,))
                await db.commit()
                return cursor.rowcount > 0  # Returns True if shadow was deleted
        except Exception as e:
            print(f"An error occurred while deleting shadow {shadow_id}: {e}")
            return False
