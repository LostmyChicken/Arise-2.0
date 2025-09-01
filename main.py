import asyncio
from pathlib import Path
import time
import json
import random
import re
from discord.ext import commands
import discord
import os
from dotenv import load_dotenv

# --- Local Imports ---
from utilis.data_migration import run_migration
from utilis.database_setup import setup_database
from structure.glory import Glory
from utilis.utilis import ELEMENT_WEAKNESSES, create_embed, INFO_COLOR
from utilis.vote import VoteReminderManager
from structure.raids import Raid
from structure.Rank import RankingLeaderboard
from structure.BossDrop import BossDrop
# Removed unused WorldBoss imports - now using Raid.spawn_world_boss()
from structure.boss import Boss
from structure.shadow import Shadow
from structure.skills import SkillManager
from structure.emoji import getClassEmoji, getEmoji
from structure.heroes import HeroManager
from structure.items import ItemManager
from structure.player import Player
from structure.guild import Guild
from structure.channel_commands import channel_command_manager, is_command_allowed

load_dotenv()

# --- Bot Setup ---
intents = discord.Intents.all()
intents.presences = False
bot = commands.Bot(command_prefix=['Sl ', 'sl ', 'sl', 'Sl'], intents=intents, help_command=None)

# --- Server Data Management ---
class Server:
    def __init__(self, server_id, channels=None):
        self.id = server_id
        self.channels = channels if channels else []
    def to_dict(self):
        return {"id": self.id, "channels": self.channels}
    @staticmethod
    def from_dict(data):
        return Server(data["id"], data.get("channels", []))

def load_servers(filename):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
            return {int(server_id): Server.from_dict(server) for server_id, server in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_servers(filename, servers):
    with open(filename, "w") as file:
        json.dump({server_id: server.to_dict() for server_id, server in servers.items()}, file, indent=4)

servers = load_servers("servers.json")
message_counts = {}

# --- Helper Functions ---
async def spawn_boss(channel):
    boss_id = "kandiaru"  # This could be randomized
    boss = await Boss.get(boss_id)
    if not boss:
        await channel.send(embed=discord.Embed(title="Spawn Error", description="Boss data not found!", color=discord.Color.red()))
        return
        
    future_time = int(time.time()) + 180
    level = random.randint(5, 10)
    xp_emoji, gold_emoji = getEmoji("xp"), getEmoji("gold")
    xp_min, xp_max = round(level * 1.1), round(level * 2.2)
    gold_min, gold_max = round(level * 100), round(level * 200)

    embed = discord.Embed(
        title=f"▬▬ {boss.name} ▬▬",
        description=f"Level: **{level}**\nPower Level: **{level * 75}**\n⏱️ __Time Remaining:__ <t:{future_time}:R>",
        color=discord.Color.dark_orange(),
    )
    embed.add_field(name="Weakness", value=f"{boss.weakness_class} {getClassEmoji(boss.weakness_class)}")
    embed.add_field(name="Rewards", value=f"- {gold_emoji} {gold_min}-{gold_max}\n- {xp_emoji} {xp_min}-{xp_max}")
    embed.set_image(url=boss.image)
    embed.set_author(name="Boss Alert", icon_url="https://files.catbox.moe/2f0938.png")
    embed.set_footer(text="Server admins can redirect spawns using `sl redirect`")
    
    view = BossDrop(boss, embed, level, random.randint(gold_min, gold_max), random.randint(xp_min, xp_max))
    message = await channel.send(embed=embed, view=view)
    view.message = message  # Set message reference for timeout handling

async def spawn_world_boss(channel):
    """Spawn the same world boss that /raid command creates"""
    # Use the same world boss system as the /raid command
    from structure.raids import Raid

    # Shadow World Boss pool (same as world boss manager)
    shadow_boss_pool = {
        'common': [
            {'name': 'Igris', 'type': 'Knight', 'rarity': 'Common', 'level_range': (60, 80), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'igris'},
            {'name': 'Iron', 'type': 'Warrior', 'rarity': 'Common', 'level_range': (55, 75), 'image': 'https://files.catbox.moe/4yd1dd.png', 'shadow_unlock': 'iron'},
            {'name': 'Tank', 'type': 'Guardian', 'rarity': 'Common', 'level_range': (50, 70), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'tank'},
        ],
        'rare': [
            {'name': 'Tusk', 'type': 'Beast', 'rarity': 'Rare', 'level_range': (70, 90), 'image': 'https://files.catbox.moe/4yd1dd.png', 'shadow_unlock': 'tusk'},
            {'name': 'Kaisel', 'type': 'Dragon', 'rarity': 'Rare', 'level_range': (75, 95), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'kaisel'},
            {'name': 'Greed', 'type': 'Assassin', 'rarity': 'Rare', 'level_range': (65, 85), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'greed'},
        ],
        'epic': [
            {'name': 'Beru', 'type': 'Ant King', 'rarity': 'Epic', 'level_range': (80, 100), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'beru'},
            {'name': 'Bellion', 'type': 'Grand Marshal', 'rarity': 'Epic', 'level_range': (85, 105), 'image': 'https://files.catbox.moe/4yd1dd.png', 'shadow_unlock': 'bellion'},
        ],
        'legendary': [
            {'name': 'Antares', 'type': 'Dragon Emperor', 'rarity': 'Legendary', 'level_range': (100, 150), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'antares'},
            {'name': 'Thomas Andre', 'type': 'Nation Level Hunter', 'rarity': 'Legendary', 'level_range': (110, 160), 'image': 'https://files.catbox.moe/donb98.webp', 'shadow_unlock': 'thomas_andre'},
        ]
    }

    # Select boss based on rarity weights (same as automatic system)
    rarity_weights = {'common': 50, 'rare': 30, 'epic': 15, 'legendary': 5}
    selected_rarity = random.choices(
        list(rarity_weights.keys()),
        weights=list(rarity_weights.values())
    )[0]

    boss_data = random.choice(shadow_boss_pool[selected_rarity])
    level = random.randint(*boss_data['level_range'])

    # Send loading message
    loading_msg = await channel.send("🌍 **Spawning shadow world boss...**")

    try:
        # Create the shadow world boss raid
        raid = await Raid.spawn_shadow_world_boss(bot, channel, boss_data, level)

        if raid:
            # Edit loading message to show success
            await loading_msg.edit(content="✅ **Shadow world boss has been spawned!**")
            print(f"🌍 Admin spawned shadow world boss '{boss_data['name']}' (Level {level}, {selected_rarity}) in {channel.guild.name}")
        else:
            await loading_msg.edit(content="❌ **Failed to spawn shadow world boss!**")

    except Exception as e:
        await loading_msg.edit(content=f"❌ **Error spawning world boss:** {str(e)}")
        print(f"❌ World boss spawn error: {e}")

# --- New Interactive Help Command ---
class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.command_categories = {
            "👤 Player & Profile": ["start", "profile", "stats", "inventory", "team", "equip", "afk"],
            "⚔️ Combat & Battles": ["fight", "arena", "dungeonui", "gates", "skills", "system"],
            "🎲 Gacha & Items": ["pull", "gacha", "upgrade", "sacrifice", "oshi", "redeem"],
            "🏰 Guild & Social": ["guild", "leaderboard", "lb", "vote"],
            "💰 Economy & Trading": ["daily", "shop", "trade", "market", "boost"],
            "📖 Story & Quests": ["story", "trivia", "train", "missions", "tutorial", "cooldowns"],
            "🔔 Notifications & Settings": ["notifications", "timezone"],
            "🌍 World Boss & Raids": ["raid", "worldboss"],
            "🔧 Utility & Help": ["help", "fixuser", "unstuck", "ping", "changelog", "view"],
            "👑 Admin Commands": ["adminhelp", "give", "create", "fix", "channelcommands"]
        }

    def create_main_embed(self, author):
        invite_url = discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(permissions=8))
        embed = create_embed(
            "🌟 **ARISE HELP DESK** 🌟",
            "Welcome to the **Complete Solo Leveling Experience**!\n"
            "Use the dropdown below to navigate through different command categories.\n\n"
            "**🔧 Command Usage**: Every command works with **both** prefixes:\n"
            "• **Slash Commands**: `/help`, `/profile`, `/guild`, etc.\n"
            "• **Text Commands**: `sl help`, `sl profile`, `sl guild`, etc.\n\n"
            "**💡 Tip**: Type `/` in chat to see all available slash commands with descriptions!\n\n"
            "**🚀 MAJOR NEW FEATURES**:\n"
            "• **Complete Solo Leveling Story** - Experience Jin-Woo's journey (13 arcs, 10 bosses)\n"
            "• **World Boss System** - Automatic cross-server epic battles with Shadow bosses\n"
            "• **Smart Notifications** - Personalized alerts with timezone support\n"
            "• **Enhanced Guild System** - Complete management with roles, bank & applications\n"
            "• **Enhanced Gate System** - Stamina system with strategic movement\n"
            "• **Channel Management** - Disable specific commands per channel",
            INFO_COLOR,
            author
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="🔗 **Quick Links**", value=f"[Invite Me]({invite_url}) | [Support Server](https://discord.gg/ariseigris) | [Vote for Us](https://top.gg/bot/1231157738629890118/vote)", inline=False)
        return embed

    @commands.hybrid_command(name="help", help="Shows this help message.")
    async def help(self, ctx: commands.Context):
        embed = self.create_main_embed(ctx.author)
        view = HelpView(self.bot, self.command_categories, self)
        await ctx.send(embed=embed, view=view)

class HelpView(discord.ui.View):
    def __init__(self, bot, command_categories, help_cog):
        super().__init__(timeout=180)
        self.bot = bot
        self.command_categories = command_categories
        self.help_cog = help_cog
        self.add_item(HelpCategorySelect(bot, command_categories))

    @discord.ui.button(label="Back", style=discord.ButtonStyle.grey, row=1, disabled=True)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.help_cog.create_main_embed(interaction.user)
        
        # Re-enable the select menu and disable the back button
        for item in self.children:
            if isinstance(item, discord.ui.Select):
                item.disabled = False
        button.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)


class HelpCategorySelect(discord.ui.Select):
    def __init__(self, bot, command_categories):
        self.bot = bot
        self.command_categories = command_categories
        options = [discord.SelectOption(label=category, emoji=category.split(" ")[0]) for category in command_categories.keys()]
        super().__init__(placeholder="Choose a command category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        command_names = self.command_categories[category]
        
        embed = create_embed(f"{category} Commands", "Here are the commands for the selected category:", INFO_COLOR, interaction.user)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Add detailed usage examples for key commands
        detailed_usage = {
            "start": "**Begin your adventure!**\nCreates your player profile and gives you starting resources. Use this first!",
            "profile": "**View player profiles**\n• View your own profile or another player's profile\n• Shows level, stats, equipped items, and achievements",
            "guild": "**Enhanced guild management**\n• Open interactive guild interface with roles and permissions\n• Manage Vice Masters, Officers, and Members\n• Access guild bank for shared resources",
            "fight": "**Quick random battles**\n• Battle random opponents for experience and gold\n• Fast combat with skill usage and strategic gameplay",
            "arena": "**PvP battles against players**\n• Fight other players for ranking points and rewards\n• Climb leaderboards with your best team",
            "dungeonui": "**Interactive dungeon battles**\n• Enter modern dungeon interface with enhanced UI\n• Choose difficulty and battle through floors",
            "gates": "**Dimensional gate access**\n• Open gate selection with instant movement\n• Stamina system for running/walking",
            "skills": "**Skill tree system**\n• Learn new abilities using skill points\n• Upgrade existing skills for better effects",
            "upgrade": "**Item upgrade tracking**\n• View all upgradeable items with material requirements\n• Track hunters, weapons, and shadows",
            "pull": "**Gacha system for hunters & weapons**\n• Use tickets to summon new hunters and weapons\n• Set oshi (favorites) to increase pull rates",
            "daily": "**Daily quest rewards**\n• Claim daily rewards and complete objectives\n• Resets every 24 hours",
            "story": "**Solo Leveling story campaign**\n• Follow Sung Jin-Woo's journey from weakest to strongest\n• Complete missions to unlock new features and rewards",
            "cooldowns": "**Command cooldown tracker**\n• View all command cooldowns with remaining time\n• Premium users get reduced cooldowns",
            "fixuser": "**Comprehensive account repair**\n• Fix common account issues and stuck states\n• Repairs corrupted cooldown data automatically",
            "unstuck": "**Quick stuck state fix**\n• Fast fix for stuck commands and 'in command' status\n• Use when commands won't work"
        }

        for cmd_name in command_names:
            command = self.bot.get_command(cmd_name)
            if command:
                # Get command parameters
                params = []
                for param_name, param in command.params.items():
                    if param_name not in ('self', 'ctx'):
                        if param.default == param.empty:
                            params.append(f"<{param_name}>")
                        else:
                            params.append(f"[{param_name}]")

                param_str = " ".join(params)

                # Create both command formats
                slash_cmd = f"/{command.name} {param_str}".strip()
                text_cmd = f"sl {command.name} {param_str}".strip()

                # For hybrid commands, get the description
                if hasattr(command, 'app_command') and command.app_command:
                    description = command.app_command.description
                else:
                    description = command.help or "No description available."

                # Use detailed description if available
                if command.name in detailed_usage:
                    description = detailed_usage[command.name]

                # Format the field with both command types
                command_display = f"**Slash**: `{slash_cmd}`\n**Text**: `{text_cmd}`\n\n{description}"

                embed.add_field(name=f"**{command.name.upper()}**", value=command_display, inline=False)
        
        # Disable the select menu and enable the back button on the view
        if self.view:
            for item in self.view.children:
                if isinstance(item, discord.ui.Select):
                    item.disabled = True
                elif isinstance(item, discord.ui.Button) and item.label == "Back":
                    item.disabled = False

        await interaction.response.edit_message(embed=embed, view=self.view)


@bot.event
async def on_command_error(ctx, error):
    # This is a global error handler.
    # It will catch errors from all commands, not just those in a specific cog.
    
    # If the command has its own error handler, that will be called first.
    # If that handler doesn't exist or re-raises the error, this one will be called.
    
    if hasattr(ctx.command, 'on_error'):
        # If the command has a local error handler, let it handle it.
        return

    if isinstance(error, commands.CheckFailure):
        # Handle check failures (like disabled commands) - message already sent in before_any_command
        return  # Don't send another error message

    if isinstance(error, commands.CommandOnCooldown):
        # Handle the cooldown error globally
        embed = discord.Embed(
            title="Command on Cooldown",
            description=f"You are on cooldown. Please try again in {error.retry_after:.2f}s.",
            color=discord.Color.orange()
        )
        try:
            from utilis.interaction_handler import InteractionHandler

            if ctx.interaction:
                success = await InteractionHandler.safe_response(ctx.interaction, embed=embed, ephemeral=True)
                if not success:
                    await ctx.send(embed=embed)
            else:
                await ctx.send(embed=embed)
        except:
            # Final fallback
            try:
                await ctx.send(embed=embed)
            except:
                pass
        return # Stop further processing

    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="Command Not Found",
            description="The command you entered does not exist. Please use `/help` to see the list of available commands.",
            color=discord.Color.red()
        )
        try:
            await ctx.send(embed=embed, ephemeral=True)
        except:
            await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Missing Argument",
            description=f"Please provide the required argument: `{error.param}`. Type `/help {ctx.command.name}` for more info.",
            color=discord.Color.orange()
        )
        try:
            from utilis.interaction_handler import InteractionHandler

            if ctx.interaction:
                success = await InteractionHandler.safe_response(ctx.interaction, embed=embed, ephemeral=True)
                if not success:
                    await ctx.send(embed=embed)
            else:
                await ctx.send(embed=embed)
        except:
            try:
                await ctx.send(embed=embed)
            except:
                pass
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            title="Invalid Argument",
            description=f"The argument provided is invalid. Please check the command usage and try again.",
            color=discord.Color.orange()
        )
        try:
            from utilis.interaction_handler import InteractionHandler

            if ctx.interaction:
                success = await InteractionHandler.safe_response(ctx.interaction, embed=embed, ephemeral=True)
                if not success:
                    await ctx.send(embed=embed)
            else:
                await ctx.send(embed=embed)
        except:
            try:
                await ctx.send(embed=embed)
            except:
                pass
    else:
        # Log the error for debugging purposes
        print(f"Ignoring exception in on_command_error: {error}")
        # Optionally, send a generic error message to the user
        embed = discord.Embed(
            title="Error",
            description="An unexpected error occurred. Please try again later.",
            color=discord.Color.red()
        )
        try:
            from utilis.interaction_handler import InteractionHandler

            if ctx.interaction:
                # Use the safe interaction handler
                success = await InteractionHandler.safe_response(
                    ctx.interaction,
                    embed=embed,
                    ephemeral=True
                )
                if not success:
                    # Fallback to channel message if interaction failed
                    try:
                        await ctx.send(embed=embed)
                    except:
                        pass
            else:
                await ctx.send(embed=embed)
        except Exception as e:
            # Final fallback - log and ignore
            print(f"Error in error handler: {e}")
            pass

# --- General Commands ---
@bot.command(name="weakness", description="Shows element weaknesses.")
async def weakness(ctx: commands.Context, element: str = None):
    if element is None:
        embed = discord.Embed(title="Element Weaknesses & Effectiveness", color=discord.Color.blue())
        for elem, data in ELEMENT_WEAKNESSES.items():
            weak = ", ".join(f"`x0.5` {w} {getClassEmoji(w)}" for w in data["weak_to"])
            eff = ", ".join(f"`x1.5` {e} {getClassEmoji(e)}" for e in data["effective_against"])
            embed.add_field(name=f"{getClassEmoji(elem)} {elem}", value=f"Weak To: {weak}\nEffective Against: {eff}", inline=False)
        await ctx.send(embed=embed)
    else:
        element = element.capitalize()
        if element in ELEMENT_WEAKNESSES:
            data = ELEMENT_WEAKNESSES[element]
            embed = discord.Embed(title=f"Element: {element}", color=discord.Color.red())
            embed.add_field(name="Weakness", value=", ".join(f"`x0.5` {w} {getClassEmoji(w)}" for w in data["weak_to"]), inline=False)
            embed.add_field(name="Effective Against", value=", ".join(f"`x1.5` {e} {getClassEmoji(e)}" for e in data["effective_against"]), inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ `{element}` is not a valid element.", ephemeral=True)

# --- Admin Commands ---
@bot.command(name="changeid", description="Change a player's ID in the database.")
async def change_id_command(ctx: commands.Context, old_id: int, new_id: int):
    from utilis.admin import is_bot_admin

    if not is_bot_admin(ctx.author.id):
        embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
        await ctx.send(embed=embed, ephemeral=True)
        return

    if old_id == new_id:
        return await ctx.send("Old ID and new ID cannot be the same.", ephemeral=True)
    success = await Player.change_id(old_id, new_id)
    if success:
        await ctx.send(f"Successfully changed player ID from {old_id} to {new_id}.", ephemeral=True)
    else:
        await ctx.send(f"Failed to change player ID from {old_id} to {new_id}. Check logs.", ephemeral=True)

@bot.command(name="redirect", description="Redirect bot spawns to specific channels.")
async def redirect(ctx: commands.Context, *channels: discord.TextChannel):
    # Import admin check
    from utilis.admin import is_bot_admin

    if not is_bot_admin(ctx.author.id):
        embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
        await ctx.send(embed=embed, ephemeral=True)
        return
    guild_id = ctx.guild.id
    if guild_id not in servers:
        servers[guild_id] = Server(guild_id)
    
    servers[guild_id].channels = [channel.id for channel in channels]
    save_servers("servers.json", servers)
    
    if channels:
        await ctx.send(f"Spawns redirected to: {', '.join(c.mention for c in channels)}", ephemeral=True)
    else:
        await ctx.send("Redirection cleared. Spawns will occur in any channel.", ephemeral=True)

@bot.command(name="adminreset", description="Remove a player from the database.")
async def adminreset(ctx: commands.Context, player_id: int):
    from utilis.admin import is_bot_admin

    if not is_bot_admin(ctx.author.id):
        embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
        await ctx.send(embed=embed, ephemeral=True)
        return

    success = await Player.delete_player(player_id)
    if success:
        await ctx.send(f"Successfully removed player {player_id}.", ephemeral=True)
    else:
        await ctx.send(f"Failed to remove player {player_id}.", ephemeral=True)

# --- Bot Startup ---
vote_reminder_manager = None

async def setup_hook():
    global vote_reminder_manager
    startup_time = time.time()
    print("🚀 Starting bot initialization...")

    # Initialize databases with progress tracking
    print("📊 Setting up database...")
    await setup_database()
    print("✅ Database setup complete")

    print("🔄 Running data migration...")
    await run_migration()
    print("✅ Data migration complete")

    print("🎒 Initializing ItemManager...")
    await ItemManager.initialize()
    print("✅ ItemManager initialized")

    print("⚡ Initializing SkillManager...")
    await SkillManager.initialize()
    await SkillManager.migrate_add_level()
    print("✅ SkillManager initialized")

    print("🌳 Initializing Skill Tree System...")
    from structure.skill_tree_system import SkillTreeSystem
    SkillTreeSystem.initialize_skill_trees()
    await SkillTreeSystem.register_all_skills_with_manager()
    print("✅ Skill Tree System initialized")

    print("👹 Initializing Boss system...")
    await Boss.initialize()
    print("✅ Boss system initialized")

    print("🌑 Initializing Shadow system...")
    await Shadow.initialize()
    print("✅ Shadow system initialized")

    print("🏆 Initializing Leaderboard...")
    await RankingLeaderboard.initialize_db()
    print("✅ Leaderboard initialized")

    print("🎖️ Initializing Ranking System...")
    from structure.ranking_system import RankingSystem
    await RankingSystem.initialize()
    print("✅ Ranking System initialized")

    print("🏰 Initializing Guild system...")
    Guild.initialize()
    print("✅ Guild system initialized")

    print("⚔️ Initializing Raid system...")
    await Raid.initialize()
    await Raid.clear_all_raids()
    print("✅ Raid system initialized")

    print("👑 Initializing Glory system...")
    Glory.initialize()
    print("✅ Glory system initialized")

    # Initialize world boss system
    print("🌍 Initializing World Boss system...")
    try:
        from structure.raids import get_world_boss_manager
        world_boss_manager = get_world_boss_manager(bot)
        await world_boss_manager.start_world_boss_system()
        print("✅ World Boss system initialized")
    except Exception as e:
        print(f"⚠️ World Boss system initialization failed: {e}")
        print("🔄 Bot will continue without world boss auto-spawning")
    
    # Reset 'inc' flag for all players (temporarily disabled for faster startup)
    print("✅ Skipping player flag reset for faster startup...")

    # Initialize channel command manager database
    print("Initializing channel command management system...")
    await channel_command_manager.initialize_database()
    print("✅ Channel command management system initialized")

    # Load cogs with progress tracking
    print("Loading extensions...")
    await bot.add_cog(HelpCog(bot))

    # Core extensions (load first for essential functionality)
    core_extensions = [
        "commands.start", "commands.profile", "commands.inventory", "commands.daily",
        "commands.guild", "commands.Fight", "commands.gates", "commands.system_commands"
    ]

    # Secondary extensions (can load in parallel)
    secondary_extensions = [
        "commands.party", "commands.gacha", "commands.edit", "commands.afk", "commands.give",
        "commands.create", "commands.upgrade", "commands.equip", "commands.Skills", "commands.shadow",
        "commands.codex", "commands.evaluate", "commands.cooldowns", "commands.Shop", "commands.Trade",
        "commands.Stat", "commands.Shards", "commands.Gallery", "commands.Raids", "commands.trivia",
        "commands.tutorial", "commands.sacrifice", "commands.patreon", "commands.admin", "commands.admin_extended",
        "commands.dungeons", "commands.train", "commands.boost", "commands.redeem", "commands.badges", "commands.vote",
        "commands.missions", "commands.arena", "commands.market", "commands.lb", "commands.inbox",
        "commands.test", "commands.hunter_weapon", "commands.changelog", "commands.oshi", "commands.elements",
        "commands.view", "commands.skill_reset", "commands.achievement_backtrack", "commands.channel_management",
        "commands.story", "commands.titles", "commands.notifications", "commands.badge", "events.server_tracking"
    ]

    # Load core extensions first
    loaded_count = 0
    total_extensions = len(core_extensions) + len(secondary_extensions)

    for cog in core_extensions:
        try:
            await bot.load_extension(cog)
            loaded_count += 1
            print(f"✅ Loaded core extension: {cog} ({loaded_count}/{total_extensions})")
        except Exception as e:
            print(f"❌ Failed to load core extension {cog}: {e}")

    # Load secondary extensions
    for cog in secondary_extensions:
        try:
            await bot.load_extension(cog)
            loaded_count += 1
            print(f"✅ Loaded extension: {cog} ({loaded_count}/{total_extensions})")
        except Exception as e:
            print(f"❌ Failed to load extension {cog}: {e}")

    print(f"🎉 Extension loading complete! ({loaded_count}/{total_extensions} loaded)")

    print("🗳️ Initializing vote reminder manager...")
    vote_reminder_manager = VoteReminderManager(bot)
    print("✅ Vote reminder manager initialized")

    # Initialize notification system
    print("🔔 Initializing notification system...")
    try:
        from structure.notification_system import get_notification_manager
        notification_manager = get_notification_manager(bot)
        await notification_manager.initialize()
        print("✅ Notification system initialized")
    except Exception as e:
        print(f"⚠️ Failed to initialize notification system: {e}")
        print("🔄 Bot will continue without notification system")

    # Initialize automated maintenance system
    print("🔧 Starting automated maintenance system...")
    try:
        from automated_maintenance import AutomatedMaintenance
        maintenance = AutomatedMaintenance()
        asyncio.create_task(maintenance.start_maintenance_loop())
        print("✅ Automated maintenance system started")
        print("📅 Daily backups at 12:00 UTC (keeps last 4 backups)")
        print("📅 Weekly database vacuum on Sundays at 12:00 UTC")
    except Exception as e:
        print(f"⚠️ Failed to start maintenance system: {e}")
        print("🔄 Bot will continue without automated maintenance")

    # Calculate and display total startup time
    total_time = time.time() - startup_time
    print(f"🎊 Bot initialization complete! Total time: {total_time:.2f} seconds")
    print("🤖 Arise is ready to rock and roll!")

@bot.event
async def on_ready():
    print(f"{bot.user.name} READY TO ROCK N ROLL")
    activity = discord.Activity(type=discord.ActivityType.watching, name="sl help | sl story | World Bosses")
    await bot.change_presence(activity=activity)
    await bot.tree.sync()

@bot.before_invoke
async def before_any_command(ctx):
    """Hook that runs before every command to check if it's allowed in the channel"""

    # Check if command is allowed in this channel
    if not await is_command_allowed(ctx):
        try:
            embed = discord.Embed(
                title="🚫 **Command Disabled**",
                description=f"The `{ctx.command.name}` command is disabled in {ctx.channel.mention}.\n\nContact a server administrator to enable it.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Use 'sl channelcommands' (with Administrator permission) to manage command availability")

            # Try to send ephemeral message if it's an interaction
            try:
                from utilis.interaction_handler import InteractionHandler
                if ctx.interaction:
                    success = await InteractionHandler.safe_response(ctx.interaction, embed=embed, ephemeral=True)
                    if not success:
                        await ctx.send(embed=embed)
                else:
                    await ctx.send(embed=embed)
            except:
                await ctx.send(embed=embed)

        except Exception as e:
            logging.error(f"Error sending disabled command message: {e}")

        # Raise the check failure to prevent command execution
        raise commands.CheckFailure(f"Command {ctx.command.name} is disabled in channel {ctx.channel.id}")

@bot.event
async def on_command_completion(ctx):
    """Track command usage for world boss triggers and specific player logging"""

    # Log commands for specific player ID
    target_player_id = 846543765476343828
    if ctx.author.id == target_player_id:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        server_name = ctx.guild.name if ctx.guild else "DM"
        server_id = ctx.guild.id if ctx.guild else "DM"
        channel_name = ctx.channel.name if hasattr(ctx.channel, 'name') else "DM"
        command_name = ctx.command.name if ctx.command else "Unknown"

        log_entry = f"[{timestamp}] Player {target_player_id} used command '{command_name}' in server '{server_name}' ({server_id}) channel '{channel_name}'"

        # Log to console
        print(f"🔍 PLAYER TRACKING: {log_entry}")

        # Also log to file
        try:
            with open("player_command_log.txt", "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}")

    if ctx.guild:
        # Track activity for world boss spawning
        from structure.raids import get_world_boss_manager
        world_boss_manager = get_world_boss_manager(bot)
        world_boss_manager.track_activity(ctx.guild.id)

        # Special triggers for world boss spawns
        if ctx.command and ctx.command.name == 'arena':
            # Check for high arena streaks
            try:
                player = await Player.get(ctx.author.id)
                if player and hasattr(player, 'aStreak') and player.aStreak >= 10:
                    await world_boss_manager.trigger_special_spawn(ctx.guild.id, 'arena_streak')
            except:
                pass

        elif ctx.command and ctx.command.name in ['gate', 'raid']:
            # Track gate/raid completions for triggers
            try:
                await world_boss_manager.trigger_special_spawn(ctx.guild.id, f'{ctx.command.name}_completion')
            except:
                pass

@bot.event
async def on_message(message: discord.Message):
    if message.guild is None or (message.webhook_id is None and message.author.bot):
        return

    # Process spawns
    guild_id = message.guild.id
    if guild_id in servers:
        message_counts.setdefault(guild_id, 0)
        message_counts[guild_id] += 1
        if message_counts[guild_id] >= 270:
            redirect_channels = servers[guild_id].channels
            if redirect_channels:
                raids_exist = await asyncio.gather(*(Raid.get(ch) for ch in redirect_channels))
                available_channels = [ch_id for ch_id, raid in zip(redirect_channels, raids_exist) if not raid]
                if available_channels:
                    channel_id = random.choice(available_channels)
                    channel = bot.get_channel(channel_id)
                    if channel:
                        spawn_type = random.randint(1, 3)
                        if spawn_type == 1:
                            await spawn_boss(channel)  # Old single-player boss
                        elif spawn_type == 2:
                            await spawn_world_boss(channel)  # New multiplayer world boss
                        else:
                            await Raid.spawn_raid(channel, shadow_name=random.choice(["Igris", "Tusk", "Tank"]), level=random.randint(50, 100))
                    message_counts[guild_id] = 0

    # Process vote webhooks
    def extract_user_id(content):
        match = re.search(r"<@!?(\d+)>", content)
        return int(match.group(1)) if match else None

    if message.channel.id == 1343191923225133127:  # DBL
        user_id = extract_user_id(message.content)
        if user_id and (player := await Player.get(user_id)):
            player.key += 1; player.ticket += 2
            await player.save()
            await vote_reminder_manager.add_reminder(user_id, "dbl")
    
    if message.channel.id == 1343115267781431306:  # Top.gg
        user_id = extract_user_id(message.content)
        if user_id and (player := await Player.get(user_id)):
            if not hasattr(player, 'vS'): player.vS = 0
            if not hasattr(player, 'lV'): player.lV = None
            
            # Convert lV to float if it exists and is not None, handle string values from database
            try:
                if player.lV and (time.time() - float(player.lV)) > 129600: 
                    player.vS = 0
            except (ValueError, TypeError):
                # If conversion fails, reset lV and vS
                player.lV = None
                player.vS = 0
            
            bonus = 1 + (min(player.vS, 15) * 0.01)
            player.key += int(random.randint(1, 2) * bonus)
            player.ticket += int(5 * bonus)
            player.gold += int(random.randint(5000, 10000) * bonus)
            player.stone += int(random.randint(100, 250) * bonus)
            player.vote = time.time()
            player.vS += 1
            player.lV = time.time()
            await player.save()
            await vote_reminder_manager.add_reminder(user_id, "topgg")

    await bot.process_commands(message)

@bot.command(name="spawnboss", help="Spawn a boss (Bot Admin only)")
async def spawn_boss_command(ctx):
    from utilis.admin import is_bot_admin

    if not is_bot_admin(ctx.author.id):
        embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
        await ctx.send(embed=embed, ephemeral=True)
        return

    await spawn_boss(ctx.channel)

@bot.command(name="spawnworldboss", help="Spawn a world boss (Bot Admin only)")
async def spawn_world_boss_command(ctx):
    from utilis.admin import is_bot_admin

    if not is_bot_admin(ctx.author.id):
        embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
        await ctx.send(embed=embed, ephemeral=True)
        return

    await spawn_world_boss(ctx.channel)

@bot.command(name="worldbossstatus", help="Check world boss status (Bot Admin only)")
async def world_boss_status_command(ctx):
    from utilis.admin import is_bot_admin
    from structure.raids import Raid

    if not is_bot_admin(ctx.author.id):
        embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
        await ctx.send(embed=embed, ephemeral=True)
        return

    # Check if there's an active raid in this channel
    raid = await Raid.get(ctx.channel.id, bot)

    if not raid:
        embed = discord.Embed(
            title="🌍 World Boss Status",
            description="No active world boss in this channel.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        return

    # Get world boss info
    is_world_boss = getattr(raid, 'is_world_boss', False)
    is_admin_spawned = getattr(raid, 'is_admin_spawned', False)
    battle_started = getattr(raid, 'started', False)

    embed = discord.Embed(
        title="🌍 World Boss Status",
        description=f"**Boss**: {raid.shadow}\n**Level**: {raid.level}\n**Rarity**: {getattr(raid, 'rarity', 'Unknown')}",
        color=discord.Color.green() if is_world_boss else discord.Color.orange()
    )

    embed.add_field(
        name="📊 Status",
        value=(
            f"**Is World Boss**: {'✅' if is_world_boss else '❌'}\n"
            f"**Admin Spawned**: {'✅' if is_admin_spawned else '❌'}\n"
            f"**Battle Started**: {'✅' if battle_started else '❌'}\n"
            f"**Players Joined**: {len(raid.members)}"
        ),
        inline=False
    )

    embed.add_field(
        name="⚔️ Stats",
        value=f"**Health**: {raid.health:,}/{raid.max_health:,}\n**Attack**: {raid.attack:,}\n**Defense**: {raid.defense:,}",
        inline=False
    )

    await ctx.send(embed=embed)

@bot.command(name="testtimer", help="Test world boss timer (Bot Admin only)")
async def test_timer_command(ctx):
    from utilis.admin import is_bot_admin
    import asyncio
    import time

    if not is_bot_admin(ctx.author.id):
        embed = discord.Embed(title="🚫 Unauthorized", description="You are not authorized to use this command.", color=discord.Color.red())
        await ctx.send(embed=embed, ephemeral=True)
        return

    # Simple timer test
    start_time = time.time() + 10  # 10 seconds from now

    embed = discord.Embed(
        title="🕐 Timer Test",
        description="Testing 10-second countdown...",
        color=discord.Color.blue()
    )
    message = await ctx.send(embed=embed)

    # Timer loop
    for i in range(10):
        time_remaining = max(0, start_time - time.time())

        embed = discord.Embed(
            title="🕐 Timer Test",
            description=f"Time remaining: {time_remaining:.1f}s",
            color=discord.Color.blue()
        )

        try:
            await message.edit(embed=embed)
            print(f"🕐 Timer test loop {i+1}: {time_remaining:.1f}s remaining")
        except Exception as e:
            print(f"❌ Error updating timer test: {e}")
            break

        if time_remaining <= 0:
            embed = discord.Embed(
                title="✅ Timer Test Complete",
                description="Timer expired successfully!",
                color=discord.Color.green()
            )
            await message.edit(embed=embed)
            print("✅ Timer test completed successfully")
            break

        await asyncio.sleep(1)

async def main():
    async with bot:
        await setup_hook()
        token = os.getenv("DISCORD_TOKEN")
        if token:
            await bot.start(token)
        else:
            print("Error: DISCORD_TOKEN environment variable not set.")

if __name__ == "__main__":
    asyncio.run(main())