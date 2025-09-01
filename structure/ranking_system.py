import json
import logging
import aiosqlite
from typing import Dict, List, Optional, Tuple
from enum import Enum

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("ranking", "ranking.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "ranking.db"

DATABASE_PATH = get_database_path()

class HunterRank(Enum):
    """Hunter ranking system from Solo Leveling"""
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"
    NATIONAL = "National"

class RankingSystem:
    """
    Solo Leveling style Hunter Ranking System
    """
    
    # Rank requirements (level, total stats) - Achievement requirement removed
    RANK_REQUIREMENTS = {
        HunterRank.E: {"level": 1, "total_stats": 0},
        HunterRank.D: {"level": 10, "total_stats": 500},
        HunterRank.C: {"level": 25, "total_stats": 1500},
        HunterRank.B: {"level": 50, "total_stats": 4000},
        HunterRank.A: {"level": 75, "total_stats": 8000},
        HunterRank.S: {"level": 100, "total_stats": 15000},
        HunterRank.NATIONAL: {"level": 150, "total_stats": 30000}
    }
    
    # Rank benefits and unlocks
    RANK_BENEFITS = {
        HunterRank.E: {
            "description": "Novice Hunter - Just starting your journey",
            "max_party_size": 2,
            "dungeon_access": ["Training Grounds"],
            "daily_quests": 3,
            "stat_bonus": 0
        },
        HunterRank.D: {
            "description": "Apprentice Hunter - Learning the basics",
            "max_party_size": 3,
            "dungeon_access": ["Training Grounds", "Goblin Caves"],
            "daily_quests": 4,
            "stat_bonus": 10
        },
        HunterRank.C: {
            "description": "Competent Hunter - Proven in battle",
            "max_party_size": 4,
            "dungeon_access": ["Training Grounds", "Goblin Caves", "Shadow Fortress"],
            "daily_quests": 5,
            "stat_bonus": 25
        },
        HunterRank.B: {
            "description": "Skilled Hunter - Respected by peers",
            "max_party_size": 5,
            "dungeon_access": ["Training Grounds", "Goblin Caves", "Shadow Fortress", "Crystal Mines"],
            "daily_quests": 6,
            "stat_bonus": 50
        },
        HunterRank.A: {
            "description": "Elite Hunter - Among the strongest",
            "max_party_size": 6,
            "dungeon_access": ["All Standard Dungeons", "Dragon's Lair"],
            "daily_quests": 7,
            "stat_bonus": 100
        },
        HunterRank.S: {
            "description": "S-Rank Hunter - Legendary warrior",
            "max_party_size": 8,
            "dungeon_access": ["All Dungeons", "Void Temple", "Raid Dungeons"],
            "daily_quests": 8,
            "stat_bonus": 200
        },
        HunterRank.NATIONAL: {
            "description": "National Level Hunter - Unmatched power",
            "max_party_size": 10,
            "dungeon_access": ["All Content", "Exclusive National Dungeons"],
            "daily_quests": 10,
            "stat_bonus": 500
        }
    }
    
    @classmethod
    async def initialize(cls):
        """Initialize the ranking database"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
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

            # Create player_ranks table for compatibility
            await db.execute("""
                CREATE TABLE IF NOT EXISTS player_ranks (
                    player_id TEXT PRIMARY KEY,
                    current_rank TEXT NOT NULL DEFAULT 'E',
                    progress INTEGER DEFAULT 0,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create leaderboard table for compatibility
            await db.execute("""
                CREATE TABLE IF NOT EXISTS leaderboard (
                    id INTEGER PRIMARY KEY,
                    rank TEXT NOT NULL,
                    rank_ INTEGER NOT NULL,
                    power INTEGER NOT NULL
                )
            """)

            await db.commit()
    
    @classmethod
    async def get_player_rank(cls, player_id: str) -> Tuple[HunterRank, int]:
        """Get player's current rank and rank points, with migration from old system"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # First check new ranking system
            cursor = await db.execute(
                "SELECT current_rank, rank_points FROM hunter_rankings WHERE player_id = ?",
                (player_id,)
            )
            result = await cursor.fetchone()
            await cursor.close()

            if result:
                rank_str, points = result
                try:
                    rank = HunterRank(rank_str)
                except ValueError:
                    rank = HunterRank.E
                return rank, points

            # Check old ranking system for migration
            try:
                # First check if leaderboard table exists
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='leaderboard'"
                )
                table_exists = await cursor.fetchone()
                await cursor.close()

                if table_exists:
                    cursor = await db.execute(
                        "SELECT rank, rank_ FROM leaderboard WHERE id = ?",
                        (int(player_id),)
                    )
                    old_result = await cursor.fetchone()
                    await cursor.close()

                    if old_result:
                        old_rank_str, old_position = old_result
                        # Convert old rank to new rank system
                        new_rank = cls._convert_old_rank_to_new(old_rank_str)

                        # Migrate to new system
                        await cls.set_player_rank(player_id, new_rank, 0)
                        return new_rank, 0
            except Exception as e:
                # Silently handle migration errors - table might not exist
                pass

            # No rank found, calculate based on player stats
            try:
                from structure.player import Player
                player = await Player.get(int(player_id))
                if player:
                    rank, _ = await cls._calculate_rank_internal(player_id)
                    return rank, 0
            except Exception as e:
                logging.error(f"Error calculating rank for {player_id}: {e}")

            # Default to E rank
            await cls.set_player_rank(player_id, HunterRank.E, 0)
            return HunterRank.E, 0

    @classmethod
    def _convert_old_rank_to_new(cls, old_rank: str) -> HunterRank:
        """Convert old ranking system ranks to new system"""
        old_to_new_mapping = {
            "E-Rank": HunterRank.E,
            "D-Rank": HunterRank.D,
            "C-Rank": HunterRank.C,
            "B-Rank": HunterRank.B,
            "A-Rank": HunterRank.A,
            "S-Rank": HunterRank.S,
            "National Level": HunterRank.NATIONAL,
            # Handle variations
            "E": HunterRank.E,
            "D": HunterRank.D,
            "C": HunterRank.C,
            "B": HunterRank.B,
            "A": HunterRank.A,
            "S": HunterRank.S,
            "National": HunterRank.NATIONAL,
        }
        return old_to_new_mapping.get(old_rank, HunterRank.E)
    
    @classmethod
    async def set_player_rank(cls, player_id: str, rank: HunterRank, points: int = 0):
        """Set player's rank and points"""
        import time
        current_time = str(time.time())
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Get current rank for history
            cursor = await db.execute(
                "SELECT current_rank, rank_history FROM hunter_rankings WHERE player_id = ?",
                (player_id,)
            )
            result = await cursor.fetchone()
            await cursor.close()
            
            rank_history = []
            if result:
                try:
                    rank_history = json.loads(result[1] or '[]')
                except:
                    rank_history = []
                
                # Add to history if rank changed
                if result[0] != rank.value:
                    rank_history.append({
                        'from_rank': result[0],
                        'to_rank': rank.value,
                        'timestamp': current_time
                    })
            
            await db.execute("""
                INSERT OR REPLACE INTO hunter_rankings 
                (player_id, current_rank, rank_points, last_evaluation, rank_history, total_evaluations)
                VALUES (?, ?, ?, ?, ?, COALESCE((SELECT total_evaluations FROM hunter_rankings WHERE player_id = ?), 0) + 1)
            """, (player_id, rank.value, points, current_time, json.dumps(rank_history), player_id))
            await db.commit()
    
    @classmethod
    async def evaluate_player_rank(cls, player_id: str, player_level: int, total_stats: int, achievement_count: int) -> Tuple[HunterRank, bool]:
        """Evaluate if player qualifies for rank up"""
        current_rank, _ = await cls.get_player_rank(player_id)
        
        # Check each rank from highest to lowest
        for rank in reversed(list(HunterRank)):
            requirements = cls.RANK_REQUIREMENTS[rank]
            
            if (player_level >= requirements["level"] and
                total_stats >= requirements["total_stats"]):
                
                # If this is higher than current rank, promote
                if cls._rank_value(rank) > cls._rank_value(current_rank):
                    await cls.set_player_rank(player_id, rank)
                    return rank, True  # Rank up occurred
                else:
                    return current_rank, False  # No change
        
        return current_rank, False
    
    @classmethod
    def _rank_value(cls, rank: HunterRank) -> int:
        """Get numeric value for rank comparison"""
        rank_values = {
            HunterRank.E: 1,
            HunterRank.D: 2,
            HunterRank.C: 3,
            HunterRank.B: 4,
            HunterRank.A: 5,
            HunterRank.S: 6,
            HunterRank.NATIONAL: 7
        }
        return rank_values.get(rank, 1)
    
    @classmethod
    def get_rank_info(cls, rank: HunterRank) -> Dict:
        """Get detailed information about a rank"""
        return cls.RANK_BENEFITS.get(rank, cls.RANK_BENEFITS[HunterRank.E])
    
    @classmethod
    def get_next_rank_requirements(cls, current_rank: HunterRank) -> Optional[Dict]:
        """Get requirements for the next rank"""
        current_value = cls._rank_value(current_rank)
        
        for rank in HunterRank:
            if cls._rank_value(rank) == current_value + 1:
                return {
                    'rank': rank,
                    'requirements': cls.RANK_REQUIREMENTS[rank],
                    'benefits': cls.RANK_BENEFITS[rank]
                }
        
        return None  # Already at max rank
    
    @classmethod
    async def get_rank_leaderboard(cls, limit: int = 10) -> List[Dict]:
        """Get top players by rank"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("""
                SELECT player_id, current_rank, rank_points, total_evaluations
                FROM hunter_rankings
                ORDER BY 
                    CASE current_rank
                        WHEN 'National' THEN 7
                        WHEN 'S' THEN 6
                        WHEN 'A' THEN 5
                        WHEN 'B' THEN 4
                        WHEN 'C' THEN 3
                        WHEN 'D' THEN 2
                        WHEN 'E' THEN 1
                        ELSE 0
                    END DESC,
                    rank_points DESC
                LIMIT ?
            """, (limit,))
            
            results = await cursor.fetchall()
            await cursor.close()
            
            leaderboard = []
            for result in results:
                player_id, rank_str, points, evaluations = result
                leaderboard.append({
                    'player_id': player_id,
                    'rank': rank_str,
                    'points': points,
                    'evaluations': evaluations
                })
            
            return leaderboard
    
    @classmethod
    def get_rank_color(cls, rank: HunterRank) -> int:
        """Get Discord color for rank"""
        colors = {
            HunterRank.E: 0x808080,      # Gray
            HunterRank.D: 0x00FF00,      # Green
            HunterRank.C: 0x0080FF,      # Blue
            HunterRank.B: 0x8000FF,      # Purple
            HunterRank.A: 0xFF0000,      # Red
            HunterRank.S: 0xFFD700,      # Gold
            HunterRank.NATIONAL: 0xFF6B35  # Orange-Red
        }
        return colors.get(rank, 0x808080)
    
    @classmethod
    def get_rank_emoji(cls, rank: HunterRank) -> str:
        """Get emoji for rank"""
        emojis = {
            HunterRank.E: "🔰",
            HunterRank.D: "🟢",
            HunterRank.C: "🔵",
            HunterRank.B: "🟣",
            HunterRank.A: "🔴",
            HunterRank.S: "⭐",
            HunterRank.NATIONAL: "👑"
        }
        return emojis.get(rank, "🔰")

    @staticmethod
    async def calculate_rank(player_id: str):
        """Calculate what rank a player should have based on their stats"""
        return await RankingSystem._calculate_rank_internal(player_id)

    @staticmethod
    async def _calculate_rank_internal(player_id: str):
        """Internal method to calculate rank without recursion"""
        try:
            from structure.player import Player

            # Get player data
            player = await Player.get(int(player_id))
            if not player:
                return HunterRank.E, False

            # Calculate total stats (using correct Player attributes)
            total_stats = (
                player.attack + player.defense + player.precision +
                player.hp + player.mp
            )

            # Get current rank directly from database to avoid recursion
            current_rank = HunterRank.E  # Default
            try:
                async with aiosqlite.connect(DATABASE_PATH) as db:
                    cursor = await db.execute(
                        "SELECT current_rank FROM hunter_rankings WHERE player_id = ?",
                        (player_id,)
                    )
                    result = await cursor.fetchone()
                    if result:
                        current_rank = HunterRank(result[0])
                    await cursor.close()
            except Exception:
                current_rank = HunterRank.E

            # Determine appropriate rank (start with E rank)
            new_rank = HunterRank.E

            # Check rank requirements in descending order
            for rank in [HunterRank.NATIONAL, HunterRank.S, HunterRank.A,
                        HunterRank.B, HunterRank.C, HunterRank.D, HunterRank.E]:
                requirements = RankingSystem.RANK_REQUIREMENTS[rank]
                if (player.level >= requirements["level"] and
                    total_stats >= requirements["total_stats"]):
                    new_rank = rank
                    break

            # Check if rank changed
            rank_changed = current_rank != new_rank

            # Update rank if changed
            if rank_changed:
                await RankingSystem.set_player_rank(player_id, new_rank, 0)

            return new_rank, rank_changed

        except Exception as e:
            logging.error(f"Error calculating rank for player {player_id}: {e}")
            return HunterRank.E, False

    @staticmethod
    async def set_player_rank(player_id: str, rank: HunterRank, progress: int = 0):
        """Set a player's rank directly"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                # Ensure tables exist before trying to insert
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS player_ranks (
                        player_id TEXT PRIMARY KEY,
                        current_rank TEXT NOT NULL DEFAULT 'E',
                        progress INTEGER DEFAULT 0,
                        last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await db.execute("""
                    INSERT OR REPLACE INTO player_ranks
                    (player_id, current_rank, progress, last_updated)
                    VALUES (?, ?, ?, datetime('now'))
                """, (player_id, rank.value, progress))
                await db.commit()

                logging.info(f"Set player {player_id} rank to {rank.value}")
                return True

        except Exception as e:
            logging.error(f"Error setting player rank: {e}")
            return False
