import discord
from discord.ext import commands
from discord import ui

class HelpView(ui.View):
    def __init__(self, ctx, embeds):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.embeds = embeds
        self.current_page = 0
        
        # Disable previous button on first page
        self.children[0].disabled = True
        # Disable next button if only one page
        if len(self.embeds) <= 1:
            self.children[1].disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("You cannot control this help menu.", ephemeral=True)
            return False
        return True

    async def update_embed(self, interaction: discord.Interaction):
        # Enable/disable buttons based on the current page
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page >= len(self.embeds) - 1
        
        # Update the footer to show the current page
        self.embeds[self.current_page].set_footer(text=f"Page {self.current_page + 1}/{len(self.embeds)} | Requested by {self.ctx.author.display_name}", icon_url=self.ctx.author.display_avatar.url)
        
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: ui.Button):
        self.current_page -= 1
        await self.update_embed(interaction)

    @ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        self.current_page += 1
        await self.update_embed(interaction)

class Help(commands.Cog):
    """The help command"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.remove_command('help')

    @commands.hybrid_command(name="help", description="Shows a list of all available commands.")
    async def help(self, ctx: commands.Context):
        """Shows a list of all available commands."""
        # Organize commands by custom categories
        command_categories = {
            "👤 Player & Profile": ["start", "profile", "stats", "inventory", "team", "equip", "afk"],
            "⚔️ Combat & Battles": ["fight", "arena", "dungeonui", "gates", "skills", "system"],
            "🎲 Gacha & Items": ["pull", "gacha", "upgrade", "sacrifice", "oshi", "redeem"],
            "🏰 Guild & Social": ["guild", "leaderboard", "lb", "vote"],
            "💰 Economy & Trading": ["daily", "shop", "trade", "market", "boost"],
            "📖 Story & Quests": ["story", "trivia", "train", "missions", "tutorial", "cooldowns"],
            "🔔 Notifications & Settings": ["notifications", "timezone"],
            "🌍 World Boss & Raids": ["raid", "worldboss"],
            "🔧 Utility & Help": ["help", "fixuser", "unstuck", "ping", "changelog", "view"],
            "👑 Admin Commands": ["adminhelp", "give", "create", "fix", "resetstory", "channelcommands"]
        }

        embeds = []
        
        # Create the main landing page for the help menu
        main_embed = discord.Embed(
            title="🌟 **ARISE HELP DESK** 🌟",
            description=(
                "Welcome to the **Complete Solo Leveling Experience**!\n"
                "Navigate through command categories using the buttons below.\n\n"
                "**🔧 Command Usage**: Every command works with **both** prefixes:\n"
                "• **Slash Commands**: `/help`, `/profile`, `/guild`, etc.\n"
                "• **Text Commands**: `sl help`, `sl profile`, `sl guild`, etc.\n\n"
                "**🆕 NEW FEATURES**:\n"
                "• **Complete Solo Leveling Story** - Experience Jin-Woo's journey!\n"
                "• **World Boss System** - Cross-server epic battles!\n"
                "• **Smart Notifications** - Personalized alerts & timezone support!\n"
                "• **Enhanced Guild System** - Complete guild management!\n\n"
                "**💡 Tip**: Type `/` in chat to see all available slash commands with descriptions!"
            ),
            color=discord.Color.gold()
        )
        main_embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # Add new features section
        main_embed.add_field(
            name="🆕 **Latest Features**",
            value=(
                "• **Interactive Story System** - Full Solo Leveling campaign with dialogue choices and real-time battles\n"
                "• **Enhanced Guild System** - Vice Masters, guild bank, applications, and role management\n"
                "• **World Boss System** - Epic battles across servers with raid-style UI\n"
                "• **Complete Upgrade Tracking** - All hunters, weapons, and shadows with material validation\n"
                "• **Fixed Skill System** - Learn skills with proper effect descriptions\n"
                "• **Improved Error Handling** - Self-repair commands and better stability\n"
                "• **Modern UI Systems** - Interactive buttons for all major features"
            ),
            inline=False
        )

        # Add quick start guide
        main_embed.add_field(
            name="🚀 **Quick Start Guide**",
            value=(
                "**New Players**: `sl start` → `sl tutorial` → `sl pull` → `sl story`\n"
                "**Complete Story**: `sl story` • Experience Jin-Woo's journey from E-rank to Shadow Monarch\n"
                "**World Bosses**: Automatic spawns • Join epic cross-server battles\n"
                "**Notifications**: `sl notifications` • `sl timezone` • Personalized alerts\n"
                "**Enhanced UI**: `sl guild` • `sl dungeonui` • `sl gates` • `sl lb`\n"
                "**Core Systems**: `sl profile` • `sl team` • `sl stats` • `sl upgrade`"
            ),
            inline=False
        )

        # Add UI commands section
        main_embed.add_field(
            name="🎮 **Major Features**",
            value=(
                "`sl story` - **Complete Solo Leveling Story** (13 arcs, 10 bosses)\n"
                "`sl notifications` - **Smart Notification System** with timezone support\n"
                "`sl guild` - **Enhanced Guild System** with roles, bank & applications\n"
                "`sl gates` - **Enhanced Gate System** with stamina & movement\n"
                "`sl cooldowns` - **Enhanced Cooldowns** with notification alerts\n"
                "`sl timezone` - **Personal Timezone** settings for display"
            ),
            inline=True
        )

        # Add world boss section
        main_embed.add_field(
            name="🌍 **World Boss System**",
            value=(
                "**Automatic Spawning** - Every 2-7 hours across servers\n"
                "**Cross-Server Battles** - Join from any server\n"
                "**Shadow Bosses** - Igris, Iron, Tusk, Beru & more\n"
                "**Smart Scaling** - Difficulty scales with players\n"
                "**Damage Rewards** - Fair loot for 1%+ damage\n"
                "**Notifications** - Get alerted when bosses spawn"
            ),
            inline=True
        )

        # Add admin commands section (if user is admin)
        from utilis.admin import is_bot_admin
        if is_bot_admin(ctx.author.id):
            main_embed.add_field(
                name="👑 **Admin Access**",
                value="`sl adminhelp` - Comprehensive admin command center",
                inline=True
            )

        invite_url = discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(8))
        support_server_url = "https://discord.gg/ariseigris"
        vote_url = "https://top.gg/bot/1231157738629890118/vote"

        main_embed.add_field(
            name="🔗 **Quick Links**",
            value=f"[Invite Bot]({invite_url}) | [Support Server]({support_server_url}) | [Vote for Us]({vote_url})",
            inline=False
        )

        main_embed.add_field(
            name="🆘 **Need Help?**",
            value=(
                "**Account Issues?** Use `sl fixuser` for comprehensive repair!\n"
                "**Stuck in Command?** Use `sl unstuck` for quick fixes!\n"
                "**Cooldown Problems?** Fixed automatically with better error handling!\n"
                "**Skill Errors?** All skill system bugs have been resolved!\n"
                "**More Help?** Join our support server for assistance."
            ),
            inline=False
        )

        main_embed.set_footer(text="Use the navigation buttons to explore command categories")
        embeds.append(main_embed)

        # Create a separate page for each category
        for category_name, command_names in command_categories.items():
            embed = discord.Embed(
                title=f"{category_name}",
                description=f"Detailed command information for {category_name.lower()}",
                color=discord.Color.random()
            )

            for cmd_name in command_names:
                command = self.bot.get_command(cmd_name)
                if not command:
                    continue

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

                signature = f"**Slash**: `{slash_cmd}`\n**Text**: `{text_cmd}`"

                # Add aliases if they exist
                if command.aliases:
                    aliases = ", ".join([f"`sl {alias}`" for alias in command.aliases])
                    signature += f"\n**Aliases**: {aliases}"

                description = command.help or "No description provided."

                # Add detailed usage examples and instructions
                detailed_usage = {
                    "start": "**Begin your adventure!**\nCreates your player profile and gives you starting resources. Use this first!",
                    "profile": "**View player profiles**\n• `/profile` - View your own profile\n• `/profile @user` - View another player's profile\nShows level, stats, equipped items, and achievements.",
                    "story": "**Complete Solo Leveling Story Campaign**\n• `/story` - Experience Jin-Woo's complete journey\n• 13 interactive story arcs from E-rank to Shadow Monarch\n• 10 epic boss battles with real combat mechanics\n• 78 meaningful choices that shape character development\n• Unlock new bot features as you progress through the story",
                    "notifications": "**Smart Notification System**\n• `/notifications` - Complete notification management center\n• Set up world boss alerts with server and rarity filtering\n• Create custom notifications with scheduling\n• Manage quiet hours and delivery preferences\n• Visual server selection with toggle buttons",
                    "timezone": "**Personal Timezone Settings**\n• `/timezone` - View your current timezone\n• `/timezone -5` - Set timezone to EST (UTC-5)\n• `/timezone +1` - Set timezone to CET (UTC+1)\n• Affects display times only, game mechanics stay UTC\n• Shows cooldown ready times in your local time",
                    "guild": "**Enhanced guild management**\n• `/guild` - Open interactive guild interface\n• Manage roles (Guild Master, Vice Master, Officer, Member)\n• Access guild bank for shared resources\n• Handle applications and member management\n• Form alliances with other guilds",
                    "pull": "**Gacha system for hunters & weapons**\n• `/pull` - Open interactive pull interface\n• Use tickets to summon new hunters and weapons\n• Set oshi (favorites) to increase pull rates\n• Sacrifice unwanted items for resources",
                    "team": "**Manage your hunter party**\n• `/team` - View and edit your active team\n• Equip hunters to different positions\n• Optimize team composition for battles",
                    "dungeonui": "**Interactive dungeon battles**\n• `/dungeonui` - Enter modern dungeon interface\n• Choose difficulty and battle through floors\n• Earn rewards and experience\n• Enhanced UI with skill usage",
                    "gates": "**Enhanced Gate System**\n• `/gates` - Open gate selection interface with stamina system\n• Instant movement without confirmation dialogs\n• Stamina system: sprint/run depletes stamina, walk to regenerate\n• Monsters move every 8 seconds except defeated ones\n• Permanent monster defeats - no re-fighting same enemies\n• Hidden boss rooms with dramatic discovery system",
                    "cooldowns": "**Enhanced Cooldown System**\n• `/cooldowns` - View all command cooldowns with 'Set Alerts' button\n• Timezone-aware display shows ready times in your local time\n• One-click notification setup for when commands are ready\n• Smart detection of active cooldowns only\n• Integration with notification system",
                    "arena": "**PvP battles against players**\n• `/arena` - Enter arena combat\n• Fight other players for ranking points\n• Climb leaderboards and earn rewards\n• Strategic combat with your best team",
                    "fight": "**Quick random battles**\n• `/fight` - Battle random opponents\n• Fast combat for experience and gold\n• Good for training and quick rewards",
                    "daily": "**Daily quest rewards**\n• `/daily` - Claim daily rewards\n• Complete objectives for bonus rewards\n• Resets every 24 hours",
                    "skills": "**Skill tree system**\n• `/skills` - Open skill learning interface\n• Learn new abilities using skill points\n• Upgrade existing skills for better effects\n• Choose from different skill trees",
                    "upgrade": "**Item upgrade tracking**\n• `/upgrade` - View all upgradeable items\n• See material requirements for upgrades\n• Track hunters, weapons, and shadows\n• Smart sorting by upgrade availability",
                    "inventory": "**Browse your collection**\n• `/inventory` - View all your items\n• Filter by type (hunters, weapons, items)\n• Check item details and stats",
                    "stats": "**Detailed player statistics**\n• `/stats` - View comprehensive stats\n• See rankings and achievements\n• Track progress and improvements",
                    "cooldowns": "**Command cooldown tracker**\n• `/cooldowns` - View all command cooldowns\n• See remaining time for each command\n• Premium users get reduced cooldowns",
                    "fixuser": "**Comprehensive account repair**\n• `/fixuser` - Fix common account issues\n• Resets stuck command states\n• Repairs corrupted cooldown data\n• Safe and automatic fixes",
                    "unstuck": "**Quick stuck state fix**\n• `/unstuck` - Fast fix for stuck commands\n• Clears 'in command' status\n• Use when commands won't work",
                    "leaderboard": "**Player rankings**\n• `/leaderboard` or `/lb` - Interactive leaderboards\n• View top players by different categories\n• Compare your progress with others",
                    "lb": "**Interactive leaderboards**\n• `/lb` - Modern leaderboard interface\n• Multiple ranking categories\n• Real-time player comparisons"
                }

                if command.name in detailed_usage:
                    description = detailed_usage[command.name]

                embed.add_field(name=f"**{command.name.upper()}**", value=f"{signature}\n\n{description}", inline=False)
            
            embeds.append(embed)

        # Set the footer for the first page
        embeds[0].set_footer(text=f"Page 1/{len(embeds)} | Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        view = HelpView(ctx, embeds)
        await ctx.send(embed=embeds[0], view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
