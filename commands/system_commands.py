import discord
from discord.ext import commands
import asyncio
from typing import Optional
import json

from structure.system_interface import SystemInterface
from structure.ranking_system import RankingSystem, HunterRank
from structure.achievement_system import AchievementSystem, AchievementCategory, AchievementRarity
from structure.skill_tree_system import SkillTreeSystem, SkillTreeType
from structure.skills import SkillType, Element
from structure.player import Player
from structure.emoji import getEmoji
from utilis.interaction_handler import InteractionHandler

class SystemInterfaceView(discord.ui.View):
    """Interactive System Interface with buttons"""

    def __init__(self, bot, user_id):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
        self.current_tree = None  # Track currently selected skill tree

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the original user to interact"""
        return interaction.user.id == self.user_id

    async def create_main_embed(self):
        """Create the main system interface embed"""
        player = await Player.get(self.user_id)
        if not player:
            return None

        # Get player data - use the same ranking system as evaluate
        try:
            from structure.Rank import RankingLeaderboard
            leaderboard = RankingLeaderboard()
            rank_data = await leaderboard.get(self.user_id)

            if rank_data:
                # rank_data is a tuple: (id, rank, rank_, power)
                rank_string = rank_data[1]  # e.g., "C-Rank"
                rank_position = rank_data[2]  # position number

                # Convert to HunterRank enum for display
                if "E-Rank" in rank_string:
                    rank = HunterRank.E
                elif "D-Rank" in rank_string:
                    rank = HunterRank.D
                elif "C-Rank" in rank_string:
                    rank = HunterRank.C
                elif "B-Rank" in rank_string:
                    rank = HunterRank.B
                elif "A-Rank" in rank_string:
                    rank = HunterRank.A
                elif "S-Rank" in rank_string:
                    rank = HunterRank.S
                else:
                    rank = HunterRank.E

                rank_points = rank_position
            else:
                rank = HunterRank.E
                rank_points = 0
        except Exception as e:
            print(f"Error getting player rank: {e}")
            rank = HunterRank.E  # Default to E rank
            rank_points = 0

        try:
            achievements = await AchievementSystem.get_player_achievements(str(self.user_id))
        except Exception as e:
            print(f"Error getting achievements: {e}")
            achievements = {'total_unlocked': 0, 'total_available': 0, 'unlocked': {}}

        embed = SystemInterface.create_system_embed(
            "HUNTER INTERFACE",
            f"Welcome, **<@{self.user_id}>**\n*The System recognizes your presence.*"
        )

        # Hunter Status
        embed.add_field(
            name="👤 **Hunter Status**",
            value=(
                f"**Level**: {player.level}\n"
                f"**Rank**: {RankingSystem.get_rank_emoji(rank)} {rank.value}-Rank Hunter\n"
                f"**XP**: {player.xp:,}\n"
                f"**Gold**: {player.gold:,}"
            ),
            inline=True
        )

        # System Stats
        embed.add_field(
            name="📊 **System Data**",
            value=(
                f"**Achievements**: {achievements['total_unlocked']}/{achievements['total_available']}\n"
                f"**Shadows**: {len(player.get_shadows())}\n"
                f"**Items**: {len(player.get_inventory())}\n"
                f"**Guild**: {player.guild or 'None'}"
            ),
            inline=True
        )

        # Stats Overview
        total_stats = player.attack + player.defense + player.hp + player.mp
        embed.add_field(
            name="⚔️ **Combat Stats**",
            value=(
                f"**Attack**: {player.attack}\n"
                f"**Defense**: {player.defense}\n"
                f"**HP**: {player.hp}\n"
                f"**MP**: {player.mp}\n"
                f"**Total**: {total_stats:,}"
            ),
            inline=False
        )

        # Set thumbnail if bot is available
        if self.bot and self.bot.get_user(self.user_id):
            user = self.bot.get_user(self.user_id)
            if user and user.avatar:
                embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{self.user_id}/{user.avatar}.png")
        return embed

    @discord.ui.button(label="🏆 Hunter Rank", style=discord.ButtonStyle.primary, row=0)
    async def rank_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show hunter rank information"""
        try:
            embed = await self.create_rank_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.InteractionResponse:
            # Interaction already responded, try followup
            embed = await self.create_rank_embed()
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)
        except Exception as e:
            print(f"Error in rank button: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ **Error loading rank information.**", ephemeral=True)
            else:
                await interaction.followup.send("❌ **Error loading rank information.**", ephemeral=True)

    @discord.ui.button(label="🏅 Achievements", style=discord.ButtonStyle.primary, row=0)
    async def achievements_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show achievements overview with interactive UI"""
        try:
            view = AchievementView(self.bot, self.user_id)
            embed = await view.create_overview_embed()
            await interaction.response.edit_message(embed=embed, view=view)
        except discord.InteractionResponse:
            # Interaction already responded, try followup
            view = AchievementView(self.bot, self.user_id)
            embed = await view.create_overview_embed()
            await interaction.followup.edit_message(interaction.message.id, embed=embed, view=view)
        except Exception as e:
            print(f"Error in achievements button: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ **Error loading achievements.**", ephemeral=True)
            else:
                await interaction.followup.send("❌ **Error loading achievements.**", ephemeral=True)

    @discord.ui.button(label="🌟 Skill Trees", style=discord.ButtonStyle.primary, row=0)
    async def skilltree_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show skill trees selection"""
        embed = await self.create_skilltree_embed()
        # Create SkillTreeView for tree selection
        view = SkillTreeView(self.bot, self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="📊 Daily Quests", style=discord.ButtonStyle.secondary, row=1)
    async def daily_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show daily quests"""
        try:
            embed = await self.create_daily_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            print(f"Error in daily button: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ **Error loading daily quests.**", ephemeral=True)
            else:
                await interaction.followup.send("❌ **Error loading daily quests.**", ephemeral=True)

    @discord.ui.button(label="� Commands", style=discord.ButtonStyle.secondary, row=1)
    async def commands_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show system commands list"""
        try:
            embed = await self.create_commands_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            print(f"Error in commands button: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ **Error loading commands.**", ephemeral=True)
            else:
                await interaction.followup.send("❌ **Error loading commands.**", ephemeral=True)



    @discord.ui.button(label="🎓 Learn Skills", style=discord.ButtonStyle.success, row=1)
    async def learn_skills_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Quick access to skill learning"""
        try:
            # Show skill tree selection for learning
            embed = await self.create_skilltree_embed()
            view = SkillTreeView(self.bot, self.user_id)
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            print(f"Error in learn skills button: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ **Error loading skill trees.**", ephemeral=True)
            else:
                await interaction.followup.send("❌ **Error loading skill trees.**", ephemeral=True)

    @discord.ui.button(label="�🔙 Main Menu", style=discord.ButtonStyle.secondary, row=1)
    async def main_menu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to main system interface"""
        try:
            embed = await self.create_main_embed()
            if embed:
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ **Error loading System interface.**", ephemeral=True)
                else:
                    await interaction.followup.send("❌ **Error loading System interface.**", ephemeral=True)
        except Exception as e:
            print(f"Error in main menu button: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ **Error loading System interface.**", ephemeral=True)
            else:
                await interaction.followup.send("❌ **Error loading System interface.**", ephemeral=True)

    async def create_rank_embed(self):
        """Create hunter rank embed - using same system as evaluate command"""
        player = await Player.get(self.user_id)
        if not player:
            return None

        # Get rank data from the same system as evaluate
        try:
            from structure.Rank import RankingLeaderboard
            leaderboard = RankingLeaderboard()
            rank_data = await leaderboard.get(self.user_id)

            if rank_data:
                # rank_data is a tuple: (id, rank, rank_, power)
                rank_string = rank_data[1]  # e.g., "C-Rank"
                rank_position = rank_data[2]  # position number
                power_level = rank_data[3]  # power level

                # Convert to HunterRank enum for display
                if "E-Rank" in rank_string:
                    rank = HunterRank.E
                elif "D-Rank" in rank_string:
                    rank = HunterRank.D
                elif "C-Rank" in rank_string:
                    rank = HunterRank.C
                elif "B-Rank" in rank_string:
                    rank = HunterRank.B
                elif "A-Rank" in rank_string:
                    rank = HunterRank.A
                elif "S-Rank" in rank_string:
                    rank = HunterRank.S
                else:
                    rank = HunterRank.E
                    rank_position = 999
                    power_level = 0
            else:
                # Player not in leaderboard yet - add them
                from commands.evaluate import RankEvaluation
                eval_cog = RankEvaluation(self.bot)

                # Calculate power level same as evaluate command
                base_stats = {"Total Power": (player.hp / 5) + player.attack + player.defense + player.precision + player.mp}
                from structure.stats import getStat
                stats = getStat(["Total Power"], level=player.level, base_stats=base_stats)

                # Calculate party power
                from commands.party import getPartyTotalPower
                party_power = await getPartyTotalPower(player)

                # Calculate weapon power
                weapon_power = 0
                for slot in ["Weapon", "Weapon_2"]:
                    if item_id := player.equipped.get(slot):
                        if item_id in player.inventory:
                            item_data = player.inventory[item_id]
                            weapon_level = item_data.get('level', 1) if isinstance(item_data, dict) else 1
                            from utilis.utilis import getStatWeapon
                            weapon_stat = await getStatWeapon(item_id, weapon_level)
                            if weapon_stat:
                                weapon_power += weapon_stat.get("total_power", 0)

                power_level = int(stats.Total_Power + party_power + weapon_power)

                # Add to leaderboard
                await leaderboard.add_player(self.user_id, power_level)

                # Get updated rank data
                rank_data = await leaderboard.get(self.user_id)
                if rank_data:
                    rank_string = rank_data[1]
                    rank_position = rank_data[2]
                    power_level = rank_data[3]

                    # Convert to HunterRank enum
                    if "E-Rank" in rank_string:
                        rank = HunterRank.E
                    elif "D-Rank" in rank_string:
                        rank = HunterRank.D
                    elif "C-Rank" in rank_string:
                        rank = HunterRank.C
                    elif "B-Rank" in rank_string:
                        rank = HunterRank.B
                    elif "A-Rank" in rank_string:
                        rank = HunterRank.A
                    elif "S-Rank" in rank_string:
                        rank = HunterRank.S
                    else:
                        rank = HunterRank.E
                else:
                    rank = HunterRank.E
                    rank_position = 999
                    power_level = 0

        except Exception as e:
            print(f"Error getting rank data: {e}")
            rank = HunterRank.E
            rank_position = 999
            power_level = 0
            rank_string = "E-Rank"

        rank_info = RankingSystem.get_rank_info(rank)
        next_rank_info = RankingSystem.get_next_rank_requirements(rank)

        # Create rank embed
        embed = discord.Embed(
            title=f"📱 **[HUNTER RANK ASSESSMENT]**",
            description=f"**<@{self.user_id}>**",
            color=RankingSystem.get_rank_color(rank)
        )

        # Current Rank - show same info as evaluate command
        embed.add_field(
            name=f"{RankingSystem.get_rank_emoji(rank)} **Current Rank**",
            value=f"**{rank_string}** - Position #{rank_position}\n*Power Level: {power_level:,}*\n*{rank_info['description']}*",
            inline=False
        )

        # Rank Benefits
        embed.add_field(
            name="🎁 **Rank Benefits**",
            value=(
                f"**Max Party Size**: {rank_info['max_party_size']}\n"
                f"**Daily Quests**: {rank_info['daily_quests']}\n"
                f"**Stat Bonus**: +{rank_info['stat_bonus']}\n"
                f"**Dungeon Access**: {len(rank_info['dungeon_access'])} types"
            ),
            inline=True
        )

        # Progress to Next Rank
        if next_rank_info:
            next_req = next_rank_info['requirements']
            # Use consistent attribute names (hp/mp are the correct ones)
            total_stats = player.attack + player.defense + player.hp + player.mp
            achievements = await AchievementSystem.get_player_achievements(str(self.user_id))

            progress_text = (
                f"**Level**: {player.level}/{next_req['level']} "
                f"{'✅' if player.level >= next_req['level'] else '❌'}\n"
                f"**Total Stats**: {total_stats:,}/{next_req['total_stats']:,} "
                f"{'✅' if total_stats >= next_req['total_stats'] else '❌'}"
            )

            embed.add_field(
                name=f"⬆️ **Next Rank: {next_rank_info['rank'].value}**",
                value=progress_text,
                inline=True
            )
        else:
            embed.add_field(
                name="👑 **Maximum Rank**",
                value="*You have reached the pinnacle of hunter rankings.*",
                inline=True
            )

        embed.set_footer(text="◆ The System ◆ • Rankings are evaluated automatically")
        return embed

    async def create_achievements_embed(self):
        """Create achievements overview embed"""
        achievements = await AchievementSystem.get_player_achievements(str(self.user_id))

        embed = discord.Embed(
            title=f"📱 **[ACHIEVEMENT SYSTEM]**",
            description=f"**<@{self.user_id}>'s Achievements**",
            color=discord.Color.gold()
        )

        # Progress Overview
        completion_rate = (achievements['total_unlocked']/achievements['total_available']*100) if achievements['total_available'] > 0 else 0
        embed.add_field(
            name="📊 **Progress Overview**",
            value=(
                f"**Unlocked**: {achievements['total_unlocked']}/{achievements['total_available']}\n"
                f"**Completion**: {completion_rate:.1f}%"
            ),
            inline=False
        )

        # Recent Achievements
        recent = list(achievements['unlocked'].values())[:5]
        if recent:
            recent_text = ""
            for ach_data in recent:
                achievement = ach_data['achievement']
                rarity_emoji = "🔸" if achievement.rarity.value == "Common" else "🔹" if achievement.rarity.value == "Rare" else "🔷" if achievement.rarity.value == "Epic" else "💎" if achievement.rarity.value == "Legendary" else "⭐"
                recent_text += f"{rarity_emoji} **{achievement.name}**\n"

            embed.add_field(
                name="🆕 **Recent Achievements**",
                value=recent_text,
                inline=False
            )

        # Categories with counts
        categories_text = ""
        for category in AchievementCategory:
            category_achievements = AchievementSystem.get_achievements_by_category(category)
            unlocked_in_category = sum(1 for ach in category_achievements if ach.id in achievements['unlocked'])
            categories_text += f"**{category.value}**: {unlocked_in_category}/{len(category_achievements)}\n"

        embed.add_field(
            name="📂 **Categories**",
            value=categories_text,
            inline=False
        )

        embed.set_footer(text="◆ The System ◆ • Use buttons to explore categories")
        return embed

    async def create_skilltree_embed(self):
        """Create skill trees overview embed"""
        player = await Player.get(self.user_id)
        if not player:
            return None

        embed = discord.Embed(
            title=f"📱 **[SKILL TREE SYSTEM]**",
            description=f"**<@{self.user_id}>'s Skill Trees**",
            color=discord.Color.purple()
        )

        # Available Skill Points
        embed.add_field(
            name="⭐ **Skill Points**",
            value=(
                f"**Available**: {player.skillPoints}\n"
                f"**Current Level**: {player.level}\n"
                f"*Skill points are earned by leveling up*"
            ),
            inline=False
        )

        # Skill Tree Overview
        trees_text = ""
        for tree_type in SkillTreeType:
            tree_data = await SkillTreeSystem.get_player_skill_tree(str(self.user_id), tree_type)
            skill_tree = tree_data['tree']
            if skill_tree:
                unlocked_count = len(tree_data['unlocked_skills'])
                total_count = len(skill_tree.nodes)
                trees_text += f"**{tree_type.value}**: {unlocked_count}/{total_count} skills\n"

        embed.add_field(
            name="🌳 **Skill Tree Progress**",
            value=trees_text,
            inline=False
        )

        # Available Trees
        embed.add_field(
            name="🎯 **Available Paths**",
            value=(
                "🌑 **Shadow Monarch** - Command darkness and undead\n"
                "⚔️ **Warrior** - Master weapons and physical combat\n"
                "🔮 **Mage** - Harness elemental forces and magic\n"
                "🗡️ **Assassin** - Strike from shadows with precision\n"
                "🛡️ **Tank** - Protect allies and endure assaults\n"
                "💚 **Support** - Heal and aid allies in battle"
            ),
            inline=False
        )

        embed.set_footer(text="◆ The System ◆ • Choose your path wisely")
        return embed

    async def create_daily_embed(self):
        """Create daily quests embed"""
        player = await Player.get(self.user_id)
        if not player:
            return None

        embed = discord.Embed(
            title=f"📱 **[DAILY QUEST SYSTEM]**",
            description=f"**<@{self.user_id}>'s Daily Training**",
            color=discord.Color.blue()
        )

        # Daily Quest Status
        quests = player.quests
        if quests:
            quest_text = ""
            for quest_name, quest_data in quests.items():
                if isinstance(quest_data, dict):
                    current = quest_data.get('current', 0)
                    required = quest_data.get('required', 1)
                    completed = quest_data.get('completed', False)
                    status = "✅" if completed else "🔄"
                    quest_text += f"{status} **{quest_name.title()}**: {current}/{required}\n"

            if quest_text:
                embed.add_field(
                    name="📋 **Today's Quests**",
                    value=quest_text,
                    inline=False
                )
        else:
            embed.add_field(
                name="📋 **Today's Quests**",
                value="*No active daily quests. Use `sl train` to start training!*",
                inline=False
            )

        # Training Options
        embed.add_field(
            name="🏋️ **Training Options**",
            value=(
                "**Push-ups** - Build physical strength\n"
                "**Running** - Increase endurance\n"
                "**Sit-ups** - Core strengthening\n"
                "**Squats** - Leg power training\n"
                "*Complete daily training to grow stronger!*"
            ),
            inline=False
        )

        embed.set_footer(text="◆ The System ◆ • Daily training makes you stronger")
        return embed

    async def create_commands_embed(self):
        """Create system commands list embed"""
        embed = discord.Embed(
            title=f"📱 **[SYSTEM COMMAND LIST]**",
            description=f"**<@{self.user_id}>'s Available Commands**",
            color=discord.Color.blue()
        )

        # Core System Commands
        embed.add_field(
            name="🎮 **Core System Commands**",
            value=(
                "`sl system` - Interactive System interface\n"
                "`sl profile` - View your hunter profile\n"
                "`sl start` - Begin your hunter journey\n"
                "`sl stats` - Allocate stat points\n"
                "`sl inventory` - Manage your items\n"
                "`sl daily` - Daily training quests\n"
                "`sl cooldowns` - Check command cooldowns"
            ),
            inline=False
        )

        # Progression Commands
        embed.add_field(
            name="📈 **Progression Commands**",
            value=(
                "`sl story` - Interactive Solo Leveling story campaign\n"
                "`sl rank [user]` - View hunter rankings\n"
                "`sl achievements [category]` - Browse achievements\n"
                "`sl skilltree [tree]` - Access skill trees\n"
                "`sl leaderboard` - View player rankings\n"
                "`sl missions` - Track mission progress\n"
                "`sl train` - Physical training system\n"
                "`sl upgrade` - Upgrade weapons and items"
            ),
            inline=False
        )

        # Combat Commands
        embed.add_field(
            name="⚔️ **Combat Commands**",
            value=(
                "`sl fight` - Challenge other hunters\n"
                "`sl arena` - Enter the arena\n"
                "`sl gates` - Explore dimensional gates\n"
                "`sl dungeons` - Enter dungeon battles\n"
                "`sl raids` - Join raid battles\n"
                "`sl shadows` - Manage shadow army\n"
                "`sl arise <shadow>` - Summon shadows\n"
                "`sl equip` - Equip weapons and items"
            ),
            inline=False
        )

        # Utility Commands
        embed.add_field(
            name="🔧 **Utility Commands**",
            value=(
                "`sl fixuser` - Comprehensive account repair\n"
                "`sl unstuck` - Quick fix for stuck status\n"
                "`sl fix` - Admin-only player repair\n"
                "`sl help` - View help information\n"
                "`sl changelog` - View bot updates\n"
                "`sl elements` - View element information"
            ),
            inline=False
        )

        # Social Commands
        embed.add_field(
            name="👥 **Social Commands**",
            value=(
                "`sl guild` - Guild management\n"
                "`sl party` - Party system\n"
                "`sl trade` - Trade with players\n"
                "`sl oshi` - Favorite characters\n"
                "`sl gallery` - View collections"
            ),
            inline=False
        )

        # Economy Commands
        embed.add_field(
            name="💰 **Economy Commands**",
            value=(
                "`sl shop` - Browse the shop\n"
                "`sl pull` - Gacha system\n"
                "`sl sacrifice` - Convert items\n"
                "`sl market` - Player marketplace\n"
                "`sl vote` - Vote for rewards\n"
                "`sl redeem` - Redeem codes\n"
                "`sl afk` - Claim AFK rewards"
            ),
            inline=False
        )

        embed.set_footer(text="◆ The System ◆ • Use buttons to navigate back")
        return embed

    async def create_skill_learning_embed(self, tree_type: SkillTreeType):
        """Create skill learning interface for a specific tree"""
        player = await Player.get(self.user_id)
        if not player:
            return None

        tree_data = await SkillTreeSystem.get_player_skill_tree(str(self.user_id), tree_type)
        skill_tree = tree_data['tree']

        if not skill_tree:
            return None

        # Enhanced visual design with tree-specific colors and emojis
        tree_configs = {
            SkillTreeType.SHADOW_MONARCH: {
                'color': discord.Color.dark_purple(),
                'emoji': '👑',
                'title': 'SHADOW MONARCH TREE'
            },
            SkillTreeType.WARRIOR: {
                'color': discord.Color.red(),
                'emoji': '⚔️',
                'title': 'WARRIOR TREE'
            },
            SkillTreeType.MAGE: {
                'color': discord.Color.blue(),
                'emoji': '🔮',
                'title': 'MAGE TREE'
            },
            SkillTreeType.ASSASSIN: {
                'color': discord.Color.dark_grey(),
                'emoji': '🗡️',
                'title': 'ASSASSIN TREE'
            },
            SkillTreeType.TANK: {
                'color': discord.Color.green(),
                'emoji': '🛡️',
                'title': 'TANK TREE'
            }
        }

        config = tree_configs.get(tree_type, {
            'color': discord.Color.purple(),
            'emoji': '🌟',
            'title': f'{tree_type.value.upper()} TREE'
        })

        embed = discord.Embed(
            title=f"{config['emoji']} **{config['title']}**",
            description=f"**<@{self.user_id}>'s {skill_tree.name} Path**\n*{skill_tree.description}*",
            color=config['color']
        )

        # Player info
        available_points = getattr(player, 'skillPoints', 0)
        embed.add_field(
            name="📊 **Hunter Status**",
            value=(
                f"**Level**: {player.level}\n"
                f"**Available Skill Points**: {available_points}\n"
                f"**Points Spent in Tree**: {tree_data['total_points_spent']}"
            ),
            inline=True
        )

        # Show available skills to learn with detailed descriptions
        learnable_skills = []
        locked_skills = []
        learnable_skill_data = []  # Store skill data for selection

        for skill_id, node in skill_tree.nodes.items():
            if skill_id in tree_data['unlocked_skills']:
                continue  # Skip already unlocked skills

            can_unlock = await SkillTreeSystem.can_unlock_skill(
                str(self.user_id), tree_type, skill_id, player.level, available_points
            )

            # Enhanced skill display with type icons
            skill_type_icons = {
                SkillType.BASIC: "⚡",
                SkillType.QTE: "🎯",
                SkillType.ULTIMATE: "💥"
            }

            type_icon = skill_type_icons.get(node.skill.skill_type, "⚡")
            element_icon = {
                Element.DARK: "🌑",
                Element.FIRE: "🔥",
                Element.LIGHT: "✨",
                Element.WATER: "💧",
                Element.WIND: "💨"
            }.get(node.skill.element, "⚡")

            # Get skill effects description
            effects_text = self.get_skill_effects_description(node.skill)

            skill_info = f"{type_icon} **{node.skill.name}** {element_icon}\n"
            skill_info += f"   📊 **DMG**: {node.skill.damage}% | **MP**: {node.skill.mp_cost} | **Req**: Lv.{node.level_requirement}\n"
            skill_info += f"   💎 **Cost**: {node.skill_points_cost} SP\n"
            skill_info += f"   📝 **Effect**: {effects_text}\n"

            if can_unlock['can_unlock']:
                learnable_skills.append(f"✅ {skill_info}")
                learnable_skill_data.append({
                    'skill_id': skill_id,
                    'node': node,
                    'name': node.skill.name,
                    'cost': node.skill_points_cost
                })
            else:
                locked_skills.append(f"🔒 {skill_info}   ❌ *{can_unlock['reason']}*\n")

        if learnable_skills:
            embed.add_field(
                name="🎯 **Ready to Learn**",
                value="\n".join(learnable_skills[:3]),  # Show max 3
                inline=False
            )

            # Add skill selection dropdown if there are learnable skills
            if learnable_skill_data:
                self.add_skill_selection_dropdown(learnable_skill_data, available_points)

        if locked_skills:
            embed.add_field(
                name="🔒 **Locked Skills**",
                value="\n".join(locked_skills[:3]),  # Show max 3
                inline=False
            )

        # Show unlocked skills with enhanced display
        unlocked_skills = []
        for skill_id in tree_data['unlocked_skills']:
            if skill_id in skill_tree.nodes:
                node = skill_tree.nodes[skill_id]
                level = tree_data['skill_levels'].get(skill_id, 1)
                max_level = node.max_level

                # Enhanced skill display with type icons
                type_icon = {
                    SkillType.BASIC: "⚡",
                    SkillType.QTE: "🎯",
                    SkillType.ULTIMATE: "💥"
                }.get(node.skill.skill_type, "⚡")

                element_icon = {
                    Element.DARK: "🌑",
                    Element.FIRE: "🔥",
                    Element.LIGHT: "✨",
                    Element.WATER: "💧",
                    Element.WIND: "💨"
                }.get(node.skill.element, "⚡")

                # Calculate current damage with scaling
                current_damage = node.skill.get_scaled_damage(level)

                level_display = f"**Lv.{level}/{max_level}**" if level < max_level else f"**Lv.{level}** ✨"
                unlocked_skills.append(f"⭐ {type_icon} **{node.skill.name}** {element_icon} {level_display}\n   📊 **DMG**: {current_damage}%")

        if unlocked_skills:
            embed.add_field(
                name="⭐ **Mastered Skills**",
                value="\n".join(unlocked_skills[:4]),  # Show max 4 for better formatting
                inline=False
            )

        embed.set_footer(text="◆ The System ◆ • Use buttons to learn skills")
        return embed

    def get_skill_effects_description(self, skill):
        """Get a description of what the skill does based on its effects"""
        from structure.skills import EffectType

        if not hasattr(skill, 'effects') or not skill.effects:
            # Default descriptions based on skill type and damage
            if skill.damage == 0:
                return "Support skill - provides buffs or utility"
            elif skill.skill_type.value == "Ultimate":
                return "Powerful ultimate attack"
            elif skill.skill_type.value == "QTE":
                return "Quick-time event skill"
            else:
                return "Basic attack skill"

        effect_descriptions = []
        for effect in skill.effects:
            if effect == EffectType.DAMAGE:
                effect_descriptions.append("Deals damage")
            elif effect == EffectType.AREA_DAMAGE:
                effect_descriptions.append("Area of effect damage")
            elif effect == EffectType.HEAL:
                effect_descriptions.append("Restores HP")
            elif effect == EffectType.BUFF:
                effect_descriptions.append("Increases stats")
            elif effect == EffectType.DEBUFF:
                effect_descriptions.append("Reduces enemy stats")
            elif effect == EffectType.STUN:
                effect_descriptions.append("Stuns target")
            elif effect == EffectType.LIFE_STEAL:
                effect_descriptions.append("Steals life from enemy")
            elif effect == EffectType.CRIT_BOOST:
                effect_descriptions.append("Increases critical hit chance")
            elif effect == EffectType.SHIELD:
                effect_descriptions.append("Provides protective shield")
            elif effect == EffectType.BLEED:
                effect_descriptions.append("Causes bleeding damage over time")
            elif effect == EffectType.INVINCIBILITY:
                effect_descriptions.append("Grants temporary invincibility")

        return ", ".join(effect_descriptions) if effect_descriptions else "Special effect"

    def add_skill_selection_dropdown(self, learnable_skills, available_points):
        """Add a dropdown for selecting which skill to learn"""
        if not learnable_skills:
            return

        options = []
        for skill_data in learnable_skills[:25]:  # Discord limit
            skill = skill_data['node'].skill
            can_afford = "✅" if available_points >= skill_data['cost'] else "❌"

            # Create option with detailed info
            option = discord.SelectOption(
                label=f"{skill.name} ({skill_data['cost']} SP)",
                description=f"{can_afford} {skill.damage}% DMG | {skill.mp_cost} MP | {skill.skill_type.value}",
                value=skill_data['skill_id'],
                emoji="🎯"
            )
            options.append(option)

        if options:
            select = discord.ui.Select(
                placeholder="🎓 Choose a skill to learn...",
                options=options,
                row=2
            )
            select.callback = self.skill_learn_callback
            self.add_item(select)

    async def skill_learn_callback(self, interaction: discord.Interaction):
        """Handle skill learning selection"""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the skill tree owner can learn skills!", ephemeral=True)
            return

        await interaction.response.defer()

        skill_id = interaction.data['values'][0]

        # Attempt to learn the skill
        result = await SkillTreeSystem.unlock_skill(str(self.user_id), self.current_tree, skill_id)

        if result['success']:
            # Create success embed
            embed = discord.Embed(
                title="🎉 **SKILL LEARNED!**",
                description=f"Successfully learned **{result['skill_name']}**!",
                color=discord.Color.green()
            )

            embed.add_field(
                name="📊 **Skill Details**",
                value=(
                    f"**Name**: {result['skill_name']}\n"
                    f"**Type**: {result.get('skill_type', 'Unknown')}\n"
                    f"**Damage**: {result.get('damage', 0)}%\n"
                    f"**MP Cost**: {result.get('mp_cost', 0)}\n"
                    f"**Cost**: {result.get('cost', 0)} Skill Points"
                ),
                inline=False
            )

            embed.add_field(
                name="💎 **Remaining Points**",
                value=f"**{result.get('remaining_points', 0)}** Skill Points left",
                inline=False
            )

            await interaction.edit_original_response(embed=embed, view=None)

            # Return to skill tree after 3 seconds
            await asyncio.sleep(3)

            # Refresh the skill tree view
            new_view = SkillLearningView(self.bot, self.user_id, self.current_tree)
            embed = await new_view.create_skill_learning_embed(self.current_tree)
            await interaction.edit_original_response(embed=embed, view=new_view)

        else:
            await interaction.followup.send(f"❌ **Failed to learn skill**: {result['reason']}", ephemeral=True)

class SkillTreeView(discord.ui.View):
    """Interactive Skill Tree interface"""

    def __init__(self, bot, user_id, tree_type: SkillTreeType = None):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
        self.current_tree = tree_type

        # Add tree selection buttons if no specific tree
        if not tree_type:
            self.add_tree_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    def add_tree_buttons(self):
        """Add skill tree selection buttons"""
        trees = [
            ("🌑 Shadow Monarch", SkillTreeType.SHADOW_MONARCH),
            ("⚔️ Warrior", SkillTreeType.WARRIOR),
            ("🔮 Mage", SkillTreeType.MAGE),
            ("🗡️ Assassin", SkillTreeType.ASSASSIN),
            ("🛡️ Tank", SkillTreeType.TANK),
            ("💚 Support", SkillTreeType.SUPPORT)
        ]

        for i, (label, tree_type) in enumerate(trees):
            button = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.secondary,
                row=i // 3
            )
            button.callback = self.create_tree_callback(tree_type)
            self.add_item(button)

    def create_tree_callback(self, tree_type: SkillTreeType):
        """Create callback for tree selection"""
        async def callback(interaction: discord.Interaction):
            self.current_tree = tree_type
            embed = await self.create_tree_embed()

            # Clear and add new buttons for this tree
            self.clear_items()
            self.add_tree_navigation_buttons()

            await interaction.response.edit_message(embed=embed, view=self)
        return callback

    def add_tree_navigation_buttons(self):
        """Add navigation buttons for specific tree"""
        # Learn Skills button
        learn_btn = discord.ui.Button(label="🎓 Learn Skills", style=discord.ButtonStyle.primary)
        learn_btn.callback = self.learn_skills_callback
        self.add_item(learn_btn)

        # Back button
        back_btn = discord.ui.Button(label="🔙 Tree Selection", style=discord.ButtonStyle.success)
        back_btn.callback = self.back_to_selection
        self.add_item(back_btn)

    async def learn_skills_callback(self, interaction: discord.Interaction):
        """Show skill learning interface"""
        if self.current_tree:
            # Create temporary SystemInterfaceView to access the embed method
            temp_view = SystemInterfaceView(self.bot, self.user_id)
            embed = await temp_view.create_skill_learning_embed(self.current_tree)
            if embed:
                # Create skill learning view
                view = SkillLearningView(self.bot, self.user_id, self.current_tree)
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await interaction.response.send_message("❌ **Error loading skill learning interface.**", ephemeral=True)
        else:
            await interaction.response.send_message("❌ **Please select a skill tree first.**", ephemeral=True)

    async def back_to_selection(self, interaction: discord.Interaction):
        """Go back to tree selection"""
        self.current_tree = None
        self.clear_items()
        self.add_tree_buttons()

        # Update embed to show tree selection
        embed = await self.create_overview_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_overview_embed(self):
        """Create skill tree overview embed"""
        player = await Player.get(self.user_id)
        if not player:
            return None

        embed = discord.Embed(
            title=f"📱 **[SKILL TREE SYSTEM]**",
            description=f"**<@{self.user_id}>'s Skill Trees**\n*Choose your path to power*",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="⭐ **Available Skill Points**",
            value=f"**{player.skillPoints}** points ready to spend",
            inline=False
        )

        # Show progress for each tree
        for tree_type in SkillTreeType:
            tree_data = await SkillTreeSystem.get_player_skill_tree(str(self.user_id), tree_type)
            unlocked = len(tree_data['unlocked_skills'])
            total = len(tree_data['tree'].nodes) if tree_data['tree'] else 0

            embed.add_field(
                name=f"{self.get_tree_emoji(tree_type)} **{tree_type.value}**",
                value=f"Skills: {unlocked}/{total}",
                inline=True
            )

        embed.set_footer(text="◆ The System ◆ • Select a skill tree to explore")
        return embed

    async def create_tree_embed(self):
        """Create specific skill tree embed"""
        if not self.current_tree:
            return await self.create_overview_embed()

        player = await Player.get(self.user_id)
        tree_data = await SkillTreeSystem.get_player_skill_tree(str(self.user_id), self.current_tree)
        skill_tree = tree_data['tree']

        if not skill_tree:
            return None

        embed = discord.Embed(
            title=f"📱 **[{skill_tree.name.upper()} TREE]**",
            description=f"*{skill_tree.description}*",
            color=discord.Color.purple()
        )

        # Available Skills
        available_skills = skill_tree.get_available_skills(player.level, tree_data['unlocked_skills'])
        if available_skills:
            skills_text = ""
            for node in available_skills[:8]:  # Show up to 8 skills
                skills_text += f"🌟 **{node.skill.name}** (Lv.{node.level_requirement}) - {node.skill_points_cost} SP\n"

            embed.add_field(
                name="✨ **Available Skills**",
                value=skills_text or "*No skills available at your level*",
                inline=False
            )

        # Unlocked Skills
        if tree_data['unlocked_skills']:
            unlocked_text = ""
            for skill_id in list(tree_data['unlocked_skills'])[:8]:
                if skill_id in skill_tree.nodes:
                    skill = skill_tree.nodes[skill_id].skill
                    level = tree_data['skill_levels'].get(skill_id, 1)
                    unlocked_text += f"⚡ **{skill.name}** (Level {level})\n"

            embed.add_field(
                name="🔓 **Unlocked Skills**",
                value=unlocked_text,
                inline=False
            )

        embed.add_field(
            name="📊 **Progress**",
            value=(
                f"**Skills**: {len(tree_data['unlocked_skills'])}/{len(skill_tree.nodes)}\n"
                f"**Points Spent**: {tree_data['total_points_spent']}\n"
                f"**Available**: {player.skillPoints} SP"
            ),
            inline=False
        )

        embed.set_footer(text="◆ The System ◆ • Master your chosen path")
        return embed

    def get_tree_emoji(self, tree_type: SkillTreeType) -> str:
        """Get emoji for tree type"""
        emojis = {
            SkillTreeType.SHADOW_MONARCH: "🌑",
            SkillTreeType.WARRIOR: "⚔️",
            SkillTreeType.MAGE: "🔮",
            SkillTreeType.ASSASSIN: "🗡️",
            SkillTreeType.TANK: "🛡️",
            SkillTreeType.SUPPORT: "💚"
        }
        return emojis.get(tree_type, "🌟")

class SkillLearningView(discord.ui.View):
    """Interactive Skill Learning Interface"""

    def __init__(self, bot, user_id, tree_type: SkillTreeType):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
        self.tree_type = tree_type
        self.current_skill = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the original user to interact"""
        return interaction.user.id == self.user_id

    @discord.ui.button(label="🎯 Learn Next Skill", style=discord.ButtonStyle.primary, row=0)
    async def learn_next_skill(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Learn the next available skill"""
        from utilis.interaction_handler import InteractionHandler

        player = await Player.get(self.user_id)
        if not player:
            await InteractionHandler.safe_response(
                interaction,
                content="❌ **Player not found.**",
                ephemeral=True
            )
            return

        # Get learnable skills
        tree_data = await SkillTreeSystem.get_player_skill_tree(str(self.user_id), self.tree_type)
        skill_tree = tree_data['tree']
        available_points = getattr(player, 'skillPoints', 0)

        learnable_skills = []
        for skill_id, node in skill_tree.nodes.items():
            if skill_id in tree_data['unlocked_skills']:
                continue

            can_unlock = await SkillTreeSystem.can_unlock_skill(
                str(self.user_id), self.tree_type, skill_id, player.level, available_points
            )

            if can_unlock['can_unlock']:
                learnable_skills.append((skill_id, node))

        if not learnable_skills:
            await InteractionHandler.safe_response(
                interaction,
                content="❌ **No skills available to learn right now.**",
                ephemeral=True
            )
            return

        # Learn the first available skill
        skill_id, node = learnable_skills[0]

        # Double-check requirements before unlocking
        if not player.can_learn_skill(node.level_requirement, node.skill_points_cost):
            await InteractionHandler.safe_response(
                interaction,
                content=(
                    f"❌ **Cannot learn {node.skill.name}:** "
                    f"Requires level {node.level_requirement} and {node.skill_points_cost} skill points."
                ),
                ephemeral=True
            )
            return

        result = await SkillTreeSystem.unlock_skill(
            str(self.user_id), self.tree_type, skill_id, player.level, available_points
        )

        if result['success']:
            # Spend skill points using the proper method
            if player.spend_skill_points(node.skill_points_cost):
                # Integrate with existing skill system
                await SkillTreeSystem.integrate_with_skill_manager(str(self.user_id), skill_id)
                await player.save()
            else:
                await InteractionHandler.safe_response(
                    interaction,
                    content=f"❌ **Insufficient skill points:** Need {node.skill_points_cost} SP.",
                    ephemeral=True
                )
                return

            # Create success embed
            embed = discord.Embed(
                title="🎉 **SKILL LEARNED!**",
                description=f"**<@{self.user_id}> has mastered {node.skill.name}!**",
                color=discord.Color.green()
            )

            embed.add_field(
                name="📖 **Skill Details**",
                value=(
                    f"**Name**: {node.skill.name}\n"
                    f"**Type**: {node.skill.skill_type.value}\n"
                    f"**Damage**: {node.skill.damage}%\n"
                    f"**MP Cost**: {node.skill.mp_cost}\n"
                    f"**Element**: {node.skill.element.value}"
                ),
                inline=True
            )

            embed.add_field(
                name="💰 **Cost**",
                value=(
                    f"**Skill Points**: {node.skill_points_cost}\n"
                    f"**Remaining Points**: {player.skillPoints}"
                ),
                inline=True
            )

            embed.set_footer(text="◆ The System ◆ • Skill added to your arsenal")
            await InteractionHandler.safe_edit(interaction, embed=embed, view=self)
        else:
            await InteractionHandler.safe_response(
                interaction,
                content=f"❌ **Failed to learn skill:** {result['message']}",
                ephemeral=True
            )

    @discord.ui.button(label="⬆️ Upgrade Skills", style=discord.ButtonStyle.secondary, row=0)
    async def upgrade_skill(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show skill upgrade interface"""
        player = await Player.get(self.user_id)
        if not player:
            await InteractionHandler.safe_response(
                interaction,
                content="❌ **Player not found.**",
                ephemeral=True
            )
            return

        # Create skill upgrade view and setup
        upgrade_view = SkillUpgradeView(self.bot, self.user_id, self.tree_type)
        await upgrade_view.setup_view()
        embed = await upgrade_view.create_upgrade_embed()

        if embed:
            await interaction.response.edit_message(embed=embed, view=upgrade_view)
        else:
            await interaction.response.send_message("❌ **No skills available to upgrade.**", ephemeral=True)

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=0)
    async def refresh_skills(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Refresh the skill learning interface"""
        from commands.system_commands import SystemInterfaceView
        temp_view = SystemInterfaceView(self.bot, self.user_id)
        temp_view.current_tree = self.tree_type
        embed = await temp_view.create_skill_learning_embed(self.tree_type)

        if embed:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ **Error refreshing interface.**", ephemeral=True)

    @discord.ui.button(label="🔙 Back to Tree", style=discord.ButtonStyle.secondary, row=0)
    async def back_to_tree(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to skill tree overview"""
        view = SkillTreeView(self.bot, self.user_id)
        view.current_tree = self.tree_type
        embed = await view.create_tree_embed()

        if embed:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("❌ **Error loading skill tree.**", ephemeral=True)

class SkillUpgradeView(discord.ui.View):
    """Interactive Skill Upgrade Interface"""

    def __init__(self, bot, user_id, tree_type: SkillTreeType):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
        self.tree_type = tree_type
        self.selected_skill = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the original user to interact"""
        return interaction.user.id == self.user_id

    async def setup_view(self):
        """Setup the view with skill selection dropdown"""
        await self.add_skill_select()
        return self

    async def add_skill_select(self):
        """Add skill selection dropdown"""
        player = await Player.get(self.user_id)
        if not player:
            return

        tree_data = await SkillTreeSystem.get_player_skill_tree(str(self.user_id), self.tree_type)
        skill_tree = tree_data['tree']
        available_points = getattr(player, 'skillPoints', 0)

        options = []
        for skill_id in tree_data['unlocked_skills']:
            if skill_id in skill_tree.nodes:
                node = skill_tree.nodes[skill_id]
                current_level = tree_data['skill_levels'].get(skill_id, 1)

                if current_level < node.max_level:
                    upgrade_cost = node.skill_points_cost * current_level
                    can_afford = "✅" if available_points >= upgrade_cost else "❌"

                    # Enhanced visual display
                    damage_info = f"DMG: {node.skill.get_scaled_damage(current_level)} → {node.skill.get_scaled_damage(current_level + 1)}"

                    options.append(discord.SelectOption(
                        label=f"{node.skill.name} (Lv.{current_level} → {current_level + 1})",
                        description=f"Cost: {upgrade_cost} SP {can_afford} | {damage_info}",
                        value=skill_id,
                        emoji="⬆️" if available_points >= upgrade_cost else "🔒"
                    ))

        if options:
            select = discord.ui.Select(
                placeholder="🎯 Choose a skill to upgrade...",
                options=options[:25],  # Discord limit
                row=0
            )
            select.callback = self.skill_selected
            self.add_item(select)

        # Add control buttons
        self.add_control_buttons()

    def add_control_buttons(self):
        """Add control buttons to the view"""
        # Upgrade button
        upgrade_btn = discord.ui.Button(
            label="🚀 Upgrade Selected Skill",
            style=discord.ButtonStyle.success,
            row=1
        )
        upgrade_btn.callback = self.confirm_upgrade
        self.add_item(upgrade_btn)

        # Refresh button
        refresh_btn = discord.ui.Button(
            label="🔄 Refresh",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        refresh_btn.callback = self.refresh_view
        self.add_item(refresh_btn)

        # Back button
        back_btn = discord.ui.Button(
            label="🔙 Back to Tree",
            style=discord.ButtonStyle.secondary,
            row=1
        )
        back_btn.callback = self.back_to_tree
        self.add_item(back_btn)

    async def skill_selected(self, interaction: discord.Interaction):
        """Handle skill selection"""
        self.selected_skill = interaction.data['values'][0]

        # Get skill info for preview
        player = await Player.get(self.user_id)
        tree_data = await SkillTreeSystem.get_player_skill_tree(str(self.user_id), self.tree_type)
        skill_tree = tree_data['tree']
        node = skill_tree.nodes[self.selected_skill]
        current_level = tree_data['skill_levels'].get(self.selected_skill, 1)
        upgrade_cost = node.skill_points_cost * current_level

        # Create preview embed
        embed = discord.Embed(
            title="🎯 **SKILL UPGRADE PREVIEW**",
            description=f"**{node.skill.name}** selected for upgrade",
            color=discord.Color.blue()
        )

        current_damage = node.skill.get_scaled_damage(current_level)
        new_damage = node.skill.get_scaled_damage(current_level + 1)
        current_mp = node.skill.get_scaled_mp_cost(current_level)
        new_mp = node.skill.get_scaled_mp_cost(current_level + 1)

        embed.add_field(
            name="📊 **Current Stats**",
            value=f"**Level**: {current_level}\n**Damage**: {current_damage}\n**MP Cost**: {current_mp}",
            inline=True
        )

        embed.add_field(
            name="📈 **After Upgrade**",
            value=f"**Level**: {current_level + 1}\n**Damage**: {new_damage}\n**MP Cost**: {new_mp}",
            inline=True
        )

        embed.add_field(
            name="💰 **Upgrade Cost**",
            value=f"**{upgrade_cost}** Skill Points\n**Available**: {player.skillPoints} SP",
            inline=False
        )

        can_afford = player.skillPoints >= upgrade_cost
        embed.add_field(
            name="✅ **Status**" if can_afford else "❌ **Status**",
            value="Ready to upgrade!" if can_afford else "Insufficient skill points!",
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=self)

    async def create_upgrade_embed(self):
        """Create main upgrade interface embed"""
        player = await Player.get(self.user_id)
        if not player:
            return None

        tree_data = await SkillTreeSystem.get_player_skill_tree(str(self.user_id), self.tree_type)
        skill_tree = tree_data['tree']

        embed = discord.Embed(
            title=f"⬆️ **{skill_tree.name} - Skill Upgrades**",
            description=f"**Available Skill Points**: {player.skillPoints} ✥\n\n🎯 Select a skill from the dropdown below to upgrade it!",
            color=discord.Color.gold()
        )

        # Count upgradeable skills
        upgradeable_count = 0
        total_unlocked = len(tree_data['unlocked_skills'])

        for skill_id in tree_data['unlocked_skills']:
            if skill_id in skill_tree.nodes:
                node = skill_tree.nodes[skill_id]
                current_level = tree_data['skill_levels'].get(skill_id, 1)
                if current_level < node.max_level:
                    upgradeable_count += 1

        embed.add_field(
            name="📊 **Upgrade Status**",
            value=(
                f"**Unlocked Skills**: {total_unlocked}\n"
                f"**Upgradeable**: {upgradeable_count}\n"
                f"**Max Level**: 5"
            ),
            inline=True
        )

        embed.add_field(
            name="⚡ **Upgrade Benefits**",
            value=(
                "• **+15% Damage** per level\n"
                "• **+5% MP Cost** per level\n"
                "• **Enhanced Effects** at higher levels\n"
                "• **Better Battle Performance**"
            ),
            inline=True
        )

        if upgradeable_count == 0:
            embed.add_field(
                name="ℹ️ **No Upgrades Available**",
                value="All your skills are at maximum level or you need more skill points!",
                inline=False
            )

        embed.set_footer(text="◆ The System ◆ • Select a skill to see upgrade details")
        return embed

    async def create_skill_detail_embed(self):
        """Create detailed skill upgrade embed"""
        if not self.selected_skill:
            return await self.create_upgrade_embed()

        player = await Player.get(self.user_id)
        tree_data = await SkillTreeSystem.get_player_skill_tree(str(self.user_id), self.tree_type)
        skill_tree = tree_data['tree']
        node = skill_tree.nodes[self.selected_skill]
        current_level = tree_data['skill_levels'].get(self.selected_skill, 1)
        upgrade_cost = node.skill_points_cost * current_level

        embed = discord.Embed(
            title="⬆️ **[SKILL UPGRADE DETAILS]**",
            description=f"**{node.skill.name}** - Ready to enhance",
            color=discord.Color.gold()
        )

        # Current stats
        current_damage = node.skill.get_scaled_damage(current_level)
        current_mp = node.skill.get_scaled_mp_cost(current_level)

        # Next level stats
        next_level = current_level + 1
        next_damage = node.skill.get_scaled_damage(next_level)
        next_mp = node.skill.get_scaled_mp_cost(next_level)

        embed.add_field(
            name="📊 **Current Stats** (Level {})".format(current_level),
            value=(
                f"**Damage**: {current_damage}%\n"
                f"**MP Cost**: {current_mp}\n"
                f"**Element**: {node.skill.element.value}"
            ),
            inline=True
        )

        embed.add_field(
            name="📈 **After Upgrade** (Level {})".format(next_level),
            value=(
                f"**Damage**: {next_damage}% (+{next_damage - current_damage})\n"
                f"**MP Cost**: {next_mp} (+{next_mp - current_mp})\n"
                f"**Element**: {node.skill.element.value}"
            ),
            inline=True
        )

        embed.add_field(
            name="💰 **Upgrade Cost**",
            value=(
                f"**Required**: {upgrade_cost} SP\n"
                f"**Available**: {player.skillPoints} SP\n"
                f"**After Upgrade**: {player.skillPoints - upgrade_cost} SP"
            ),
            inline=False
        )

        can_afford = player.skillPoints >= upgrade_cost
        status_color = "🟢" if can_afford else "🔴"
        status_text = "Ready to upgrade!" if can_afford else "Insufficient skill points"

        embed.add_field(
            name=f"{status_color} **Status**",
            value=status_text,
            inline=False
        )

        embed.set_footer(text="◆ The System ◆ • Use the button below to confirm upgrade")
        return embed

    async def confirm_upgrade(self, interaction: discord.Interaction):
        """Confirm skill upgrade"""
        if not self.selected_skill:
            await interaction.response.send_message("❌ **Please select a skill first.**", ephemeral=True)
            return

        player = await Player.get(self.user_id)
        tree_data = await SkillTreeSystem.get_player_skill_tree(str(self.user_id), self.tree_type)
        skill_tree = tree_data['tree']
        node = skill_tree.nodes[self.selected_skill]
        current_level = tree_data['skill_levels'].get(self.selected_skill, 1)
        upgrade_cost = node.skill_points_cost * current_level

        if not player.can_learn_skill(1, upgrade_cost):  # Level 1 since it's an upgrade
            await interaction.response.send_message(
                f"❌ **Insufficient skill points:** Need {upgrade_cost} SP.",
                ephemeral=True
            )
            return

        result = await SkillTreeSystem.upgrade_skill(
            str(self.user_id), self.tree_type, self.selected_skill, player.level, player.skillPoints
        )

        if result['success']:
            player.spend_skill_points(upgrade_cost)
            await player.save()

            # Create success embed
            embed = discord.Embed(
                title="🎉 **SKILL UPGRADED SUCCESSFULLY!**",
                description=f"**{node.skill.name}** has been enhanced!",
                color=discord.Color.green()
            )

            new_damage = node.skill.get_scaled_damage(result['new_level'])
            new_mp = node.skill.get_scaled_mp_cost(result['new_level'])

            embed.add_field(
                name="📈 **Upgrade Complete**",
                value=(
                    f"**Skill**: {node.skill.name}\n"
                    f"**Level**: {current_level} → {result['new_level']}\n"
                    f"**New Damage**: {new_damage}%\n"
                    f"**New MP Cost**: {new_mp}\n"
                    f"**Cost**: {upgrade_cost} SP"
                ),
                inline=True
            )

            embed.add_field(
                name="💰 **Skill Points**",
                value=(
                    f"**Spent**: {upgrade_cost} SP\n"
                    f"**Remaining**: {player.skillPoints} SP"
                ),
                inline=True
            )

            embed.set_footer(text="◆ The System ◆ • Your skill is now more powerful in battle!")

            # Reset selection and update view
            self.selected_skill = None
            self.clear_items()
            await self.add_skill_select()

            # Add back button with proper callback
            back_btn = discord.ui.Button(label="🔙 Back to Learning", style=discord.ButtonStyle.secondary)

            async def back_callback(interaction):
                await self.back_to_learning(interaction)

            back_btn.callback = back_callback
            self.add_item(back_btn)

            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message(f"❌ **Upgrade failed:** {result['message']}", ephemeral=True)

    async def back_to_learning(self, interaction: discord.Interaction):
        """Return to skill learning interface"""
        view = SkillLearningView(self.bot, self.user_id, self.tree_type)

        # Create temporary SystemInterfaceView to access the embed method
        temp_view = SystemInterfaceView(self.bot, self.user_id)
        embed = await temp_view.create_skill_learning_embed(self.tree_type)

        if embed:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("❌ **Error returning to learning interface.**", ephemeral=True)

    async def refresh_view(self, interaction: discord.Interaction):
        """Refresh the upgrade view"""
        # Clear existing items
        self.clear_items()

        # Re-setup the view
        await self.setup_view()
        embed = await self.create_upgrade_embed()

        if embed:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ **Error refreshing view.**", ephemeral=True)

    async def back_to_tree(self, interaction: discord.Interaction):
        """Return to skill tree overview"""
        view = SkillTreeView(self.bot, self.user_id)
        view.current_tree = self.tree_type
        embed = await view.create_tree_embed()

        if embed:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("❌ **Error loading skill tree.**", ephemeral=True)

class AchievementView(discord.ui.View):
    """Interactive Achievement System Interface"""

    def __init__(self, bot, user_id):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
        self.current_category = None

        # Add category selection dropdown
        self.add_category_select()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the original user to interact"""
        return interaction.user.id == self.user_id

    def add_category_select(self):
        """Add category selection dropdown"""
        options = [
            discord.SelectOption(
                label="Overview",
                description="View achievement progress overview",
                value="overview",
                emoji="📊"
            )
        ]

        # Add category options
        for category in AchievementCategory:
            options.append(discord.SelectOption(
                label=category.value,
                description=f"View {category.value.lower()} achievements",
                value=category.value.lower(),
                emoji="🏅"
            ))

        select = discord.ui.Select(
            placeholder="Choose achievement category...",
            options=options,
            row=0
        )
        select.callback = self.category_selected
        self.add_item(select)

    async def category_selected(self, interaction: discord.Interaction):
        """Handle category selection"""
        selected = interaction.data['values'][0]

        if selected == "overview":
            self.current_category = None
            embed = await self.create_overview_embed()
        else:
            # Find the category enum
            for category in AchievementCategory:
                if category.value.lower() == selected:
                    self.current_category = category
                    embed = await self.create_category_embed(category)
                    break

        await interaction.response.edit_message(embed=embed, view=self)

    async def create_overview_embed(self):
        """Create achievements overview embed"""
        achievements = await AchievementSystem.get_player_achievements(str(self.user_id))

        embed = discord.Embed(
            title="🏅 **[ACHIEVEMENT SYSTEM]**",
            description=f"**<@{self.user_id}>'s Achievement Progress**",
            color=discord.Color.gold()
        )

        # Progress Overview
        completion_rate = (achievements['total_unlocked']/achievements['total_available']*100) if achievements['total_available'] > 0 else 0
        embed.add_field(
            name="📊 **Progress Overview**",
            value=(
                f"**Unlocked**: {achievements['total_unlocked']}/{achievements['total_available']}\n"
                f"**Completion**: {completion_rate:.1f}%\n"
                f"**Progress Bar**: {'█' * int(completion_rate/10)}{'░' * (10-int(completion_rate/10))} {completion_rate:.1f}%"
            ),
            inline=False
        )

        # Recent Achievements
        recent = list(achievements['unlocked'].values())[:5]
        if recent:
            recent_text = ""
            for ach_data in recent:
                achievement = ach_data['achievement']
                rarity_emoji = self.get_rarity_emoji(achievement.rarity.value)
                recent_text += f"{rarity_emoji} **{achievement.name}**\n   *{achievement.description}*\n\n"

            embed.add_field(
                name="🆕 **Recent Achievements**",
                value=recent_text[:1024],  # Discord field limit
                inline=False
            )

        # Categories with counts
        categories_text = ""
        for category in AchievementCategory:
            category_achievements = AchievementSystem.get_achievements_by_category(category)
            unlocked_in_category = sum(1 for ach in category_achievements if ach.id in achievements['unlocked'])
            progress_bar = "█" * (unlocked_in_category * 5 // len(category_achievements)) if category_achievements else ""
            progress_bar += "░" * (5 - len(progress_bar))
            categories_text += f"**{category.value}**: {unlocked_in_category}/{len(category_achievements)} {progress_bar}\n"

        embed.add_field(
            name="📂 **Categories Progress**",
            value=categories_text,
            inline=False
        )

        embed.add_field(
            name="💡 **How to Use**",
            value="Use the dropdown above to explore different achievement categories!",
            inline=False
        )

        embed.set_footer(text="◆ The System ◆ • Achievements unlock automatically")
        return embed

    async def create_category_embed(self, category: AchievementCategory):
        """Create category-specific achievements embed"""
        achievements = await AchievementSystem.get_player_achievements(str(self.user_id))
        category_achievements = AchievementSystem.get_achievements_by_category(category)

        embed = discord.Embed(
            title=f"🏅 **[{category.value.upper()} ACHIEVEMENTS]**",
            description=f"**{category.value} Category Progress**",
            color=discord.Color.gold()
        )

        # Category progress
        unlocked_in_category = sum(1 for ach in category_achievements if ach.id in achievements['unlocked'])
        completion_rate = (unlocked_in_category / len(category_achievements) * 100) if category_achievements else 0

        embed.add_field(
            name="📊 **Category Progress**",
            value=(
                f"**Unlocked**: {unlocked_in_category}/{len(category_achievements)}\n"
                f"**Completion**: {completion_rate:.1f}%\n"
                f"**Progress**: {'█' * int(completion_rate/10)}{'░' * (10-int(completion_rate/10))}"
            ),
            inline=False
        )

        # Show achievements (up to 8 to fit in embed)
        for i, achievement in enumerate(category_achievements[:8]):
            status = "✅" if achievement.id in achievements['unlocked'] else "🔒"
            rarity_emoji = self.get_rarity_emoji(achievement.rarity.value)

            # Get unlock date if unlocked
            unlock_info = ""
            if achievement.id in achievements['unlocked']:
                unlock_date = achievements['unlocked'][achievement.id].get('unlocked_at', 'Unknown')
                unlock_info = f"\n*Unlocked: {unlock_date}*"

            embed.add_field(
                name=f"{status} {rarity_emoji} **{achievement.name}**",
                value=f"*{achievement.description}*\n**Rarity**: {achievement.rarity.value}{unlock_info}",
                inline=True
            )

        if len(category_achievements) > 8:
            embed.add_field(
                name="ℹ️ **More Achievements**",
                value=f"This category has {len(category_achievements) - 8} more achievements!\nKeep playing to discover them all.",
                inline=False
            )

        embed.set_footer(text="◆ The System ◆ • Complete objectives to unlock achievements")
        return embed

    def get_rarity_emoji(self, rarity: str) -> str:
        """Get emoji for achievement rarity"""
        rarity_emojis = {
            "Common": "🔸",
            "Rare": "🔹",
            "Epic": "🔷",
            "Legendary": "💎",
            "Mythic": "⭐"
        }
        return rarity_emojis.get(rarity, "🏅")

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary, row=1)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Refresh achievement data"""
        if self.current_category:
            embed = await self.create_category_embed(self.current_category)
        else:
            embed = await self.create_overview_embed()

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔙 Back to System", style=discord.ButtonStyle.secondary, row=1)
    async def back_to_system(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to main system interface"""
        view = SystemInterfaceView(self.bot, self.user_id)
        embed = await view.create_main_embed()

        if embed:
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("❌ **Error loading system interface.**", ephemeral=True)

class SystemCommands(commands.Cog):
    """Solo Leveling System Commands with Interactive UI"""

    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="system", description="Access the System interface")
    async def system_interface(self, ctx):
        """Main System interface command with interactive buttons"""
        player = await Player.get(ctx.author.id)
        if not player:
            await ctx.send("❌ **You need to create a profile first!** Use `sl profile` to start your journey.")
            return

        # Create interactive system interface
        view = SystemInterfaceView(self.bot, ctx.author.id)
        embed = await view.create_main_embed()

        if embed:
            await ctx.send(embed=embed, view=view)
        else:
            await ctx.send("❌ **Error loading System interface.**")
    
    @commands.hybrid_command(name="rank", description="View your hunter rank and progression")
    async def hunter_rank(self, ctx, user: Optional[discord.Member] = None):
        """Display hunter rank information"""
        target = user or ctx.author
        player = await Player.get(target.id)
        
        if not player:
            await ctx.send("❌ **Hunter not found in the System database.**")
            return
        
        # Get rank data
        rank, _ = await RankingSystem.get_player_rank(str(target.id))
        rank_info = RankingSystem.get_rank_info(rank)
        next_rank_info = RankingSystem.get_next_rank_requirements(rank)
        
        # Create rank embed
        embed = discord.Embed(
            title=f"📱 **[HUNTER RANK ASSESSMENT]**",
            description=f"**{target.display_name}**",
            color=RankingSystem.get_rank_color(rank)
        )
        
        # Current Rank
        embed.add_field(
            name=f"{RankingSystem.get_rank_emoji(rank)} **Current Rank**",
            value=f"**{rank.value}-Rank Hunter**\n*{rank_info['description']}*",
            inline=False
        )
        
        # Rank Benefits
        embed.add_field(
            name="🎁 **Rank Benefits**",
            value=(
                f"**Max Party Size**: {rank_info['max_party_size']}\n"
                f"**Daily Quests**: {rank_info['daily_quests']}\n"
                f"**Stat Bonus**: +{rank_info['stat_bonus']}\n"
                f"**Dungeon Access**: {len(rank_info['dungeon_access'])} types"
            ),
            inline=True
        )
        
        # Progress to Next Rank
        if next_rank_info:
            next_req = next_rank_info['requirements']
            # Use consistent attribute names (hp/mp are the correct ones)
            total_stats = player.attack + player.defense + player.hp + player.mp
            achievements = await AchievementSystem.get_player_achievements(str(target.id))

            progress_text = (
                f"**Level**: {player.level}/{next_req['level']} "
                f"{'✅' if player.level >= next_req['level'] else '❌'}\n"
                f"**Total Stats**: {total_stats:,}/{next_req['total_stats']:,} "
                f"{'✅' if total_stats >= next_req['total_stats'] else '❌'}"
            )
            
            embed.add_field(
                name=f"⬆️ **Next Rank: {next_rank_info['rank'].value}**",
                value=progress_text,
                inline=True
            )
        else:
            embed.add_field(
                name="👑 **Maximum Rank**",
                value="*You have reached the pinnacle of hunter rankings.*",
                inline=True
            )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="◆ The System ◆ • Rankings are evaluated automatically")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="achievements", description="View your achievements and progress")
    async def achievements(self, ctx, category: Optional[str] = None):
        """Display achievement information with interactive UI"""
        player = await Player.get(ctx.author.id)
        if not player:
            await ctx.send("❌ **You need to create a profile first!** Use `sl profile` to start your journey.")
            return

        # Create interactive achievement view
        view = AchievementView(self.bot, ctx.author.id)

        if category:
            # Show specific category if requested
            try:
                cat_enum = AchievementCategory(category.title())
                view.current_category = cat_enum
                embed = await view.create_category_embed(cat_enum)
            except ValueError:
                await ctx.send("❌ **Invalid category!** Use: Combat, Progression, Collection, Social, Exploration, Special")
                return
        else:
            # Show overview by default
            embed = await view.create_overview_embed()

        await ctx.send(embed=embed, view=view)
    
    @commands.hybrid_command(name="skilltree", description="Access your skill trees")
    async def skill_tree(self, ctx, tree: Optional[str] = None):
        """Interactive skill tree interface"""
        player = await Player.get(ctx.author.id)
        if not player:
            await ctx.send("❌ **You need to create a profile first!**")
            return

        # Parse tree type if provided
        tree_type = None
        if tree:
            try:
                tree_type = SkillTreeType(tree.replace("_", " ").title())
            except ValueError:
                await ctx.send("❌ **Invalid skill tree!** Use: Shadow_Monarch, Warrior, Mage, Assassin, Tank, Support")
                return

        # Create interactive skill tree interface
        view = SkillTreeView(self.bot, ctx.author.id, tree_type)

        if tree_type:
            embed = await view.create_tree_embed()
        else:
            embed = await view.create_overview_embed()

        if embed:
            await ctx.send(embed=embed, view=view)
        else:
            await ctx.send("❌ **Error loading skill tree interface.**")

    @commands.command(name="testskills", help="Test your skills and see damage calculations")
    async def test_skills(self, ctx):
        """Test skill system functionality"""
        player = await Player.get(ctx.author.id)
        if not player:
            await ctx.send("❌ **You need to create a profile first!** Use `sl profile` to start your journey.")
            return

        from structure.battle_skills import SkillTestView

        embed = discord.Embed(
            title="🧪 **SKILL SYSTEM TESTER**",
            description="Test your skills and see their damage calculations!",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🎯 **How to Test**",
            value=(
                "1. Click **⚡ Test Skills** to see your available skills\n"
                "2. Select a skill to see damage calculation\n"
                "3. Test different skills to compare effectiveness"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 **Test Parameters**",
            value=(
                "**Your Attack**: 1,000\n"
                "**Enemy Defense**: 100\n"
                "**Your MP**: 1,000\n"
                "**Scenario**: Standard battle test"
            ),
            inline=False
        )

        embed.set_footer(text="◆ The System ◆ • Skill testing interface")

        view = SkillTestView(ctx.author.id)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(SystemCommands(bot))
