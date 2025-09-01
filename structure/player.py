import json
import logging
import random
import time
import traceback
import aiohttp
import aiosqlite
import discord
from discord.ext import commands
from structure.skills import SkillManager
from structure.emoji import getEmoji
from structure.items import ItemManager
from datetime import datetime, timedelta

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("player","player.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "player.db"

DATABASE_PATH = get_database_path()

class Player:
    _players = {}

    def __init__(self, player_id, data=None):
        if data is None:
            data = {}
        
        self.id = player_id
        self.level = data.get('level', 1)
        self.xp = data.get('xp', 0)  # Ensure XP always exists
        self.attack = data.get('attack', 10)
        self.defense = data.get('defense', 10)
        self.hp = data.get('hp', 100)
        self.mp = data.get('mp', 10)

        # Migration fix: Ensure XP exists for all players
        if 'xp' not in data and hasattr(self, 'level') and self.level > 1:
            # Calculate approximate XP based on level for existing players
            self.xp = max(0, (self.level - 1) * 50)  # Conservative estimate
        self.gold = data.get('gold', 0)
        self.precision = data.get('precision', 10)
        self.diamond = data.get('diamond', 0)
        self.stone = data.get('stone', 0)
        self.ticket = data.get('ticket', 0)
        self.crystals = data.get('crystals', 0)
        self.premiumT = data.get('premiumT', 0)
        self.premium = data.get('premium', False)
        self.quests = data.get('quests', {})
        self.inventory = data.get('inventory', {})
        self.equipped = data.get('equipped', {
            'Weapon': None, 'Weapon_2': None, 'Basic': None, 'QTE': None, 'Ultimate': None,
            'Helmet': None, 'Armor': None, 'Gloves': None, 'Boots': None, 'Necklaces': None,
            'Bracelets': None, 'Rings': None, 'Earrings': None, 'Party_1': None, 'Party_2': None,
            'Party_3': None, 'army_1': None, 'army_2': None, 'army_3': None
        })
        self.hunters = data.get('hunters', {})

        # SEPARATE STAT POINTS AND SKILL POINTS
        # Stat Points: Used for upgrading base stats (attack, defense, hp, mp, precision)
        # Skill Points: Used for skill tree progression

        # Calculate stat points based on level (10 per level)
        if 'statPoints' not in data or data.get('statPoints', 0) == 0:
            # New player OR existing player without stat points - give stat points based on their level
            self.statPoints = self.calculate_stat_points()
        else:
            # Existing player with stat points - use stored stat points
            self.statPoints = data.get('statPoints', 0)

        # Calculate skill points based on level (5 per level)
        if 'skillPoints' not in data:
            # New player - give skill points based on their level
            self.skillPoints = self.calculate_skill_points()
        else:
            # Existing player - check if skill points need recalculation
            stored_points = data.get('skillPoints', 0)
            calculated_points = self.calculate_skill_points()

            # If stored points are way higher than calculated (old system), use calculated
            if stored_points > calculated_points * 2:  # More than double expected
                self.skillPoints = calculated_points
                print(f"Player {self.id}: Adjusted skill points from {stored_points} to {calculated_points}")
            else:
                self.skillPoints = stored_points

        # Skill reset cooldown (2 weeks)
        self.last_skill_reset = data.get('last_skill_reset', None)
        self.afk = data.get('afk', None)
        self.afk_level = data.get('afk_level', 1)
        self.gacha = data.get('gacha', 0)
        self.skills = data.get('skills', {})
        self.army_lv = data.get('army_lv', 1)
        self.shadows = data.get('shadows', {})
        self.oshi_list = data.get('oshi_list', [])  # List of favorite character/item IDs
        self.locked_items = data.get('locked_items', {})  # Items locked from pulls
        self.badge_collection = data.get('badge_collection', {})  # Legacy items/hunters for badge display
        self.fcube = data.get('fcube', 0)
        self.icube = data.get('icube', 0)
        self.wcube = data.get('wcube', 0)
        self.ecube = data.get('ecube', 0)
        self.dcube = data.get('dcube', 0)
        self.lcube = data.get('lcube', 0)
        self.ccube = data.get('ccube', 0)  # Custom cubes
        self.tos = data.get('tos', 0)
        self.gear1 = data.get('gear1', 0)
        self.gear2 = data.get('gear2', 0)
        self.gear3 = data.get('gear3', 0)
        self.boss = data.get('boss', None)
        self.train = data.get('train', None)
        self.daily = data.get('daily', None)
        self.guild = data.get('guild', None)
        self.trivia = data.get('trivia', None)
        self.raid = data.get('raid', None)
        self.prem1 = data.get('prem1', None)
        self.prem2 = data.get('prem2', None)
        self.prem3 = data.get('prem3', None)
        self.inc = data.get('inc', False)
        self.fight = data.get('fight', None)
        self.dungeon = data.get('dungeon', None)
        self.trade = data.get('trade', False)
        self.key = data.get('key', 0)
        self.vote = data.get('vote', None)
        self.mission = data.get('mission', {"cmd": "", "times": 0})
        self.aStreak = data.get('aStreak', 0)
        self.aC = data.get('aC', 0)
        self.dS = data.get('dS', 0)
        self.lD = data.get('lD', None)
        self.vS = data.get('vS', 0)
        self.lV = data.get('lV', None)
        self.loot = data.get('loot', {"won": 0, "lose": 0})
        self.market = data.get('market', {})
        self.last_stat_reset = data.get('last_stat_reset', None)
        self.defeated_bosses = data.get('defeated_bosses', {})

        # Handle story_progress - ensure it's always a dict
        story_progress_data = data.get('story_progress', {})
        if isinstance(story_progress_data, str):
            try:
                self.story_progress = json.loads(story_progress_data) if story_progress_data else {}
            except json.JSONDecodeError:
                self.story_progress = {}
        else:
            self.story_progress = story_progress_data if isinstance(story_progress_data, dict) else {}

        # Handle unlocked_features - ensure it's always a dict
        unlocked_features_data = data.get('unlocked_features', {})
        if isinstance(unlocked_features_data, str):
            try:
                self.unlocked_features = json.loads(unlocked_features_data) if unlocked_features_data else {}
            except json.JSONDecodeError:
                self.unlocked_features = {}
        else:
            self.unlocked_features = unlocked_features_data if isinstance(unlocked_features_data, dict) else {}

        # Handle titles - ensure it's always a dict
        titles_data = data.get('titles', {})
        if isinstance(titles_data, str):
            try:
                self.titles = json.loads(titles_data) if titles_data else {}
            except json.JSONDecodeError:
                self.titles = {}
        else:
            self.titles = titles_data if isinstance(titles_data, dict) else {}

        # Active title (currently equipped title)
        self.active_title = data.get('active_title', None)
        
    def get_inventory(self):
        """Safely gets the player's inventory."""
        return self.inventory

    def get_hunters(self):
        """Safely gets the player's hunters."""
        return self.hunters

    def calculate_stat_points(self):
        """Calculate total stat points based on player level"""
        # CORRECTED: Stat points: 10 per level for upgrading base stats
        return self.level * 10

    async def calculate_total_stat_points_with_achievements(self):
        """Calculate total stat points including achievement bonuses"""
        base_points = self.level * 10
        achievement_bonus = await self.get_achievement_stat_points()
        return base_points + achievement_bonus

    async def get_achievement_stat_points(self):
        """Get total stat points earned from achievements"""
        from structure.achievement_system import AchievementSystem

        if not hasattr(self, 'achievements') or not self.achievements:
            return 0

        total_bonus = 0

        # Check each unlocked achievement for stat point rewards
        for achievement_id, achievement_data in self.achievements.items():
            if achievement_data.get('unlocked', False):
                # Get the achievement definition
                if achievement_id in AchievementSystem.ACHIEVEMENTS:
                    achievement = AchievementSystem.ACHIEVEMENTS[achievement_id]
                    if hasattr(achievement, 'rewards') and 'stat_points' in achievement.rewards:
                        total_bonus += achievement.rewards['stat_points']

        return total_bonus

    def calculate_skill_points(self):
        """Calculate total skill points based on player level"""
        # CORRECTED: Skill points: 5 per level for skill tree progression
        return self.level * 5

    def update_skill_points_on_levelup(self, old_level):
        """Update skill points when player levels up"""
        # CORRECTED: 5 skill points per level
        old_total = old_level * 5
        new_total = self.calculate_skill_points()
        points_gained = new_total - old_total

        if points_gained > 0:
            self.skillPoints += points_gained
            return points_gained
        return 0

    def spend_skill_points(self, amount):
        """Spend skill points if available"""
        if self.skillPoints >= amount:
            self.skillPoints -= amount
            return True
        return False

    def can_learn_skill(self, level_requirement, skill_points_cost):
        """Check if player can learn a skill"""
        return (self.level >= level_requirement and
                self.skillPoints >= skill_points_cost)

    def add_item(self, item_id, level=1, tier=1, xp=0):
        """
        Adds an item to the player's inventory.
        If the item is a duplicate, it adds a corresponding shard instead.
        Returns True if the item was a duplicate, False otherwise.
        """
        if item_id in self.inventory:
            # It's a duplicate, add a shard instead
            shard_id = f"s_{item_id}"
            self.inventory[shard_id] = self.inventory.get(shard_id, 0) + 1
            return True
        else:
            # It's a new item
            self.inventory[item_id] = {'level': level, 'tier': tier, 'xp': xp}
            return False

    def add_hunter(self, hunter_id, level=1, tier=1, xp=0):
        """
        Adds a hunter to the player's collection.
        If the hunter is a duplicate, it adds a corresponding shard instead.
        Returns True if the hunter was a duplicate, False otherwise.
        """
        if hunter_id in self.hunters:
            # It's a duplicate, add a shard
            shard_id = f"s_{hunter_id}"
            self.inventory[shard_id] = self.inventory.get(shard_id, 0) + 1
            return True
        else:
            # It's a new hunter
            self.hunters[hunter_id] = {'level': level, 'tier': tier, 'xp': xp}
            return False

    # Inside your structure/player.py file

    async def dq_update(self, quest_name: str, amount: int):
        """Updates the progress of a daily quest, safely handling data types."""
        if self.quests and quest_name in self.quests:
            quest = self.quests[quest_name]

            # Handle case where quest might be a string (corrupted data)
            if isinstance(quest, str):
                # Reset to default quest structure
                quest = {'current': 0, 'required': 100, 'completed': False}
                self.quests[quest_name] = quest

            # Ensure quest is a dictionary
            if not isinstance(quest, dict):
                quest = {'current': 0, 'required': 100, 'completed': False}
                self.quests[quest_name] = quest

            if not quest.get('completed', False):
                # --- DEFINITIVE BUG FIX ---
                # Safely convert 'current' to an integer before adding.
                current_progress = int(quest.get('current', 0))
                required_progress = int(quest.get('required', 100))

                quest['current'] = current_progress + amount

                if quest['current'] >= required_progress:
                    quest['completed'] = True
                    quest['current'] = required_progress

    async def add_xp(self, bot: commands.Bot, amount: int, channel: discord.TextChannel):
        """Adds XP to the player and handles level-ups with System notifications."""
        old_level = self.level
        self.xp += amount

        # Track level progression
        starting_level = self.level
        levels_gained = 0
        total_skill_points_gained = 0

        # Handle multiple level-ups
        while True:
            xp_needed = self.level * 100
            if self.xp >= xp_needed:
                self.level += 1
                self.xp -= xp_needed
                levels_gained += 1

                # Give both stat points and skill points on level up
                stat_points_gained = 10  # 10 stat points per level
                skill_points_gained = 5  # 5 skill points per level

                self.statPoints += stat_points_gained
                self.skillPoints += skill_points_gained
                total_skill_points_gained += skill_points_gained
            else:
                break

        # Send System-style level up notification if any levels were gained
        if levels_gained > 0:
            try:
                # Send System-style level up notification
                from structure.system_interface import SystemInterface
                level_up_embed = SystemInterface.create_level_up_notification(
                    old_level, self.level, total_skill_points_gained
                )

                # Try to send notification, but don't crash if it fails
                try:
                    await SystemInterface.send_system_notification(channel, level_up_embed)
                except Exception as e:
                    logging.warning(f"Failed to send level up notification: {e}")
                    # Continue with the rest of the level up process

                # Check for rank up and achievements
                from structure.ranking_system import RankingSystem
                from structure.achievement_system import AchievementSystem

                # Update achievement progress
                # Use consistent attribute names (hp/mp are the correct ones)
                total_stats = self.attack + self.defense + self.hp + self.mp
                achievements = await AchievementSystem.get_player_achievements(str(self.id))

                # Evaluate rank
                new_rank, rank_up_occurred = await RankingSystem.evaluate_player_rank(
                    str(self.id), self.level, total_stats, achievements['total_unlocked']
                )

                if rank_up_occurred:
                    rank_up_embed = SystemInterface.create_rank_up_notification(
                        "Previous", new_rank.value
                    )
                    await SystemInterface.send_system_notification(channel, rank_up_embed, 1.0)

                # Update achievement progress
                newly_unlocked = await AchievementSystem.update_progress(
                    str(self.id),
                    level=self.level,
                    total_xp_gained=self.xp
                )

                # Send achievement notifications
                for achievement in newly_unlocked:
                    achievement_embed = SystemInterface.create_achievement_notification(
                        achievement.name, achievement.description,
                        f"Gold: {achievement.rewards.get('gold', 0)}, SP: {achievement.rewards.get('stat_points', 0)}"
                    )
                    await SystemInterface.send_system_notification(channel, achievement_embed, 1.5)

            except Exception as e:
                # Fallback to original level up message if System fails
                try:
                    member = channel.guild.get_member(self.id) or await bot.fetch_user(self.id)
                    mention = member.mention
                except:
                    mention = f"User (ID: {self.id})"

                embed = discord.Embed(
                    title="🎉 LEVEL UP! 🎉" if levels_gained == 1 else f"🎉 MULTIPLE LEVEL UPS! 🎉",
                    description=f"Congratulations {mention}! You've gained **{levels_gained}** level{'s' if levels_gained > 1 else ''}!",
                    color=discord.Color.gold()
                )
                embed.add_field(
                    name="📈 Level Progression",
                    value=f"`{starting_level}` → `{self.level}` **(+{levels_gained})**",
                    inline=False
                )
                await channel.send(embed=embed)

    def get_shadows(self):
        """Returns the player's shadows dictionary."""
        if isinstance(self.shadows, str):
            try:
                return json.loads(self.shadows)
            except json.JSONDecodeError:
                return {}
        return self.shadows or {}

    def add_shadow(self, shadow_id: str, xp: int = 0):
        """Adds a shadow to the player's collection or adds XP to existing shadow."""
        if isinstance(self.shadows, str):
            try:
                self.shadows = json.loads(self.shadows)
            except json.JSONDecodeError:
                self.shadows = {}

        if not isinstance(self.shadows, dict):
            self.shadows = {}

        if shadow_id not in self.shadows:
            # New shadow
            self.shadows[shadow_id] = {
                "level": 1,
                "xp": xp
            }
        else:
            # Existing shadow - ensure XP field exists and add XP
            if "xp" not in self.shadows[shadow_id]:
                self.shadows[shadow_id]["xp"] = 0
            self.shadows[shadow_id]["xp"] += xp

            # Handle level ups
            while True:
                required_xp = self.get_required_xp(self.shadows[shadow_id]["level"])
                if self.shadows[shadow_id]["xp"] >= required_xp:
                    self.shadows[shadow_id]["xp"] -= required_xp
                    self.shadows[shadow_id]["level"] += 1
                else:
                    break

    def get_required_xp(self, level: int) -> int:
        """Calculate required XP for a given level."""
        return level * 1000  # Simple formula: level * 1000

    def add_boss_defeat(self, boss_id: str):
        """Track that the player has defeated a specific boss."""
        if isinstance(self.defeated_bosses, str):
            try:
                self.defeated_bosses = json.loads(self.defeated_bosses)
            except json.JSONDecodeError:
                self.defeated_bosses = {}

        if not isinstance(self.defeated_bosses, dict):
            self.defeated_bosses = {}

        # Track defeat count and timestamp
        try:
            if boss_id not in self.defeated_bosses:
                self.defeated_bosses[boss_id] = {
                    "count": 1,
                    "first_defeat": int(time.time()),
                    "last_defeat": int(time.time())
                }
            else:
                # Handle case where existing data might not be a dict
                if isinstance(self.defeated_bosses[boss_id], dict):
                    self.defeated_bosses[boss_id]["count"] += 1
                    self.defeated_bosses[boss_id]["last_defeat"] = int(time.time())
                else:
                    # Convert old format to new format
                    self.defeated_bosses[boss_id] = {
                        "count": 2,  # Assume this is the second defeat
                        "first_defeat": int(time.time()) - 3600,  # Estimate first defeat was 1 hour ago
                        "last_defeat": int(time.time())
                    }
        except Exception as e:
            print(f"Error in add_boss_defeat for player {self.id}, boss {boss_id}: {e}")
            # Fallback: create new entry
            self.defeated_bosses[boss_id] = {
                "count": 1,
                "first_defeat": int(time.time()),
                "last_defeat": int(time.time())
            }

    def has_defeated_boss(self, boss_id: str) -> bool:
        """Check if the player has defeated a specific boss."""
        try:
            # Handle string format
            if isinstance(self.defeated_bosses, str):
                try:
                    defeated_bosses = json.loads(self.defeated_bosses)
                except json.JSONDecodeError:
                    return False
            else:
                defeated_bosses = self.defeated_bosses or {}

            # Ensure defeated_bosses is a dictionary
            if not isinstance(defeated_bosses, dict):
                return False

            # Check if boss_id exists
            if boss_id not in defeated_bosses:
                return False

            # Handle both old format (just boss_id as key) and new format (dict with count)
            boss_data = defeated_bosses[boss_id]

            # If boss_data is a dictionary with count
            if isinstance(boss_data, dict):
                return boss_data.get("count", 0) > 0
            # If boss_data is a simple value (old format)
            elif isinstance(boss_data, (int, str, bool)):
                # Old format - just presence means defeated
                return bool(boss_data)
            else:
                # Unknown format, assume not defeated
                return False

        except Exception as e:
            # Log the error and return False for safety
            print(f"Error in has_defeated_boss for player {self.id}, boss {boss_id}: {e}")
            return False

    def setFightCooldown(self):
        """Sets the fight cooldown timestamp."""
        self.fight = time.time()

    def setTriviaCooldown(self):
        """Sets the trivia cooldown timestamp."""
        self.trivia = time.time()

    def mIncrease(self, command_name: str):
        """Increase mission progress for the given command"""
        if self.mission and self.mission.get("cmd") == command_name:
            self.mission["times"] = self.mission.get("times", 0) + 1

    @classmethod
    async def all(cls):
        """Loads all players from the database into the cache."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA busy_timeout = 5000;")
            try:
                cursor = await db.execute("SELECT * FROM players")
                rows = await cursor.fetchall()
            except aiosqlite.OperationalError as e:
                logging.error(f"Failed to load players, table might not exist yet. Error: {e}")
                return []


        for row in rows:
            player_id = row['id']
            if player_id not in cls._players:
                player_data = dict(row)
                # JSON fields need to be decoded
                for key in ['quests', 'inventory', 'equipped', 'hunters', 'skills', 'shadows', 'mission', 'loot', 'market', 'story_progress']:
                    if key in player_data and isinstance(player_data[key], str):
                        try:
                            player_data[key] = json.loads(player_data[key])
                        except (json.JSONDecodeError, TypeError):
                            logging.warning(f"Could not decode JSON for key '{key}' for player {player_id}. Using default.")
                            player_data[key] = {}
                cls._players[player_id] = cls(player_id, data=player_data)
        return list(cls._players.values())

    @classmethod
    async def get(cls, player_id):
        """Gets a player from cache or database."""
        if player_id in cls._players:
            return cls._players[player_id]

        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.cursor() as cursor:
                    await cursor.execute('SELECT * FROM players WHERE id = ?', (player_id,))
                    row = await cursor.fetchone()

                    if row:
                        player_data = dict(row)
                        # JSON fields need to be decoded
                        for key in ['quests', 'inventory', 'equipped', 'hunters', 'skills', 'shadows', 'mission', 'loot', 'market', 'defeated_bosses', 'oshi_list', 'locked_items', 'badge_collection']:
                             if key in player_data and isinstance(player_data[key], str):
                                try:
                                    player_data[key] = json.loads(player_data[key])
                                except (json.JSONDecodeError, TypeError):
                                    logging.warning(f"Could not decode JSON for key '{key}' for player {player_id}. Using default.")
                                    if key in ['oshi_list']:
                                        player_data[key] = []
                                    elif key in ['locked_items', 'badge_collection']:
                                        player_data[key] = {}
                                    else:
                                        player_data[key] = {}
                        
                        player = cls(player_id, data=player_data)
                        cls._players[player_id] = player
                        return player
            # If player not in DB, create a new one, add to cache, and return
            new_player = cls(player_id)
            cls._players[player_id] = new_player
            return new_player
        except Exception as e:
            if "database is locked" in str(e).lower():
                pass
            logging.error(f"Error retrieving player {player_id}: {e}")
            logging.debug(traceback.format_exc())
            # Return a new player instance on error to prevent crashes
            return cls(player_id)

    def _clean_data_for_save(self, data_dict):
        """Clean and optimize data before saving to reduce size."""
        if not isinstance(data_dict, dict):
            return data_dict

        cleaned = {}
        for key, value in data_dict.items():
            # Skip None values and empty strings
            if value is None or value == "":
                continue
            # Clean nested dictionaries
            if isinstance(value, dict):
                cleaned_nested = self._clean_data_for_save(value)
                if cleaned_nested:  # Only add if not empty
                    cleaned[key] = cleaned_nested
            else:
                cleaned[key] = value
        return cleaned

    async def _emergency_cleanup(self):
        """Emergency cleanup for players with extremely large data"""
        try:
            logging.info(f"Performing emergency cleanup for player {self.id}")

            # Reset temporary/cache data
            self.inc = False
            self.trade = False

            # Clean inventory - keep only items with valid data
            if hasattr(self, 'inventory') and self.inventory:
                cleaned_inventory = {}
                for item_id, item_data in list(self.inventory.items())[:1000]:  # Limit to 1000 items
                    if isinstance(item_data, dict) and 'level' in item_data:
                        cleaned_inventory[item_id] = item_data
                self.inventory = cleaned_inventory
                logging.info(f"Cleaned inventory for player {self.id}: {len(cleaned_inventory)} items kept")

            # Clean hunters - keep only hunters with valid data
            if hasattr(self, 'hunters') and self.hunters:
                cleaned_hunters = {}
                for hunter_id, hunter_data in list(self.hunters.items())[:500]:  # Limit to 500 hunters
                    if isinstance(hunter_data, dict) and 'level' in hunter_data:
                        cleaned_hunters[hunter_id] = hunter_data
                self.hunters = cleaned_hunters
                logging.info(f"Cleaned hunters for player {self.id}: {len(cleaned_hunters)} hunters kept")

            # Reset any other large data structures
            large_fields = ['temp_data', 'cache', 'battle_log', 'transaction_history']
            for field in large_fields:
                if hasattr(self, field):
                    setattr(self, field, None)

            logging.info(f"Emergency cleanup completed for player {self.id}")

        except Exception as e:
            logging.error(f"Error during emergency cleanup for player {self.id}: {e}")

    async def save(self):
        """Save the player's data to the database using named parameters for safety."""
        try:
            # Check data size before saving
            import json
            import sys

            player_data_json = json.dumps(self.__dict__, default=str)
            data_size = sys.getsizeof(player_data_json)

            # Warn if data is very large (> 5MB)
            if data_size > 5 * 1024 * 1024:
                logging.warning(f"Player {self.id} data size is {data_size} bytes, which is very large")

                # Auto-cleanup for extremely large data (> 10MB)
                if data_size > 10 * 1024 * 1024:
                    logging.error(f"Player {self.id} data size exceeds 10MB, performing emergency cleanup")
                    await self._emergency_cleanup()
            elif data_size > 1 * 1024 * 1024:  # > 1MB
                logging.info(f"Player {self.id} data size is {data_size} bytes ({data_size / 1024 / 1024:.2f} MB)")

        except Exception as e:
            logging.error(f"Error checking player data size: {e}")

        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                await conn.execute("PRAGMA journal_mode=WAL;")
                await conn.execute("PRAGMA busy_timeout = 5000;")

                # Clean data before saving to reduce size
                cleaned_inventory = self._clean_data_for_save(self.inventory)
                cleaned_hunters = self._clean_data_for_save(self.hunters)
                cleaned_shadows = self._clean_data_for_save(self.shadows)
                cleaned_quests = self._clean_data_for_save(self.quests)
                cleaned_skills = self._clean_data_for_save(self.skills)
                cleaned_market = self._clean_data_for_save(self.market)
                cleaned_defeated_bosses = self._clean_data_for_save(self.defeated_bosses)

                # Ensure story_progress is always a dict before cleaning
                if not hasattr(self, 'story_progress') or self.story_progress is None:
                    self.story_progress = {}
                cleaned_story_progress = self._clean_data_for_save(self.story_progress)

                # Ensure titles is always a dict before cleaning
                if not hasattr(self, 'titles') or self.titles is None:
                    self.titles = {}
                cleaned_titles = self._clean_data_for_save(self.titles)

                # Ensure unlocked_features is always a dict before cleaning
                if not hasattr(self, 'unlocked_features') or self.unlocked_features is None:
                    self.unlocked_features = {}
                cleaned_unlocked_features = self._clean_data_for_save(self.unlocked_features)

                # Create a dictionary of data to save, ensuring JSON fields are encoded
                data = {
                    "id": self.id, "level": self.level, "xp": self.xp, "attack": self.attack, "defense": self.defense,
                    "hp": self.hp, "mp": self.mp, "gold": self.gold, "precision": self.precision, "diamond": self.diamond,
                    "stone": self.stone, "ticket": self.ticket, "crystals": self.crystals, "premiumT": self.premiumT,
                    "premium": self.premium, "skillPoints": self.skillPoints, "statPoints": self.statPoints, "afk": self.afk, "afk_level": self.afk_level,
                    "gacha": self.gacha, "army_lv": self.army_lv, "fcube": self.fcube, "icube": self.icube,
                    "wcube": self.wcube, "ecube": self.ecube, "dcube": self.dcube, "lcube": self.lcube, "ccube": self.ccube, "tos": self.tos, "gear1": self.gear1,
                    "gear2": self.gear2, "gear3": self.gear3, "boss": self.boss, "train": self.train, "daily": self.daily,
                    "guild": self.guild, "trivia": self.trivia, "raid": self.raid, "prem1": self.prem1, "prem2": self.prem2,
                    "prem3": self.prem3, "inc": self.inc, "fight": self.fight, "dungeon": self.dungeon, "trade": self.trade,
                    "key": self.key, "vote": self.vote, "aStreak": self.aStreak, "aC": self.aC, "dS": self.dS, "lD": self.lD,
                    "vS": self.vS, "lV": self.lV, "last_stat_reset": self.last_stat_reset, "last_skill_reset": self.last_skill_reset,
                    "market": json.dumps(cleaned_market, separators=(',', ':')),
                    "loot": json.dumps(self.loot, separators=(',', ':')),
                    "mission": json.dumps(self.mission, separators=(',', ':')),
                    "story_progress": json.dumps(cleaned_story_progress, separators=(',', ':')),
                    "shadows": json.dumps(cleaned_shadows, separators=(',', ':')),
                    "quests": json.dumps(cleaned_quests, separators=(',', ':')),
                    "inventory": json.dumps(cleaned_inventory, separators=(',', ':')),
                    "equipped": json.dumps(self.equipped, separators=(',', ':')),
                    "hunters": json.dumps(cleaned_hunters, separators=(',', ':')),
                    "skills": json.dumps(cleaned_skills, separators=(',', ':')),
                    "defeated_bosses": json.dumps(cleaned_defeated_bosses, separators=(',', ':')),
                    "oshi_list": json.dumps(self.oshi_list, separators=(',', ':')),
                    "locked_items": json.dumps(self.locked_items, separators=(',', ':')),
                    "badge_collection": json.dumps(self.badge_collection, separators=(',', ':')),
                    "titles": json.dumps(cleaned_titles, separators=(',', ':')),
                    "active_title": self.active_title,
                    "unlocked_features": json.dumps(cleaned_unlocked_features, separators=(',', ':'))
                }

                # Check total data size before saving
                total_size = sum(len(str(v).encode('utf-8')) for v in data.values())
                if total_size > 1000000:  # 1MB limit
                    logging.warning(f"Player {self.id} data size is {total_size} bytes, which is very large")
                    # Try to reduce size by removing old/unnecessary data
                    if len(cleaned_inventory) > 1000:
                        logging.warning(f"Player {self.id} has {len(cleaned_inventory)} inventory items - this might be too many")

                columns = ', '.join(data.keys())
                placeholders = ', '.join(f':{key}' for key in data.keys())

                query = f"INSERT OR REPLACE INTO players ({columns}) VALUES ({placeholders})"

                await conn.execute(query, data)
                await conn.commit()
        except Exception as e:
            logging.error(f"Failed to save player {self.id}: {e}")
            logging.debug(traceback.format_exc())
            # If it's a size error, try to provide more helpful information
            if "string or blob too big" in str(e).lower():
                logging.error(f"Database size error for player {self.id}. Inventory items: {len(self.inventory)}, Hunters: {len(self.hunters)}")
                raise Exception(f"Player data too large to save. Use debug commands to analyze and clean up data.")

    def add_skill(self, skill_id: str, level: int = 1):
        """Adds a skill to the player's collection."""
        if not hasattr(self, 'skills') or not self.skills:
            self.skills = {}

        if skill_id in self.skills:
            # Skill already exists, could upgrade level
            self.skills[skill_id]['level'] = max(self.skills[skill_id].get('level', 1), level)
        else:
            # New skill
            self.skills[skill_id] = {'level': level}

    def hunter_add_xp(self, hunter_id: str, xp_amount: int):
        """Adds XP to a hunter and handles level ups."""
        if hunter_id not in self.hunters:
            return None, 0, 0  # Hunter not found

        hunter_data = self.hunters[hunter_id]
        current_xp = hunter_data.get('xp', 0)
        current_level = hunter_data.get('level', 1)
        current_tier = hunter_data.get('tier', 0)

        # Add XP
        new_xp = current_xp + xp_amount
        hunter_data['xp'] = new_xp

        # Calculate level ups
        levels_gained = 0
        level_cap = {0: 10, 1: 20, 2: 40, 3: 60, 4: 80, 5: 100}.get(current_tier, 100)

        # Simple XP to level conversion (100 XP per level)
        target_level = min(current_level + (new_xp // 100), level_cap)
        levels_gained = target_level - current_level

        if levels_gained > 0:
            hunter_data['level'] = target_level
            # Reset XP after level up
            hunter_data['xp'] = new_xp % 100

        return hunter_data, xp_amount, levels_gained

    def weapon_add_xp(self, weapon_id: str, xp_amount: int):
        """Adds XP to a weapon and handles level ups."""
        if weapon_id not in self.inventory:
            return None, 0, 0  # Weapon not found

        weapon_data = self.inventory[weapon_id]
        current_xp = weapon_data.get('xp', 0)
        current_level = weapon_data.get('level', 1)
        current_tier = weapon_data.get('tier', 0)

        # Add XP
        new_xp = current_xp + xp_amount
        weapon_data['xp'] = new_xp

        # Calculate level ups
        levels_gained = 0
        level_cap = {0: 10, 1: 20, 2: 40, 3: 60, 4: 80, 5: 100}.get(current_tier, 100)

        # Simple XP to level conversion (100 XP per level)
        target_level = min(current_level + (new_xp // 100), level_cap)
        levels_gained = target_level - current_level

        if levels_gained > 0:
            weapon_data['level'] = target_level
            # Reset XP after level up
            weapon_data['xp'] = new_xp % 100

        return weapon_data, xp_amount, levels_gained

    @staticmethod
    async def vacuum_database():
        """Perform database maintenance to prevent bloat"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                await conn.execute("PRAGMA optimize")
                await conn.execute("VACUUM")
                await conn.commit()
                logging.info("Database vacuum completed successfully")
        except Exception as e:
            logging.error(f"Error during database vacuum: {e}")

    @staticmethod
    async def get_database_size():
        """Get current database size"""
        try:
            import os
            if os.path.exists(DATABASE_PATH):
                return os.path.getsize(DATABASE_PATH)
            return 0
        except Exception:
            return 0

    @staticmethod
    async def delete_player(player_id: int):
        """Delete a player from the database (Admin only)"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                # Delete from main players table
                await conn.execute("DELETE FROM players WHERE id = ?", (player_id,))

                # Delete from related tables if they exist
                tables_to_clean = [
                    "player_skill_trees",
                    "player_achievements",
                    "player_missions",
                    "player_quests",
                    "player_inventory",
                    "player_stats"
                ]

                for table in tables_to_clean:
                    try:
                        await conn.execute(f"DELETE FROM {table} WHERE player_id = ?", (str(player_id),))
                    except:
                        # Table might not exist, continue
                        pass

                await conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error deleting player {player_id}: {e}")
            return False


async def send_webhook(player_id, error_message):
        WEBHOOK_URL = "https://discord.com/api/webhooks/1334586308047405166/ApqdQVPEEPU4pPa32Y719c6Szac-uZzPBc92UYXw6x8T2iGZGDJuPYK_AnNIVhGiU1QB"

        async with aiohttp.ClientSession() as session:
            payload = {
                "embeds": [{
                    "title": "Database Lock Detected ⚠️",
                    "color": 16711680,  # Red color
                    "fields": [
                        {"name": "Player ID", "value": str(player_id), "inline": True},
                        {"name": "Time", "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), "inline": False},
                        {"name": "Error", "value": str(error_message), "inline": False}
                    ]
                }]
            }
            await session.post(WEBHOOK_URL, json=payload)