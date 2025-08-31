import time
import discord
from discord.ext import commands
import discord.ui as ui
from utilis.utilis import PremiumCheck
from structure.player import Player

class CooldownView(ui.View):
    def __init__(self, author: discord.User, player, cooldowns_data):
        super().__init__(timeout=300)
        self.author = author
        self.player = player
        self.cooldowns_data = cooldowns_data

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This cooldown panel doesn't belong to you!", ephemeral=True)
            return False
        return True

    def get_cooldown_status(self, last_time, cooldown_duration, name, timezone_offset=0):
        """Get cooldown status using original bot emojis with timezone display"""
        current_time = time.time()
        try:
            last_time = float(last_time) if last_time is not None else None
        except (ValueError, TypeError):
            last_time = None

        if last_time is None or current_time - last_time >= cooldown_duration:
            return f"`☑️` --- {name}: `Available`"
        else:
            remaining_time = cooldown_duration - (current_time - last_time)
            ready_time = current_time + remaining_time

            # Calculate time display
            minutes, seconds = divmod(int(remaining_time), 60)
            hours, minutes = divmod(minutes, 60)

            # Ensure all values are integers for string formatting
            hours = int(hours)
            minutes = int(minutes)
            seconds = int(seconds)

            # Show ready time in user's timezone if set
            if timezone_offset != 0:
                from datetime import datetime, timedelta
                ready_dt = datetime.utcfromtimestamp(ready_time) + timedelta(hours=timezone_offset)
                ready_time_str = ready_dt.strftime("%H:%M")
                timezone_str = f"UTC{timezone_offset:+d}"

                if hours > 0:
                    return f"`⏳` --- {name}: `( {hours}h {minutes}m {seconds}s )` Ready at `{ready_time_str} {timezone_str}`"
                elif minutes > 0:
                    return f"`⏳` --- {name}: `( {minutes}m {seconds}s )` Ready at `{ready_time_str} {timezone_str}`"
                else:
                    return f"`⏳` --- {name}: `( {seconds}s )` Ready at `{ready_time_str} {timezone_str}`"
            else:
                if hours > 0:
                    return f"`⏳` --- {name}: `( {hours} hours {minutes} min {seconds} sec)`"
                elif minutes > 0:
                    return f"`⏳` --- {name}: `( {minutes} min {seconds} sec )`"
                else:
                    return f"`⏳` --- {name}: `( {seconds} sec )`"

    async def get_cooldown_embed(self):
        """Generate the cooldown embed matching original style"""
        try:
            # Get user's timezone offset for display
            timezone_offset = 0
            try:
                from structure.notification_system import get_notification_manager
                notification_manager = get_notification_manager(None)  # We'll handle the None bot case
                if notification_manager:
                    settings = await notification_manager.get_user_settings(self.author.id)
                    timezone_offset = settings.get('timezone_offset', 0)
            except:
                pass  # Use default timezone_offset = 0

            # Get all cooldown statuses with timezone
            statuses = {
                "daily": self.get_cooldown_status(self.cooldowns_data["daily"]["last_time"],
                                                self.cooldowns_data["daily"]["duration"], "Daily", timezone_offset),
                "vote": self.get_cooldown_status(self.cooldowns_data["vote"]["last_time"],
                                               self.cooldowns_data["vote"]["duration"], "Vote", timezone_offset),
                "train": self.get_cooldown_status(self.cooldowns_data["train"]["last_time"],
                                                self.cooldowns_data["train"]["duration"], "Train", timezone_offset),
                "trivia": self.get_cooldown_status(self.cooldowns_data["trivia"]["last_time"],
                                                 self.cooldowns_data["trivia"]["duration"], "Trivia", timezone_offset),
                "fight": self.get_cooldown_status(self.cooldowns_data["fight"]["last_time"],
                                                self.cooldowns_data["fight"]["duration"], "Fight", timezone_offset),
                "raid": self.get_cooldown_status(self.cooldowns_data["raid"]["last_time"],
                                               self.cooldowns_data["raid"]["duration"], "Raid", timezone_offset),
                "dungeon": self.get_cooldown_status(self.cooldowns_data["dungeon"]["last_time"],
                                                  self.cooldowns_data["dungeon"]["duration"], "Dungeon", timezone_offset),
                "arena": self.get_cooldown_status(self.cooldowns_data["arena"]["last_time"],
                                                self.cooldowns_data["arena"]["duration"], "Arena", timezone_offset)
            }
        except ValueError:
            statuses = {key: "⚠️ Error reading cooldown" for key in self.cooldowns_data.keys()}

        # Create the embed
        embed = discord.Embed(
            title=f"{self.author.display_name}'s Cooldowns"
        )

        # Add fields with organized cooldowns
        embed.add_field(
            name="Claims",
            value=f"{statuses['daily']}\n{statuses['vote']}",
            inline=False
        )

        embed.add_field(
            name="Combat",
            value=f"{statuses['arena']}\n{statuses['fight']}\n{statuses['dungeon']}\n{statuses['raid']}",
            inline=False
        )

        embed.add_field(
            name="Activities",
            value=f"{statuses['train']}\n{statuses['trivia']}",
            inline=False
        )

        # Add premium info
        cooldown_reduction = PremiumCheck(self.player)
        if cooldown_reduction == 0.75:
            reduction_text = "Cooldown Reduction: 25%"
        elif cooldown_reduction == 0.90:
            reduction_text = "Cooldown Reduction: 10%"
        elif cooldown_reduction == 0.95:
            reduction_text = "Cooldown Reduction: 5%"
        else:
            reduction_text = "Patreon Users have reduced cooldown"

        embed.set_footer(text=reduction_text, icon_url=self.author.display_avatar.url)
        return embed

    @ui.button(label="Refresh", style=discord.ButtonStyle.gray, emoji="🔄")
    async def refresh_cooldowns(self, interaction: discord.Interaction, _button: ui.Button):
        # Refresh player data and cooldowns
        refreshed_player = await Player.get(self.author.id)
        if not refreshed_player:
            await interaction.response.send_message("Error refreshing cooldowns!", ephemeral=True)
            return

        self.player = refreshed_player

        # Regenerate cooldowns data
        base_cooldowns = {
            "dungeon": 1800,    # 30 minutes
            "train": 180,       # 3 minutes
            "daily": 86400,     # 24 hours
            "trivia": 120,      # 2 minutes
            "raid": 28800,      # 8 hours
            "fight": 180,       # 3 minutes
            "vote": 43200,      # 12 hours
            "arena": 120        # 2 minutes
        }

        cooldown_reduction = PremiumCheck(self.player)

        # Update cooldowns data
        for key, base_duration in base_cooldowns.items():
            duration = int(base_duration * cooldown_reduction) if key not in ["daily", "vote"] else base_duration

            last_time = None
            if key == "arena":
                last_time = getattr(self.player, 'aC', None)
            else:
                last_time = getattr(self.player, key, None)

            self.cooldowns_data[key] = {
                "name": key.title(),
                "duration": duration,
                "last_time": last_time
            }

        # Refresh the embed
        embed = await self.get_cooldown_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @ui.button(label="Set Alerts", style=discord.ButtonStyle.blurple, emoji="🔔")
    async def set_cooldown_alerts(self, interaction: discord.Interaction, _button: ui.Button):
        """Set up notifications for when cooldowns are ready"""
        try:
            from structure.notification_system import get_notification_manager
            notification_manager = get_notification_manager(interaction.client)

            # Get user settings to check if cooldown alerts are enabled
            settings = await notification_manager.get_user_settings(self.author.id)
            if not settings.get('cooldown_alerts', 1):
                await interaction.response.send_message(
                    "🔔 Cooldown alerts are disabled in your notification settings. Use `sl notifications` to enable them!",
                    ephemeral=True
                )
                return

            # Find cooldowns that are currently active and can have alerts set
            current_time = time.time()
            available_alerts = []

            for key, cooldown_data in self.cooldowns_data.items():
                last_time = cooldown_data.get("last_time")
                duration = cooldown_data.get("duration")

                if last_time and isinstance(last_time, (int, float)):
                    remaining_time = duration - (current_time - float(last_time))
                    if remaining_time > 60:  # Only show if more than 1 minute remaining
                        ready_time = current_time + remaining_time
                        available_alerts.append({
                            'name': cooldown_data['name'],
                            'key': key,
                            'ready_time': ready_time,
                            'remaining_minutes': int(remaining_time / 60)
                        })

            if not available_alerts:
                await interaction.response.send_message(
                    "⏰ All your cooldowns are ready or will be ready within a minute! No alerts needed.",
                    ephemeral=True
                )
                return

            # Create alert options embed
            embed = discord.Embed(
                title="🔔 Set Cooldown Alerts",
                description="Choose which cooldowns you want to be notified about when they're ready:",
                color=discord.Color.blue()
            )

            alert_text = []
            for alert in available_alerts[:8]:  # Limit to 8 to avoid embed limits
                alert_text.append(f"**{alert['name']}** - Ready in `{alert['remaining_minutes']}` minutes")

            embed.add_field(
                name="Available Alerts",
                value="\n".join(alert_text),
                inline=False
            )

            embed.set_footer(text="Click the buttons below to set alerts for specific cooldowns")

            # Create view with buttons for each cooldown
            alert_view = CooldownAlertView(self.author, available_alerts, notification_manager)
            await interaction.response.send_message(embed=embed, view=alert_view, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting up alerts: {str(e)}", ephemeral=True)

class CooldownAlertView(ui.View):
    def __init__(self, author, available_alerts, notification_manager):
        super().__init__(timeout=300)
        self.author = author
        self.available_alerts = available_alerts
        self.notification_manager = notification_manager

        # Add buttons for each cooldown (max 5 per row, 25 total)
        for i, alert in enumerate(available_alerts[:20]):  # Limit to 20 buttons
            button = ui.Button(
                label=f"{alert['name']} ({alert['remaining_minutes']}m)",
                style=discord.ButtonStyle.secondary,
                custom_id=f"alert_{alert['key']}"
            )
            button.callback = self.create_alert_callback(alert)
            self.add_item(button)

    def create_alert_callback(self, alert_data):
        async def alert_callback(interaction):
            try:
                # Create notification
                notification_id = await self.notification_manager.add_notification(
                    user_id=self.author.id,
                    notification_type="cooldown",
                    title=f"{alert_data['name']} Ready!",
                    message=f"Your {alert_data['name'].lower()} cooldown has finished. You can use the command again!",
                    scheduled_time=alert_data['ready_time']
                )

                if notification_id > 0:
                    embed = discord.Embed(
                        title="✅ Alert Set!",
                        description=f"You'll be notified when **{alert_data['name']}** is ready!",
                        color=discord.Color.green()
                    )
                    embed.set_footer(text=f"Notification ID: {notification_id}")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Failed to set alert!", ephemeral=True)

            except Exception as e:
                await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

        return alert_callback

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This alert panel doesn't belong to you!", ephemeral=True)
            return False
        return True


class CooldownsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="cooldowns", aliases=["cd", "cooldown"], help="View your current command cooldowns with an interactive interface.")
    async def cooldowns(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="Profile Not Found",
                description="You haven't started the bot yet. Use `sl start` to get started!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Base cooldown durations in seconds
        base_cooldowns = {
            "dungeon": 1800,    # 30 minutes
            "train": 180,       # 3 minutes
            "daily": 86400,     # 24 hours
            "trivia": 120,      # 2 minutes
            "raid": 28800,      # 8 hours
            "fight": 180,       # 3 minutes
            "vote": 43200,      # 12 hours
            "arena": 120        # 2 minutes
        }

        # Get cooldown reduction multiplier
        cooldown_reduction = PremiumCheck(player)

        # Prepare cooldowns data
        cooldowns_data = {}
        
        try:
            for key, base_duration in base_cooldowns.items():
                # Apply reduction (excluding daily and vote)
                duration = int(base_duration * cooldown_reduction) if key not in ["daily", "vote"] else base_duration
                
                # Get last time for this cooldown
                last_time = None
                if key == "arena":
                    last_time = getattr(player, 'aC', None)
                else:
                    last_time = getattr(player, key, None)
                
                cooldowns_data[key] = {
                    "name": key.title(),
                    "duration": duration,
                    "last_time": last_time
                }
                
        except (ValueError, TypeError, AttributeError):
            embed = discord.Embed(
                title="Error",
                description="There was an error reading your cooldown data. Please try again.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Create interactive view
        view = CooldownView(ctx.author, player, cooldowns_data)
        embed = await view.get_cooldown_embed()

        await ctx.reply(embed=embed, view=view, mention_author=False)

async def setup(bot):
    await bot.add_cog(CooldownsCog(bot))