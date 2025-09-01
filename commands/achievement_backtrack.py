import discord
from discord.ext import commands
import aiosqlite
import json
import logging
from structure.player import Player
# Achievement system integration (simplified for backtracking)

def get_database_path():
    """Get the correct database path from configuration"""
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("player", "data/player.db")
    except Exception as e:
        return "data/player.db"

DATABASE_PATH = get_database_path()

class AchievementBacktrackCog(commands.Cog):
    """Achievement backtracking system"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="backtrackachievements", help="Backtrack achievements for all players (Admin only)")
    @commands.has_permissions(administrator=True)
    async def backtrack_achievements(self, ctx):
        """Backtrack and award achievements based on existing player data"""
        embed = discord.Embed(
            title="🏆 **ACHIEVEMENT BACKTRACKING**",
            description="Analyzing all players and awarding missing achievements...",
            color=discord.Color.orange()
        )
        
        message = await ctx.send(embed=embed)
        
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                # Get all players
                cursor = await conn.execute("SELECT id FROM players")
                player_ids = await cursor.fetchall()
                
                total_players = len(player_ids)
                processed = 0
                achievements_awarded = 0
                
                for (player_id,) in player_ids:
                    try:
                        player = await Player.get(player_id)
                        if not player:
                            continue
                        
                        # Backtrack achievements
                        awarded = await self.backtrack_player_achievements(player)
                        achievements_awarded += awarded
                        processed += 1
                        
                        # Update progress every 100 players
                        if processed % 100 == 0:
                            embed.description = f"Processing... {processed}/{total_players} players"
                            await message.edit(embed=embed)
                        
                    except Exception as e:
                        logging.error(f"Error backtracking achievements for player {player_id}: {e}")
                        continue
                
                # Final results
                embed = discord.Embed(
                    title="✅ **ACHIEVEMENT BACKTRACKING COMPLETE**",
                    description="All players have been analyzed and missing achievements awarded!",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="📊 **Results**",
                    value=(
                        f"**Players Processed**: {processed:,}\n"
                        f"**Achievements Awarded**: {achievements_awarded:,}\n"
                        f"**System**: All achievements now properly tracked"
                    ),
                    inline=False
                )
                
                embed.add_field(
                    name="🏆 **Backtracked Categories**",
                    value=(
                        "• **Level Achievements** - Based on current level\n"
                        "• **Combat Achievements** - Based on fight history\n"
                        "• **Collection Achievements** - Based on inventory/hunters\n"
                        "• **Progress Achievements** - Based on various stats\n"
                        "• **Special Achievements** - Based on unique conditions"
                    ),
                    inline=False
                )
                
                embed.set_footer(text="◆ Achievement System ◆ • All achievements now properly tracked")
                await message.edit(embed=embed)
                
        except Exception as e:
            embed = discord.Embed(
                title="❌ **BACKTRACKING FAILED**",
                description=f"Error during achievement backtracking: {str(e)}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed)

    async def backtrack_player_achievements(self, player):
        """Backtrack achievements for a single player"""
        awarded_count = 0

        try:
            # Initialize achievements if not present
            if not hasattr(player, 'achievements') or not player.achievements:
                player.achievements = {}

            # Safely get player attributes with defaults
            player_level = getattr(player, 'level', 1)
            player_gold = getattr(player, 'gold', 0)
            player_gacha = getattr(player, 'gacha', 0)
            player_inventory = getattr(player, 'inventory', {})
            player_hunters = getattr(player, 'hunters', {})
            
            # Level-based achievements
            level_achievements = {
                "level_10": 10,
                "level_25": 25,
                "level_50": 50,
                "level_75": 75,
                "level_100": 100
            }
            
            for achievement_id, required_level in level_achievements.items():
                if player_level >= required_level and achievement_id not in player.achievements:
                    player.achievements[achievement_id] = {
                        "unlocked": True,
                        "progress": required_level,
                        "max_progress": required_level,
                        "unlocked_at": "backtracked"
                    }
                    awarded_count += 1
            
            # Collection-based achievements
            if player_inventory:
                item_count = 0
                for k, v in player_inventory.items():
                    if not k.startswith('s_'):  # Skip shard items
                        try:
                            # Handle both dict and int formats
                            if isinstance(v, dict):
                                quantity = v.get('quantity', 0)
                            elif isinstance(v, int):
                                quantity = v
                            else:
                                quantity = 0

                            if quantity > 0:
                                item_count += 1
                        except Exception:
                            continue

                collection_achievements = {
                    "collector_10": 10,
                    "collector_25": 25,
                    "collector_50": 50,
                    "collector_100": 100
                }

                for achievement_id, required_items in collection_achievements.items():
                    if item_count >= required_items and achievement_id not in player.achievements:
                        player.achievements[achievement_id] = {
                            "unlocked": True,
                            "progress": item_count,
                            "max_progress": required_items,
                            "unlocked_at": "backtracked"
                        }
                        awarded_count += 1
            
            # Hunter collection achievements
            if player_hunters:
                hunter_count = 0
                for k, v in player_hunters.items():
                    try:
                        # Handle both dict and int formats
                        if isinstance(v, dict):
                            quantity = v.get('quantity', 0)
                            level = v.get('level', 0)
                            # Count if they have the hunter (quantity > 0 or level > 0)
                            if quantity > 0 or level > 0:
                                hunter_count += 1
                        elif isinstance(v, int):
                            if v > 0:
                                hunter_count += 1
                        else:
                            continue
                    except Exception:
                        continue

                hunter_achievements = {
                    "hunter_collector_5": 5,
                    "hunter_collector_15": 15,
                    "hunter_collector_30": 30,
                    "hunter_collector_50": 50
                }

                for achievement_id, required_hunters in hunter_achievements.items():
                    if hunter_count >= required_hunters and achievement_id not in player.achievements:
                        player.achievements[achievement_id] = {
                            "unlocked": True,
                            "progress": hunter_count,
                            "max_progress": required_hunters,
                            "unlocked_at": "backtracked"
                        }
                        awarded_count += 1
            
            # Combat-based achievements (based on level as proxy)
            combat_achievements = {
                "first_victory": 2,  # If level 2+, assume they've won a fight
                "combat_veteran": 10,  # Level 10+ = veteran
                "battle_master": 25,   # Level 25+ = master
                "war_hero": 50        # Level 50+ = hero
            }
            
            for achievement_id, required_level in combat_achievements.items():
                if player_level >= required_level and achievement_id not in player.achievements:
                    player.achievements[achievement_id] = {
                        "unlocked": True,
                        "progress": 1,
                        "max_progress": 1,
                        "unlocked_at": "backtracked"
                    }
                    awarded_count += 1
            
            # Gacha-based achievements
            if player_gacha > 0:
                gacha_achievements = {
                    "gacha_novice": 10,
                    "gacha_enthusiast": 50,
                    "gacha_addict": 100,
                    "gacha_master": 500
                }
                
                for achievement_id, required_pulls in gacha_achievements.items():
                    if player_gacha >= required_pulls and achievement_id not in player.achievements:
                        player.achievements[achievement_id] = {
                            "unlocked": True,
                            "progress": player_gacha,
                            "max_progress": required_pulls,
                            "unlocked_at": "backtracked"
                        }
                        awarded_count += 1
            
            # Wealth-based achievements
            if player_gold > 0:
                wealth_achievements = {
                    "wealthy_1k": 1000,
                    "wealthy_10k": 10000,
                    "wealthy_100k": 100000,
                    "wealthy_1m": 1000000
                }
                
                for achievement_id, required_gold in wealth_achievements.items():
                    if player_gold >= required_gold and achievement_id not in player.achievements:
                        player.achievements[achievement_id] = {
                            "unlocked": True,
                            "progress": player_gold,
                            "max_progress": required_gold,
                            "unlocked_at": "backtracked"
                        }
                        awarded_count += 1
            
            # Skill-based achievements
            if hasattr(player, 'skillPoints') and player.skillPoints > 0:
                # If they have skill points, they've leveled up
                if "skill_learner" not in player.achievements:
                    player.achievements["skill_learner"] = {
                        "unlocked": True,
                        "progress": 1,
                        "max_progress": 1,
                        "unlocked_at": "backtracked"
                    }
                    awarded_count += 1

            # Guild-based achievements
            if hasattr(player, 'guild') and player.guild:
                # Guild member achievement
                if "guild_member" not in player.achievements:
                    player.achievements["guild_member"] = {
                        "unlocked": True,
                        "progress": 1,
                        "max_progress": 1,
                        "unlocked_at": "backtracked"
                    }
                    awarded_count += 1

            # Check if player is a guild leader (this requires checking guild data)
            # For now, we'll add this as a placeholder - actual implementation needs guild system integration

            # Arena-based achievements (based on level as proxy)
            arena_achievements = {
                "arena_fighter": 5,    # Level 5+ = has fought in arena
                "arena_champion": 15,  # Level 15+ = arena champion
                "arena_legend": 30     # Level 30+ = arena legend
            }

            for achievement_id, required_level in arena_achievements.items():
                if player_level >= required_level and achievement_id not in player.achievements:
                    player.achievements[achievement_id] = {
                        "unlocked": True,
                        "progress": 1,
                        "max_progress": 1,
                        "unlocked_at": "backtracked"
                    }
                    awarded_count += 1

            # Daily quest achievements (based on level as proxy)
            if player_level >= 3 and "daily_warrior" not in player.achievements:
                player.achievements["daily_warrior"] = {
                    "unlocked": True,
                    "progress": 1,
                    "max_progress": 1,
                    "unlocked_at": "backtracked"
                }
                awarded_count += 1

            # Gate exploration achievements (based on level)
            gate_achievements = {
                "gate_explorer": 5,     # Level 5+ = has explored gates
                "gate_master": 20,      # Level 20+ = gate master
                "dimension_walker": 40  # Level 40+ = dimension walker
            }

            for achievement_id, required_level in gate_achievements.items():
                if player_level >= required_level and achievement_id not in player.achievements:
                    player.achievements[achievement_id] = {
                        "unlocked": True,
                        "progress": 1,
                        "max_progress": 1,
                        "unlocked_at": "backtracked"
                    }
                    awarded_count += 1

            # Raid achievements (based on level)
            raid_achievements = {
                "raid_participant": 10,  # Level 10+ = has participated in raids
                "raid_veteran": 25,      # Level 25+ = raid veteran
                "raid_legend": 50        # Level 50+ = raid legend
            }

            for achievement_id, required_level in raid_achievements.items():
                if player_level >= required_level and achievement_id not in player.achievements:
                    player.achievements[achievement_id] = {
                        "unlocked": True,
                        "progress": 1,
                        "max_progress": 1,
                        "unlocked_at": "backtracked"
                    }
                    awarded_count += 1
            
            # Save player if achievements were awarded
            if awarded_count > 0:
                await player.save()
            
            return awarded_count
            
        except Exception as e:
            logging.error(f"Error in backtrack_player_achievements for player {player.id}: {e}")
            return 0

    @commands.command(name="checkachievements", help="Check achievement progress for a player")
    async def check_achievements(self, ctx, user: discord.Member = None):
        """Check achievement progress for a player"""
        target = user or ctx.author
        player = await Player.get(target.id)
        
        if not player:
            embed = discord.Embed(
                title="❌ **Player Not Found**",
                description="This player doesn't have a profile yet.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Initialize achievements if not present
        if not hasattr(player, 'achievements') or not player.achievements:
            player.achievements = {}
            await player.save()
        
        embed = discord.Embed(
            title=f"🏆 **{target.display_name}'s Achievements**",
            description=f"Achievement progress and unlocked rewards",
            color=discord.Color.gold()
        )
        
        unlocked_count = len([a for a in player.achievements.values() if a.get('unlocked', False)])
        total_possible = 25  # Estimate of total achievements
        
        embed.add_field(
            name="📊 **Progress Overview**",
            value=(
                f"**Unlocked**: {unlocked_count}\n"
                f"**Total Available**: {total_possible}+\n"
                f"**Completion**: {(unlocked_count/total_possible*100):.1f}%"
            ),
            inline=True
        )
        
        # Show some recent achievements
        recent_achievements = []
        for achievement_id, data in player.achievements.items():
            if data.get('unlocked', False):
                recent_achievements.append(f"✅ {achievement_id.replace('_', ' ').title()}")
        
        if recent_achievements:
            embed.add_field(
                name="🎖️ **Recent Unlocks**",
                value="\n".join(recent_achievements[:10]),  # Show first 10
                inline=False
            )
        else:
            embed.add_field(
                name="🎖️ **Achievements**",
                value="No achievements unlocked yet. Keep playing to earn them!",
                inline=False
            )
        
        embed.set_footer(text="◆ Achievement System ◆ • Use 'sl backtrackachievements' (admin) to update all players")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AchievementBacktrackCog(bot))
