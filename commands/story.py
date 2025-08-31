import discord
from discord.ext import commands
import asyncio
import json
import random
from typing import Optional, Dict, List
from structure.player import Player
from structure.story_campaign import StoryCampaign, StoryChapter, StoryDifficulty
from structure.interactive_story import InteractiveStorySession
from structure.story_battle import StoryBattleSystem
from structure.emoji import getEmoji
from utilis.utilis import create_embed, INFO_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR

# Button classes for story interface
class InteractiveStoryButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Interactive Story",
            emoji="📖",
            custom_id="interactive_story"
        )

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        await view._do_interactive_story(interaction)

class InteractiveStoryUnavailableButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="Interactive Story",
            emoji="📖",
            custom_id="interactive_story_unavailable",
            disabled=True
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "❌ Interactive story events are not available for this mission yet.",
            ephemeral=True
        )

class StoryMissionView(discord.ui.View):
    """Interactive view for story mission details and actions"""

    def __init__(self, ctx, player, mission):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.mission = mission
        self.author = ctx.author

        # Check if interactive story is available for this mission
        self.has_interactive_story = self._check_interactive_story_available()

        # Setup buttons based on available features
        self.setup_buttons()

    def _check_interactive_story_available(self):
        """Check if interactive story events are available for this mission"""
        try:
            # Use the converted STORY_EVENTS from interactive_story.py
            from structure.interactive_story import STORY_EVENTS
            return self.mission.id in STORY_EVENTS and len(STORY_EVENTS[self.mission.id]) > 0
        except ImportError:
            return False

    def setup_buttons(self):
        """Setup buttons based on available features"""
        # Only add interactive story button if events are available
        if self.has_interactive_story:
            self.add_item(InteractiveStoryButton())
        else:
            # Add a disabled button to show it's not available
            self.add_item(InteractiveStoryUnavailableButton())
    
    async def create_mission_embed(self):
        """Create detailed mission embed"""
        embed = discord.Embed(
            title=f"📖 {self.mission.name}",
            description=self.mission.description,
            color=INFO_COLOR
        )
        
        # Chapter and difficulty
        chapter_emoji = {
            StoryChapter.PROLOGUE: "🌅",
            StoryChapter.DOUBLE_DUNGEON: "⚡",
            StoryChapter.FIRST_REAWAKENING: "🔥",
            StoryChapter.CARTENON_TEMPLE: "🏛️",
            StoryChapter.DEMON_CASTLE: "🏰",
            StoryChapter.RED_GATE: "🔴",
            StoryChapter.SHADOW_MONARCH: "👑",
            StoryChapter.JEJU_ISLAND: "🏝️",
            StoryChapter.MONARCHS_WAR: "⚔️",
            StoryChapter.FINAL_BATTLE: "💀"
        }.get(self.mission.chapter, "📖")
        
        difficulty_emoji = {
            StoryDifficulty.NORMAL: "🟢",
            StoryDifficulty.HARD: "🟡",
            StoryDifficulty.NIGHTMARE: "🔴"
        }.get(self.mission.difficulty, "🟢")
        
        embed.add_field(
            name="📚 Chapter",
            value=f"{chapter_emoji} {self.mission.chapter.value.replace('_', ' ').title()}",
            inline=True
        )
        
        embed.add_field(
            name="⚡ Difficulty",
            value=f"{difficulty_emoji} {self.mission.difficulty.value.title()}",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Level Required",
            value=f"Level {self.mission.level_requirement}",
            inline=True
        )
        
        # Objectives
        if self.mission.objectives:
            objectives_text = "\n".join([f"• {obj}" for obj in self.mission.objectives])
            embed.add_field(
                name="🎯 Objectives",
                value=objectives_text,
                inline=False
            )
        
        # Rewards
        rewards = self.mission.rewards
        reward_text = []
        if rewards.gold > 0:
            reward_text.append(f"{getEmoji('gold')} {rewards.gold:,} Gold")
        if rewards.xp > 0:
            reward_text.append(f"⭐ {rewards.xp:,} XP")
        if rewards.diamonds > 0:
            reward_text.append(f"{getEmoji('diamond')} {rewards.diamonds} Diamonds")
        if rewards.tickets > 0:
            reward_text.append(f"{getEmoji('ticket')} {rewards.tickets} Tickets")
        if rewards.stat_points > 0:
            reward_text.append(f"💪 {rewards.stat_points} Stat Points")
        if rewards.skill_points > 0:
            reward_text.append(f"🧠 {rewards.skill_points} Skill Points")
        if rewards.title:
            reward_text.append(f"🏆 Title: {rewards.title}")
        
        if reward_text:
            embed.add_field(
                name="🎁 Rewards",
                value="\n".join(reward_text),
                inline=False
            )
        
        # Prerequisites
        if self.mission.prerequisites:
            prereq_names = []
            for prereq_id in self.mission.prerequisites:
                prereq_mission = StoryCampaign.STORY_MISSIONS.get(prereq_id)
                if prereq_mission:
                    prereq_names.append(prereq_mission.name)
                else:
                    prereq_names.append(prereq_id)
            
            embed.add_field(
                name="📋 Prerequisites",
                value="\n".join([f"• {name}" for name in prereq_names]),
                inline=False
            )
        
        # Check availability
        is_available, reason = await StoryCampaign.is_mission_available(self.player.id, self.mission.id)
        if not is_available:
            embed.add_field(
                name="❌ Status",
                value=reason,
                inline=False
            )
            embed.color = ERROR_COLOR
        else:
            embed.add_field(
                name="✅ Status",
                value="Ready to start!",
                inline=False
            )
            embed.color = SUCCESS_COLOR
        
        embed.set_footer(text=f"Mission ID: {self.mission.id}")
        return embed



    async def _do_interactive_story(self, interaction: discord.Interaction):
        """Start interactive story mode for this mission"""
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can start missions.", ephemeral=True)
            return

        # Check if mission is available
        is_available, reason = await StoryCampaign.is_mission_available(self.player.id, self.mission.id)
        if not is_available:
            await interaction.response.send_message(f"❌ Mission not available: {reason}", ephemeral=True)
            return

        # Check if interactive story is available
        if not self.has_interactive_story:
            await interaction.response.send_message(
                "❌ Interactive story events are not available for this mission yet.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            # Start interactive story session with correct constructor
            story_session = InteractiveStorySession(
                player_id=str(self.player.id),
                mission_id=self.mission.id,
                ctx=self.ctx,
                bot=interaction.client
            )

            # Start the interactive story session with interaction
            success = await story_session.start_story_session(interaction=interaction)
            if not success:
                await interaction.followup.send(
                    "❌ Interactive story events are not available for this mission yet.",
                    ephemeral=True
                )

        except Exception as e:
            print(f"Error starting interactive story: {e}")
            await interaction.followup.send(
                "❌ Failed to start interactive story. Please try again later.",
                ephemeral=True
            )

    @discord.ui.button(label="Back to Campaign", style=discord.ButtonStyle.gray, emoji="🔙")
    async def back_to_campaign(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can navigate.", ephemeral=True)
            return

        # Go back to main story campaign view
        view = StoryCampaignView(self.ctx, self.player)
        await view.update_select_options()  # Ensure dropdown is properly initialized
        embed = await view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=view)

class StoryCampaignView(discord.ui.View):
    """Main story campaign interface"""
    
    def __init__(self, ctx, player):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player = player
        self.author = ctx.author
        self.current_page = 0

        # Initialize the select dropdown with placeholder options
        self.mission_select_dropdown = discord.ui.Select(
            placeholder="Choose a story mission to view details...",
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label="Loading...", value="loading", description="Please wait...")]
        )
        self.mission_select_dropdown.callback = self.mission_select_callback
        self.add_item(self.mission_select_dropdown)
    
    async def create_main_embed(self):
        """Create main story campaign embed"""
        embed = discord.Embed(
            title="📖 Solo Leveling - Story Campaign",
            description="Follow Sung Jin-Woo's journey from the weakest hunter to the Shadow Monarch",
            color=INFO_COLOR
        )
        
        # Get player progress
        progress = await StoryCampaign.get_player_story_progress(self.player.id)
        completed_missions = await StoryCampaign.get_completed_missions(self.player.id)
        available_missions = await StoryCampaign.get_available_missions(self.player.id)
        
        # Progress summary
        total_missions = len(StoryCampaign.STORY_MISSIONS)
        completed_count = len(completed_missions)
        progress_percentage = (completed_count / total_missions) * 100 if total_missions > 0 else 0
        
        embed.add_field(
            name="📊 Progress",
            value=f"**{completed_count}/{total_missions}** missions completed ({progress_percentage:.1f}%)",
            inline=False
        )
        
        # Available missions
        if available_missions:
            mission_text = []
            for mission in available_missions[:5]:  # Show first 5 available
                chapter_emoji = {
                    StoryChapter.PROLOGUE: "🌅",
                    StoryChapter.DOUBLE_DUNGEON: "⚡",
                    StoryChapter.FIRST_REAWAKENING: "🔥"
                }.get(mission.chapter, "📖")
                
                difficulty_emoji = {
                    StoryDifficulty.NORMAL: "🟢",
                    StoryDifficulty.HARD: "🟡",
                    StoryDifficulty.NIGHTMARE: "🔴"
                }.get(mission.difficulty, "🟢")
                
                mission_text.append(f"{chapter_emoji} **{mission.name}** {difficulty_emoji}")
            
            embed.add_field(
                name="🎯 Available Missions",
                value="\n".join(mission_text) if mission_text else "No missions available",
                inline=False
            )
        
        # Recent completions
        if completed_missions:
            recent = completed_missions[-3:]  # Last 3 completed
            recent_text = []
            for mission in recent:
                recent_text.append(f"✅ {mission.name}")
            
            embed.add_field(
                name="✅ Recently Completed",
                value="\n".join(recent_text),
                inline=False
            )
        
        embed.set_footer(text="Select a mission below to view details and start your adventure!")
        return embed

    async def mission_select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ Only the command user can select missions.", ephemeral=True)
            return

        mission_id = interaction.data['values'][0]

        # Handle "none" option
        if mission_id == "none":
            await interaction.response.send_message("❌ No missions are currently available. Complete prerequisites or level up to unlock missions.", ephemeral=True)
            return

        mission = StoryCampaign.STORY_MISSIONS.get(mission_id)

        if not mission:
            await interaction.response.send_message("❌ Mission not found.", ephemeral=True)
            return

        # Create mission detail view
        mission_view = StoryMissionView(self.ctx, self.player, mission)
        embed = await mission_view.create_mission_embed()
        await interaction.response.edit_message(embed=embed, view=mission_view)

    async def update_select_options(self):
        """Update the select dropdown with available missions"""
        available_missions = await StoryCampaign.get_available_missions(self.player.id)
        completed_missions = await StoryCampaign.get_completed_missions(self.player.id)

        # Combine available and completed missions for selection
        all_missions = available_missions + completed_missions

        # Sort by chapter and mission order
        chapter_order = {
            StoryChapter.PROLOGUE: 0,
            StoryChapter.DOUBLE_DUNGEON: 1,
            StoryChapter.FIRST_REAWAKENING: 2,
            StoryChapter.CARTENON_TEMPLE: 3,
            StoryChapter.DEMON_CASTLE: 4,
            StoryChapter.RED_GATE: 5,
            StoryChapter.SHADOW_MONARCH: 6,
            StoryChapter.JEJU_ISLAND: 7,
            StoryChapter.MONARCHS_WAR: 8,
            StoryChapter.FINAL_BATTLE: 9
        }

        all_missions.sort(key=lambda m: (chapter_order.get(m.chapter, 999), m.id))

        # Create select options (max 25) - ensure unique values
        options = []
        used_values = set()

        for mission in all_missions[:25]:
            # Skip if we've already added this mission ID (prevent duplicates)
            if mission.id in used_values:
                continue
            used_values.add(mission.id)

            # Check if completed
            progress = await StoryCampaign.get_player_story_progress(self.player.id)
            is_completed = mission.id in progress and progress[mission.id].get("completed", False)

            chapter_emoji = {
                StoryChapter.PROLOGUE: "🌅",
                StoryChapter.DOUBLE_DUNGEON: "⚡",
                StoryChapter.FIRST_REAWAKENING: "🔥",
                StoryChapter.CARTENON_TEMPLE: "🏛️",
                StoryChapter.DEMON_CASTLE: "🏰",
                StoryChapter.RED_GATE: "🔴",
                StoryChapter.SHADOW_MONARCH: "👑",
                StoryChapter.JEJU_ISLAND: "🏝️",
                StoryChapter.MONARCHS_WAR: "⚔️",
                StoryChapter.FINAL_BATTLE: "💀"
            }.get(mission.chapter, "📖")

            status_emoji = "✅" if is_completed else "🎯"

            options.append(discord.SelectOption(
                label=f"{mission.name}",
                description=f"Level {mission.level_requirement} | {mission.chapter.value.replace('_', ' ').title()}",
                value=mission.id,
                emoji=f"{status_emoji}"
            ))

        if not options:
            options.append(discord.SelectOption(
                label="No missions available",
                description="Complete prerequisites to unlock missions",
                value="none",
                emoji="❌"
            ))

        # Update the select dropdown options
        if hasattr(self, 'mission_select_dropdown') and self.mission_select_dropdown:
            self.mission_select_dropdown.options = options





class StoryCog(commands.Cog):
    """Story Campaign system for Solo Leveling bot"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="story", aliases=["campaign", "storyline"], help="Access the Solo Leveling story campaign system.")
    async def story_campaign(self, ctx: commands.Context, mission: Optional[str] = None):
        """Main story campaign command"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = create_embed(
                "❌ Not Started",
                "You haven't started your adventure yet. Use `sl start` to begin your journey as a hunter!",
                ERROR_COLOR,
                ctx.author
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # If specific mission requested
        if mission:
            mission_data = StoryCampaign.STORY_MISSIONS.get(mission)
            if not mission_data:
                embed = create_embed(
                    "❌ Mission Not Found",
                    f"Mission '{mission}' does not exist. Use `sl story` to see available missions.",
                    ERROR_COLOR,
                    ctx.author
                )
                await ctx.reply(embed=embed, mention_author=False)
                return

            # Show specific mission
            mission_view = StoryMissionView(ctx, player, mission_data)
            embed = await mission_view.create_mission_embed()
            await ctx.reply(embed=embed, view=mission_view, mention_author=False)
            return

        # Show main campaign interface
        view = StoryCampaignView(ctx, player)
        await view.update_select_options()
        embed = await view.create_main_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)

    @commands.command(name="story_progress", aliases=["progress"], help="View your story campaign progress.")
    async def story_progress(self, ctx: commands.Context):
        """View detailed story progress"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = create_embed(
                "❌ Not Started",
                "You haven't started your adventure yet. Use `sl start` to begin!",
                ERROR_COLOR,
                ctx.author
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        progress = await StoryCampaign.get_player_story_progress(player.id)
        completed_missions = await StoryCampaign.get_completed_missions(player.id)
        available_missions = await StoryCampaign.get_available_missions(player.id)

        embed = discord.Embed(
            title=f"📊 {ctx.author.display_name}'s Story Progress",
            description="Your journey through the Solo Leveling story campaign",
            color=INFO_COLOR
        )

        # Overall progress
        total_missions = len(StoryCampaign.STORY_MISSIONS)
        completed_count = len(completed_missions)
        progress_percentage = (completed_count / total_missions) * 100 if total_missions > 0 else 0

        embed.add_field(
            name="📈 Overall Progress",
            value=f"**{completed_count}/{total_missions}** missions completed\n**{progress_percentage:.1f}%** story completion",
            inline=False
        )

        # Chapter progress
        chapter_progress = {}
        for mission in StoryCampaign.STORY_MISSIONS.values():
            chapter = mission.chapter
            if chapter not in chapter_progress:
                chapter_progress[chapter] = {"total": 0, "completed": 0}
            chapter_progress[chapter]["total"] += 1
            if mission.id in progress and progress[mission.id].get("completed", False):
                chapter_progress[chapter]["completed"] += 1

        chapter_text = []
        for chapter, data in chapter_progress.items():
            chapter_name = chapter.value.replace('_', ' ').title()
            completion = (data["completed"] / data["total"]) * 100 if data["total"] > 0 else 0
            chapter_emoji = {
                StoryChapter.PROLOGUE: "🌅",
                StoryChapter.DOUBLE_DUNGEON: "⚡",
                StoryChapter.FIRST_REAWAKENING: "🔥"
            }.get(chapter, "📖")

            chapter_text.append(f"{chapter_emoji} **{chapter_name}**: {data['completed']}/{data['total']} ({completion:.0f}%)")

        if chapter_text:
            embed.add_field(
                name="📚 Chapter Progress",
                value="\n".join(chapter_text),
                inline=False
            )

        # Next available missions
        if available_missions:
            next_missions = available_missions[:3]
            next_text = []
            for mission in next_missions:
                next_text.append(f"🎯 **{mission.name}** (Level {mission.level_requirement})")

            embed.add_field(
                name="🎯 Next Available",
                value="\n".join(next_text),
                inline=False
            )

        embed.set_footer(text="Use 'sl story' to continue your adventure!")
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(StoryCog(bot))
