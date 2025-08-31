import random
import aiosqlite
import json
from enum import Enum

class Rarity(Enum):
    UR = "UR"
    SSR = "SSR"
    SUPER_RARE = "Super Rare"
    CUSTOM = "Custom"

class ItemClass(Enum):
    DARK = "Dark"
    EARTH = "Earth"
    FIRE = "Fire"
    LIGHT = "Light"
    WATER = "Water"
    WIND = "Wind"

class ItemType(Enum):
    HERO_WEAPON = "Hero_Weapon"
    WEAPON = "Weapon"

def get_database_path():
    """Load the database path from the db.json configuration file."""
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("items", "items.db")  # Default path if not specified
    except Exception as e:
        print(f"Error loading database configuration: {e}")
        return "items.db"  # Fallback to default path


DATABASE_PATH = get_database_path()


class Item:
    """Represents an item with all its attributes."""

    def __init__(
        self,
        id,
        name,
        rarity,
        classType,
        type,
        image,
        description="",
        health=0,
        attack=0,
        defense=0,
        speed=0,
        mp=0,
        precision=0,
        custom_emoji="",
        emoji_name="",
    ):
        self.id = id
        self.name = name
        self.rarity = rarity
        self.classType = classType
        self.type = type
        self.image = image
        self.description = description
        self.health = health
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.mp = mp
        self.precision = precision
        self.custom_emoji = custom_emoji
        self.emoji_name = emoji_name

    @staticmethod
    def from_row(row, column_names):
        """Creates an Item instance from a database row."""
        item_data = dict(zip(column_names, row))
        return Item(**item_data)


class ItemManager:
    """Handles database operations for items."""

    @staticmethod
    async def initialize():
        """Initialize the items table in the database."""
        async with aiosqlite.connect(DATABASE_PATH) as conn:
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    rarity TEXT NOT NULL,
                    classType TEXT NOT NULL,
                    type TEXT NOT NULL,
                    image TEXT NOT NULL,
                    description TEXT,
                    health INTEGER DEFAULT 0,
                    attack INTEGER DEFAULT 0,
                    defense INTEGER DEFAULT 0,
                    speed INTEGER DEFAULT 0,
                    mp INTEGER DEFAULT 0,
                    precision INTEGER DEFAULT 0,
                    custom_emoji TEXT DEFAULT "",
                    emoji_name TEXT DEFAULT ""
                )
                '''
            )

            # Add new columns to existing tables if they don't exist
            try:
                await conn.execute("ALTER TABLE items ADD COLUMN custom_emoji TEXT DEFAULT ''")
            except:
                pass  # Column already exists
            try:
                await conn.execute("ALTER TABLE items ADD COLUMN emoji_name TEXT DEFAULT ''")
            except:
                pass  # Column already exists
            await conn.commit()

    @staticmethod
    async def save(item):
        """Save or update an item in the database."""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                await conn.execute(
                    '''
                    INSERT INTO items (id, name, rarity, classType, type, image, description, health, attack, defense, speed, mp, precision, custom_emoji, emoji_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name=excluded.name,
                        rarity=excluded.rarity,
                        classType=excluded.classType,
                        type=excluded.type,
                        image=excluded.image,
                        description=excluded.description,
                        health=excluded.health,
                        attack=excluded.attack,
                        defense=excluded.defense,
                        speed=excluded.speed,
                        mp=excluded.mp,
                        precision=excluded.precision,
                        custom_emoji=excluded.custom_emoji,
                        emoji_name=excluded.emoji_name
                    ''',
                    (
                        item.id,
                        item.name,
                        item.rarity,
                        item.classType,
                        item.type,
                        item.image,
                        item.description,
                        item.health,
                        item.attack,
                        item.defense,
                        item.speed,
                        item.mp,
                        item.precision,
                        getattr(item, 'custom_emoji', ''),
                        getattr(item, 'emoji_name', ''),
                    ),
                )
                await conn.commit()
        except Exception as e:
            print(f"An error occurred while saving item: {e}")

    @staticmethod
    async def get_all():
        """Retrieve all items from the database."""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                cursor = await conn.execute("SELECT * FROM items")
                rows = await cursor.fetchall()
                column_names = [description[0] for description in cursor.description]
                return [Item.from_row(row, column_names) for row in rows]
        except Exception as e:
            print(f"An error occurred while retrieving items: {e}")
            return []

    @staticmethod
    async def get(item_id):
        """Retrieve a specific item by its ID."""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                cursor = await conn.execute("SELECT * FROM items WHERE id = ?", (item_id,))
                row = await cursor.fetchone()
                if row:
                    column_names = [description[0] for description in cursor.description]
                    return Item.from_row(row, column_names)
                return None
        except Exception as e:
            print(f"An error occurred while retrieving item: {e}")
            return None

    @staticmethod
    async def get_random_item_by_rarity(rarity):
        """Retrieve a random item of a specified rarity."""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                cursor = await conn.execute("SELECT * FROM items WHERE rarity = ?", (rarity,))
                rows = await cursor.fetchall()
                if not rows:
                    return None
                column_names = [description[0] for description in cursor.description]
                selected_row = random.choice(rows)
                return Item.from_row(selected_row, column_names)
        except Exception as e:
            print(f"An error occurred while retrieving a random item by rarity: {e}")
            return None

    @staticmethod
    async def delete(item_id):
        """Delete an item from the database."""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                cursor = await conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
                await conn.commit()
                return cursor.rowcount > 0  # Returns True if item was deleted
        except Exception as e:
            print(f"An error occurred while deleting item {item_id}: {e}")
            return False
