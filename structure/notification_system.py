import asyncio
import json
import time
import logging
import aiosqlite
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import discord
from discord.ext import tasks

DATABASE_PATH = "new_player.db"

class NotificationManager:
    """Manages custom notifications for players"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_notifications: Dict[int, List[dict]] = {}  # user_id -> [notifications]
        self.scheduled_tasks: Dict[int, asyncio.Task] = {}  # notification_id -> task
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize the notification system"""
        try:
            await self.load_active_notifications()
            self.notification_loop.start()
            self.logger.info("✅ Notification system initialized")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize notification system: {e}")
    
    async def load_active_notifications(self):
        """Load active notifications from database and schedule them"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute("""
                    SELECT * FROM notifications
                    WHERE is_active = 1 AND scheduled_time > ?
                    ORDER BY scheduled_time ASC
                """, (time.time(),))

                notifications = await cursor.fetchall()

                for notification in notifications:
                    await self.schedule_notification(dict(notification))
                    
                self.logger.info(f"Loaded {len(notifications)} active notifications")
        except Exception as e:
            self.logger.error(f"Error loading notifications: {e}")
    
    async def schedule_notification(self, notification_data: dict):
        """Schedule a notification for delivery"""
        notification_id = notification_data['id']
        user_id = notification_data['user_id']
        scheduled_time = notification_data['scheduled_time']
        
        # Calculate delay
        delay = scheduled_time - time.time()
        if delay <= 0:
            # Notification is overdue, send immediately
            await self.deliver_notification(notification_data)
            return
        
        # Schedule the notification
        task = asyncio.create_task(self._schedule_delivery(notification_data, delay))
        self.scheduled_tasks[notification_id] = task
        
        # Add to active notifications
        if user_id not in self.active_notifications:
            self.active_notifications[user_id] = []
        self.active_notifications[user_id].append(notification_data)
    
    async def _schedule_delivery(self, notification_data: dict, delay: float):
        """Internal method to handle scheduled delivery"""
        try:
            await asyncio.sleep(delay)
            await self.deliver_notification(notification_data)
        except asyncio.CancelledError:
            pass  # Task was cancelled
        except Exception as e:
            self.logger.error(f"Error in scheduled delivery: {e}")
    
    async def deliver_notification(self, notification_data: dict):
        """Deliver a notification to the user"""
        try:
            user_id = notification_data['user_id']
            notification_id = notification_data['id']
            
            # Get user settings
            settings = await self.get_user_settings(user_id)
            
            # Check quiet hours
            if await self.is_quiet_hours(settings):
                # Reschedule for after quiet hours
                await self.reschedule_after_quiet_hours(notification_data, settings)
                return
            
            # Get user
            user = self.bot.get_user(user_id)
            if not user:
                try:
                    user = await self.bot.fetch_user(user_id)
                except discord.NotFound:
                    await self.mark_notification_failed(notification_id)
                    return
            
            # Create embed
            embed = self.create_notification_embed(notification_data)
            
            # Deliver based on settings
            if settings.get('dm_notifications', 1):
                try:
                    await user.send(embed=embed)
                except discord.Forbidden:
                    # Try channel notification if DM fails
                    if settings.get('channel_notifications', 0):
                        await self.send_channel_notification(user_id, embed, settings)
            elif settings.get('channel_notifications', 0):
                await self.send_channel_notification(user_id, embed, settings)
            
            # Handle recurring notifications
            if notification_data['is_recurring']:
                await self.schedule_recurring_notification(notification_data)
            else:
                await self.mark_notification_delivered(notification_id)
            
            # Remove from active notifications
            if user_id in self.active_notifications:
                self.active_notifications[user_id] = [
                    n for n in self.active_notifications[user_id] 
                    if n['id'] != notification_id
                ]
            
            # Remove scheduled task
            if notification_id in self.scheduled_tasks:
                del self.scheduled_tasks[notification_id]
                
        except Exception as e:
            self.logger.error(f"Error delivering notification {notification_data.get('id')}: {e}")
    
    def create_notification_embed(self, notification_data: dict) -> discord.Embed:
        """Create an embed for the notification"""
        notification_type = notification_data['notification_type']
        title = notification_data['title']
        message = notification_data['message']
        
        # Color based on notification type
        color_map = {
            'cooldown': discord.Color.blue(),
            'world_boss': discord.Color.red(),
            'daily_reminder': discord.Color.green(),
            'custom': discord.Color.purple(),
            'event': discord.Color.orange()
        }
        
        color = color_map.get(notification_type, discord.Color.blue())
        
        embed = discord.Embed(
            title=f"🔔 {title}",
            description=message,
            color=color,
            timestamp=datetime.utcnow()
        )
        
        # Add type-specific information
        if notification_type == 'cooldown':
            embed.set_footer(text="⏰ Cooldown Alert • Solo Leveling Bot")
        elif notification_type == 'world_boss':
            embed.set_footer(text="⚔️ World Boss Alert • Solo Leveling Bot")
        elif notification_type == 'daily_reminder':
            embed.set_footer(text="📅 Daily Reminder • Solo Leveling Bot")
        elif notification_type == 'custom':
            embed.set_footer(text="📝 Custom Alert • Solo Leveling Bot")
        else:
            embed.set_footer(text="🔔 Notification • Solo Leveling Bot")
        
        return embed
    
    async def send_channel_notification(self, user_id: int, embed: discord.Embed, settings: dict, ephemeral: bool = False):
        """Send notification to a channel (ephemeral for world boss to avoid spam)"""
        try:
            channel_id = settings.get('preferred_channel')
            if not channel_id:
                return

            channel = self.bot.get_channel(channel_id)
            if not channel:
                return

            user = self.bot.get_user(user_id)
            if user:
                if ephemeral:
                    # For world boss notifications, send as ephemeral to avoid spam
                    # This requires interaction context, so we'll use a different approach
                    # Send a brief message that auto-deletes
                    message = await channel.send(f"{user.mention} - World Boss Alert (auto-deleting in 30s)", embed=embed)
                    # Delete after 30 seconds to avoid channel spam
                    await asyncio.sleep(30)
                    try:
                        await message.delete()
                    except:
                        pass  # Message might already be deleted
                else:
                    await channel.send(f"{user.mention}", embed=embed)
        except Exception as e:
            self.logger.error(f"Error sending channel notification: {e}")
    
    async def get_user_settings(self, user_id: int) -> dict:
        """Get user notification settings"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute("""
                    SELECT * FROM notification_settings WHERE user_id = ?
                """, (user_id,))

                row = await cursor.fetchone()
                if row:
                    return dict(row)
                else:
                    # Create default settings
                    await self.create_default_settings(user_id)
                    return {
                        'user_id': user_id,
                        'cooldown_alerts': 1,
                        'world_boss_alerts': 1,
                        'daily_reminders': 0,
                        'custom_alerts': 1,
                        'dm_notifications': 1,
                        'channel_notifications': 0,
                        'preferred_channel': None,
                        'notification_sound': 1,
                        'quiet_hours_start': None,
                        'quiet_hours_end': None,
                        'timezone_offset': 0,
                        'settings_data': '{}'
                    }
        except Exception as e:
            self.logger.error(f"Error getting user settings: {e}")
            return {}
    
    async def create_default_settings(self, user_id: int):
        """Create default notification settings for a user"""
        try:
            # Set your main server as default for world boss notifications
            main_server_id = "1396927787213918309"  # Your main server
            default_servers = f'["{main_server_id}"]'

            # Check if user is in the main server, if not, find their first server
            if self.bot:
                main_guild = self.bot.get_guild(int(main_server_id))
                if not main_guild or not main_guild.get_member(user_id):
                    # User not in main server, find their first server
                    for guild in self.bot.guilds:
                        member = guild.get_member(user_id)
                        if member:
                            default_servers = f'["{guild.id}"]'
                            break
                    else:
                        default_servers = '[]'  # User not in any server

            async with aiosqlite.connect(DATABASE_PATH) as conn:
                await conn.execute("""
                    INSERT OR IGNORE INTO notification_settings
                    (user_id, world_boss_servers) VALUES (?, ?)
                """, (user_id, default_servers))
                await conn.commit()
        except Exception as e:
            self.logger.error(f"Error creating default settings: {e}")
    
    async def is_quiet_hours(self, settings: dict) -> bool:
        """Check if current time is within user's quiet hours (UTC time)"""
        try:
            start_hour = settings.get('quiet_hours_start')
            end_hour = settings.get('quiet_hours_end')

            if start_hour is None or end_hour is None:
                return False

            # Use UTC time for quiet hours (no timezone conversion)
            current_hour = datetime.utcnow().hour

            # Handle quiet hours that span midnight
            if start_hour <= end_hour:
                return start_hour <= current_hour < end_hour
            else:
                return current_hour >= start_hour or current_hour < end_hour
                
        except Exception as e:
            self.logger.error(f"Error checking quiet hours: {e}")
            return False
    
    async def reschedule_after_quiet_hours(self, notification_data: dict, settings: dict):
        """Reschedule notification after quiet hours end"""
        try:
            end_hour = settings.get('quiet_hours_end', 8)  # Default to 8 AM
            timezone_offset = settings.get('timezone_offset', 0)
            
            # Calculate next delivery time (after quiet hours end)
            now = datetime.utcnow()
            next_delivery = now.replace(hour=(end_hour - timezone_offset) % 24, minute=0, second=0, microsecond=0)
            
            if next_delivery <= now:
                next_delivery += timedelta(days=1)
            
            # Update notification in database
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                await conn.execute("""
                    UPDATE notifications SET scheduled_time = ? WHERE id = ?
                """, (next_delivery.timestamp(), notification_data['id']))
                await conn.commit()
            
            # Reschedule
            notification_data['scheduled_time'] = next_delivery.timestamp()
            await self.schedule_notification(notification_data)
            
        except Exception as e:
            self.logger.error(f"Error rescheduling notification: {e}")
    
    @tasks.loop(minutes=5)
    async def notification_loop(self):
        """Background loop to check for notifications"""
        try:
            # Clean up completed tasks
            completed_tasks = [
                nid for nid, task in self.scheduled_tasks.items() 
                if task.done()
            ]
            for nid in completed_tasks:
                del self.scheduled_tasks[nid]
            
            # Check for any missed notifications
            current_time = time.time()
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                cursor = await conn.execute("""
                    SELECT * FROM notifications 
                    WHERE is_active = 1 AND scheduled_time <= ? AND scheduled_time > ?
                """, (current_time, current_time - 300))  # Last 5 minutes
                
                missed_notifications = await cursor.fetchall()
                
                for notification in missed_notifications:
                    notification_data = dict(notification)
                    if notification_data['id'] not in self.scheduled_tasks:
                        await self.deliver_notification(notification_data)
                        
        except Exception as e:
            self.logger.error(f"Error in notification loop: {e}")

    async def add_notification(self, user_id: int, notification_type: str, title: str,
                             message: str, scheduled_time: float, is_recurring: bool = False,
                             recurring_interval: int = 0, notification_data: dict = None) -> int:
        """Add a new notification"""
        try:
            if notification_data is None:
                notification_data = {}

            async with aiosqlite.connect(DATABASE_PATH) as conn:
                cursor = await conn.execute("""
                    INSERT INTO notifications
                    (user_id, notification_type, title, message, scheduled_time,
                     created_time, is_recurring, recurring_interval, notification_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, notification_type, title, message, scheduled_time,
                      time.time(), is_recurring, recurring_interval, json.dumps(notification_data)))

                notification_id = cursor.lastrowid
                await conn.commit()

            # Schedule the notification
            new_notification = {
                'id': notification_id,
                'user_id': user_id,
                'notification_type': notification_type,
                'title': title,
                'message': message,
                'scheduled_time': scheduled_time,
                'created_time': time.time(),
                'is_active': 1,
                'is_recurring': is_recurring,
                'recurring_interval': recurring_interval,
                'notification_data': json.dumps(notification_data),
                'delivery_method': 'dm'
            }

            await self.schedule_notification(new_notification)
            return notification_id

        except Exception as e:
            self.logger.error(f"Error adding notification: {e}")
            return -1

    async def cancel_notification(self, notification_id: int, user_id: int) -> bool:
        """Cancel a notification"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                # Verify ownership
                cursor = await conn.execute("""
                    SELECT user_id FROM notifications WHERE id = ?
                """, (notification_id,))

                row = await cursor.fetchone()
                if not row or row[0] != user_id:
                    return False

                # Mark as inactive
                await conn.execute("""
                    UPDATE notifications SET is_active = 0 WHERE id = ?
                """, (notification_id,))
                await conn.commit()

            # Cancel scheduled task
            if notification_id in self.scheduled_tasks:
                self.scheduled_tasks[notification_id].cancel()
                del self.scheduled_tasks[notification_id]

            # Remove from active notifications
            if user_id in self.active_notifications:
                self.active_notifications[user_id] = [
                    n for n in self.active_notifications[user_id]
                    if n['id'] != notification_id
                ]

            return True

        except Exception as e:
            self.logger.error(f"Error cancelling notification: {e}")
            return False

    async def get_user_notifications(self, user_id: int, active_only: bool = True) -> List[dict]:
        """Get all notifications for a user"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                if active_only:
                    cursor = await conn.execute("""
                        SELECT * FROM notifications
                        WHERE user_id = ? AND is_active = 1
                        ORDER BY scheduled_time ASC
                    """, (user_id,))
                else:
                    cursor = await conn.execute("""
                        SELECT * FROM notifications
                        WHERE user_id = ?
                        ORDER BY scheduled_time DESC
                    """, (user_id,))

                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error getting user notifications: {e}")
            return []

    async def update_user_settings(self, user_id: int, settings: dict) -> bool:
        """Update user notification settings"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                # First, ensure the user has a settings record
                await conn.execute("""
                    INSERT OR IGNORE INTO notification_settings (user_id) VALUES (?)
                """, (user_id,))

                # Build update query dynamically
                set_clauses = []
                values = []

                for key, value in settings.items():
                    if key != 'user_id':  # Don't update user_id
                        set_clauses.append(f"{key} = ?")
                        values.append(value)

                if not set_clauses:
                    return False

                values.append(user_id)

                await conn.execute(f"""
                    UPDATE notification_settings
                    SET {', '.join(set_clauses)}
                    WHERE user_id = ?
                """, values)

                await conn.commit()
                return True

        except Exception as e:
            self.logger.error(f"Error updating user settings: {e}")
            return False

    async def schedule_recurring_notification(self, notification_data: dict):
        """Schedule the next occurrence of a recurring notification"""
        try:
            interval = notification_data['recurring_interval']
            next_time = notification_data['scheduled_time'] + interval

            # Create new notification entry
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                await conn.execute("""
                    INSERT INTO notifications
                    (user_id, notification_type, title, message, scheduled_time,
                     created_time, is_recurring, recurring_interval, notification_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (notification_data['user_id'], notification_data['notification_type'],
                      notification_data['title'], notification_data['message'], next_time,
                      time.time(), notification_data['is_recurring'],
                      notification_data['recurring_interval'], notification_data['notification_data']))

                new_id = cursor.lastrowid
                await conn.commit()

            # Schedule the new notification
            new_notification = notification_data.copy()
            new_notification['id'] = new_id
            new_notification['scheduled_time'] = next_time
            new_notification['created_time'] = time.time()

            await self.schedule_notification(new_notification)

        except Exception as e:
            self.logger.error(f"Error scheduling recurring notification: {e}")

    async def mark_notification_delivered(self, notification_id: int):
        """Mark a notification as delivered"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                await conn.execute("""
                    UPDATE notifications SET is_active = 0 WHERE id = ?
                """, (notification_id,))
                await conn.commit()
        except Exception as e:
            self.logger.error(f"Error marking notification delivered: {e}")

    async def mark_notification_failed(self, notification_id: int):
        """Mark a notification as failed"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                await conn.execute("""
                    UPDATE notifications SET is_active = 0 WHERE id = ?
                """, (notification_id,))
                await conn.commit()
        except Exception as e:
            self.logger.error(f"Error marking notification failed: {e}")

    async def cleanup_old_notifications(self, days_old: int = 30):
        """Clean up old notifications"""
        try:
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                await conn.execute("""
                    DELETE FROM notifications
                    WHERE is_active = 0 AND created_time < ?
                """, (cutoff_time,))
                await conn.commit()
        except Exception as e:
            self.logger.error(f"Error cleaning up notifications: {e}")

    # Convenience methods for common notification types
    async def add_cooldown_notification(self, user_id: int, cooldown_name: str, ready_time: float) -> int:
        """Add a cooldown ready notification"""
        return await self.add_notification(
            user_id=user_id,
            notification_type="cooldown",
            title=f"{cooldown_name} Ready!",
            message=f"Your {cooldown_name.lower()} cooldown has finished. You can use the command again!",
            scheduled_time=ready_time
        )

    async def add_daily_reminder(self, user_id: int, reminder_time: float, message: str = None) -> int:
        """Add a daily reminder notification"""
        if message is None:
            message = "Don't forget to claim your daily rewards and complete your activities!"

        return await self.add_notification(
            user_id=user_id,
            notification_type="daily_reminder",
            title="Daily Reminder",
            message=message,
            scheduled_time=reminder_time,
            is_recurring=True,
            recurring_interval=86400  # 24 hours
        )

    async def add_world_boss_notification(self, user_id: int, boss_name: str, guild_name: str, channel_url: str) -> int:
        """Add a world boss spawn notification"""
        return await self.add_notification(
            user_id=user_id,
            notification_type="world_boss",
            title="World Boss Spawned!",
            message=f"**{boss_name}** has appeared in **{guild_name}**!\n\n🔗 **[Join the Battle]({channel_url})**",
            scheduled_time=time.time()  # Immediate notification
        )

# Global notification manager instance
notification_manager = None

def get_notification_manager(bot) -> NotificationManager:
    """Get the global notification manager instance"""
    global notification_manager
    if notification_manager is None:
        notification_manager = NotificationManager(bot)
    return notification_manager
