import discord
from discord.ext import commands
from commands.tutorial import getTutorialEmbed
from structure.emoji import getEmoji
from structure.player import Player

class StartView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60.0)
        self.target_user = user
        self.decision_made = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.target_user.id:
            await interaction.response.send_message(
                "This is not for you. Please let the intended user decide.", 
                ephemeral=True
            )
            return False
        if self.decision_made:
            await interaction.response.send_message(
                "A decision has already been made.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="ACCEPT", style=discord.ButtonStyle.success, custom_id="accept_button")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.decision_made = True
        for item in self.children:
            item.disabled = True
        
        await interaction.response.defer()
        
        right = getEmoji("rights")
        gacha = getEmoji("ticket")
        gold = getEmoji("gold")
        stone = getEmoji("stone")

        embed = discord.Embed(
            title="Secret Quest Initiated",
            description=( 
                f"Congratulations! You have been chosen to undertake a **classified mission** as a **Hunter**.\n\n"
                f"**__Startup Rewards__**\n"
                f"{right}Obtained 50,000 {gold} Gold\n"
                f"{right}Obtained 5 {gacha} Gacha tickets\n"
                f"{right}Obtained 1000 {stone} Essence Stones"
            ),
            color=discord.Color.dark_gold()
        )
        embed.set_author(name="System Notification", icon_url="https://files.catbox.moe/f46m08.webp")
        embed.set_image(url="https://images-ext-1.discordapp.net/external/pfTmp02lQ0Wglq3n2_MTdDvJnOqg3Swsw8qymAHYLao/%3Fcb%3D20241202155341/https/static.wikia.nocookie.net/solo-leveling-arise/images/2/23/Sung_Jin_Woo_Full_Body.png/revision/latest/scale-to-width-down/1000?format=webp&width=349&height=622")
        embed.add_field(name="Hunter Status", value="> Rank: `[E-Class]`\n> Level: `[01]`", inline=False)
        embed.set_footer(text="Your status has been recorded. Let the hunt begin. Use `sl help` for more info.")
        
        await interaction.edit_original_response(embed=embed, view=self)

        player = Player(interaction.user.id)
        player.stone += 1000
        player.gold += 50000
        player.ticket += 5
        await player.save()

        # Initialize story progress with first mission available
        try:
            from structure.story_campaign import StoryCampaign
            # The first mission (prologue_001) will be automatically available since it has no prerequisites
            # and level requirement is 1, which new players start at
        except ImportError:
            pass  # Story system not available

        tutorial_embed = getTutorialEmbed()
        support_view = discord.ui.View()
        support_view.add_item(discord.ui.Button(label="Support Server", url="https://discord.gg/ariseigris", style=discord.ButtonStyle.link))
        
        try:
            await interaction.user.send(embed=tutorial_embed, view=support_view)
        except discord.Forbidden:
            await interaction.followup.send("I couldn't send you a DM with the tutorial. Please check your privacy settings.", ephemeral=True)

    @discord.ui.button(label="DECLINE", style=discord.ButtonStyle.red, custom_id="decline_button")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.decision_made = True
        for item in self.children:
            item.disabled = True
            
        embed = interaction.message.embeds[0]
        embed.title = "Registration Declined"
        embed.description = "You have chosen not to become a Player at this time. If you change your mind, you can use the `start` command again."
        embed.color = discord.Color.red()
        embed.set_image(url=None)
        embed.clear_fields()
        embed.set_footer(text="You have declined to become a player.")
        
        await interaction.response.edit_message(embed=embed, view=self)


class StartCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='start', help="Begin your journey as a hunter and create your profile.")
    async def start(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)

        if player:
            embed = discord.Embed(
                title="SYSTEM MESSAGE",
                description="**[NOTICE] Already Registered**\nYou have already started your journey as a Hunter.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="Welcome to Arise!",
            color=discord.Color.dark_blue()
        )
        embed.set_author(name="Notice", icon_url="https://files.catbox.moe/f46m08.webp")
        embed.description = (
            "Before you proceed, please read and agree to the following rules:\n\n"
            "1. **No self-botting** - Using automation tools is strictly prohibited.\n"
            "2. **Respect the community** - Toxic behavior will not be tolerated.\n"
            "3. **Follow Discord's Terms of Service** - Ensure compliance with platform rules.\n\n"
            "**[YOU HAVE MET ALL OF THE REQUIREMENTS TO COMPLETE THE SECRET QUEST: 'COURAGE OF THE WEAK']**\n\n"
            "Do you accept the challenge to become a Player?"
        )
        embed.set_image(url="https://files.catbox.moe/blrzkb.webp")
        embed.set_footer(text="Click Accept to start your journey or Decline to opt out.")

        await ctx.send(embed=embed, view=StartView(ctx.author))

async def setup(bot):
    await bot.add_cog(StartCog(bot))
