import json
import os
import logging
from typing import Dict, List
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button

from structure.skills import SkillManager
from utilis.utilis import extractId, extractName
from structure.items import ItemManager
from structure.emoji import getClassEmoji, getEmoji
from structure.heroes import HeroManager
from structure.player import Player
import traceback

class GalleryView(View):
    def __init__(self, embed_pages, author):
        super().__init__(timeout=60) # Increased timeout
        self.embed_pages = embed_pages
        self.current_page = 0
        self.author = author
        self.update_buttons()

    def update_buttons(self):
        # Clear existing buttons and add new ones to ensure order
        self.clear_items()
        
        # Previous Button
        prev_button = Button(label="Previous", style=discord.ButtonStyle.secondary, disabled=self.current_page == 0)
        prev_button.callback = self.prev_page
        self.add_item(prev_button)

        # Next Button
        next_button = Button(label="Next", style=discord.ButtonStyle.secondary, disabled=self.current_page >= len(self.embed_pages) - 1)
        next_button.callback = self.next_page
        self.add_item(next_button)

    async def prev_page(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot control this pagination.", ephemeral=True)
            return

        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embed_pages[self.current_page], view=self)

    async def next_page(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot control this pagination.", ephemeral=True)
            return

        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embed_pages[self.current_page], view=self)

class AllGalleryView(View):
    def __init__(self, gallery_data, author):
        super().__init__(timeout=120)
        self.gallery_data = gallery_data  # Dict with all gallery embeds
        self.current_gallery = "hunters"
        self.current_page = 0
        self.author = author
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        
        # Gallery navigation buttons (first row)
        hunters_button = Button(label="Hunters", style=discord.ButtonStyle.primary if self.current_gallery == "hunters" else discord.ButtonStyle.secondary, row=0)
        hunters_button.callback = self.show_hunters
        self.add_item(hunters_button)
        
        weapons_button = Button(label="Weapons", style=discord.ButtonStyle.primary if self.current_gallery == "weapons" else discord.ButtonStyle.secondary, row=0)
        weapons_button.callback = self.show_weapons
        self.add_item(weapons_button)
        
        skills_button = Button(label="Skills", style=discord.ButtonStyle.primary if self.current_gallery == "skills" else discord.ButtonStyle.secondary, row=0)
        skills_button.callback = self.show_skills
        self.add_item(skills_button)
        
        customs_button = Button(label="Customs", style=discord.ButtonStyle.primary if self.current_gallery == "customs" else discord.ButtonStyle.secondary, row=0)
        customs_button.callback = self.show_customs
        self.add_item(customs_button)
        
        # Page navigation buttons (second row)
        current_embeds = self.gallery_data[self.current_gallery]
        if len(current_embeds) > 1:
            prev_button = Button(label="◀ Previous", style=discord.ButtonStyle.secondary, disabled=self.current_page == 0, row=1)
            prev_button.callback = self.prev_page
            self.add_item(prev_button)
            
            next_button = Button(label="Next ▶", style=discord.ButtonStyle.secondary, disabled=self.current_page >= len(current_embeds) - 1, row=1)
            next_button.callback = self.next_page
            self.add_item(next_button)

    async def show_hunters(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot control this gallery.", ephemeral=True)
            return
        self.current_gallery = "hunters"
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.gallery_data[self.current_gallery][self.current_page], view=self)

    async def show_weapons(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot control this gallery.", ephemeral=True)
            return
        self.current_gallery = "weapons"
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.gallery_data[self.current_gallery][self.current_page], view=self)

    async def show_skills(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot control this gallery.", ephemeral=True)
            return
        self.current_gallery = "skills"
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.gallery_data[self.current_gallery][self.current_page], view=self)

    async def show_customs(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot control this gallery.", ephemeral=True)
            return
        self.current_gallery = "customs"
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.gallery_data[self.current_gallery][self.current_page], view=self)

    async def prev_page(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot control this gallery.", ephemeral=True)
            return
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.gallery_data[self.current_gallery][self.current_page], view=self)

    async def next_page(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot control this gallery.", ephemeral=True)
            return
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.gallery_data[self.current_gallery][self.current_page], view=self)

class Gallery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.customs_file = "customs.json"
        
    async def load_customs_data(self) -> List[Dict]:
        if not os.path.exists(self.customs_file):
            return []
        try:
            with open(self.customs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    @commands.hybrid_command(name="gallery", help="View your collection of hunters, weapons, and skills.")
    @app_commands.describe(type="The type of gallery to view (hunters, weapons, skills, customs) - leave empty for all")
    @app_commands.choices(type=[
        app_commands.Choice(name="Hunters", value="hunters"),
        app_commands.Choice(name="Weapons", value="weapons"),
        app_commands.Choice(name="Skills", value="skills"),
        app_commands.Choice(name="Customs", value="customs"),
    ])
    async def gallery(self, ctx: commands.Context, type: str = None):
        player = await Player.get(ctx.author.id)
        if player is None:
            embed = discord.Embed(title="Not Started", description=f"You haven't started yet. Use `sl start`.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        # If no type specified, show unified gallery
        if type is None:
            await self.show_all_galleries(ctx, player)
            return

        if type.lower() == "hunters":
            await self.show_hunter_gallery(ctx, player)
        elif type.lower() == "weapons":
            await self.show_weapon_gallery(ctx, player)
        elif type.lower() == "skills":
            await self.show_skill_gallery(ctx)
        elif type.lower() == "customs":
            await self.show_customs_gallery(ctx)
        else:
            await ctx.send("Invalid gallery type selected.")

    async def show_all_galleries(self, ctx, player):
        """Create unified gallery with all types accessible via buttons"""
        try:
            # Generate all gallery embeds
            gallery_data = {}
            
            # Hunter gallery embeds
            gallery_data["hunters"] = await self.get_hunter_gallery_embeds(player)
            
            # Weapon gallery embeds
            gallery_data["weapons"] = await self.get_weapon_gallery_embeds(player)
            
            # Skills gallery embeds
            gallery_data["skills"] = await self.get_skill_gallery_embeds()
            
            # Customs gallery embeds
            gallery_data["customs"] = await self.get_customs_gallery_embeds()
            
            # Start with hunters gallery
            view = AllGalleryView(gallery_data, ctx.author)
            await ctx.reply(embed=gallery_data["hunters"][0], view=view, mention_author=False)
            
        except Exception as e:
            logging.error(f"Error in show_all_galleries: {e}")
            await ctx.send("An error occurred while loading the galleries.", ephemeral=True)

    async def get_hunter_gallery_embeds(self, player):
        """Generate hunter gallery embeds"""
        owned_hunters = player.get_hunters()
        all_hunters = [h for h in await HeroManager.get_all() if h.rarity != "Custom"]

        if not all_hunters:
            embed = discord.Embed(title="Hunter Gallery", description="No hunters found in the database.", color=discord.Color.orange())
            return [embed]

        # Sort alphabetically by name
        all_hunters.sort(key=lambda h: h.name.lower())

        total_hunters = len(all_hunters)
        owned_count = len([h_id for h_id in owned_hunters if h_id in [h.id for h in all_hunters]])

        return self.create_paginated_embeds(
            items=all_hunters,
            owned_ids=owned_hunters,
            title="🏆 Hunter Gallery",
            header=f"You own **{owned_count}/{total_hunters}** hunters.\nCollect **{total_hunters - owned_count}** more to complete your collection!\n",
            formatter=lambda item, owned: f"`{owned}` {getEmoji(item.id)} {getClassEmoji(item.classType)} • **{item.name}** • `{item.type}`\n",
            footer_text="Use `sl codex hunter <name>` for more details."
        )

    async def get_weapon_gallery_embeds(self, player):
        """Generate weapon gallery embeds"""
        inventory = player.get_inventory()
        all_items = [i for i in await ItemManager.get_all() if i.rarity != "Custom"]
        
        if not all_items:
            embed = discord.Embed(title="Weapon Gallery", description="No weapons found.", color=discord.Color.orange())
            return [embed]

        # Sort alphabetically by name
        all_items.sort(key=lambda i: i.name.lower())

        total_items = len(all_items)
        owned_count = len([i_id for i_id in inventory if i_id in [i.id for i in all_items]])

        return self.create_paginated_embeds(
            items=all_items,
            owned_ids=inventory,
            title="⚔️ Weapon Gallery",
            header=f"You own **{owned_count}/{total_items}** weapons.\nCollect **{total_items - owned_count}** more!\n",
            formatter=lambda item, owned: f"`{owned}` {getattr(item, 'custom_emoji', '') or getEmoji(item.id)} {getClassEmoji(item.classType)} • **{item.name}** • `{extractName(item.type)}`\n",
            footer_text="Use `sl codex weapon <name>` for more details."
        )

    async def get_skill_gallery_embeds(self):
        """Generate skill gallery embeds"""
        all_skills = await SkillManager.get_all()
        if not all_skills:
            embed = discord.Embed(title="Skill Gallery", description="No skills found.", color=discord.Color.orange())
            return [embed]

        # Sort skills alphabetically by name for consistent ordering
        all_skills.sort(key=lambda skill: skill.name.lower())

        return self.create_paginated_embeds(
            items=all_skills,
            owned_ids=None, # Skills don't have ownership in the same way
            title="⚡ Skill Gallery",
            header="Here are all the skills available.\n🌳 **Use `sl skilltree` to learn skills through skill trees**\n📚 **Use `sl learn <skill name>` for direct learning**\n",
            formatter=self.format_skill_entry,
            footer_text="💡 Tip: Use `sl codex skill <name>` for detailed information",
            items_per_page=8
        )

    def format_skill_entry(self, skill, _):
        """Enhanced skill formatting for gallery"""
        # Skill type icons
        type_icons = {
            'Basic': '⚡',
            'QTE': '🎯',
            'Ultimate': '💥'
        }

        # Element icons
        element_icons = {
            'Dark': '🌑',
            'Fire': '🔥',
            'Light': '✨',
            'Water': '💧',
            'Wind': '💨'
        }

        type_icon = type_icons.get(skill.skill_type.value, '⚡')
        element_icon = element_icons.get(skill.element.value, '⚡')

        return (f"`{skill.level:02d}` {type_icon} **{skill.name}** {element_icon}\n"
                f"     📊 **DMG**: {skill.damage}% | **MP**: {skill.mp_cost} | **Type**: {skill.skill_type.value}\n")

    async def get_customs_gallery_embeds(self):
        """Generate customs gallery embeds"""
        customs_data = await self.load_customs_data()
        if not customs_data:
            embed = discord.Embed(title="Customs Gallery", description="No custom purchases found.", color=discord.Color.orange())
            return [embed]

        user_customs = {}
        for purchase in customs_data:
            user_id = purchase.get('user_id', 'Unknown')
            user_customs.setdefault(user_id, []).append(purchase)

        sorted_users = sorted(user_customs.items(), key=lambda x: len(x[1]), reverse=True)
        total_customs = len(customs_data)

        users_per_page = 5
        total_pages = (len(sorted_users) + users_per_page - 1) // users_per_page
        embeds = []

        for i in range(0, len(sorted_users), users_per_page):
            description = f"Total Custom Items Created: `{total_customs}`\n\n"
            page_users = sorted_users[i:i + users_per_page]
            
            for user_id, purchases in page_users:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    user_name = user.name
                except (discord.NotFound, ValueError):
                    user_name = f"Unknown User ({user_id})"
                
                description += f"**{user_name}** ({len(purchases)} custom{'s' if len(purchases) > 1 else ''})\n"
                
                for p in purchases:
                    tier_stars = "★" * p.get('tier', 0) + "☆" * (5 - p.get('tier', 0))
                    description += f"┗ {getEmoji(extractId(p.get('name', '')))} **{p.get('name', 'N/A')}** • `{p.get('element', 'N/A')}` • {tier_stars}\n"
            
            embed = discord.Embed(title="Customs Gallery", description=description, color=discord.Color.purple())
            embed.set_footer(text=f"Page {(i // users_per_page) + 1}/{total_pages}")
            embeds.append(embed)

        return embeds

    async def show_hunter_gallery(self, ctx, player):
        owned_hunters = player.get_hunters()
        all_hunters = [h for h in await HeroManager.get_all() if h.rarity != "Custom"]

        if not all_hunters:
            return await ctx.send(embed=discord.Embed(title="Empty Gallery", description="No hunters found in the database.", color=discord.Color.orange()))

        # Sort alphabetically by name
        all_hunters.sort(key=lambda h: h.name.lower())

        total_hunters = len(all_hunters)
        owned_count = len([h_id for h_id in owned_hunters if h_id in [h.id for h in all_hunters]])
        
        embeds = self.create_paginated_embeds(
            items=all_hunters,
            owned_ids=owned_hunters,
            title="🏆 Hunter Gallery",
            header=f"You own **{owned_count}/{total_hunters}** hunters.\nCollect **{total_hunters - owned_count}** more to complete your collection!\n",
            formatter=lambda item, owned: f"`{owned}` {getattr(item, 'custom_emoji', '') or getEmoji(item.id)} {getClassEmoji(item.classType)} • **{item.name}** • `{item.type}`\n",
            footer_text="Use `sl codex hunter <name>` for more details."
        )
        await ctx.reply(embed=embeds[0], view=GalleryView(embeds, ctx.author), mention_author=False)

    async def show_weapon_gallery(self, ctx, player):
        inventory = player.get_inventory()
        all_items = [i for i in await ItemManager.get_all() if i.rarity != "Custom"]

        if not all_items:
            return await ctx.send(embed=discord.Embed(title="Empty Gallery", description="No weapons found.", color=discord.Color.orange()))

        # Sort alphabetically by name
        all_items.sort(key=lambda i: i.name.lower())

        total_items = len(all_items)
        owned_count = len([i_id for i_id in inventory if i_id in [i.id for i in all_items]])

        embeds = self.create_paginated_embeds(
            items=all_items,
            owned_ids=inventory,
            title="⚔️ Weapon Gallery",
            header=f"You own **{owned_count}/{total_items}** weapons.\nCollect **{total_items - owned_count}** more!\n",
            formatter=lambda item, owned: f"`{owned}` {getattr(item, 'custom_emoji', '') or getEmoji(item.id)} {getClassEmoji(item.classType)} • **{item.name}** • `{extractName(item.type)}`\n",
            footer_text="Use `sl codex weapon <name>` for more details."
        )
        await ctx.reply(embed=embeds[0], view=GalleryView(embeds, ctx.author), mention_author=False)

    async def show_skill_gallery(self, ctx):
        all_skills = await SkillManager.get_all()
        if not all_skills:
            return await ctx.send(embed=discord.Embed(title="Empty Gallery", description="No skills found.", color=discord.Color.orange()))

        # Sort alphabetically by name
        all_skills.sort(key=lambda s: s.name.lower())

        embeds = self.create_paginated_embeds(
            items=all_skills,
            owned_ids=None, # Skills don't have ownership in the same way
            title="⚡ Skill Gallery",
            header="Here are all the skills available.\n🌳 **Use `sl skilltree` to learn skills through skill trees**\n📚 **Use `sl learn <skill name>` for direct learning**\n",
            formatter=self.format_skill_entry,
            footer_text="💡 Tip: Use `sl codex skill <name>` for detailed information",
            items_per_page=8
        )
        await ctx.reply(embed=embeds[0], view=GalleryView(embeds, ctx.author), mention_author=False)

    async def show_customs_gallery(self, ctx):
        customs_data = await self.load_customs_data()
        if not customs_data:
            return await ctx.send(embed=discord.Embed(title="Empty Gallery", description="No custom purchases found.", color=discord.Color.orange()))

        user_customs = {}
        for purchase in customs_data:
            user_id = purchase.get('user_id', 'Unknown')
            user_customs.setdefault(user_id, []).append(purchase)

        sorted_users = sorted(user_customs.items(), key=lambda x: len(x[1]), reverse=True)
        total_customs = len(customs_data)

        users_per_page = 5
        total_pages = (len(sorted_users) + users_per_page - 1) // users_per_page
        embeds = []

        for i in range(0, len(sorted_users), users_per_page):
            description = f"Total Custom Items Created: `{total_customs}`\n\n"
            page_users = sorted_users[i:i + users_per_page]
            
            for user_id, purchases in page_users:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    user_name = user.name
                except (discord.NotFound, ValueError):
                    user_name = f"Unknown User ({user_id})"
                
                description += f"**{user_name}** ({len(purchases)} custom{'s' if len(purchases) > 1 else ''})\n"
                
                for p in purchases:
                    tier_stars = "★" * p.get('tier', 0) + "☆" * (5 - p.get('tier', 0))
                    description += f"┗ {getEmoji(extractId(p.get('name', '')))} **{p.get('name', 'N/A')}** • `{p.get('element', 'N/A')}` • {tier_stars}\n"
            
            embed = discord.Embed(title="Customs Gallery", description=description, color=discord.Color.purple())
            embed.set_footer(text=f"Page {(i // users_per_page) + 1}/{total_pages}")
            embeds.append(embed)

        await ctx.reply(embed=embeds[0], view=GalleryView(embeds, ctx.author), mention_author=False)
        
    def create_paginated_embeds(self, *, items, owned_ids, title, header, formatter, footer_text, items_per_page=12):
        total_items = len(items)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        embeds = []
        
        for i in range(total_pages):
            start_index = i * items_per_page
            end_index = start_index + items_per_page
            page_items = items[start_index:end_index]
            
            description = header
            for item in page_items:
                owned_symbol = "☑️" if owned_ids and item.id in owned_ids else "❌"
                description += formatter(item, owned_symbol)
            
            embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
            embed.set_footer(text=f"Page {i + 1}/{total_pages} | {footer_text}")
            embeds.append(embed)
            
        return embeds
    
    @gallery.error
    async def gallery_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.errors.CommandInvokeError):
            original = error.original
            logging.error(f"Error in 'gallery' command: {original}")
            traceback.print_exception(type(original), original, original.__traceback__)
            await ctx.send("An unexpected error occurred. The developers have been notified.", ephemeral=True)
        else:
            await ctx.send(f"An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Gallery(bot))