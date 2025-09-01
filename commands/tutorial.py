import discord
from discord.ext import commands
from structure.emoji import getEmoji

def getTutorialEmbed() -> discord.Embed:
    """Creates and returns the comprehensive tutorial embed."""
    right = getEmoji("rights")
    embed = discord.Embed(
        title="🌟 **ARISE COMPLETE TUTORIAL** 🌟",
        description=(
            "Welcome to Arise! This comprehensive guide covers everything you need to know.\n"
            "**Start your journey**: `sl start` - Registers you and gives starting rewards!"
        ),
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url="https://static.wikia.nocookie.net/solo-leveling/images/5/5a/Igris.png/revision/latest?cb=20210329184537")

    # Getting Started Section
    embed.add_field(
        name="🚀 **Getting Started**",
        value=(
            f"{right} `sl start` - Begin your adventure\n"
            f"{right} `sl profile` - View your character\n"
            f"{right} `sl stats` - Check your current stats\n"
            f"{right} `sl tutorial` - View this guide anytime"
        ),
        inline=False
    )

    # Modern UI Systems
    embed.add_field(
        name="🎮 **Modern Interactive Systems**",
        value=(
            f"{right} `sl story` - Interactive Solo Leveling story campaign\n"
            f"{right} `sl guild` - Modern guild interface with buttons\n"
            f"{right} `sl dungeon` - Interactive dungeon system\n"
            f"{right} `sl lb` - Interactive leaderboard system\n"
            f"{right} `sl gates` - Enhanced gate movement system\n"
            f"{right} `sl pull` - Streamlined gacha with modern UI"
        ),
        inline=False
    )

    # Core Gameplay
    embed.add_field(
        name=f"{getEmoji('attack')} **Character Development**",
        value=(
            f"{right} `sl statupgrade` - Spend skill points on stats\n"
            f"{right} `sl team` - Manage your hunter party\n"
            f"{right} `sl skills` - Learn and upgrade skills\n"
            f"{right} Level up by fighting and completing activities"
        ),
        inline=False
    )

    # Gacha & Collection
    embed.add_field(
        name="🎫 **Gacha & Collection System**",
        value=(
            f"{right} `sl pull` - Use tickets to summon hunters/weapons\n"
            f"{right} `sl gacha` - View summon rates and pity system\n"
            f"{right} Duplicate pulls give shards for upgrades\n"
            f"{right} Use **Sacrifice** button to convert shards to cubes"
        ),
        inline=False
    )

    # Combat Systems
    embed.add_field(
        name="⚔️ **Combat & Battles**",
        value=(
            f"{right} `sl dungeon` - Challenge multi-tier dungeons\n"
            f"{right} `sl raid` - Join or create raid battles\n"
            f"{right} `sl gates` - Enter dimensional gates\n"
            f"{right} **World Bosses** spawn automatically across servers"
        ),
        inline=False
    )

    # Story System
    embed.add_field(
        name="📖 **Interactive Story Campaign**",
        value=(
            f"{right} `sl story` - Experience the complete Solo Leveling story\n"
            f"{right} **Interactive Mode**: Make choices that affect the story\n"
            f"{right} **Real-time Battles**: Strategic combat with skills and items\n"
            f"{right} **Balanced Rewards**: Fair progression without game-breaking\n"
            f"{right} **20 Missions** across 10 chapters from Prologue to Final Battle"
        ),
        inline=False
    )

    # Guild System
    embed.add_field(
        name="🏰 **Guild System**",
        value=(
            f"{right} `sl guild` - Modern guild interface\n"
            f"{right} `sl guild create <name> <desc> <image>` - Create guild (200k gold)\n"
            f"{right} `sl guild join <name>` - Join existing guild\n"
            f"{right} Guilds provide shared progression and benefits"
        ),
        inline=False
    )

    # Advanced Features
    embed.add_field(
        name="🔧 **Advanced Features**",
        value=(
            f"{right} **Elemental System**: Dark↔Light, Water→Fire→Wind→Water\n"
            f"{right} **Rarities**: SSR (Gold) > SR (Purple) > R (Blue)\n"
            f"{right} **Shadows**: Unlock by defeating world bosses\n"
            f"{right} **Oshi System**: Mark favorite hunters with ❤️"
        ),
        inline=False
    )

    embed.set_image(url="https://files.catbox.moe/wqq7l7.jpg")
    embed.set_footer(text="💡 Pro Tip: Use interactive UI commands (guild_ui, dungeon_ui) for the best experience!")
    return embed

class TutorialCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="tutorial", help="Displays a comprehensive tutorial on how to play the bot.")
    async def tutorial(self, ctx: commands.Context):
        """Displays the enhanced tutorial embed with interactive elements."""
        embed = getTutorialEmbed()

        # Create interactive view with helpful buttons
        view = discord.ui.View(timeout=300)

        # Support server button
        view.add_item(discord.ui.Button(
            label="🆘 Support Server",
            url="https://discord.gg/ariseigris",
            style=discord.ButtonStyle.link
        ))

        # Quick start button
        quick_start_button = discord.ui.Button(
            label="🚀 Quick Start",
            style=discord.ButtonStyle.success,
            emoji="🚀"
        )

        async def quick_start_callback(interaction):
            quick_embed = discord.Embed(
                title="🚀 **QUICK START GUIDE** 🚀",
                description="Get started in just a few commands!",
                color=discord.Color.green()
            )

            quick_embed.add_field(
                name="**Step 1: Register**",
                value="`sl start` - Begin your adventure",
                inline=False
            )

            quick_embed.add_field(
                name="**Step 2: Get Hunters**",
                value="`sl pull` - Use your starting tickets",
                inline=False
            )

            quick_embed.add_field(
                name="**Step 3: Build Team**",
                value="`sl team` - Equip your best hunters",
                inline=False
            )

            quick_embed.add_field(
                name="**Step 4: Explore**",
                value="`sl guild` • `sl dungeon` • `sl lb` • `sl gates`",
                inline=False
            )

            await interaction.response.send_message(embed=quick_embed, ephemeral=True)

        quick_start_button.callback = quick_start_callback
        view.add_item(quick_start_button)

        # Modern UI showcase button
        ui_button = discord.ui.Button(
            label="🎮 Try Modern UI",
            style=discord.ButtonStyle.primary,
            emoji="🎮"
        )

        async def ui_callback(interaction):
            ui_embed = discord.Embed(
                title="🎮 **MODERN UI COMMANDS** 🎮",
                description="Try these interactive command interfaces!",
                color=discord.Color.blue()
            )

            ui_embed.add_field(
                name="🏰 Guild System",
                value="`sl guild` - Interactive guild management",
                inline=False
            )

            ui_embed.add_field(
                name="🏰 Dungeon System",
                value="`sl dungeon` - Modern dungeon interface",
                inline=False
            )

            ui_embed.add_field(
                name="🏆 Leaderboard System",
                value="`sl lb` - Interactive leaderboards",
                inline=False
            )

            ui_embed.add_field(
                name="🚪 Gate System",
                value="`sl gates` - Enhanced gate movement",
                inline=False
            )

            ui_embed.add_field(
                name="🎫 Gacha System",
                value="`sl pull` - Streamlined summoning",
                inline=False
            )

            await interaction.response.send_message(embed=ui_embed, ephemeral=True)

        ui_button.callback = ui_callback
        view.add_item(ui_button)

        await ctx.reply(embed=embed, view=view, mention_author=False)

async def setup(bot):
    await bot.add_cog(TutorialCog(bot))