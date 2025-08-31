import asyncio
from discord import Embed, app_commands
import discord
from discord.ext import commands
from typing import Optional
from datetime import datetime

from structure.glory import Glory

class LogPaginator(discord.ui.View):
    def __init__(self, ctx, pages):
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.pages = pages
        self.current_page = 0
        self.message = None

    async def start(self):
        self.update_buttons()
        self.message = await self.ctx.send(embed=self.pages[self.current_page], view=self)

    def update_buttons(self):
        self.children[0].disabled = self.current_page == 0
        self.children[2].disabled = self.current_page == len(self.pages) - 1

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="⏹️", style=discord.ButtonStyle.danger)
    async def stop_pagination(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        await self.message.delete()
        self.stop()

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
            
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    async def on_timeout(self):
        if self.message:
            for item in self.children:
                item.disabled = True
            await self.message.edit(view=self)


class LogsView(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def _create_empty_embed(self, user):
        embed = Embed(title=f"{user.display_name}'s INBOX")
        embed.set_thumbnail(url="https://ua.stgrm.com/uploads/images/solo-leveling-sticker-pack/solo-leveling-sticker-pack-0.webp")
        embed.description = "*You have nothing to do here. Don't waste your time reading.*"
        return embed
    
    def _format_log_entry(self, log):
        """Format a single log entry with just date and content"""
        try:
            # Parse the timestamp if it exists
            timestamp = datetime.fromisoformat(log.get('timestamp'))
            date_str = timestamp.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            date_str = "Unknown date"
        
        content = log.get('content', 'No content provided')
        return f"**{date_str}**\n{content}\n"
    
    def _create_log_embed(self, user, logs, page, total_pages):
        embed = Embed(title=f"{user.display_name}'s INBOX")
        embed.set_thumbnail(url="https://ua.stgrm.com/uploads/images/solo-leveling-sticker-pack/solo-leveling-sticker-pack-0.webp")
        
        # Add each log entry to the description
        description = ""
        for log in logs:
            description += self._format_log_entry(log) + "\n"
        
        embed.description = description
        embed.set_footer(text=f"Page {page}/{total_pages}")
        return embed
    
    @commands.hybrid_command(name="logs", aliases=["defenselogs", "inbox"], help="View your defense logs or another user's inbox.")
    @app_commands.describe(user="The user whose logs you want to see.")
    async def view_logs(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        """View your defense logs showing only date and content"""
        target_user = user or ctx.author
        glory = await Glory.get(target_user.id)
        
        if not glory or not glory.logs:
            embed = self._create_empty_embed(target_user)
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # Get logs in reverse chronological order (newest first)
        logs = sorted(
            glory.logs,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        items_per_page = 5
        pages = []
        
        if not logs:
            embed = self._create_empty_embed(target_user)
            await ctx.reply(embed=embed, mention_author=False)
            return

        for i in range(0, len(logs), items_per_page):
            page_logs = logs[i:i + items_per_page]
            page_num = (i // items_per_page) + 1
            total_pages = ((len(logs) - 1) // items_per_page) + 1
            pages.append(self._create_log_embed(target_user, page_logs, page_num, total_pages))
        
        if not pages:
             embed = self._create_empty_embed(target_user)
             await ctx.reply(embed=embed, mention_author=False)
             return

        if len(pages) == 1:
            await ctx.send(embed=pages[0])
            return
        
        paginator = LogPaginator(ctx, pages)
        await paginator.start()


async def setup(bot):
    await bot.add_cog(LogsView(bot))