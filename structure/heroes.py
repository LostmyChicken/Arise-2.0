from enum import Enum
import json
import logging
import random
import aiosqlite


class HeroType(Enum):
    HEALER = "Healer"
    TANK = "Tank"
    DPS = "DPS"
    SUPPORT = "Support"
    MAGE = "Mage"
    ASSASSIN = "Assassin"
    
DATABASE_PATH = "heroes.db"
JSON_PATH = "hunters.json"

async def migrate_to_json():
    try:
        async with aiosqlite.connect(DATABASE_PATH) as conn:
            cursor = await conn.execute("SELECT * FROM heroes")
            rows = await cursor.fetchall()
            
            column_names = [description[0] for description in cursor.description]
            heroes = [dict(zip(column_names, row)) for row in rows]
            
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(heroes, f, indent=4, ensure_ascii=False)
            
            logging.info(f"Successfully migrated {len(heroes)} heroes to {JSON_PATH}")
    except Exception as e:
        logging.error(f"An error occurred during migration: {e}")

# Run the migration

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("hunter", "heroes.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "heroes.db"


DATABASE_PATH = get_database_path()

class Hero:
    def __init__(self, id, name, rarity, classType, type, image, description, health, attack, defense, speed, mp,
                 age, gender, country, weapon, guild, rank, custom_emoji="", emoji_name=""):  # Add custom emoji support
        self.id = id
        self.name = name
        self.rarity = rarity
        self.classType = classType
        self.type = type  # Hero type (e.g., Healer, DPS)
        self.image = image
        self.description = description
        self.health = health
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.mp = mp
        self.age = age  # Integer
        self.gender = gender  # String
        self.country = country  # String
        self.weapon = weapon  # String
        self.guild = guild  # String
        self.rank = rank  # Rank attribute
        self.custom_emoji = custom_emoji  # Custom emoji string
        self.emoji_name = emoji_name  # Emoji name

    def to_dict(self):
        """Convert Hero attributes to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "rarity": self.rarity,
            "classType": self.classType,
            "type": self.type,
            "image": self.image,
            "description": self.description,
            "health": self.health,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "mp": self.mp,
            "age": self.age,
            "gender": self.gender,
            "country": self.country,
            "weapon": self.weapon,
            "guild": self.guild,
            "rank": self.rank,
            "custom_emoji": getattr(self, 'custom_emoji', ''),
            "emoji_name": getattr(self, 'emoji_name', ''),
        }
    @staticmethod
    def from_row(row, column_names):
        """Creates an Item instance from a database row."""
        item_data = dict(zip(column_names, row))
        return Hero(**item_data)
    def __repr__(self):
        return (f"Hero(id={self.id}, name={self.name}, rarity={self.rarity}, classType={self.classType}, "
                f"type={self.type}, rank={self.rank}, age={self.age}, gender={self.gender}, country={self.country}, "
                f"weapon={self.weapon}, guild={self.guild})")

HUNTERS_JSON_PATH = "hunters.json"

class HeroManager:
    @staticmethod
    async def get(hero_id):
        """Retrieve a hero by ID from hunters.json and return it as a Hero object."""
        try:
            with open(HUNTERS_JSON_PATH, "r", encoding="utf-8") as file:
                heroes = json.load(file)

            for hero_data in heroes:
                if hero_data["id"] == hero_id:
                    return Hero(**hero_data)  # Return as a Hero object
            return None
        except Exception as e:
            logging.error(f"An error occurred while retrieving hero: {e}")
            return None

    @staticmethod
    async def get_all():
        """Retrieve all heroes from hunters.json and return them as a list of Hero objects."""
        try:
            with open(HUNTERS_JSON_PATH, "r", encoding="utf-8") as file:
                heroes = json.load(file)

            return [Hero(**hero_data) for hero_data in heroes]  # Convert each to a Hero object
        except Exception as e:
            logging.error(f"An error occurred while retrieving heroes: {e}")
            return []

    @staticmethod
    async def save(hero: Hero):
        """Save a hero to hunters.json (update if exists, otherwise add new)."""
        try:
            with open(HUNTERS_JSON_PATH, "r", encoding="utf-8") as file:
                heroes = json.load(file)

            hero_dict = hero.to_dict()  # Convert Hero object to dictionary

            for i, existing_hero in enumerate(heroes):
                if existing_hero["id"] == hero.id:
                    heroes[i] = hero_dict  # Update existing hero
                    break
            else:
                heroes.append(hero_dict)  # Add new hero if not found

            with open(HUNTERS_JSON_PATH, "w", encoding="utf-8") as file:
                json.dump(heroes, file, indent=4)

        except Exception as e:
            logging.error(f"An error occurred while saving hero: {e}")

    @staticmethod
    async def get_random(rarity):
        """Retrieve a random hero of a specified rarity. If none are found, return a random hero."""
        try:
            with open(HUNTERS_JSON_PATH, "r", encoding="utf-8") as file:
                heroes = json.load(file)

            filtered_heroes = [Hero(**hero) for hero in heroes if hero["rarity"] == rarity]

            if not filtered_heroes:
                filtered_heroes = [Hero(**hero) for hero in heroes]  # If no heroes match rarity, pick from all

            if not filtered_heroes:
                return None  # No heroes available

            return random.choice(filtered_heroes)  # Return as a Hero object

        except Exception as e:
            logging.error(f"An error occurred while retrieving a random hero: {e}")
            return None

    @staticmethod
    async def delete(hero_id):
        """Delete a hero from hunters.json."""
        try:
            with open(HUNTERS_JSON_PATH, "r", encoding="utf-8") as file:
                heroes = json.load(file)

            # Find and remove the hero
            original_count = len(heroes)
            heroes = [hero for hero in heroes if hero["id"] != hero_id]

            if len(heroes) < original_count:
                # Hero was found and removed
                with open(HUNTERS_JSON_PATH, "w", encoding="utf-8") as file:
                    json.dump(heroes, file, indent=4)
                return True
            else:
                # Hero not found
                return False

        except Exception as e:
            logging.error(f"An error occurred while deleting hero {hero_id}: {e}")
            return False
