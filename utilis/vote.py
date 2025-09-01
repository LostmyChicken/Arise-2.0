import asyncio
import json
import os
import time
import discord

REMINDER_FILE = "vote_reminders.json"

class VoteReminderManager:
    def __init__(self, bot):
        self.bot = bot
        self.reminders = {}  # user_id: (platform, timestamp)
        self.load_reminders()

    def load_reminders(self):
        if os.path.exists(REMINDER_FILE):
            try:
                with open(REMINDER_FILE, "r") as f:
                    data = json.load(f)
                    now = time.time()
                    for user_id, (platform, timestamp) in data.items():
                        remaining = 43200 - (now - timestamp)
                        if remaining > 0:
                            self.reminders[int(user_id)] = (platform, timestamp)
                            asyncio.create_task(self._schedule(int(user_id), remaining))
            except Exception as e:
                print(f"Error loading reminders: {e}")

    def save_reminders(self):
        try:
            with open(REMINDER_FILE, "w") as f:
                json.dump(self.reminders, f)
        except Exception as e:
            print(f"Error saving reminders: {e}")

    async def add_reminder(self, user_id: int, platform: str):
        if user_id in self.reminders:
            return
        now = time.time()
        self.reminders[user_id] = (platform, now)
        self.save_reminders()
        asyncio.create_task(self._schedule(user_id, 43200))

    async def _schedule(self, user_id: int, delay: float = 43200):
        await asyncio.sleep(delay)
        platform, _ = self.reminders.pop(user_id, (None, None))
        self.save_reminders()

        if platform:
            for guild in self.bot.guilds:
                try:
                    user = await guild.fetch_member(user_id)
                    if user:
                        await self._send_reminder(user, platform)
                        break
                except discord.NotFound:
                    continue
                except discord.HTTPException:
                    continue

    async def _send_reminder(self, user, platform):
        try:
            if platform == "dbl":
                embed = discord.Embed(title="Voting Reminder")
                embed.description = "🔔 You can now vote again on [Discord Bot List](https://discordbotlist.com/bots/arise/upvote)"
                await user.send(embed=embed)
            elif platform == "topgg":
                embed = discord.Embed(title="Voting Reminder")
                embed.description = "🔔 You can now vote again on [Top.gg](https://top.gg/bot/1231157738629890118/vote)"
                await user.send(embed=embed)
        except discord.Forbidden:
            pass  # User has DMs off
