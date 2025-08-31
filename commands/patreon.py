import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from structure.player import Player

class Patreon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="patreon",aliases=['donate'], help="Check your Patreon subscription status or view available packs.")
    async def patreon(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(title="Error", description="You haven't registered yet. Use `sl start` to register.", color=discord.Color.red())
            await ctx.send(embed=embed, delete_after=10)
            return

        # Subscription details with features
        subscription_packs = {
            "Premium 1": {
                "timestamp": player.prem1,
                "name": "Silver Pack",
                "price": "$5",
                "features": [
                    "5% Cooldown reduction",
                    "Activity Fund: Lv 2",
                    "5% Experience Bonus",
                    "Early Supporter role"
                ]
            },
            "Premium 2": {
                "timestamp": player.prem2,
                "name": "Gold Pack",
                "price": "$15",
                "features": [
                    "10% Cooldown reduction",
                    "10% experience boost",
                    "Activity Fund: Lv 3",
                    "Early Supporter Role"
                ]
            },
            "Premium 3": {
                "timestamp": player.prem3,
                "name": "Platinum Pack",
                "price": "$25",
                "features": [
                    "25% Cooldown reduction",
                    "25% experience boost",
                    "Activity Fund: Lv 4",
                    "Early Supporter Role",
                    "Custom Channel"
                ]
            },
        }

        current_time = datetime.utcnow()
        one_month_duration = timedelta(days=30)

        active_pack = None

        for key, details in subscription_packs.items():
            timestamp = details["timestamp"]
            if timestamp:
                subscription_time = datetime.utcfromtimestamp(timestamp)
                time_left = (subscription_time + one_month_duration) - current_time
                if time_left.total_seconds() > 0:
                    active_pack = {
                        "name": details["name"],
                        "price": details["price"],
                        "status": f"⏳ {int(time_left.days)} days, {int(time_left.seconds // 3600)} hours left.",
                        "features": details["features"]
                    }
                    break

        embed = discord.Embed(
            title="Patreon Subscription Status",
            description="Check your current subscription details below. Renew or upgrade your subscription anytime!",
            color=discord.Color.blue(),
        )

        if active_pack:
            p = active_pack["price"]
            features = "\n".join([f"• {feature}" for feature in active_pack["features"]])
            embed.add_field(
                name=f"**{p} {active_pack['name']}**",
                value=(f"**Status**: {active_pack['status']}\n**Features**:\n{features}"),
                inline=False,
            )
        else:
            # Display "Not purchased" for all packs
            embed.description = (
                "You currently don't have an active subscription. By subscribing, you not only gain exclusive rewards but also help support the continued development and improvement of this bot. "
                "Check out the subscription packs below and become a valued supporter today!"
            )

            for key, details in subscription_packs.items():
                features = "\n".join([f"• {feature}" for feature in details["features"]])
                embed.add_field(
                    name=f"{details['price']} {details['name']} ({key})",
                    value=(f"**Features**:\n{features}"),
                    inline=False,
                )

        # Add a shop button
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="Shop",
                url="https://buymeacoffee.com/azazelarise/extras",  # Replace with your actual shop link
                style=discord.ButtonStyle.link,
            )
        )
        view.add_item(
            discord.ui.Button(
                label="Subscriptions",
                url="https://www.patreon.com/c/AzazelArise",  # Replace with your actual shop link
                style=discord.ButtonStyle.link,
            )
        )
        support_button = discord.ui.Button(
            label="Support Server",
            url="https://discord.gg/wX2mAzZRkC",  # Replace with your actual support server link
            style=discord.ButtonStyle.link
        )
        view.add_item(support_button)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Patreon(bot))