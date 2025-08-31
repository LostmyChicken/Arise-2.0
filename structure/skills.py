from enum import Enum, auto
import json
from typing import List, Dict, Any, Optional
import discord
from discord.ext import commands
import aiosqlite
import logging

class EffectType(Enum):
    DAMAGE = auto()          # Direct damage
    HEAL = auto()            # Restores health
    STUN = auto()            # Stuns the enemy
    BLEED = auto()           # Applies a damage-over-time effect
    SHIELD = auto()          # Grants a shield to absorb damage
    BUFF = auto()            # Enhances player stats
    DEBUFF = auto()          # Reduces enemy stats
    LIFE_STEAL = auto()      # Converts damage dealt into healing
    CRIT_BOOST = auto()      # Increases critical hit chance
    AREA_DAMAGE = auto()     # Deals damage to multiple enemies
    INVINCIBILITY = auto()   # Grants temporary immunity to damage
    def getDes(self):
        descriptions = {
            EffectType.DAMAGE: "Deals direct damage to target enemy.",
            EffectType.HEAL: "Restores health to the target ally.",
            EffectType.STUN: "Temporarily disables the enemy's actions.",
            EffectType.BLEED: "Inflicts damage over time to the enemy.",
            EffectType.SHIELD: "Absorbs incoming damage with a protective shield.",
            EffectType.BUFF: "Enhances the stats of the target ally.",
            EffectType.DEBUFF: "Reduces the stats of the target enemy.",
            EffectType.LIFE_STEAL: "Heals the user based on dealt damage.",
            EffectType.CRIT_BOOST: "Increases the user's critical hit chance.",
            EffectType.AREA_DAMAGE: "Deals damage to multiple nearby enemies.",
            EffectType.INVINCIBILITY: "Grants temporary immunity to all incoming damage."
        }
        return descriptions.get(self, "Unknown effect type.")

class SkillType(Enum):
    BASIC = "Basic"
    QTE = "QTE"              # Quick-Time Event Skill
    ULTIMATE = "Ultimate"


class Element(Enum):
    DARK = "Dark"
    EARTH = "Earth"
    FIRE = "Fire"
    LIGHT = "Light"
    WATER = "Water"
    WIND = "Wind"


class Skill:
    def __init__(
        self, 
        id: str, 
        skill_type: SkillType, 
        name: str, 
        effects: List[EffectType], 
        damage: int, 
        mp_cost: int, 
        element: Element, 
        character_id: Optional[str] = None,  # Add character ID
        level: int = 1
    ):
        
        self.id = id
        self.skill_type = skill_type
        self.name = name
        self.effects = effects
        self.damage = damage
        self.mp_cost = mp_cost
        self.element = element
        self.character_id = character_id  # Associate skill with a character
        self.level = level

        # Base stats for scaling calculations
        self.base_damage = damage
        self.base_mp_cost = mp_cost

    def get_scaled_damage(self, skill_level: int = None) -> int:
        """Get damage scaled by skill level"""
        level = skill_level or self.level
        # Damage increases by 15% per level (rounded properly)
        scaling_factor = 1 + (level - 1) * 0.15
        return round(self.base_damage * scaling_factor)

    def get_scaled_mp_cost(self, skill_level: int = None) -> int:
        """Get MP cost scaled by skill level (slightly increases)"""
        level = skill_level or self.level
        # MP cost increases by 5% per level (diminishing returns)
        scaling_factor = 1 + (level - 1) * 0.05
        return round(self.base_mp_cost * scaling_factor)

    def get_skill_description(self, skill_level: int = None) -> str:
        """Get detailed skill description with current stats"""
        level = skill_level or self.level
        damage = self.get_scaled_damage(level)
        mp_cost = self.get_scaled_mp_cost(level)

        effects_desc = ", ".join([effect.name.replace("_", " ").title() for effect in self.effects])

        # Check if this is a buff-only skill
        is_buff_only = (damage == 0 or
                       (EffectType.BUFF in self.effects and
                        EffectType.DAMAGE not in self.effects and
                        EffectType.AREA_DAMAGE not in self.effects))

        damage_text = "No Damage (Buff Only)" if is_buff_only else f"{damage}% ({self.base_damage}% base)"

        return (
            f"**{self.name}** (Level {level})\n"
            f"**Type**: {self.skill_type.value}\n"
            f"**Damage**: {damage_text}\n"
            f"**MP Cost**: {mp_cost} ({self.base_mp_cost} base)\n"
            f"**Element**: {self.element.value}\n"
            f"**Effects**: {effects_desc}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.skill_type.value,
            "name": self.name,
            "effects": [effect.name for effect in self.effects],
            "damage": self.damage,
            "mp_cost": self.mp_cost,
            "element": self.element.value,
            "character_id": self.character_id,
            "level":self.level# Include character ID in dictionary
        }

    def __repr__(self) -> str:
        return (f"Skill(id={self.id}, type={self.skill_type.value}, name={self.name}, "
                f"effects={[effect.name for effect in self.effects]}, damage={self.damage}, "
                f"mp_cost={self.mp_cost}, element={self.element.value}, character_id={self.character_id}, level={self.level}")


def get_database_path():
    """Load the database path from the db.json configuration file."""
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("skills", "skills.db")  # Default path if not specified
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "skills.db"  # Fallback to default path

DATABASE_PATH = get_database_path()

class SkillManager:
    DATABASE_PATH = get_database_path()

    @staticmethod
    async def migrate_add_level():
        """
        Add a default level of 1 to all existing skills in the database.
        """
        try:
            async with aiosqlite.connect(SkillManager.DATABASE_PATH) as conn:
                # Add the `level` column if it doesn't already exist
                await conn.execute("ALTER TABLE skills ADD COLUMN level INTEGER NOT NULL DEFAULT 1")
                await conn.commit()
                logging.info("Migration successful: Added 'level' column with default value 1 to all skills.")
        except aiosqlite.OperationalError as e:
            if "duplicate column name: level" in str(e).lower():
                logging.info("Migration skipped: 'level' column already exists.")
            else:
                logging.error(f"Migration failed: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during migration: {e}")
    @staticmethod
    async def initialize():
        try:
            async with aiosqlite.connect(SkillManager.DATABASE_PATH) as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS skills (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        effects TEXT NOT NULL,  -- Store effects as a comma-separated string
                        damage INTEGER NOT NULL,
                        mp_cost INTEGER NOT NULL,  -- Mana points required
                        element TEXT NOT NULL,  -- Store element as a string
                        character_id TEXT,  -- Add character ID column
                        level INTEGER NOT NULL DEFAULT 1  -- Add level column with default value
                    )
                ''')

                await conn.commit()
        except Exception as e:
            logging.error(f"Failed to initialize skills database: {e}")

    @staticmethod
    async def get(skill_id: str) -> Optional[Skill]:
        try:
            async with aiosqlite.connect(SkillManager.DATABASE_PATH) as conn:
                cursor = await conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,))
                row = await cursor.fetchone()
                if row:
                    return Skill(
                        id=row[0],
                        skill_type=SkillType(row[1]),
                        name=row[2],
                        effects=[EffectType[effect] for effect in row[3].split(",")],
                        damage=row[4],
                        mp_cost=row[5],
                        element=Element[row[6]],
                        character_id=row[7],
                        level=row[8]# Retrieve character ID
                    )
                return None
        except Exception as e:
            logging.error(f"Failed to retrieve skill with ID {skill_id}: {e}")
            return None

    @staticmethod
    async def save(skill: Skill):
        try:
            async with aiosqlite.connect(SkillManager.DATABASE_PATH) as conn:
                query = '''
                    INSERT INTO skills (id, type, name, effects, damage, mp_cost, element, character_id, level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        type = excluded.type,
                        name = excluded.name,
                        effects = excluded.effects,
                        damage = excluded.damage,
                        mp_cost = excluded.mp_cost,
                        element = excluded.element,
                        character_id = excluded.character_id,
                        level = excluded.level
                '''
                await conn.execute(
                    query,
                    (
                        skill.id,
                        skill.skill_type.value,
                        skill.name,
                        ",".join([effect.name for effect in skill.effects]),
                        skill.damage,
                        skill.mp_cost,
                        skill.element.value.upper(),
                        skill.character_id,
                        skill.level
                    )
                )
                await conn.commit()
        except Exception as e:
            logging.error(f"Failed to save skill {skill.id}: {e}")

    @staticmethod
    async def get_all() -> List[Skill]:
        try:
            async with aiosqlite.connect(SkillManager.DATABASE_PATH) as conn:
                cursor = await conn.execute("SELECT * FROM skills")
                rows = await cursor.fetchall()
                return [
                    Skill(
                        id=row[0],
                        skill_type=SkillType(row[1]),
                        name=row[2],
                        effects=[EffectType[effect.strip()] for effect in row[3].split(",")],
                        damage=row[4],
                        mp_cost=row[5],
                        element=Element[row[6]],
                        character_id=row[7],
                        level=row[8]
                    )
                    for row in rows
                ]
        except Exception as e:
            logging.error(f"Failed to retrieve all skills: {e}")
            return []

    @staticmethod
    async def get_player_skill_level(player_id: str, skill_id: str) -> int:
        """Get the player's level for a specific skill"""
        try:
            from structure.skill_tree_system import SkillTreeSystem, SkillTreeType

            # Check all skill trees for this skill
            for tree_type in SkillTreeType:
                tree_data = await SkillTreeSystem.get_player_skill_tree(player_id, tree_type)
                if skill_id in tree_data['unlocked_skills']:
                    return tree_data['skill_levels'].get(skill_id, 1)

            return 1  # Default level if not found
        except Exception as e:
            logging.error(f"Error getting player skill level: {e}")
            return 1

    @staticmethod
    async def get_skill_with_player_level(skill_id: str, player_id: str) -> Optional[Skill]:
        """Get skill with player's current level applied"""
        try:
            skill = await SkillManager.get(skill_id)
            if not skill:
                return None

            player_skill_level = await SkillManager.get_player_skill_level(str(player_id), skill_id)

            # Create a copy with scaled stats
            scaled_skill = Skill(
                skill.id,
                skill.skill_type,
                skill.name,
                skill.effects,
                skill.get_scaled_damage(player_skill_level),
                skill.get_scaled_mp_cost(player_skill_level),
                skill.element,
                skill.character_id,
                player_skill_level
            )

            return scaled_skill
        except Exception as e:
            logging.error(f"Error getting skill with player level: {e}")
            return await SkillManager.get(skill_id)  # Fallback to base skill

