import time
import discord
from discord.ext import commands
import discord.ui as ui
from datetime import datetime, timedelta
from structure.player import Player
from structure.notification_system import get_notification_manager
from structure.emoji import getEmoji

class NotificationView(ui.View):
    def __init__(self, author: discord.User, notification_manager):
        super().__init__(timeout=300)
        self.author = author
        self.notification_manager = notification_manager
        self.current_page = "main"
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This notification panel doesn't belong to you!", ephemeral=True)
            return False
        return True
    
    async def get_main_embed(self):
        """Create the main notifications embed"""
        embed = discord.Embed(
            title=f"🔔 {self.author.display_name}'s Notification Center",
            description="Manage your personal alerts and reminders",
            color=discord.Color.blue()
        )
        
        # Get user settings
        settings = await self.notification_manager.get_user_settings(self.author.id)
        
        # Get active notifications count
        notifications = await self.notification_manager.get_user_notifications(self.author.id)
        active_count = len(notifications)
        
        embed.add_field(
            name="📊 **Status**",
            value=f"Active Notifications: `{active_count}`\nDM Alerts: `{'✅' if settings.get('dm_notifications', 1) else '❌'}`\nChannel Alerts: `{'✅' if settings.get('channel_notifications', 0) else '❌'}`",
            inline=True
        )
        
        embed.add_field(
            name="🔔 **Alert Types**",
            value=f"Cooldown Alerts: `{'✅' if settings.get('cooldown_alerts', 1) else '❌'}`\nWorld Boss Alerts: `{'✅' if settings.get('world_boss_alerts', 1) else '❌'}`\nDaily Reminders: `{'✅' if settings.get('daily_reminders', 0) else '❌'}`",
            inline=True
        )
        
        embed.add_field(
            name="⏰ **Quiet Hours**",
            value=f"Start: `{settings.get('quiet_hours_start', 'Not Set')}`\nEnd: `{settings.get('quiet_hours_end', 'Not Set')}`\nTimezone: `UTC{settings.get('timezone_offset', 0):+d}`",
            inline=True
        )
        
        embed.set_footer(text="Use the buttons below to manage your notifications")
        return embed
    
    async def get_active_notifications_embed(self):
        """Create embed showing active notifications"""
        notifications = await self.notification_manager.get_user_notifications(self.author.id)
        
        embed = discord.Embed(
            title="📋 Active Notifications",
            color=discord.Color.green()
        )
        
        if not notifications:
            embed.description = "You have no active notifications."
            return embed
        
        # Group by type
        notification_groups = {}
        for notif in notifications:
            notif_type = notif['notification_type']
            if notif_type not in notification_groups:
                notification_groups[notif_type] = []
            notification_groups[notif_type].append(notif)
        
        for notif_type, notifs in notification_groups.items():
            type_emoji = {
                'cooldown': '⏰',
                'world_boss': '⚔️',
                'daily_reminder': '📅',
                'custom': '📝',
                'event': '🎉'
            }.get(notif_type, '🔔')
            
            value_lines = []
            for notif in notifs[:5]:  # Show max 5 per type
                scheduled_dt = datetime.fromtimestamp(notif['scheduled_time'])
                time_str = scheduled_dt.strftime("%m/%d %H:%M")
                value_lines.append(f"`{notif['id']}` - {notif['title']} - `{time_str}`")
            
            if len(notifs) > 5:
                value_lines.append(f"... and {len(notifs) - 5} more")
            
            embed.add_field(
                name=f"{type_emoji} {notif_type.title()} ({len(notifs)})",
                value="\n".join(value_lines) if value_lines else "None",
                inline=False
            )
        
        embed.set_footer(text="Use 'Cancel Notification' to remove specific alerts by ID")
        return embed
    
    async def get_settings_embed(self):
        """Create settings configuration embed"""
        settings = await self.notification_manager.get_user_settings(self.author.id)
        
        embed = discord.Embed(
            title="⚙️ Notification Settings",
            description="Configure your notification preferences",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="🔔 **Alert Types**",
            value=f"Cooldown Alerts: `{'ON' if settings.get('cooldown_alerts', 1) else 'OFF'}`\n"
                  f"World Boss Alerts: `{'ON' if settings.get('world_boss_alerts', 1) else 'OFF'}`\n"
                  f"Daily Reminders: `{'ON' if settings.get('daily_reminders', 0) else 'OFF'}`\n"
                  f"Custom Alerts: `{'ON' if settings.get('custom_alerts', 1) else 'OFF'}`",
            inline=False
        )
        
        embed.add_field(
            name="📱 **Delivery Methods**",
            value=f"DM Notifications: `{'ON' if settings.get('dm_notifications', 1) else 'OFF'}`\n"
                  f"Channel Notifications: `{'ON' if settings.get('channel_notifications', 0) else 'OFF'}`\n"
                  f"Preferred Channel: `{settings.get('preferred_channel', 'Not Set')}`",
            inline=False
        )
        
        embed.add_field(
            name="⏰ **Quiet Hours**",
            value=f"Start Hour: `{settings.get('quiet_hours_start', 'Not Set')}`\n"
                  f"End Hour: `{settings.get('quiet_hours_end', 'Not Set')}`\n"
                  f"Timezone Offset: `UTC{settings.get('timezone_offset', 0):+d}`",
            inline=False
        )
        
        embed.set_footer(text="Use the buttons to toggle settings on/off")
        return embed
    
    @ui.button(label="View Active", style=discord.ButtonStyle.green, emoji="📋")
    async def view_active_notifications(self, interaction: discord.Interaction, _button: ui.Button):
        embed = await self.get_active_notifications_embed()
        self.current_page = "active"
        await interaction.response.edit_message(embed=embed, view=self)
    
    @ui.button(label="Settings", style=discord.ButtonStyle.blurple, emoji="⚙️")
    async def view_settings(self, interaction: discord.Interaction, _button: ui.Button):
        settings_view = SettingsView(self.author, self.notification_manager)
        embed = await settings_view.get_settings_embed()
        await interaction.response.edit_message(embed=embed, view=settings_view)
    
    @ui.button(label="Add Custom", style=discord.ButtonStyle.gray, emoji="➕")
    async def add_custom_notification(self, interaction: discord.Interaction, _button: ui.Button):
        modal = CustomNotificationModal(self.notification_manager)
        await interaction.response.send_modal(modal)
    
    @ui.button(label="Cancel Alert", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel_notification(self, interaction: discord.Interaction, _button: ui.Button):
        modal = CancelNotificationModal(self.notification_manager)
        await interaction.response.send_modal(modal)
    
    @ui.button(label="Back to Main", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def back_to_main(self, interaction: discord.Interaction, _button: ui.Button):
        embed = await self.get_main_embed()
        self.current_page = "main"
        await interaction.response.edit_message(embed=embed, view=self)

class SettingsView(ui.View):
    def __init__(self, author: discord.User, notification_manager):
        super().__init__(timeout=300)
        self.author = author
        self.notification_manager = notification_manager

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This settings panel doesn't belong to you!", ephemeral=True)
            return False
        return True

    async def get_settings_embed(self):
        """Create settings configuration embed"""
        settings = await self.notification_manager.get_user_settings(self.author.id)

        embed = discord.Embed(
            title="⚙️ Notification Settings",
            description="Click the buttons below to toggle settings on/off",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="🔔 **Alert Types**",
            value=f"Cooldown Alerts: `{'ON' if settings.get('cooldown_alerts', 1) else 'OFF'}`\n"
                  f"World Boss Alerts: `{'ON' if settings.get('world_boss_alerts', 1) else 'OFF'}`\n"
                  f"Daily Reminders: `{'ON' if settings.get('daily_reminders', 0) else 'OFF'}`\n"
                  f"Custom Alerts: `{'ON' if settings.get('custom_alerts', 1) else 'OFF'}`",
            inline=False
        )

        embed.add_field(
            name="📱 **Delivery Methods**",
            value=f"DM Notifications: `{'ON' if settings.get('dm_notifications', 1) else 'OFF'}`\n"
                  f"Channel Notifications: `{'ON' if settings.get('channel_notifications', 0) else 'OFF'}`\n"
                  f"Preferred Channel: `{settings.get('preferred_channel', 'Not Set')}`",
            inline=False
        )

        embed.add_field(
            name="⏰ **Quiet Hours**",
            value=f"Start Hour: `{settings.get('quiet_hours_start', 'Not Set')}`\n"
                  f"End Hour: `{settings.get('quiet_hours_end', 'Not Set')}`\n"
                  f"Timezone Offset: `UTC{settings.get('timezone_offset', 0):+d}`",
            inline=False
        )

        embed.set_footer(text="Use the buttons to toggle settings on/off")
        return embed

    @ui.button(label="Toggle Cooldown Alerts", style=discord.ButtonStyle.blurple, emoji="⏰")
    async def toggle_cooldown_alerts(self, interaction: discord.Interaction, _button: ui.Button):
        settings = await self.notification_manager.get_user_settings(self.author.id)
        new_value = 0 if settings.get('cooldown_alerts', 1) else 1

        success = await self.notification_manager.update_user_settings(
            self.author.id, {'cooldown_alerts': new_value}
        )

        if success:
            status = "ON" if new_value else "OFF"
            embed = await self.get_settings_embed()
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"✅ Cooldown Alerts turned **{status}**!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Failed to update setting!", ephemeral=True)

    @ui.button(label="Toggle World Boss Alerts", style=discord.ButtonStyle.red, emoji="⚔️")
    async def toggle_world_boss_alerts(self, interaction: discord.Interaction, _button: ui.Button):
        settings = await self.notification_manager.get_user_settings(self.author.id)
        new_value = 0 if settings.get('world_boss_alerts', 1) else 1

        success = await self.notification_manager.update_user_settings(
            self.author.id, {'world_boss_alerts': new_value}
        )

        if success:
            status = "ON" if new_value else "OFF"
            embed = await self.get_settings_embed()
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"✅ World Boss Alerts turned **{status}**!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Failed to update setting!", ephemeral=True)

    @ui.button(label="Toggle Daily Reminders", style=discord.ButtonStyle.green, emoji="📅")
    async def toggle_daily_reminders(self, interaction: discord.Interaction, _button: ui.Button):
        settings = await self.notification_manager.get_user_settings(self.author.id)
        new_value = 0 if settings.get('daily_reminders', 0) else 1

        success = await self.notification_manager.update_user_settings(
            self.author.id, {'daily_reminders': new_value}
        )

        if success:
            status = "ON" if new_value else "OFF"
            embed = await self.get_settings_embed()
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"✅ Daily Reminders turned **{status}**!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Failed to update setting!", ephemeral=True)

    @ui.button(label="Toggle DM Notifications", style=discord.ButtonStyle.secondary, emoji="📱")
    async def toggle_dm_notifications(self, interaction: discord.Interaction, _button: ui.Button):
        settings = await self.notification_manager.get_user_settings(self.author.id)
        new_value = 0 if settings.get('dm_notifications', 1) else 1

        success = await self.notification_manager.update_user_settings(
            self.author.id, {'dm_notifications': new_value}
        )

        if success:
            status = "ON" if new_value else "OFF"
            embed = await self.get_settings_embed()
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"✅ DM Notifications turned **{status}**!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Failed to update setting!", ephemeral=True)

    @ui.button(label="Set Quiet Hours", style=discord.ButtonStyle.gray, emoji="🌙")
    async def set_quiet_hours(self, interaction: discord.Interaction, _button: ui.Button):
        modal = QuietHoursModal(self.notification_manager)
        await interaction.response.send_modal(modal)

    @ui.button(label="World Boss Settings", style=discord.ButtonStyle.red, emoji="🌍", row=1)
    async def world_boss_settings(self, interaction: discord.Interaction, _button: ui.Button):
        world_boss_view = WorldBossSettingsView(self.author, self.notification_manager)
        embed = await world_boss_view.get_world_boss_settings_embed()
        await interaction.response.edit_message(embed=embed, view=world_boss_view)

    @ui.button(label="Set Channel", style=discord.ButtonStyle.green, emoji="📺", row=1)
    async def set_channel_notifications(self, interaction: discord.Interaction, _button: ui.Button):
        modal = ChannelSetupModal(self.notification_manager)
        await interaction.response.send_modal(modal)

    @ui.button(label="Manage Servers", style=discord.ButtonStyle.secondary, emoji="🏰", row=1)
    async def manage_servers(self, interaction: discord.Interaction, _button: ui.Button):
        server_view = EasyServerSelectionView(self.author, self.notification_manager)
        embed = await server_view.get_server_selection_embed()
        await interaction.response.edit_message(embed=embed, view=server_view)

    @ui.button(label="View My Settings", style=discord.ButtonStyle.blurple, emoji="👤", row=1)
    async def view_my_settings(self, interaction: discord.Interaction, _button: ui.Button):
        settings = await self.notification_manager.get_user_settings(self.author.id)

        embed = discord.Embed(
            title="👤 Your Current Settings",
            color=discord.Color.blue()
        )

        # Timezone info
        timezone_offset = settings.get('timezone_offset', 0)
        if timezone_offset == 0:
            timezone_str = "UTC+0 (Not Set)"
        else:
            timezone_str = f"UTC{timezone_offset:+d}"

        embed.add_field(
            name="🌍 Timezone",
            value=timezone_str,
            inline=True
        )

        # Channel info
        channel_id = settings.get('preferred_channel')
        if channel_id:
            channel = interaction.client.get_channel(int(channel_id))
            channel_str = channel.mention if channel else f"Channel ID: {channel_id}"
        else:
            channel_str = "Not Set"

        embed.add_field(
            name="📺 Preferred Channel",
            value=channel_str,
            inline=True
        )

        # World boss servers with easy management
        import json
        allowed_servers = json.loads(settings.get('world_boss_servers', '[]'))
        if allowed_servers:
            server_names = []
            for server_id in allowed_servers[:3]:  # Show max 3
                try:
                    guild = interaction.client.get_guild(int(server_id))
                    if guild:
                        server_names.append(guild.name)
                    else:
                        server_names.append(f"Server {server_id}")
                except:
                    server_names.append(f"Server {server_id}")

            if len(allowed_servers) > 3:
                server_names.append(f"... and {len(allowed_servers) - 3} more")

            server_text = "\n".join([f"• {name}" for name in server_names])
            server_text += f"\n\n🔧 **[Click 'Manage Servers' to change]**"
        else:
            server_text = "All servers\n\n🔧 **[Click 'Manage Servers' to change]**"

        embed.add_field(
            name="🏰 World Boss Servers",
            value=server_text,
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

class CustomNotificationModal(ui.Modal, title="Create Custom Notification"):
    def __init__(self, notification_manager):
        super().__init__()
        self.notification_manager = notification_manager
    
    title_input = ui.TextInput(
        label="Notification Title",
        placeholder="Enter a title for your notification...",
        max_length=100
    )
    
    message_input = ui.TextInput(
        label="Message",
        placeholder="Enter your notification message...",
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    
    time_input = ui.TextInput(
        label="Time (minutes from now)",
        placeholder="Enter minutes from now (e.g., 30 for 30 minutes)",
        max_length=10
    )
    
    recurring_input = ui.TextInput(
        label="Recurring? (optional)",
        placeholder="Enter interval in minutes for recurring (leave empty for one-time)",
        required=False,
        max_length=10
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Parse time
            minutes = int(self.time_input.value)
            if minutes <= 0:
                await interaction.response.send_message("⚠️ Time must be a positive number!", ephemeral=True)
                return
            
            scheduled_time = time.time() + (minutes * 60)
            
            # Parse recurring
            is_recurring = False
            recurring_interval = 0
            if self.recurring_input.value.strip():
                recurring_interval = int(self.recurring_input.value) * 60  # Convert to seconds
                is_recurring = True
            
            # Add notification
            notification_id = await self.notification_manager.add_notification(
                user_id=interaction.user.id,
                notification_type="custom",
                title=self.title_input.value,
                message=self.message_input.value,
                scheduled_time=scheduled_time,
                is_recurring=is_recurring,
                recurring_interval=recurring_interval
            )
            
            if notification_id > 0:
                scheduled_dt = datetime.fromtimestamp(scheduled_time)
                embed = discord.Embed(
                    title="✅ Notification Created!",
                    description=f"**{self.title_input.value}**\n\n{self.message_input.value}",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="⏰ Scheduled Time",
                    value=scheduled_dt.strftime("%B %d, %Y at %H:%M UTC"),
                    inline=False
                )
                if is_recurring:
                    embed.add_field(
                        name="🔄 Recurring",
                        value=f"Every {recurring_interval // 60} minutes",
                        inline=False
                    )
                embed.set_footer(text=f"Notification ID: {notification_id}")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Failed to create notification!", ephemeral=True)
                
        except ValueError:
            await interaction.response.send_message("⚠️ Please enter valid numbers for time and recurring interval!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error creating notification: {str(e)}", ephemeral=True)

class CancelNotificationModal(ui.Modal, title="Cancel Notification"):
    def __init__(self, notification_manager):
        super().__init__()
        self.notification_manager = notification_manager
    
    notification_id = ui.TextInput(
        label="Notification ID",
        placeholder="Enter the ID of the notification to cancel...",
        max_length=10
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            notif_id = int(self.notification_id.value)
            
            success = await self.notification_manager.cancel_notification(notif_id, interaction.user.id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Notification Cancelled",
                    description=f"Notification ID `{notif_id}` has been cancelled.",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="❌ Cancellation Failed",
                    description=f"Could not cancel notification ID `{notif_id}`. Make sure the ID is correct and belongs to you.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except ValueError:
            await interaction.response.send_message("⚠️ Please enter a valid notification ID number!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error cancelling notification: {str(e)}", ephemeral=True)

class QuietHoursModal(ui.Modal, title="Set Quiet Hours (UTC Time)"):
    def __init__(self, notification_manager):
        super().__init__()
        self.notification_manager = notification_manager

    start_hour = ui.TextInput(
        label="Start Hour (0-23 UTC)",
        placeholder="Enter start hour for quiet time in UTC (e.g., 22 for 10 PM UTC)",
        max_length=2
    )

    end_hour = ui.TextInput(
        label="End Hour (0-23 UTC)",
        placeholder="Enter end hour for quiet time in UTC (e.g., 8 for 8 AM UTC)",
        max_length=2
    )

    timezone_offset = ui.TextInput(
        label="Your Timezone Offset (for display)",
        placeholder="Enter your UTC offset for time display (e.g., -5 for EST, +1 for CET)",
        required=False,
        max_length=3
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            start = int(self.start_hour.value)
            end = int(self.end_hour.value)

            if not (0 <= start <= 23) or not (0 <= end <= 23):
                await interaction.response.send_message("⚠️ Hours must be between 0 and 23!", ephemeral=True)
                return

            settings_update = {
                'quiet_hours_start': start,
                'quiet_hours_end': end
            }

            if self.timezone_offset.value.strip():
                try:
                    offset = int(self.timezone_offset.value)
                    if -12 <= offset <= 14:  # Valid timezone range
                        settings_update['timezone_offset'] = offset
                    else:
                        await interaction.response.send_message("⚠️ Timezone offset must be between -12 and +14!", ephemeral=True)
                        return
                except ValueError:
                    await interaction.response.send_message("⚠️ Invalid timezone offset format!", ephemeral=True)
                    return

            success = await self.notification_manager.update_user_settings(
                interaction.user.id, settings_update
            )

            if success:
                embed = discord.Embed(
                    title="✅ Quiet Hours Set!",
                    description=f"**Quiet Hours:** {start:02d}:00 - {end:02d}:00\n"
                               f"**Timezone:** UTC{settings_update.get('timezone_offset', 0):+d}\n\n"
                               f"Notifications will be delayed during these hours.",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Failed to set quiet hours!", ephemeral=True)

        except ValueError:
            await interaction.response.send_message("⚠️ Please enter valid hour numbers (0-23)!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting quiet hours: {str(e)}", ephemeral=True)

class WorldBossSettingsView(ui.View):
    def __init__(self, author: discord.User, notification_manager):
        super().__init__(timeout=300)
        self.author = author
        self.notification_manager = notification_manager

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This settings panel doesn't belong to you!", ephemeral=True)
            return False
        return True

    async def get_world_boss_settings_embed(self):
        """Create world boss settings embed"""
        settings = await self.notification_manager.get_user_settings(self.author.id)

        import json
        allowed_servers = json.loads(settings.get('world_boss_servers', '[]'))
        allowed_rarities = json.loads(settings.get('world_boss_rarities', '["common","rare","epic","legendary","ur"]'))

        embed = discord.Embed(
            title="🌍 World Boss Notification Settings",
            description="Configure when and where you want world boss alerts",
            color=discord.Color.red()
        )

        # Server settings
        if allowed_servers:
            server_names = []
            for server_id in allowed_servers[:5]:  # Show max 5
                try:
                    guild = self.notification_manager.bot.get_guild(int(server_id))
                    if guild:
                        server_names.append(guild.name)
                    else:
                        server_names.append(f"Server {server_id}")
                except:
                    server_names.append(f"Server {server_id}")

            if len(allowed_servers) > 5:
                server_names.append(f"... and {len(allowed_servers) - 5} more")

            server_text = "\n".join([f"• {name}" for name in server_names])
        else:
            server_text = "All servers (default)"

        embed.add_field(
            name="🏰 **Allowed Servers**",
            value=server_text,
            inline=False
        )

        # Rarity settings
        rarity_emojis = {
            'common': '⚪',
            'rare': '🔵',
            'epic': '🟣',
            'legendary': '🟡'
        }

        rarity_text = []
        for rarity in ['common', 'rare', 'epic', 'legendary', 'ur']:
            emoji = rarity_emojis.get(rarity, '⚪')
            status = '✅' if rarity in allowed_rarities else '❌'
            rarity_text.append(f"{emoji} {rarity.title()}: {status}")

        embed.add_field(
            name="⭐ **Rarity Filter**",
            value="\n".join(rarity_text),
            inline=True
        )

        # Time settings
        wb_start = settings.get('world_boss_hours_start')
        wb_end = settings.get('world_boss_hours_end')

        if wb_start is not None and wb_end is not None:
            time_text = f"Only between {wb_start:02d}:00 - {wb_end:02d}:00"
        else:
            time_text = "Any time (24/7)"

        embed.add_field(
            name="⏰ **Time Filter**",
            value=time_text,
            inline=True
        )

        embed.set_footer(text="Use the buttons below to configure your world boss alerts")
        return embed

    @ui.button(label="Set Servers", style=discord.ButtonStyle.blurple, emoji="🏰")
    async def set_servers(self, interaction: discord.Interaction, _button: ui.Button):
        modal = ServerSelectionModal(self.notification_manager)
        await interaction.response.send_modal(modal)

    @ui.button(label="Set Rarities", style=discord.ButtonStyle.secondary, emoji="⭐")
    async def set_rarities(self, interaction: discord.Interaction, _button: ui.Button):
        rarity_view = RaritySelectionView(self.author, self.notification_manager)
        embed = await rarity_view.get_rarity_embed()
        await interaction.response.edit_message(embed=embed, view=rarity_view)

    @ui.button(label="Set Time Filter", style=discord.ButtonStyle.green, emoji="⏰")
    async def set_time_filter(self, interaction: discord.Interaction, _button: ui.Button):
        modal = WorldBossTimeModal(self.notification_manager)
        await interaction.response.send_modal(modal)

    @ui.button(label="Reset to Default", style=discord.ButtonStyle.red, emoji="🔄")
    async def reset_to_default(self, interaction: discord.Interaction, _button: ui.Button):
        success = await self.notification_manager.update_user_settings(
            self.author.id, {
                'world_boss_servers': '[]',
                'world_boss_rarities': '["common","rare","epic","legendary"]',
                'world_boss_hours_start': None,
                'world_boss_hours_end': None
            }
        )

        if success:
            embed = await self.get_world_boss_settings_embed()
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send("✅ World boss settings reset to default!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Failed to reset settings!", ephemeral=True)

    @ui.button(label="Back to Settings", style=discord.ButtonStyle.gray, emoji="⬅️")
    async def back_to_settings(self, interaction: discord.Interaction, _button: ui.Button):
        settings_view = SettingsView(self.author, self.notification_manager)
        embed = await settings_view.get_settings_embed()
        await interaction.response.edit_message(embed=embed, view=settings_view)

class ServerSelectionModal(ui.Modal, title="Select Servers for World Boss Alerts"):
    def __init__(self, notification_manager):
        super().__init__()
        self.notification_manager = notification_manager

    server_ids = ui.TextInput(
        label="Server IDs (comma-separated)",
        placeholder="Enter server IDs separated by commas (e.g., 123456789, 987654321)",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=False
    )

    help_text = ui.TextInput(
        label="How to get Server ID:",
        placeholder="Right-click server name → Copy Server ID (Developer Mode must be enabled)",
        style=discord.TextStyle.paragraph,
        max_length=200,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if not self.server_ids.value.strip():
                # Empty means all servers
                success = await self.notification_manager.update_user_settings(
                    interaction.user.id, {'world_boss_servers': '[]'}
                )

                if success:
                    embed = discord.Embed(
                        title="✅ Server Settings Updated!",
                        description="You will now receive world boss alerts from **all servers**.",
                        color=discord.Color.green()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Failed to update settings!", ephemeral=True)
                return

            # Parse server IDs
            server_ids = []
            for server_id in self.server_ids.value.split(','):
                server_id = server_id.strip()
                if server_id.isdigit():
                    server_ids.append(server_id)

            if not server_ids:
                await interaction.response.send_message("⚠️ No valid server IDs found!", ephemeral=True)
                return

            # Validate server IDs (check if bot is in those servers)
            valid_servers = []
            invalid_servers = []

            for server_id in server_ids:
                guild = interaction.client.get_guild(int(server_id))
                if guild:
                    valid_servers.append(server_id)
                else:
                    invalid_servers.append(server_id)

            if not valid_servers:
                await interaction.response.send_message("⚠️ Bot is not in any of the specified servers!", ephemeral=True)
                return

            # Update settings
            import json
            success = await self.notification_manager.update_user_settings(
                interaction.user.id, {'world_boss_servers': json.dumps(valid_servers)}
            )

            if success:
                embed = discord.Embed(
                    title="✅ Server Settings Updated!",
                    color=discord.Color.green()
                )

                if valid_servers:
                    server_names = []
                    for server_id in valid_servers:
                        guild = interaction.client.get_guild(int(server_id))
                        server_names.append(guild.name if guild else f"Server {server_id}")

                    embed.add_field(
                        name="✅ Valid Servers",
                        value="\n".join([f"• {name}" for name in server_names]),
                        inline=False
                    )

                if invalid_servers:
                    embed.add_field(
                        name="❌ Invalid Servers",
                        value=f"Bot is not in: {', '.join(invalid_servers)}",
                        inline=False
                    )

                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Failed to update settings!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error updating servers: {str(e)}", ephemeral=True)

class RaritySelectionView(ui.View):
    def __init__(self, author: discord.User, notification_manager):
        super().__init__(timeout=300)
        self.author = author
        self.notification_manager = notification_manager

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This panel doesn't belong to you!", ephemeral=True)
            return False
        return True

    async def get_rarity_embed(self):
        """Create rarity selection embed"""
        settings = await self.notification_manager.get_user_settings(self.author.id)

        import json
        allowed_rarities = json.loads(settings.get('world_boss_rarities', '["common","rare","epic","legendary","ur"]'))

        embed = discord.Embed(
            title="⭐ World Boss Rarity Filter",
            description="Choose which rarities you want to be notified about",
            color=discord.Color.purple()
        )

        rarity_info = {
            'common': {'emoji': '⚪', 'desc': 'Most frequent spawns'},
            'rare': {'emoji': '🔵', 'desc': 'Moderate rewards'},
            'epic': {'emoji': '🟣', 'desc': 'Good rewards'},
            'legendary': {'emoji': '🟡', 'desc': 'Best rewards, very rare'},
            'ur': {'emoji': '💎', 'desc': 'Ultimate rewards, extremely rare'}
        }

        for rarity in ['common', 'rare', 'epic', 'legendary', 'ur']:
            info = rarity_info[rarity]
            status = '✅ ON' if rarity in allowed_rarities else '❌ OFF'

            embed.add_field(
                name=f"{info['emoji']} {rarity.title()} {status}",
                value=info['desc'],
                inline=True
            )

        embed.set_footer(text="Click the buttons below to toggle rarities on/off")
        return embed

    async def toggle_rarity(self, interaction: discord.Interaction, rarity: str):
        """Toggle a specific rarity on/off"""
        settings = await self.notification_manager.get_user_settings(self.author.id)

        import json
        allowed_rarities = json.loads(settings.get('world_boss_rarities', '["common","rare","epic","legendary","ur"]'))

        if rarity in allowed_rarities:
            allowed_rarities.remove(rarity)
            action = "disabled"
        else:
            allowed_rarities.append(rarity)
            action = "enabled"

        # Ensure at least one rarity is selected
        if not allowed_rarities:
            await interaction.response.send_message("⚠️ You must have at least one rarity enabled!", ephemeral=True)
            return

        success = await self.notification_manager.update_user_settings(
            self.author.id, {'world_boss_rarities': json.dumps(allowed_rarities)}
        )

        if success:
            embed = await self.get_rarity_embed()
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"✅ {rarity.title()} notifications {action}!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Failed to update settings!", ephemeral=True)

    @ui.button(label="Common", style=discord.ButtonStyle.secondary, emoji="⚪")
    async def toggle_common(self, interaction: discord.Interaction, _button: ui.Button):
        await self.toggle_rarity(interaction, 'common')

    @ui.button(label="Rare", style=discord.ButtonStyle.primary, emoji="🔵")
    async def toggle_rare(self, interaction: discord.Interaction, _button: ui.Button):
        await self.toggle_rarity(interaction, 'rare')

    @ui.button(label="Epic", style=discord.ButtonStyle.secondary, emoji="🟣")
    async def toggle_epic(self, interaction: discord.Interaction, _button: ui.Button):
        await self.toggle_rarity(interaction, 'epic')

    @ui.button(label="Legendary", style=discord.ButtonStyle.secondary, emoji="🟡")
    async def toggle_legendary(self, interaction: discord.Interaction, _button: ui.Button):
        await self.toggle_rarity(interaction, 'legendary')

    @ui.button(label="UR", style=discord.ButtonStyle.secondary, emoji="💎")
    async def toggle_ur(self, interaction: discord.Interaction, _button: ui.Button):
        await self.toggle_rarity(interaction, 'ur')

    @ui.button(label="Back", style=discord.ButtonStyle.gray, emoji="⬅️", row=1)
    async def back_to_world_boss_settings(self, interaction: discord.Interaction, _button: ui.Button):
        world_boss_view = WorldBossSettingsView(self.author, self.notification_manager)
        embed = await world_boss_view.get_world_boss_settings_embed()
        await interaction.response.edit_message(embed=embed, view=world_boss_view)

class WorldBossTimeModal(ui.Modal, title="Set World Boss Time Filter (UTC)"):
    def __init__(self, notification_manager):
        super().__init__()
        self.notification_manager = notification_manager

    start_hour = ui.TextInput(
        label="Start Hour (0-23 UTC, optional)",
        placeholder="Enter start hour for world boss alerts in UTC (e.g., 8 for 8 AM UTC)",
        required=False,
        max_length=2
    )

    end_hour = ui.TextInput(
        label="End Hour (0-23 UTC, optional)",
        placeholder="Enter end hour for world boss alerts in UTC (e.g., 22 for 10 PM UTC)",
        required=False,
        max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            settings_update = {}

            # Handle empty inputs (disable time filter)
            if not self.start_hour.value.strip() and not self.end_hour.value.strip():
                settings_update['world_boss_hours_start'] = None
                settings_update['world_boss_hours_end'] = None

                success = await self.notification_manager.update_user_settings(
                    interaction.user.id, settings_update
                )

                if success:
                    embed = discord.Embed(
                        title="✅ Time Filter Disabled!",
                        description="You will now receive world boss alerts **24/7**.",
                        color=discord.Color.green()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Failed to update settings!", ephemeral=True)
                return

            # Validate both hours are provided
            if not self.start_hour.value.strip() or not self.end_hour.value.strip():
                await interaction.response.send_message("⚠️ Please provide both start and end hours, or leave both empty to disable!", ephemeral=True)
                return

            start = int(self.start_hour.value)
            end = int(self.end_hour.value)

            if not (0 <= start <= 23) or not (0 <= end <= 23):
                await interaction.response.send_message("⚠️ Hours must be between 0 and 23!", ephemeral=True)
                return

            settings_update['world_boss_hours_start'] = start
            settings_update['world_boss_hours_end'] = end

            success = await self.notification_manager.update_user_settings(
                interaction.user.id, settings_update
            )

            if success:
                embed = discord.Embed(
                    title="✅ Time Filter Set!",
                    description=f"You will only receive world boss alerts between **{start:02d}:00 - {end:02d}:00 UTC**.",
                    color=discord.Color.green()
                )
                embed.set_footer(text="Time filter uses UTC time for consistency across all servers")
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Failed to set time filter!", ephemeral=True)

        except ValueError:
            await interaction.response.send_message("⚠️ Please enter valid hour numbers (0-23)!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting time filter: {str(e)}", ephemeral=True)

class ChannelSetupModal(ui.Modal, title="Set Channel Notifications"):
    def __init__(self, notification_manager):
        super().__init__()
        self.notification_manager = notification_manager

    channel_id = ui.TextInput(
        label="Channel ID (optional)",
        placeholder="Right-click channel → Copy Channel ID (leave empty to disable)",
        required=False,
        max_length=20
    )

    enable_channel = ui.TextInput(
        label="Enable Channel Notifications? (yes/no)",
        placeholder="Type 'yes' to enable or 'no' to disable channel notifications",
        max_length=3
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            enable = self.enable_channel.value.lower().strip() in ['yes', 'y', '1', 'true', 'on']

            settings_update = {
                'channel_notifications': 1 if enable else 0
            }

            # Handle channel ID
            if self.channel_id.value.strip():
                try:
                    channel_id = int(self.channel_id.value.strip())

                    # Validate channel exists and bot can access it
                    channel = interaction.client.get_channel(channel_id)
                    if not channel:
                        await interaction.response.send_message("⚠️ Channel not found or bot doesn't have access!", ephemeral=True)
                        return

                    # Check if bot can send messages in the channel
                    if not channel.permissions_for(channel.guild.me).send_messages:
                        await interaction.response.send_message("⚠️ Bot doesn't have permission to send messages in that channel!", ephemeral=True)
                        return

                    settings_update['preferred_channel'] = channel_id

                except ValueError:
                    await interaction.response.send_message("⚠️ Invalid channel ID format!", ephemeral=True)
                    return
            elif not enable:
                # If disabling channel notifications, clear the channel
                settings_update['preferred_channel'] = None

            success = await self.notification_manager.update_user_settings(
                interaction.user.id, settings_update
            )

            if success:
                embed = discord.Embed(
                    title="✅ Channel Settings Updated!",
                    color=discord.Color.green()
                )

                if enable:
                    if 'preferred_channel' in settings_update:
                        channel = interaction.client.get_channel(settings_update['preferred_channel'])
                        embed.description = f"Channel notifications **enabled** for {channel.mention}"
                    else:
                        embed.description = "Channel notifications **enabled** (no specific channel set)"
                else:
                    embed.description = "Channel notifications **disabled**"

                embed.add_field(
                    name="ℹ️ How it works:",
                    value="• **DM First**: Bot tries to send DM first\n"
                          "• **Channel Fallback**: If DM fails, uses channel\n"
                          "• **World Boss**: Channel notifications auto-delete after 30s to avoid spam",
                    inline=False
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Failed to update channel settings!", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error setting up channel: {str(e)}", ephemeral=True)

class EasyServerSelectionView(ui.View):
    def __init__(self, author: discord.User, notification_manager):
        super().__init__(timeout=300)
        self.author = author
        self.notification_manager = notification_manager
        self.current_page = 0
        self.servers_per_page = 10

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("This server panel doesn't belong to you!", ephemeral=True)
            return False
        return True

    async def get_user_servers(self):
        """Get all servers the user is in that the bot is also in (player-specific only)"""
        user_servers = []
        if self.notification_manager.bot:
            for guild in self.notification_manager.bot.guilds:
                # Only include servers where THIS USER is a member
                member = guild.get_member(self.author.id)
                if member:  # User must be in the server to see it
                    user_servers.append({
                        'id': str(guild.id),
                        'name': guild.name,
                        'member_count': guild.member_count
                    })
        return sorted(user_servers, key=lambda x: x['name'])

    async def get_server_selection_embed(self):
        """Create server selection embed with toggle buttons"""
        settings = await self.notification_manager.get_user_settings(self.author.id)

        import json
        allowed_servers = json.loads(settings.get('world_boss_servers', '[]'))
        user_servers = await self.get_user_servers()

        embed = discord.Embed(
            title="🏰 World Boss Server Selection",
            description="Choose which servers **you're in** to get world boss notifications from\n*(Only shows servers where you're a member)*",
            color=discord.Color.blue()
        )

        if not user_servers:
            embed.add_field(
                name="❌ No Servers Found",
                value="You're not in any servers that this bot is also in.",
                inline=False
            )
            return embed

        # Calculate pagination
        start_idx = self.current_page * self.servers_per_page
        end_idx = start_idx + self.servers_per_page
        page_servers = user_servers[start_idx:end_idx]

        # Show current selection status
        if not allowed_servers:
            status_text = "**Current:** All servers (default)"
        else:
            enabled_count = len(allowed_servers)
            total_count = len(user_servers)
            status_text = f"**Current:** {enabled_count}/{total_count} servers selected"

        embed.add_field(
            name="📊 Status",
            value=status_text,
            inline=False
        )

        # Show servers on current page
        server_list = []
        for server in page_servers:
            is_enabled = not allowed_servers or server['id'] in allowed_servers
            status_emoji = "✅" if is_enabled else "❌"
            server_list.append(f"{status_emoji} **{server['name']}** ({server['member_count']} members)")

        if server_list:
            embed.add_field(
                name=f"🏰 Servers (Page {self.current_page + 1}/{(len(user_servers) - 1) // self.servers_per_page + 1})",
                value="\n".join(server_list),
                inline=False
            )

        embed.add_field(
            name="💡 How it works:",
            value="• **Green ✅** = You'll get notifications from this server\n"
                  "• **Red ❌** = No notifications from this server\n"
                  "• **All servers** = Get notifications from every server you're in",
            inline=False
        )

        embed.set_footer(text="Click the buttons below to toggle servers on/off")

        # Clear existing buttons and add new ones
        self.clear_items()
        await self.add_server_buttons(page_servers, allowed_servers)

        return embed

    async def add_server_buttons(self, page_servers, allowed_servers):
        """Add toggle buttons for servers on current page"""
        for i, server in enumerate(page_servers):
            is_enabled = not allowed_servers or server['id'] in allowed_servers

            # Truncate server name if too long
            button_label = server['name']
            if len(button_label) > 20:
                button_label = button_label[:17] + "..."

            style = discord.ButtonStyle.green if is_enabled else discord.ButtonStyle.red
            emoji = "✅" if is_enabled else "❌"

            button = ui.Button(
                label=button_label,
                style=style,
                emoji=emoji,
                custom_id=f"toggle_{server['id']}",
                row=i // 5  # 5 buttons per row
            )
            button.callback = self.create_toggle_callback(server)
            self.add_item(button)

        # Add control buttons
        control_row = (len(page_servers) - 1) // 5 + 1

        # Previous page button
        if self.current_page > 0:
            prev_button = ui.Button(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=control_row)
            prev_button.callback = self.previous_page
            self.add_item(prev_button)

        # Next page button
        user_servers = await self.get_user_servers()
        if (self.current_page + 1) * self.servers_per_page < len(user_servers):
            next_button = ui.Button(label="Next ▶️", style=discord.ButtonStyle.secondary, row=control_row)
            next_button.callback = self.next_page
            self.add_item(next_button)

        # All servers button
        all_button = ui.Button(label="Enable All", style=discord.ButtonStyle.blurple, emoji="🌍", row=control_row)
        all_button.callback = self.enable_all_servers
        self.add_item(all_button)

        # Back button
        back_button = ui.Button(label="Back", style=discord.ButtonStyle.gray, emoji="⬅️", row=control_row)
        back_button.callback = self.back_to_main
        self.add_item(back_button)

    def create_toggle_callback(self, server):
        async def toggle_callback(interaction):
            await self.toggle_server(interaction, server)
        return toggle_callback

    async def toggle_server(self, interaction: discord.Interaction, server: dict):
        """Toggle a specific server on/off"""
        settings = await self.notification_manager.get_user_settings(self.author.id)

        import json
        allowed_servers = json.loads(settings.get('world_boss_servers', '[]'))

        if not allowed_servers:
            # Currently "all servers", switch to specific selection
            user_servers = await self.get_user_servers()
            allowed_servers = [s['id'] for s in user_servers]  # Start with all enabled

        if server['id'] in allowed_servers:
            allowed_servers.remove(server['id'])
            action = "disabled"
        else:
            allowed_servers.append(server['id'])
            action = "enabled"

        # Update settings
        success = await self.notification_manager.update_user_settings(
            self.author.id, {'world_boss_servers': json.dumps(allowed_servers)}
        )

        if success:
            embed = await self.get_server_selection_embed()
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"✅ **{server['name']}** notifications {action}!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Failed to update server settings!", ephemeral=True)

    async def enable_all_servers(self, interaction: discord.Interaction):
        """Enable notifications for all servers"""
        success = await self.notification_manager.update_user_settings(
            self.author.id, {'world_boss_servers': '[]'}  # Empty array = all servers
        )

        if success:
            embed = await self.get_server_selection_embed()
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send("✅ Enabled notifications for **all servers**!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Failed to update server settings!", ephemeral=True)

    async def previous_page(self, interaction: discord.Interaction):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.get_server_selection_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def next_page(self, interaction: discord.Interaction):
        """Go to next page"""
        user_servers = await self.get_user_servers()
        if (self.current_page + 1) * self.servers_per_page < len(user_servers):
            self.current_page += 1
            embed = await self.get_server_selection_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    async def back_to_main(self, interaction: discord.Interaction):
        """Go back to main notifications view"""
        main_view = NotificationView(self.author, self.notification_manager)
        embed = await main_view.get_main_embed()
        await interaction.response.edit_message(embed=embed, view=main_view)

class NotificationsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notification_manager = get_notification_manager(bot)
    
    @commands.command(name="notifications", aliases=["notify", "alerts", "reminders"], 
                     help="Manage your personal notifications and alerts")
    async def notifications(self, ctx: commands.Context):
        """Main notifications command"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="Profile Not Found",
                description="You haven't started the bot yet. Use `sl start` to get started!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # Initialize notification manager if needed
        if not hasattr(self.notification_manager, 'bot') or self.notification_manager.bot is None:
            self.notification_manager.bot = self.bot
            await self.notification_manager.initialize()
        
        # Create interactive view
        view = NotificationView(ctx.author, self.notification_manager)
        embed = await view.get_main_embed()
        
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @commands.command(name="timezone", aliases=["tz"],
                     help="Set your timezone for notification display")
    async def set_timezone(self, ctx: commands.Context, offset: int = None):
        """Set your timezone offset for display purposes"""
        if offset is None:
            # Show current timezone
            settings = await self.notification_manager.get_user_settings(ctx.author.id)
            current_offset = settings.get('timezone_offset', 0)

            embed = discord.Embed(
                title="🌍 Your Current Timezone",
                color=discord.Color.blue()
            )

            if current_offset == 0:
                embed.description = "**UTC+0** (Not set - using UTC)"
            else:
                embed.description = f"**UTC{current_offset:+d}**"

            embed.add_field(
                name="📝 How to set:",
                value=f"`{ctx.prefix}timezone <offset>`\n\n"
                      "**Examples:**\n"
                      "• `{ctx.prefix}timezone -5` (EST)\n"
                      "• `{ctx.prefix}timezone -8` (PST)\n"
                      "• `{ctx.prefix}timezone +1` (CET)\n"
                      "• `{ctx.prefix}timezone +9` (JST)",
                inline=False
            )

            embed.set_footer(text="This only affects display times. All resets and filters still use UTC.")
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Validate offset
        if not -12 <= offset <= 14:
            embed = discord.Embed(
                title="⚠️ Invalid Timezone",
                description="Timezone offset must be between -12 and +14 hours.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Update timezone
        success = await self.notification_manager.update_user_settings(
            ctx.author.id, {'timezone_offset': offset}
        )

        if success:
            embed = discord.Embed(
                title="✅ Timezone Updated!",
                description=f"Your timezone is now set to **UTC{offset:+d}**",
                color=discord.Color.green()
            )

            embed.add_field(
                name="📊 What this affects:",
                value="• Cooldown ready times display\n"
                      "• Notification time displays\n"
                      "• Time-related UI elements",
                inline=False
            )

            embed.add_field(
                name="⚠️ What stays UTC:",
                value="• Daily resets\n"
                      "• Quiet hours filtering\n"
                      "• World boss time filtering\n"
                      "• All game mechanics",
                inline=False
            )

            await ctx.reply(embed=embed, mention_author=False)
        else:
            embed = discord.Embed(
                title="❌ Failed to Update",
                description="Could not update your timezone. Please try again.",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(NotificationsCog(bot))
