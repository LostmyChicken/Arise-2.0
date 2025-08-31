from difflib import get_close_matches
import discord
import math
from discord import Embed
from discord.ext import commands
from discord import app_commands
from main import bot
from structure.items import ItemManager
from structure.shadow import Shadow
from structure.heroes import HeroManager
from structure.emoji import getClassEmoji, getEmoji, getRarityEmoji, getSkillTypeEmoji
from utilis.utilis import extractId, get_emoji_url, getStat, getStatHunter, hunter_autocomplete, item_autocomplete, skill_autocomplete, shadow_autocomplete
from structure.player import Player
from structure.skills import SkillManager, Skill, SkillType, Element, EffectType
from utilis.interaction_handler import InteractionHandler
from rapidfuzz import process
import math

class Codex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_group(name="codex", aliases=["c"], invoke_without_command=True, help="Access the in-game codex for information on hunters, weapons, skills, and shadows.")
    async def codex(self, ctx: commands.Context):
        """Main command for codex with interactive UI."""
        view = CodexMainView(ctx.author.id)
        embed = await view.create_main_embed()
        await ctx.send(embed=embed, view=view)

    @codex.command(name="skill", help="Browse all skills with interactive UI or get info about a specific skill.", aliases=["ss", "skills"])
    @app_commands.describe(name="Optional: The name of a specific skill to view.")
    async def skill_info(self, ctx: commands.Context, *, name: str = None):
        if name:
            # Show specific skill info
            skill = await SkillManager.get(extractId(name))

            if not skill:
                all_skills = [s.name for s in await SkillManager.get_all()]
                close_matches = get_close_matches(name, all_skills, n=3, cutoff=0.6)

                if close_matches:
                    suggestions = "\n".join(f"- {match}" for match in close_matches)
                    embed = discord.Embed(title="Skill Not Found", description=f"Skill `{name}` not found.\nDid you mean:\n{suggestions}", color=discord.Color.orange())
                else:
                    embed = discord.Embed(title="Skill Not Found", description=f"Skill `{name}` not found, and no close matches were found.", color=discord.Color.red())
                await ctx.send(embed=embed)
                return

            down = getEmoji("down")
            e = getClassEmoji(skill.element.value)
            effects_description = "\n".join([f"{effect.getDes()}" for effect in skill.effects])

            # Check if this is a buff-only skill
            from structure.skills import EffectType
            is_buff_only = (skill.damage == 0 or
                           (EffectType.BUFF in skill.effects and
                            EffectType.DAMAGE not in skill.effects and
                            EffectType.AREA_DAMAGE not in skill.effects))

            damage_text = "No Damage (Buff Only)" if is_buff_only else f"{skill.damage}% of Jinwoo's attack"

            embed = Embed(
                title=f"{skill.name}",
                description=(
                    f"**Type:** {skill.skill_type.value} Skill\n"
                    f"**Damage:** {damage_text}\n"
                    f"**MP Consumption:** {skill.mp_cost}\n"
                    f"- Deals {e} **{skill.element.value}** Elemental Damage.\n\n"
                    f"**Effects:**\n{down}{effects_description}"
                ),
                color=discord.Color.dark_red()
            )
            await ctx.reply(embed=embed, mention_author=False)
        else:
            # Show interactive skill codex UI
            view = SkillCodexView(ctx.author.id)
            embed = await view.create_main_embed()
            await ctx.send(embed=embed, view=view)
        
    @codex.command(name="hunter", description="Retrieve information about a specific hunter", aliases=["hs", "hunters", "hunterstats", "h"])
    @app_commands.describe(name="The name of the hunter.")
    async def hunter_info(self, ctx: commands.Context, *, name: str):
        all_hunters = {s.name: s for s in await HeroManager.get_all()}
        best_match = process.extractOne(name, all_hunters.keys(), score_cutoff=50)
        
        if not best_match:
            embed = discord.Embed(title="Hunter Not Found", description=f"Hunter with name `{name}` not found.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
        
        hunter_data = all_hunters[best_match[0]]

        element_colors = {
            "Dark": discord.Color.purple(), "Light": discord.Color.gold(),
            "Water": discord.Color.blue(), "Fire": discord.Color.orange(),
            "Wind": discord.Color.green(),
        }
        embed_color = element_colors.get(hunter_data.classType, discord.Color.default())

        embed = discord.Embed(title=hunter_data.name, color=embed_color)
        embed.description = f"-# {hunter_data.description}"
        
        embed.add_field(
            name="General Information", 
            value=f"- Type: `{hunter_data.type}`\n- Rank: `{hunter_data.rank}`\n- Element: `{hunter_data.classType}`", 
            inline=True
        )
        
        stat_lines = []
        atk = getStat("Attack", 100, hunter_data.attack)
        defe = getStat("Defense", 100, hunter_data.defense)
        hea = getStat("HP", 100, hunter_data.health)
        
        if hunter_data.attack > 0: stat_lines.append(f"- Attack: `{hunter_data.attack}-{atk}`")
        if hunter_data.defense > 0: stat_lines.append(f"- Defense: `{hunter_data.defense}-{defe}`")
        if hunter_data.health > 0: stat_lines.append(f"- Health: `{hunter_data.health}-{hea}`")
        if hunter_data.mp > 0: stat_lines.append(f"- MP: `{hunter_data.mp}`")
        if hunter_data.speed > 0: stat_lines.append(f"- Speed: `{hunter_data.speed}`")
        
        if stat_lines:
            embed.add_field(name="Hunter Statistics", value="\n".join(stat_lines), inline=True)
            
        emoji_url = get_emoji_url(getRarityEmoji(hunter_data.rarity))
        embed.set_thumbnail(url=emoji_url)
        embed.set_image(url=hunter_data.image)
        
        owns_hunter = False
        player = await Player.get(ctx.author.id)
        if player:
            inventory = player.get_hunters()
            owns_hunter = any(hunter_id == extractId(hunter_data.name) for hunter_id in inventory)
        
        if owns_hunter:
            embed.set_footer(text="You already own this hunter.")
        else:
            embed.set_footer(text="You don't own this hunter yet. Use `sl gacha` to try pulling it!")
        
        await ctx.reply(embed=embed, mention_author=False)

    @codex.command(name="weapon", aliases=['ws', 'weaponstats','w'], description="Information and stats about a weapon.")
    @app_commands.describe(name="The name of the weapon.")
    async def iteminfo(self, ctx: commands.Context, *, name: str):
        all_items = await ItemManager.get_all()
        item_names = [i.name for i in all_items]
        best_match = process.extractOne(name, item_names, score_cutoff=50)
        
        if not best_match:
            embed = discord.Embed(title="Item Not Found", description=f"No item found with the name `{name}`.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
            
        item = next(i for i in all_items if i.name == best_match[0])

        embed = discord.Embed(title=f"{item.name}", color=discord.Color.gold())
        embed.set_thumbnail(url=item.image)
        
        stats = []
        if item.attack > 0: stats.append(f"> {getEmoji('attack')} Increased Attack: `{item.attack}`")
        if item.defense > 0: stats.append(f"> {getEmoji('defense')} Increased Defense: `{item.defense}`")
        if item.health > 0: stats.append(f"**Increased Health:** `+{item.health}`")
        
        stats_description = "\n".join(stats) if stats else "_No additional stats available._"
        
        embed.description = (
            f"__Information__\n"
            f"> {getClassEmoji(item.classType)} Class: `{item.classType}`\n"
            f"> {getRarityEmoji(item.rarity.lower())} Rarity: `{item.rarity}`\n"
            f"__Statistics__\n{stats_description}\n"
            f"__Description__\n> -# {item.description}"
        )
        embed.set_footer(text="Solo Leveling Bot | Weapon Info")

        await ctx.reply(embed=embed, mention_author=False)

    @codex.command(name="shadow", description="Get information about a shadow.")
    @app_commands.describe(name="The name of the shadow.")
    async def shadow_info(self, ctx: commands.Context, name: str):
        trace = getEmoji("trace")
        down = getEmoji("down")
        shadow = await Shadow.get(extractId(name))
        
        if not shadow:
            embed = discord.Embed(title="Shadow Not Found", description=f"No shadow found with name `{name}`.", color=discord.Color.red())
            await ctx.reply(embed=embed, mention_author=True)
            return

        embed = discord.Embed(
            title=f"Shadow: {shadow.name}",
            description=f"**Attack Boost:** {shadow.attack}%\n{shadow.description}",
            color=discord.Color.dark_blue()
        )
        embed.add_field(name="Unlock Requirements", value=f"x{shadow.price} {trace} Traces of Shadow\nUse `sl arise <{shadow.name}>` to try unlocking it", inline=True)
        embed.set_image(url=shadow.image)
        
        owns_shadow = False
        player = await Player.get(ctx.author.id)
        if player:
            inventory = player.get_shadows()
            owns_shadow = any(shadow_id == extractId(name) for shadow_id in inventory)

        if owns_shadow:
            embed.set_footer(text="You already own this shadow.")
        else:
            embed.set_footer(text="You don't own this shadow yet. Use `sl arise` to try getting it!")

        await ctx.reply(embed=embed, mention_author=False)


class SkillCodexView(discord.ui.View):
    """Interactive skill codex with filtering and pagination"""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.current_page = 0
        self.skills_per_page = 6  # Reduced to prevent field length issues
        self.current_filter = "all"
        self.current_element = "all"
        self.current_type = "all"
        self.search_query = ""

    async def create_main_embed(self):
        """Create the main skill codex embed"""
        all_skills = await SkillManager.get_all()

        # Apply filters
        filtered_skills = self.apply_filters(all_skills)

        # Sort alphabetically
        filtered_skills.sort(key=lambda s: s.name.lower())

        total_skills = len(filtered_skills)
        total_pages = max(1, math.ceil(total_skills / self.skills_per_page))

        # Ensure current page is valid
        self.current_page = min(self.current_page, total_pages - 1)

        start_idx = self.current_page * self.skills_per_page
        end_idx = min(start_idx + self.skills_per_page, total_skills)
        page_skills = filtered_skills[start_idx:end_idx]

        # Create embed
        embed = discord.Embed(
            title="📚 **SKILL CODEX**",
            description=f"Complete database of all skills in Solo Leveling\n"
                       f"**Total Skills**: {total_skills} | **Page**: {self.current_page + 1}/{total_pages}",
            color=discord.Color.gold()
        )

        # Add filter info
        filter_info = []
        if self.current_filter != "all":
            filter_info.append(f"Filter: {self.current_filter.title()}")
        if self.current_element != "all":
            filter_info.append(f"Element: {self.current_element.title()}")
        if self.current_type != "all":
            filter_info.append(f"Type: {self.current_type.title()}")
        if self.search_query:
            filter_info.append(f"Search: '{self.search_query}'")

        if filter_info:
            embed.add_field(
                name="🔍 **Active Filters**",
                value=" • ".join(filter_info),
                inline=False
            )

        # Add skills to embed
        if page_skills:
            skills_text = ""
            for skill in page_skills:
                # Get element emoji
                element_emoji = getClassEmoji(skill.element.value)

                # Get skill type emoji
                type_emoji = "💥" if skill.skill_type.value == "Ultimate" else "⚡" if skill.skill_type.value == "QTE" else "🔸"

                # Check if buff-only
                is_buff_only = (skill.damage == 0 or
                               (EffectType.BUFF in skill.effects and
                                EffectType.DAMAGE not in skill.effects and
                                EffectType.AREA_DAMAGE not in skill.effects))

                damage_display = "Buff" if is_buff_only else f"{skill.damage}%"

                skill_entry = (
                    f"{type_emoji} **{skill.name}**\n"
                    f"   {element_emoji} {skill.element.value} • {damage_display} DMG • {skill.mp_cost} MP\n"
                    f"   *{skill.skill_type.value} Skill*\n\n"
                )

                # Check if adding this skill would exceed Discord's field limit
                if len(skills_text + skill_entry) > 1000:  # Leave some buffer
                    skills_text += "... (more skills available on next page)"
                    break

                skills_text += skill_entry

            # Ensure the field value isn't empty and doesn't exceed limits
            if not skills_text:
                skills_text = "No skills to display."
            elif len(skills_text) > 1024:
                skills_text = skills_text[:1000] + "..."

            embed.add_field(
                name=f"⚔️ **Skills ({start_idx + 1}-{min(end_idx, start_idx + len(page_skills))})**",
                value=skills_text,
                inline=False
            )
        else:
            embed.add_field(
                name="❌ **No Skills Found**",
                value="No skills match your current filters. Try adjusting your search criteria.",
                inline=False
            )

        embed.set_footer(text="Use the buttons below to filter, search, and navigate • Select a skill for details • Timeout: 5 minutes")

        # Initialize skill select dropdown
        await self.update_skill_select()

        return embed

    def apply_filters(self, skills):
        """Apply current filters to skill list"""
        filtered = skills

        # Apply element filter
        if self.current_element != "all":
            filtered = [s for s in filtered if s.element.value.lower() == self.current_element.lower()]

        # Apply type filter
        if self.current_type != "all":
            filtered = [s for s in filtered if s.skill_type.value.lower() == self.current_type.lower()]

        # Apply effect filter
        if self.current_filter == "damage":
            filtered = [s for s in filtered if s.damage > 0 and (EffectType.DAMAGE in s.effects or EffectType.AREA_DAMAGE in s.effects)]
        elif self.current_filter == "heal":
            filtered = [s for s in filtered if EffectType.HEAL in s.effects]
        elif self.current_filter == "buff":
            filtered = [s for s in filtered if EffectType.BUFF in s.effects]
        elif self.current_filter == "debuff":
            filtered = [s for s in filtered if EffectType.DEBUFF in s.effects]
        elif self.current_filter == "ultimate":
            filtered = [s for s in filtered if s.skill_type == SkillType.ULTIMATE]

        # Apply search query
        if self.search_query:
            query = self.search_query.lower()
            filtered = [s for s in filtered if query in s.name.lower()]

        return filtered

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ You're already on the first page.", ephemeral=True)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        all_skills = await SkillManager.get_all()
        filtered_skills = self.apply_filters(all_skills)
        total_pages = max(1, math.ceil(len(filtered_skills) / self.skills_per_page))

        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ You're already on the last page.", ephemeral=True)

    @discord.ui.select(
        placeholder="🔍 Filter by Effect Type",
        options=[
            discord.SelectOption(label="All Skills", value="all", emoji="📚"),
            discord.SelectOption(label="Damage Skills", value="damage", emoji="⚔️"),
            discord.SelectOption(label="Healing Skills", value="heal", emoji="💚"),
            discord.SelectOption(label="Buff Skills", value="buff", emoji="✨"),
            discord.SelectOption(label="Debuff Skills", value="debuff", emoji="💀"),
            discord.SelectOption(label="Ultimate Skills", value="ultimate", emoji="💥")
        ],
        row=1
    )
    async def filter_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await InteractionHandler.safe_response(interaction, content="❌ This is not your codex.", ephemeral=True)
            return

        self.current_filter = select.values[0]
        self.current_page = 0  # Reset to first page
        embed = await self.create_main_embed()

        # Use safe edit to prevent timeout errors
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.NotFound:
            await InteractionHandler.safe_response(interaction, embed=embed, view=self)
        except Exception as e:
            logging.error(f"Error updating codex filter: {e}")
            await InteractionHandler.safe_response(interaction, content="❌ Error updating filters. Please try again.", ephemeral=True)

    @discord.ui.select(
        placeholder="🌟 Filter by Element",
        options=[
            discord.SelectOption(label="All Elements", value="all", emoji="🌈"),
            discord.SelectOption(label="Fire", value="fire", emoji="🔥"),
            discord.SelectOption(label="Water", value="water", emoji="💧"),
            discord.SelectOption(label="Wind", value="wind", emoji="💨"),
            discord.SelectOption(label="Earth", value="earth", emoji="🌍"),
            discord.SelectOption(label="Light", value="light", emoji="✨"),
            discord.SelectOption(label="Dark", value="dark", emoji="🌑")
        ],
        row=2
    )
    async def element_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        self.current_element = select.values[0]
        self.current_page = 0  # Reset to first page
        embed = await self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.select(
        placeholder="⚡ Filter by Skill Type",
        options=[
            discord.SelectOption(label="All Types", value="all", emoji="📋"),
            discord.SelectOption(label="Basic Skills", value="basic", emoji="🔸"),
            discord.SelectOption(label="QTE Skills", value="qte", emoji="⚡"),
            discord.SelectOption(label="Ultimate Skills", value="ultimate", emoji="💥")
        ],
        row=1
    )
    async def type_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        self.current_type = select.values[0]
        self.current_page = 0  # Reset to first page
        embed = await self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔄 Reset Filters", style=discord.ButtonStyle.danger, row=4)
    async def reset_filters(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        self.current_filter = "all"
        self.current_element = "all"
        self.current_type = "all"
        self.search_query = ""
        self.current_page = 0
        embed = await self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.select(
        placeholder="⚔️ Select Skill for Details",
        options=[discord.SelectOption(label="Loading...", value="loading")],
        row=3
    )
    async def select_skill(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        skill_name = select.values[0]
        if skill_name == "loading":
            await interaction.response.send_message("❌ Please wait for skills to load.", ephemeral=True)
            return

        # Use the existing skill info command functionality
        bot = interaction.client

        # Create a mock context for the command
        class MockContext:
            def __init__(self, interaction):
                self.author = interaction.user
                self.send = interaction.followup.send

            async def reply(self, *args, **kwargs):
                # Remove mention_author parameter as followup.send doesn't support it
                kwargs.pop('mention_author', None)
                return await interaction.followup.send(*args, **kwargs)

        mock_ctx = MockContext(interaction)

        # Get the codex cog and call the skill command
        codex_cog = bot.get_cog('Codex')
        if codex_cog:
            await interaction.response.defer()
            await codex_cog.skill_info(mock_ctx, name=skill_name)
        else:
            await interaction.response.send_message("❌ Codex system not available.", ephemeral=True)

    async def update_skill_select(self):
        """Update the skill select dropdown with current page skills"""
        all_skills = await SkillManager.get_all()
        filtered_skills = self.apply_filters(all_skills)
        filtered_skills.sort(key=lambda s: s.name.lower())

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(filtered_skills))
        page_skills = filtered_skills[start_idx:end_idx]

        options = []
        for skill in page_skills:
            type_emoji = getSkillTypeEmoji(skill.skillType)
            options.append(discord.SelectOption(
                label=skill.name,
                value=skill.name,
                description=f"{skill.skillType} • {getattr(skill, 'element', 'Neutral')}",
                emoji=type_emoji
            ))

        if not options:
            options = [discord.SelectOption(label="No skills available", value="none")]

        # Update the select component
        for item in self.children:
            if isinstance(item, discord.ui.Select) and item.placeholder == "⚔️ Select Skill for Details":
                item.options = options
                break


class CodexMainView(discord.ui.View):
    """Interactive main codex view with category selection"""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id

    async def create_main_embed(self):
        """Create the main codex embed"""
        embed = discord.Embed(
            title="📚 **SOLO LEVELING CODEX**",
            description="Complete database of all Solo Leveling content\n"
                       "Select a category below to browse or search for specific items.",
            color=discord.Color.gold()
        )

        # Get counts for each category
        try:
            all_skills = await SkillManager.get_all()
            all_hunters = [h for h in await HeroManager.get_all() if h.rarity != "Custom"]
            all_weapons = [w for w in await ItemManager.get_all() if w.rarity != "Custom"]
            all_shadows = await Shadow.get_all()

            skill_count = len(all_skills)
            hunter_count = len(all_hunters)
            weapon_count = len(all_weapons)
            shadow_count = len(all_shadows)

        except Exception:
            skill_count = hunter_count = weapon_count = shadow_count = "?"

        embed.add_field(
            name="⚔️ **Skills**",
            value=f"**{skill_count}** combat abilities\n"
                  f"Browse all skills with advanced filtering\n"
                  f"View damage, effects, and requirements",
            inline=True
        )

        embed.add_field(
            name="🏆 **Hunters**",
            value=f"**{hunter_count}** elite hunters\n"
                  f"Detailed stats and abilities\n"
                  f"Rarity and class information",
            inline=True
        )

        embed.add_field(
            name="⚔️ **Weapons**",
            value=f"**{weapon_count}** legendary weapons\n"
                  f"Complete weapon database\n"
                  f"Stats, types, and rarities",
            inline=True
        )

        embed.add_field(
            name="👻 **Shadows**",
            value=f"**{shadow_count}** shadow soldiers\n"
                  f"Unlockable shadow army\n"
                  f"Powers and abilities",
            inline=True
        )

        embed.add_field(
            name="🔍 **Search Features**",
            value="• **Advanced Filtering** by type, element, rarity\n"
                  "• **Alphabetical Ordering** for easy browsing\n"
                  "• **Detailed Information** with stats and descriptions",
            inline=True
        )

        embed.add_field(
            name="📖 **How to Use**",
            value="• **Click buttons** below to browse categories\n"
                  "• **Use dropdowns** for filtering options\n"
                  "• **Search by name** for specific items\n"
                  "• **Interactive UI** with pagination and filters",
            inline=True
        )

        embed.set_footer(text="Select a category to begin browsing • Timeout: 5 minutes")
        return embed

    @discord.ui.button(label="Skills", style=discord.ButtonStyle.primary, emoji="⚔️", row=0)
    async def skills_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        # Open skill codex
        view = SkillCodexView(self.user_id)
        embed = await view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Hunters", style=discord.ButtonStyle.primary, emoji="🏆", row=0)
    async def hunters_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        # Open hunter codex
        view = HunterCodexView(self.user_id)
        embed = await view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Weapons", style=discord.ButtonStyle.primary, emoji="🗡️", row=0)
    async def weapons_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        # Open weapon codex
        view = WeaponCodexView(self.user_id)
        embed = await view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Shadows", style=discord.ButtonStyle.primary, emoji="👻", row=0)
    async def shadows_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        # Open shadow codex
        view = ShadowCodexView(self.user_id)
        embed = await view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Search All", style=discord.ButtonStyle.secondary, emoji="🔍", row=1)
    async def search_all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        # Open comprehensive search view
        view = CodexSearchView(self.user_id)
        embed = await view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Statistics", style=discord.ButtonStyle.secondary, emoji="📊", row=1)
    async def statistics_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        # Show codex statistics
        embed = await self.create_statistics_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_statistics_embed(self):
        """Create statistics embed for the codex"""
        try:
            all_skills = await SkillManager.get_all()
            all_hunters = [h for h in await HeroManager.get_all() if h.rarity != "Custom"]
            all_weapons = [w for w in await ItemManager.get_all() if w.rarity != "Custom"]
            all_shadows = await Shadow.get_all()

            embed = discord.Embed(
                title="📊 **CODEX STATISTICS**",
                description="Complete breakdown of all Solo Leveling content",
                color=discord.Color.blue()
            )

            # Skills breakdown
            skill_types = {}
            skill_elements = {}
            for skill in all_skills:
                skill_type = skill.skill_type.value
                skill_element = skill.element.value
                skill_types[skill_type] = skill_types.get(skill_type, 0) + 1
                skill_elements[skill_element] = skill_elements.get(skill_element, 0) + 1

            skills_text = f"**Total Skills**: {len(all_skills)}\n"
            for skill_type, count in skill_types.items():
                skills_text += f"• {skill_type}: {count}\n"

            embed.add_field(name="⚔️ **Skills**", value=skills_text, inline=True)

            # Hunters breakdown
            hunter_rarities = {}
            for hunter in all_hunters:
                rarity = hunter.rarity
                hunter_rarities[rarity] = hunter_rarities.get(rarity, 0) + 1

            hunters_text = f"**Total Hunters**: {len(all_hunters)}\n"
            for rarity, count in hunter_rarities.items():
                hunters_text += f"• {rarity}: {count}\n"

            embed.add_field(name="🏆 **Hunters**", value=hunters_text, inline=True)

            # Weapons breakdown
            weapon_rarities = {}
            for weapon in all_weapons:
                rarity = weapon.rarity
                weapon_rarities[rarity] = weapon_rarities.get(rarity, 0) + 1

            weapons_text = f"**Total Weapons**: {len(all_weapons)}\n"
            for rarity, count in weapon_rarities.items():
                weapons_text += f"• {rarity}: {count}\n"

            embed.add_field(name="⚔️ **Weapons**", value=weapons_text, inline=True)

            # Shadows
            shadows_text = f"**Total Shadows**: {len(all_shadows)}\n"
            shadows_text += f"• Unlockable through world boss battles\n"
            shadows_text += f"• Each shadow has unique abilities"

            embed.add_field(name="👻 **Shadows**", value=shadows_text, inline=True)

            # Elements breakdown
            elements_text = ""
            for element, count in skill_elements.items():
                elements_text += f"• {element}: {count} skills\n"

            embed.add_field(name="🌟 **Elements**", value=elements_text, inline=True)

            # Total content
            total_content = len(all_skills) + len(all_hunters) + len(all_weapons) + len(all_shadows)
            embed.add_field(
                name="📈 **Total Content**",
                value=f"**{total_content}** items in the codex\n"
                      f"Constantly expanding with new content!",
                inline=True
            )

            embed.set_footer(text="Click the buttons below to explore each category")
            return embed

        except Exception as e:
            embed = discord.Embed(
                title="📊 **CODEX STATISTICS**",
                description="Error loading statistics. Please try again later.",
                color=discord.Color.red()
            )
            return embed


class HunterCodexView(discord.ui.View):
    """Interactive hunter codex with filtering and pagination"""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.current_page = 0
        self.items_per_page = 6  # Reduced to prevent Discord 1024 char limit
        self.current_filter = "all"
        self.current_rarity = "all"

    async def create_main_embed(self):
        """Create the main hunter codex embed"""
        all_hunters = [h for h in await HeroManager.get_all() if h.rarity != "Custom"]

        # Apply filters
        filtered_hunters = self.apply_filters(all_hunters)

        # Sort alphabetically
        filtered_hunters.sort(key=lambda h: h.name.lower())

        total_hunters = len(filtered_hunters)
        total_pages = max(1, math.ceil(total_hunters / self.items_per_page))

        # Ensure current page is valid
        self.current_page = min(self.current_page, total_pages - 1)

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_hunters)
        page_hunters = filtered_hunters[start_idx:end_idx]

        embed = discord.Embed(
            title="🏆 **HUNTER CODEX**",
            description=f"Complete database of all hunters in Solo Leveling\n"
                       f"**Total Hunters**: {total_hunters} | **Page**: {self.current_page + 1}/{total_pages}",
            color=discord.Color.gold()
        )

        # Add filter info
        filter_info = []
        if self.current_filter != "all":
            filter_info.append(f"Type: {self.current_filter.title()}")
        if self.current_rarity != "all":
            filter_info.append(f"Rarity: {self.current_rarity.title()}")

        if filter_info:
            embed.add_field(
                name="🔍 **Active Filters**",
                value=" • ".join(filter_info),
                inline=False
            )

        # Add hunters to embed
        if page_hunters:
            hunters_text = ""
            for hunter in page_hunters:
                rarity_emoji = getRarityEmoji(hunter.rarity)
                class_emoji = getClassEmoji(hunter.classType)

                # Shortened format to prevent Discord 1024 char limit
                hunters_text += (
                    f"{rarity_emoji} **{hunter.name}** {class_emoji}\n"
                    f"   {hunter.type} • ATK:{hunter.attack} DEF:{hunter.defense} HP:{hunter.health}\n\n"
                )

            embed.add_field(
                name=f"🏆 **Hunters ({start_idx + 1}-{end_idx})**",
                value=hunters_text,
                inline=False
            )
        else:
            embed.add_field(
                name="❌ **No Hunters Found**",
                value="No hunters match your current filters. Try adjusting your search criteria.",
                inline=False
            )

        embed.set_footer(text="Use the buttons below to filter and navigate • Select a hunter for details • Timeout: 5 minutes")

        # Initialize hunter select dropdown after embed creation
        await self.update_hunter_select()

        return embed

    def apply_filters(self, hunters):
        """Apply current filters to hunter list"""
        filtered = hunters

        # Apply type filter
        if self.current_filter != "all":
            filtered = [h for h in filtered if h.type.lower() == self.current_filter.lower()]

        # Apply rarity filter
        if self.current_rarity != "all":
            filtered = [h for h in filtered if h.rarity.lower() == self.current_rarity.lower()]

        return filtered

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_main_embed()
            await self.update_hunter_select()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ You're already on the first page.", ephemeral=True)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        all_hunters = [h for h in await HeroManager.get_all() if h.rarity != "Custom"]
        filtered_hunters = self.apply_filters(all_hunters)
        total_pages = max(1, math.ceil(len(filtered_hunters) / self.items_per_page))

        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.create_main_embed()
            await self.update_hunter_select()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ You're already on the last page.", ephemeral=True)

    @discord.ui.button(label="🔄 Back to Codex", style=discord.ButtonStyle.danger, row=0)
    async def back_to_codex(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        view = CodexMainView(self.user_id)
        embed = await view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.select(
        placeholder="👤 Select Hunter for Details",
        options=[discord.SelectOption(label="Loading...", value="loading")],
        row=1
    )
    async def select_hunter(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        hunter_name = select.values[0]
        if hunter_name == "loading":
            await interaction.response.send_message("❌ Please wait for hunters to load.", ephemeral=True)
            return

        # Use the existing hunter info command functionality
        bot = interaction.client

        # Create a mock context for the command
        class MockContext:
            def __init__(self, interaction):
                self.author = interaction.user
                self.send = interaction.followup.send

            async def reply(self, *args, **kwargs):
                # Remove mention_author parameter as followup.send doesn't support it
                kwargs.pop('mention_author', None)
                return await interaction.followup.send(*args, **kwargs)

        mock_ctx = MockContext(interaction)

        # Get the codex cog and call the hunter command
        codex_cog = bot.get_cog('Codex')
        if codex_cog:
            await interaction.response.defer()
            await codex_cog.hunter_info(mock_ctx, name=hunter_name)
        else:
            await interaction.response.send_message("❌ Codex system not available.", ephemeral=True)

    async def update_hunter_select(self):
        """Update the hunter select dropdown with current page hunters"""
        all_hunters = [h for h in await HeroManager.get_all() if h.rarity != "Custom"]
        filtered_hunters = self.apply_filters(all_hunters)
        filtered_hunters.sort(key=lambda h: h.name.lower())

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(filtered_hunters))
        page_hunters = filtered_hunters[start_idx:end_idx]

        options = []
        for hunter in page_hunters:
            rarity_emoji = getRarityEmoji(hunter.rarity)
            class_emoji = getClassEmoji(hunter.classType)
            options.append(discord.SelectOption(
                label=hunter.name,
                value=hunter.name,
                description=f"{hunter.type} • {hunter.rarity}",
                emoji=rarity_emoji
            ))

        if not options:
            options = [discord.SelectOption(label="No hunters available", value="none")]

        # Update the select component
        for item in self.children:
            if isinstance(item, discord.ui.Select) and item.placeholder == "👤 Select Hunter for Details":
                item.options = options
                break

    @discord.ui.select(
        placeholder="🏷️ Filter by Hunter Type",
        options=[
            discord.SelectOption(label="All Types", value="all", emoji="📋"),
            discord.SelectOption(label="Assassin", value="assassin", emoji="🗡️"),
            discord.SelectOption(label="Fighter", value="fighter", emoji="👊"),
            discord.SelectOption(label="Mage", value="mage", emoji="🔮"),
            discord.SelectOption(label="Tank", value="tank", emoji="🛡️"),
            discord.SelectOption(label="Healer", value="healer", emoji="💚"),
        ],
        row=2
    )
    async def filter_by_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        self.current_filter = select.values[0]
        self.current_page = 0  # Reset to first page
        embed = await self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.select(
        placeholder="⭐ Filter by Rarity",
        options=[
            discord.SelectOption(label="All Rarities", value="all", emoji="🌟"),
            discord.SelectOption(label="UR", value="ur", emoji="💎"),
            discord.SelectOption(label="SSR", value="ssr", emoji="🔴"),
            discord.SelectOption(label="Super Rare", value="super rare", emoji="🟣"),
        ],
        row=3
    )
    async def filter_by_rarity(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        self.current_rarity = select.values[0]
        self.current_page = 0  # Reset to first page
        embed = await self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)


class WeaponCodexView(discord.ui.View):
    """Interactive weapon codex with filtering and pagination"""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.current_page = 0
        self.items_per_page = 6  # Reduced to prevent Discord 1024 char limit
        self.current_filter = "all"
        self.current_rarity = "all"

    async def create_main_embed(self):
        """Create the main weapon codex embed"""
        all_weapons = [w for w in await ItemManager.get_all() if w.rarity != "Custom"]

        # Apply filters
        filtered_weapons = self.apply_filters(all_weapons)

        # Sort alphabetically
        filtered_weapons.sort(key=lambda w: w.name.lower())

        total_weapons = len(filtered_weapons)
        total_pages = max(1, math.ceil(total_weapons / self.items_per_page))

        # Ensure current page is valid
        self.current_page = min(self.current_page, total_pages - 1)

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_weapons)
        page_weapons = filtered_weapons[start_idx:end_idx]

        embed = discord.Embed(
            title="⚔️ **WEAPON CODEX**",
            description=f"Complete database of all weapons in Solo Leveling\n"
                       f"**Total Weapons**: {total_weapons} | **Page**: {self.current_page + 1}/{total_pages}",
            color=discord.Color.gold()
        )

        # Add filter info
        filter_info = []
        if self.current_filter != "all":
            filter_info.append(f"Type: {self.current_filter.title()}")
        if self.current_rarity != "all":
            filter_info.append(f"Rarity: {self.current_rarity.title()}")

        if filter_info:
            embed.add_field(
                name="🔍 **Active Filters**",
                value=" • ".join(filter_info),
                inline=False
            )

        # Add weapons to embed
        if page_weapons:
            weapons_text = ""
            for weapon in page_weapons:
                rarity_emoji = getRarityEmoji(weapon.rarity)
                class_emoji = getClassEmoji(weapon.classType)

                # Shortened format to prevent Discord 1024 char limit
                weapons_text += (
                    f"{rarity_emoji} **{weapon.name}** {class_emoji}\n"
                    f"   {weapon.type} • ATK:{weapon.attack} DEF:{weapon.defense}\n\n"
                )

            embed.add_field(
                name=f"⚔️ **Weapons ({start_idx + 1}-{end_idx})**",
                value=weapons_text,
                inline=False
            )
        else:
            embed.add_field(
                name="❌ **No Weapons Found**",
                value="No weapons match your current filters. Try adjusting your search criteria.",
                inline=False
            )

        embed.set_footer(text="Use the buttons below to filter and navigate • Select a weapon for details • Timeout: 5 minutes")

        # Initialize weapon select dropdown
        await self.update_weapon_select()

        return embed

    def apply_filters(self, weapons):
        """Apply current filters to weapon list"""
        filtered = weapons

        # Apply type filter
        if self.current_filter != "all":
            filtered = [w for w in filtered if w.type.lower() == self.current_filter.lower()]

        # Apply rarity filter
        if self.current_rarity != "all":
            filtered = [w for w in filtered if w.rarity.lower() == self.current_rarity.lower()]

        return filtered

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ You're already on the first page.", ephemeral=True)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        all_weapons = [w for w in await ItemManager.get_all() if w.rarity != "Custom"]
        filtered_weapons = self.apply_filters(all_weapons)
        total_pages = max(1, math.ceil(len(filtered_weapons) / self.items_per_page))

        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ You're already on the last page.", ephemeral=True)

    @discord.ui.button(label="🔄 Back to Codex", style=discord.ButtonStyle.danger, row=0)
    async def back_to_codex(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        view = CodexMainView(self.user_id)
        embed = await view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.select(
        placeholder="⚔️ Select Weapon for Details",
        options=[discord.SelectOption(label="Loading...", value="loading")],
        row=1
    )
    async def select_weapon(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        weapon_name = select.values[0]
        if weapon_name == "loading":
            await interaction.response.send_message("❌ Please wait for weapons to load.", ephemeral=True)
            return

        # Use the existing weapon info command functionality
        bot = interaction.client

        # Create a mock context for the command
        class MockContext:
            def __init__(self, interaction):
                self.author = interaction.user
                self.send = interaction.followup.send

            async def reply(self, *args, **kwargs):
                # Remove mention_author parameter as followup.send doesn't support it
                kwargs.pop('mention_author', None)
                return await interaction.followup.send(*args, **kwargs)

        mock_ctx = MockContext(interaction)

        # Get the codex cog and call the weapon command
        codex_cog = bot.get_cog('Codex')
        if codex_cog:
            await interaction.response.defer()
            await codex_cog.iteminfo(mock_ctx, name=weapon_name)
        else:
            await interaction.response.send_message("❌ Codex system not available.", ephemeral=True)

    async def update_weapon_select(self):
        """Update the weapon select dropdown with current page weapons"""
        all_weapons = [w for w in await ItemManager.get_all() if w.rarity != "Custom"]
        filtered_weapons = self.apply_filters(all_weapons)
        filtered_weapons.sort(key=lambda w: w.name.lower())

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(filtered_weapons))
        page_weapons = filtered_weapons[start_idx:end_idx]

        options = []
        for weapon in page_weapons:
            rarity_emoji = getRarityEmoji(weapon.rarity)
            type_emoji = "⚔️"  # Default weapon emoji
            options.append(discord.SelectOption(
                label=weapon.name,
                value=weapon.name,
                description=f"{weapon.type} • {weapon.rarity}",
                emoji=rarity_emoji
            ))

        if not options:
            options = [discord.SelectOption(label="No weapons available", value="none")]

        # Update the select component
        for item in self.children:
            if isinstance(item, discord.ui.Select) and item.placeholder == "⚔️ Select Weapon for Details":
                item.options = options
                break


class ShadowCodexView(discord.ui.View):
    """Interactive shadow codex with filtering and pagination"""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.current_page = 0
        self.items_per_page = 10
        self.current_filter = "all"

    async def create_main_embed(self):
        """Create the main shadow codex embed"""
        all_shadows = await Shadow.get_all()

        # Apply filters
        filtered_shadows = self.apply_filters(all_shadows)

        # Sort alphabetically
        filtered_shadows.sort(key=lambda s: s.name.lower())

        total_shadows = len(filtered_shadows)
        total_pages = max(1, math.ceil(total_shadows / self.items_per_page))

        # Ensure current page is valid
        self.current_page = min(self.current_page, total_pages - 1)

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_shadows)
        page_shadows = filtered_shadows[start_idx:end_idx]

        embed = discord.Embed(
            title="👻 **SHADOW CODEX**",
            description=f"Complete database of all shadows in Solo Leveling\n"
                       f"**Total Shadows**: {total_shadows} | **Page**: {self.current_page + 1}/{total_pages}",
            color=discord.Color.dark_purple()
        )

        # Add filter info
        if self.current_filter != "all":
            embed.add_field(
                name="🔍 **Active Filters**",
                value=f"Type: {self.current_filter.title()}",
                inline=False
            )

        # Add shadows to embed
        if page_shadows:
            shadows_text = ""
            for shadow in page_shadows:
                rarity_emoji = getRarityEmoji(shadow.rarity)

                shadows_text += (
                    f"{rarity_emoji} **{shadow.name}**\n"
                    f"   👻 {shadow.rarity} Shadow • Price: {shadow.price} TOS\n"
                    f"   ATK: {shadow.attack} • DEF: {shadow.defense}\n\n"
                )

            embed.add_field(
                name=f"👻 **Shadows ({start_idx + 1}-{end_idx})**",
                value=shadows_text,
                inline=False
            )
        else:
            embed.add_field(
                name="❌ **No Shadows Found**",
                value="No shadows match your current filters. Try adjusting your search criteria.",
                inline=False
            )

        embed.set_footer(text="Use the buttons below to filter and navigate • Select a shadow for details • Timeout: 5 minutes")

        # Initialize shadow select dropdown
        await self.update_shadow_select()

        return embed

    def apply_filters(self, shadows):
        """Apply current filters to shadow list"""
        filtered = shadows

        # Apply type filter
        if self.current_filter != "all":
            filtered = [s for s in filtered if s.type.lower() == self.current_filter.lower()]

        return filtered

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ You're already on the first page.", ephemeral=True)

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        all_shadows = await Shadow.get_all()
        filtered_shadows = self.apply_filters(all_shadows)
        total_pages = max(1, math.ceil(len(filtered_shadows) / self.items_per_page))

        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ You're already on the last page.", ephemeral=True)

    @discord.ui.button(label="🔄 Back to Codex", style=discord.ButtonStyle.danger, row=0)
    async def back_to_codex(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        view = CodexMainView(self.user_id)
        embed = await view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.select(
        placeholder="👻 Select Shadow for Details",
        options=[discord.SelectOption(label="Loading...", value="loading")],
        row=1
    )
    async def select_shadow(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your codex.", ephemeral=True)
            return

        shadow_name = select.values[0]
        if shadow_name == "loading":
            await interaction.response.send_message("❌ Please wait for shadows to load.", ephemeral=True)
            return

        # Use the existing shadow info command functionality
        bot = interaction.client

        # Create a mock context for the command
        class MockContext:
            def __init__(self, interaction):
                self.author = interaction.user
                self.send = interaction.followup.send

            async def reply(self, *args, **kwargs):
                # Remove mention_author parameter as followup.send doesn't support it
                kwargs.pop('mention_author', None)
                return await interaction.followup.send(*args, **kwargs)

        mock_ctx = MockContext(interaction)

        # Get the codex cog and call the shadow command
        codex_cog = bot.get_cog('Codex')
        if codex_cog:
            await interaction.response.defer()
            await codex_cog.shadow_info(mock_ctx, name=shadow_name)
        else:
            await interaction.response.send_message("❌ Codex system not available.", ephemeral=True)

    async def update_shadow_select(self):
        """Update the shadow select dropdown with current page shadows"""
        all_shadows = await Shadow.get_all()
        filtered_shadows = self.apply_filters(all_shadows)
        filtered_shadows.sort(key=lambda s: s.name.lower())

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(filtered_shadows))
        page_shadows = filtered_shadows[start_idx:end_idx]

        options = []
        for shadow in page_shadows:
            rarity_emoji = getRarityEmoji(shadow.rarity)
            options.append(discord.SelectOption(
                label=shadow.name,
                value=shadow.name,
                description=f"Shadow • {shadow.rarity}",
                emoji=rarity_emoji
            ))

        if not options:
            options = [discord.SelectOption(label="No shadows available", value="none")]

        # Update the select component
        for item in self.children:
            if isinstance(item, discord.ui.Select) and item.placeholder == "👻 Select Shadow for Details":
                item.options = options
                break


class CodexSearchView(discord.ui.View):
    """Comprehensive search view for all codex content"""

    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.current_page = 0
        self.items_per_page = 8
        self.search_results = []

    async def create_main_embed(self):
        """Create the main search embed"""
        embed = discord.Embed(
            title="🔍 **CODEX SEARCH**",
            description="Search across all Solo Leveling content\n"
                       "Use the dropdown below to select a search category.",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="🎯 **Search Categories**",
            value="• **All Content** - Search everything at once\n"
                  "• **Skills** - Combat abilities and techniques\n"
                  "• **Hunters** - Elite hunters and their stats\n"
                  "• **Weapons** - Legendary weapons and equipment\n"
                  "• **Shadows** - Shadow army members",
            inline=False
        )

        embed.add_field(
            name="📝 **How to Search**",
            value="1. Select a category from the dropdown\n"
                  "2. Enter your search term\n"
                  "3. Browse results with pagination\n"
                  "4. Click items for detailed information",
            inline=False
        )

        embed.set_footer(text="Select a search category to begin")
        return embed

    @discord.ui.select(
        placeholder="🔍 Select Search Category",
        options=[
            discord.SelectOption(label="All Content", value="all", emoji="🌟"),
            discord.SelectOption(label="Skills", value="skills", emoji="⚔️"),
            discord.SelectOption(label="Hunters", value="hunters", emoji="🏆"),
            discord.SelectOption(label="Weapons", value="weapons", emoji="⚔️"),
            discord.SelectOption(label="Shadows", value="shadows", emoji="👻")
        ]
    )
    async def search_category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your search.", ephemeral=True)
            return

        category = select.values[0]

        if category == "all":
            # Search all content
            embed = discord.Embed(
                title="🔍 **SEARCH ALL CONTENT**",
                description="Enter a search term to find matching content across all categories.",
                color=discord.Color.purple()
            )
        elif category == "skills":
            view = SkillCodexView(self.user_id)
            embed = await view.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=view)
            return
        elif category == "hunters":
            view = HunterCodexView(self.user_id)
            embed = await view.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=view)
            return
        elif category == "weapons":
            view = WeaponCodexView(self.user_id)
            embed = await view.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=view)
            return
        elif category == "shadows":
            view = ShadowCodexView(self.user_id)
            embed = await view.create_main_embed()
            await interaction.response.edit_message(embed=embed, view=view)
            return

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔄 Back to Codex", style=discord.ButtonStyle.danger, row=1)
    async def back_to_codex(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your search.", ephemeral=True)
            return

        view = CodexMainView(self.user_id)
        embed = await view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Codex(bot))