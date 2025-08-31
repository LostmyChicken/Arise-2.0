"""
Enhanced Interactive Story System for Solo Leveling
Provides immersive story experiences with choices, battles, and character interactions
"""
import discord
import asyncio
import random
import json
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from structure.player import Player
from structure.emoji import getEmoji
from utilis.utilis import create_embed, INFO_COLOR, SUCCESS_COLOR, ERROR_COLOR, WARNING_COLOR

# Custom GIF links for boss battles - EDIT THESE URLs
BOSS_BATTLE_GIFS = {
    "victory": {
        # PROLOGUE CHAPTER
        "prologue_001": "https://your-custom-gif-url-here.gif",  # TODO: Goblin Scout victory GIF
        "prologue_002": "https://your-custom-gif-url-here.gif",  # TODO: Hunter's License celebration GIF
        "prologue_003": "https://your-custom-gif-url-here.gif",  # TODO: Goblin Warrior victory GIF

        # DOUBLE DUNGEON CHAPTER
        "double_dungeon_001": "https://your-custom-gif-url-here.gif",  # TODO: Stone Statue victory GIF
        "double_dungeon_002": "https://your-custom-gif-url-here.gif",  # TODO: System awakening GIF

        # INSTANT DUNGEON & JOB CHANGE
        "instant_dungeon_001": "https://your-custom-gif-url-here.gif",  # TODO: Giant Centipede victory GIF
        "job_change_001": "https://i.imgur.com/YourJobChangeGIF.gif",  # Job Change Quest completion GIF

        # REAWAKENING CHAPTER
        "reawakening_001": "https://your-custom-gif-url-here.gif",  # TODO: Testing Golem victory GIF

        # CARTENON TEMPLE CHAPTER
        "cartenon_001": "https://your-custom-gif-url-here.gif",  # TODO: Temple Guardian victory GIF
        "cartenon_002": "https://your-custom-gif-url-here.gif",  # TODO: Temple Secret discovery GIF

        # DEMON CASTLE CHAPTER
        "demon_castle_001": "https://your-custom-gif-url-here.gif",  # TODO: Demon Guards victory GIF
        "demon_castle_002": "https://your-custom-gif-url-here.gif",  # TODO: Demon King victory GIF (the one that was auto-completing!)

        # RED GATE CHAPTER
        "red_gate_001": "https://your-custom-gif-url-here.gif",  # TODO: Red Gate Guardian victory GIF

        # SHADOW MONARCH CHAPTER
        "shadow_monarch_001": "https://your-custom-gif-url-here.gif",  # TODO: Shadow Monarch awakening GIF

        # JEJU ISLAND CHAPTER
        "jeju_island_001": "https://your-custom-gif-url-here.gif",  # TODO: Ant Queen victory GIF
        "jeju_island_002": "https://your-custom-gif-url-here.gif",  # TODO: Beru extraction GIF

        # MONARCHS WAR CHAPTER
        "monarchs_war_001": "https://your-custom-gif-url-here.gif",  # TODO: Beast Monarch victory GIF
        "monarchs_war_002": "https://your-custom-gif-url-here.gif",  # TODO: Ice Monarch victory GIF
        "monarchs_war_003": "https://your-custom-gif-url-here.gif",  # TODO: Dragon Emperor victory GIF

        # FINAL BATTLE CHAPTER
        "final_battle_001": "https://your-custom-gif-url-here.gif",  # TODO: Architect victory GIF
        "final_battle_002": "https://your-custom-gif-url-here.gif",  # TODO: Ultimate Sacrifice GIF
        "final_battle_003": "https://your-custom-gif-url-here.gif",  # TODO: New Beginning GIF

        # FALLBACK GIFS
        "prologue": "https://your-custom-gif-url-here.gif",  # TODO: General prologue victory GIF
        "double_dungeon": "https://your-custom-gif-url-here.gif",  # TODO: General double dungeon victory GIF
        "first_reawakening": "https://your-custom-gif-url-here.gif",  # TODO: General reawakening victory GIF
        "cartenon_temple": "https://your-custom-gif-url-here.gif",  # TODO: General temple victory GIF
        "demon_castle": "https://your-custom-gif-url-here.gif",  # TODO: General demon castle victory GIF
        "red_gate": "https://your-custom-gif-url-here.gif",  # TODO: General red gate victory GIF
        "shadow_monarch": "https://your-custom-gif-url-here.gif",  # TODO: General shadow monarch victory GIF
        "jeju_island": "https://your-custom-gif-url-here.gif",  # TODO: General jeju island victory GIF
        "monarchs_war": "https://your-custom-gif-url-here.gif",  # TODO: General monarchs war victory GIF
        "final_battle": "https://your-custom-gif-url-here.gif",  # TODO: General final battle victory GIF
        "default": "https://your-custom-gif-url-here.gif"  # TODO: Default victory GIF
    },
    "defeat": {
        # SPECIFIC DEFEAT GIFS
        "prologue_001": "https://your-custom-gif-url-here.gif",  # TODO: Goblin defeat GIF
        "double_dungeon_001": "https://your-custom-gif-url-here.gif",  # TODO: Stone Statue defeat GIF
        "demon_castle_002": "https://your-custom-gif-url-here.gif",  # TODO: Demon King defeat GIF
        "monarchs_war_001": "https://your-custom-gif-url-here.gif",  # TODO: Beast Monarch defeat GIF
        "monarchs_war_002": "https://your-custom-gif-url-here.gif",  # TODO: Ice Monarch defeat GIF
        "monarchs_war_003": "https://your-custom-gif-url-here.gif",  # TODO: Dragon Emperor defeat GIF
        "final_battle_001": "https://your-custom-gif-url-here.gif",  # TODO: Architect defeat GIF

        # FALLBACK DEFEAT GIFS
        "default": "https://your-custom-gif-url-here.gif"  # TODO: Default defeat GIF
    }
}

def get_boss_battle_gif(mission_id: str, result: str = "victory") -> str:
    """Get the appropriate GIF URL for a boss battle result"""
    if result in BOSS_BATTLE_GIFS and mission_id in BOSS_BATTLE_GIFS[result]:
        return BOSS_BATTLE_GIFS[result][mission_id]

    # Try chapter-based fallback
    chapter_mapping = {
        "prologue": ["prologue_001", "prologue_002", "prologue_003"],
        "double_dungeon": ["double_dungeon_001", "double_dungeon_002"],
        "first_reawakening": ["reawakening_001"],
        "cartenon_temple": ["cartenon_001", "cartenon_002"],
        "demon_castle": ["demon_castle_001", "demon_castle_002"],
        "red_gate": ["red_gate_001"],
        "shadow_monarch": ["shadow_monarch_001"],
        "jeju_island": ["jeju_island_001", "jeju_island_002"],
        "monarchs_war": ["monarchs_war_001", "monarchs_war_002", "monarchs_war_003"],
        "final_battle": ["final_battle_001", "final_battle_002", "final_battle_003"]
    }

    for chapter, missions in chapter_mapping.items():
        if mission_id in missions and chapter in BOSS_BATTLE_GIFS[result]:
            return BOSS_BATTLE_GIFS[result][chapter]

    # Default fallback
    return BOSS_BATTLE_GIFS[result].get("default", "https://your-custom-gif-url-here.gif")

class StoryEventType(Enum):
    """Types of story events"""
    DIALOGUE = "dialogue"
    CHOICE = "choice"
    BATTLE = "battle"
    EXPLORATION = "exploration"
    CUTSCENE = "cutscene"
    REWARD = "reward"
    SYSTEM_MESSAGE = "system_message"
    CHARACTER_INTERACTION = "character_interaction"

class StoryChoiceType(Enum):
    """Types of story choices"""
    DIALOGUE_RESPONSE = "dialogue_response"
    ACTION_CHOICE = "action_choice"
    MORAL_CHOICE = "moral_choice"
    BATTLE_STRATEGY = "battle_strategy"
    EXPLORATION_PATH = "exploration_path"
    EXPLORATION_CHOICE = "exploration_choice"
    SYSTEM_CHOICE = "system_choice"

@dataclass
class StoryChoice:
    """A choice the player can make in the story"""
    id: str
    text: str
    description: str
    choice_type: StoryChoiceType
    requirements: Dict[str, Any] = None  # Level, stats, items, etc.
    consequences: Dict[str, Any] = None  # What happens when chosen
    emoji: str = "🔹"
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = {}
        if self.consequences is None:
            self.consequences = {}

@dataclass
class StoryEvent:
    """A story event with interactive elements"""
    id: str
    event_type: StoryEventType
    title: str
    description: str
    speaker: str = None
    dialogue: str = None  # What the speaker says
    choices: List[StoryChoice] = None
    battle_enemies: List[Dict] = None  # For battle events
    auto_continue: bool = False
    delay: float = 2.0
    image_url: str = None
    color: int = INFO_COLOR
    
    def __post_init__(self):
        if self.choices is None:
            self.choices = []
        if self.battle_enemies is None:
            self.battle_enemies = []

@dataclass
class StoryBattleEnemy:
    """Enemy in story battles"""
    name: str
    level: int
    hp: int
    max_hp: int
    attack: int
    defense: int
    skills: List[str] = None
    weakness: str = None
    resistance: str = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []

@dataclass
class StoryBattle:
    """Interactive story battle"""
    id: str
    name: str
    description: str
    enemies: List[StoryBattleEnemy]
    environment: str = "dungeon"
    special_conditions: Dict[str, Any] = None
    victory_conditions: Dict[str, Any] = None
    defeat_conditions: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.special_conditions is None:
            self.special_conditions = {}
        if self.victory_conditions is None:
            self.victory_conditions = {"defeat_all_enemies": True}
        if self.defeat_conditions is None:
            self.defeat_conditions = {"player_hp_zero": True}

class InteractiveStorySession:
    """Manages an interactive story session for a player"""
    
    def __init__(self, player_id: str, mission_id: str, ctx, bot):
        self.player_id = player_id
        self.mission_id = mission_id
        self.ctx = ctx
        self.bot = bot
        self.current_event_index = 0
        self.story_state = {}
        self.player_choices = {}
        self.battle_state = None
        self.session_active = True
        
    async def start_story_session(self, message=None, interaction=None) -> bool:
        """Start the interactive story session"""
        try:
            # Load story events for this mission
            self.story_events = self.load_story_events()
            if not self.story_events:
                # Fallback to basic story completion
                return False

            # Initialize session
            self.session_active = True
            self.current_event_index = 0
            self.story_message = message  # Store the message to edit

            # Get player data for proper stats
            from structure.player import Player
            player = await Player.get(self.player_id)

            # Initialize story state with actual player stats
            self.story_state = {
                "player_hp": player.hp if player else 100,
                "player_max_hp": player.hp if player else 100,
                "player_mp": player.mp if player else 100,
                "player_max_mp": player.mp if player else 100,
                "player_attack": player.attack if player else 10,
                "player_defense": player.defense if player else 10,
                "confidence": 0,
                "humility": 0,
                "caution": 0,
                "courage": 0,
                "team_relationships": {},
                "inventory_used": [],
                "allies_met": [],
                "enemies_defeated": []
            }

            # Ensure all required lists are properly initialized
            for key in ["inventory_used", "allies_met", "enemies_defeated"]:
                if key not in self.story_state or not isinstance(self.story_state[key], list):
                    self.story_state[key] = []

            # Display first event
            await self.display_current_event(message, interaction)

            return True

        except Exception as e:
            print(f"Error starting story session: {e}")
            return False

    def load_story_events(self) -> List[StoryEvent]:
        """Load story events for the current mission"""
        return STORY_EVENTS.get(self.mission_id, [])

    async def display_current_event(self, message=None, interaction=None):
        """Display the current story event in the same UI"""
        if self.current_event_index >= len(self.story_events):
            await self.complete_story_session(message)
            return

        current_event = self.story_events[self.current_event_index]

        # Check if this is a battle event
        if current_event.event_type == StoryEventType.BATTLE:
            await self.start_story_battle(current_event, message)
            return

        # Create event embed
        embed = discord.Embed(
            title=f"{getEmoji('info')} {current_event.title}",
            description=current_event.description,
            color=INFO_COLOR
        )

        # Add speaker and dialogue
        if current_event.speaker and current_event.dialogue:
            embed.add_field(
                name=f"💬 {current_event.speaker}",
                value=f"*\"{current_event.dialogue}\"*",
                inline=False
            )

        # Add progress indicator
        embed.add_field(
            name="📊 Progress",
            value=f"{self.current_event_index + 1}/{len(self.story_events)}",
            inline=True
        )

        # Create choice view if there are choices
        if current_event.choices:
            view = StoryChoiceView(self, current_event)
            if interaction and not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=view)
                self.story_message = await interaction.original_response()
            elif message:
                await message.edit(embed=embed, view=view)
            else:
                self.story_message = await self.ctx.send(embed=embed, view=view)
        else:
            # Create continue button for proper story pacing
            view = StoryContinueView(self)
            if interaction and not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=view)
                self.story_message = await interaction.original_response()
            elif message:
                await message.edit(embed=embed, view=view)
            else:
                self.story_message = await self.ctx.send(embed=embed, view=view)

    async def start_story_battle(self, event: StoryEvent, message=None):
        """Start a story battle using the gate battle system"""
        try:
            # Get the first enemy from the event
            if not event.battle_enemies:
                # No enemies, skip battle
                await self.advance_to_next_event()
                return

            enemy_data = event.battle_enemies[0]

            # Create battle embed
            embed = discord.Embed(
                title=f"{getEmoji('attack')} {event.title}",
                description=event.description,
                color=ERROR_COLOR
            )

            if event.speaker and event.dialogue:
                embed.add_field(
                    name=f"💬 {event.speaker}",
                    value=f"*\"{event.dialogue}\"*",
                    inline=False
                )

            # Enemy info
            embed.add_field(
                name="👹 Enemy Encountered",
                value=f"**{enemy_data['name']}** (Level {enemy_data['level']})\n"
                      f"HP: {enemy_data['hp']} | ATK: {enemy_data['attack']} | DEF: {enemy_data['defense']}",
                inline=False
            )

            # Battle strategy choices
            if event.choices:
                embed.add_field(
                    name=f"{getEmoji('attack')} Choose Your Strategy",
                    value="Select how you want to approach this battle:",
                    inline=False
                )

                try:
                    view = StoryBattleChoiceView(self, event, enemy_data)
                    if message:
                        await message.edit(embed=embed, view=view)
                    else:
                        self.story_message = await self.ctx.send(embed=embed, view=view)
                except Exception as view_error:
                    print(f"Error creating battle choice view: {view_error}")
                    # Fallback to direct battle
                    await self.start_direct_battle(enemy_data)
            else:
                # Direct battle without strategy choices
                await self.start_direct_battle(enemy_data)

        except Exception as e:
            print(f"Error starting story battle: {e}")
            # Fallback to next event
            await self.advance_to_next_event()

    async def start_direct_battle(self, enemy_data: Dict, battle_modifiers: Dict = None):
        """Start a direct battle using gate battle mechanics"""
        try:
            # Import the new story battle system
            from structure.story_battle import StoryBattleView

            # Create battle view with gate battle mechanics
            battle_view = StoryBattleView(
                bot=self.bot,
                player_id=self.player_id,
                enemy_data=enemy_data,
                story_session=self,
                battle_modifiers=battle_modifiers or {}
            )

            # Create battle embed
            embed = discord.Embed(
                title=f"{getEmoji('attack')} Story Battle!",
                description=f"You face the **{enemy_data['name']}** in combat!",
                color=ERROR_COLOR
            )

            embed.add_field(
                name="👹 Enemy",
                value=f"**{enemy_data['name']}** (Level {enemy_data['level']})\n"
                      f"HP: {enemy_data['hp']} | ATK: {enemy_data['attack']}",
                inline=False
            )

            # Use existing story message or create new one
            if self.story_message:
                await self.story_message.edit(embed=embed, view=None)
                message = self.story_message
            else:
                message = await self.ctx.send(embed=embed)
                self.story_message = message

            # Create fake interaction for battle system
            class StoryBattleInteraction:
                def __init__(self, user, channel, message):
                    self.user = user
                    self.channel = channel
                    self.message = message
                    self.response = self
                    self._responded = False

                async def send_message(self, embed=None, view=None, ephemeral=False):
                    if embed and view:
                        return await self.message.edit(embed=embed, view=view)
                    elif embed:
                        return await self.message.edit(embed=embed, view=None)
                    else:
                        return await self.message.edit(content="Battle in progress...")

                async def edit_original_response(self, embed=None, view=None):
                    if embed and view:
                        return await self.message.edit(embed=embed, view=view)
                    elif embed:
                        return await self.message.edit(embed=embed, view=None)
                    else:
                        return self.message

                async def defer(self):
                    pass

                async def response(self):
                    return self

            # Start the battle
            fake_interaction = StoryBattleInteraction(self.ctx.author, self.ctx.channel, message)
            await battle_view.start(fake_interaction)

        except Exception as e:
            print(f"Error in direct battle: {e}")
            # Fallback to next event
            await self.advance_to_next_event()

    async def handle_battle_result(self, won: bool):
        """Handle the result of a story battle"""
        try:
            # Update story state with battle results
            await self.update_story_state_after_battle(won)

            if won:
                embed = discord.Embed(
                    title=f"{getEmoji('tick')} Victory!",
                    description="You have won the battle! Click 'Continue Story' to proceed...",
                    color=SUCCESS_COLOR
                )

                # Add custom victory GIF for this specific mission
                try:
                    victory_gif_url = get_boss_battle_gif(self.mission_id, "victory")
                    if victory_gif_url and victory_gif_url != "https://your-custom-gif-url-here.gif":
                        embed.set_image(url=victory_gif_url)
                except Exception as gif_error:
                    print(f"Error loading victory GIF: {gif_error}")
                    # Continue without GIF

            else:
                embed = discord.Embed(
                    title=f"{getEmoji('negative')} Defeat...",
                    description="You were defeated, but in the world of Solo Leveling, even defeats lead to growth. Click 'Continue Story' to proceed...",
                    color=WARNING_COLOR
                )

                # Add custom defeat GIF for this specific mission
                try:
                    defeat_gif_url = get_boss_battle_gif(self.mission_id, "defeat")
                    if defeat_gif_url and defeat_gif_url != "https://your-custom-gif-url-here.gif":
                        embed.set_image(url=defeat_gif_url)
                except Exception as gif_error:
                    print(f"Error loading defeat GIF: {gif_error}")
                    # Continue without GIF

            # Create continue button instead of auto-advancing
            view = ContinueStoryView(self)

            # Update the same message
            if self.story_message:
                await self.story_message.edit(embed=embed, view=view)
            else:
                self.story_message = await self.ctx.send(embed=embed, view=view)

        except Exception as e:
            print(f"Error handling battle result: {e}")
            await self.advance_to_next_event()

    async def update_story_state_after_battle(self, won: bool):
        """Update story state with current player stats after battle"""
        try:
            from structure.player import Player
            player = await Player.get(self.player_id)

            if player:
                # Update story state with current player stats
                self.story_state["player_hp"] = player.hp
                self.story_state["player_max_hp"] = player.hp
                self.story_state["player_mp"] = player.mp
                self.story_state["player_max_mp"] = player.mp
                self.story_state["player_attack"] = player.attack
                self.story_state["player_defense"] = player.defense

                # Track battle results
                if won:
                    self.story_state["confidence"] = self.story_state.get("confidence", 0) + 1

                    # Safely access current event with bounds checking
                    if (self.current_event_index < len(self.story_events) and
                        self.current_event_index >= 0):
                        current_event = self.story_events[self.current_event_index]
                        if current_event.battle_enemies and len(current_event.battle_enemies) > 0:
                            enemy_name = current_event.battle_enemies[0].get("name", "Unknown Enemy")
                            # Ensure enemies_defeated list exists
                            if "enemies_defeated" not in self.story_state:
                                self.story_state["enemies_defeated"] = []
                            self.story_state["enemies_defeated"].append(enemy_name)
                else:
                    self.story_state["humility"] = self.story_state.get("humility", 0) + 1

        except Exception as e:
            print(f"Error updating story state after battle: {e}")

    async def handle_battle_failure(self):
        """Handle battle failure in story mode"""
        embed = discord.Embed(
            title="💀 Battle Defeat",
            description="You were defeated in battle, but the story continues...",
            color=ERROR_COLOR
        )

        embed.add_field(
            name="📖 Story Continues",
            value="In the world of Solo Leveling, even defeats can lead to growth. Your journey continues.",
            inline=False
        )

        await self.ctx.send(embed=embed)
        await asyncio.sleep(3.0)
        await self.advance_to_next_event()

    async def advance_to_next_event(self):
        """Advance to the next story event - REQUIRES PLAYER INTERACTION"""
        self.current_event_index += 1
        if self.current_event_index < len(self.story_events):
            # NO auto-advancing - always require player interaction
            await self.display_current_event(self.story_message)
        else:
            await self.complete_story_session(self.story_message)

    async def complete_story_session(self, message=None):
        """Complete the story session and offer to continue to next chapter"""
        try:
            # Complete the current mission
            from structure.story_campaign import StoryCampaign
            success, completion_message, reward = await StoryCampaign.complete_mission(self.player_id, self.mission_id)

            embed = discord.Embed(
                title="🎉 Chapter Complete!",
                description="You have completed this chapter of the Solo Leveling story!",
                color=SUCCESS_COLOR
            )

            # Add victory GIF for this mission
            victory_gif_url = get_boss_battle_gif(self.mission_id, "victory")
            if victory_gif_url and victory_gif_url != "https://your-custom-gif-url-here.gif":
                embed.set_image(url=victory_gif_url)

            if success:
                embed.add_field(
                    name="✅ Mission Completed",
                    value=completion_message,
                    inline=False
                )

                # Show rewards if available
                if reward:
                    reward_text = []
                    if reward.gold > 0:
                        reward_text.append(f"💰 **{reward.gold:,}** Gold")
                    if reward.xp > 0:
                        reward_text.append(f"⭐ **{reward.xp:,}** EXP")
                    if reward.diamonds > 0:
                        reward_text.append(f"💎 **{reward.diamonds:,}** Diamonds")
                    if reward.tickets > 0:
                        reward_text.append(f"🎫 **{reward.tickets:,}** Tickets")
                    if reward.stat_points > 0:
                        reward_text.append(f"📊 **{reward.stat_points:,}** Stat Points")
                    if reward.skill_points > 0:
                        reward_text.append(f"🎯 **{reward.skill_points:,}** Skill Points")
                    if reward.title:
                        reward_text.append(f"🏆 **{reward.title}** Title")
                    if hasattr(reward, 'items') and reward.items:
                        from structure.items import ItemManager
                        for item_id in reward.items:
                            # Get actual item from database to show proper name
                            item = await ItemManager.get(item_id)
                            if item:
                                reward_text.append(f"🎁 **{item.name}**")
                            else:
                                # Fallback for items not in database
                                item_name = item_id.replace("_", " ").title()
                                reward_text.append(f"🎁 **{item_name}** (Custom)")

                    if reward_text:
                        embed.add_field(
                            name="🎁 Chapter Rewards",
                            value="\n".join(reward_text),
                            inline=False
                        )

            # Show condensed character development summary
            if self.story_state:
                # Count different types of development
                combat_stats = 0
                personality_traits = 0
                relationships = 0

                for stat, value in self.story_state.items():
                    if isinstance(value, int) and value > 0 and stat not in ['player_hp', 'player_mp']:
                        if stat.lower() in ['player_max_hp', 'player_max_mp', 'player_attack', 'player_defense', 'damage_bonus']:
                            combat_stats += 1
                        elif stat.lower() in ['family_bond', 'teamwork', 'relationships']:
                            relationships += 1
                        else:
                            personality_traits += 1

                if combat_stats > 0 or personality_traits > 0 or relationships > 0:
                    summary_parts = []
                    if combat_stats > 0:
                        summary_parts.append(f"⚔️ Combat: {combat_stats} stats")
                    if personality_traits > 0:
                        summary_parts.append(f"🧠 Personality: {personality_traits} traits")
                    if relationships > 0:
                        summary_parts.append(f"👥 Social: {relationships} bonds")

                    embed.add_field(
                        name="📊 Character Development",
                        value=" • ".join(summary_parts) + "\n*Click button below for details*",
                        inline=False
                    )

            # Check if there's a next mission available
            next_mission = await self.get_next_available_mission()

            if next_mission:
                embed.add_field(
                    name="📚 Next Chapter Available",
                    value=f"**{next_mission.name}**\n{next_mission.description}",
                    inline=False
                )

                # Create completion view with continue option
                view = StoryCompletionView(self.ctx, self.player_id, next_mission, self.story_state)

                if message:
                    await message.edit(embed=embed, view=view)
                else:
                    await self.ctx.send(embed=embed, view=view)
            else:
                embed.add_field(
                    name="🏁 Story Progress",
                    value="You've completed all available chapters! More story content coming soon...",
                    inline=False
                )

                # Create completion view without continue option
                view = StoryCompletionView(self.ctx, self.player_id, None, self.story_state)
                if message:
                    await message.edit(embed=embed, view=view)
                else:
                    await self.ctx.send(embed=embed, view=view)

            self.session_active = False

        except Exception as e:
            print(f"Error completing story session: {e}")
            # Fallback completion
            embed = discord.Embed(
                title=f"{getEmoji('tick')} Story Complete!",
                description="You have completed this chapter of the Solo Leveling story!",
                color=SUCCESS_COLOR
            )

            if message:
                await message.edit(embed=embed, view=None)
            else:
                await self.ctx.send(embed=embed)

            self.session_active = False

    async def get_next_available_mission(self):
        """Get the next available mission for the player"""
        try:
            from structure.story_campaign import StoryCampaign

            # Get all missions
            all_missions = StoryCampaign.STORY_MISSIONS
            mission_order = list(all_missions.keys())

            # Find current mission index
            try:
                current_index = mission_order.index(self.mission_id)
                next_index = current_index + 1

                if next_index < len(mission_order):
                    next_mission_id = mission_order[next_index]
                    next_mission = all_missions[next_mission_id]

                    # Check if it's available
                    is_available, _ = await StoryCampaign.is_mission_available(self.player_id, next_mission_id)
                    if is_available:
                        return next_mission

            except ValueError:
                pass  # Mission not found in order

            return None

        except Exception as e:
            print(f"Error getting next mission: {e}")
            return None

    async def process_choice(self, choice: StoryChoice, interaction: discord.Interaction):
        """Process a story choice"""
        try:
            # Apply choice consequences
            await self.apply_choice_consequences(choice.consequences)

            # Show choice result briefly
            embed = discord.Embed(
                title="✅ Choice Made",
                description=f"You chose: **{choice.text}**",
                color=SUCCESS_COLOR
            )

            if choice.description:
                embed.add_field(
                    name="📝 Result",
                    value=choice.description,
                    inline=False
                )

            # Handle interaction response properly - no back button, just continue
            try:
                await interaction.response.edit_message(embed=embed, view=None)
            except discord.InteractionResponded:
                # If already responded, use followup
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=None)
            except Exception as e:
                # If edit fails, send new message
                await interaction.followup.send(embed=embed, ephemeral=True)

            # Super fast advance to next event
            await asyncio.sleep(0.8)  # Quick pause to read choice result
            await self.advance_to_next_event()

        except Exception as e:
            print(f"Error processing choice: {e}")
            # Try to continue the story even if there's an error
            try:
                await self.advance_to_next_event()
            except Exception as e2:
                print(f"Error advancing to next event: {e2}")
                # Final fallback - complete the session
                await self.complete_story_session(self.story_message)

    async def apply_choice_consequences(self, consequences: Dict[str, Any]):
        """Apply consequences of a choice"""
        if not consequences:
            return

        for key, value in consequences.items():
            if key in self.story_state:
                if isinstance(self.story_state[key], int) and isinstance(value, int):
                    self.story_state[key] += value
                else:
                    self.story_state[key] = value
            else:
                self.story_state[key] = value
    
    async def get_mission_story_events(self) -> List[StoryEvent]:
        """Get story events for the current mission"""
        # This would be expanded with actual story data
        # For now, return sample events based on mission
        
        if self.mission_id == "prologue_001":
            return await self.get_prologue_001_events()
        elif self.mission_id == "double_dungeon_001":
            return await self.get_double_dungeon_001_events()
        elif self.mission_id == "reawakening_001":
            return await self.get_reawakening_001_events()
        else:
            # Default story events
            return await self.get_default_story_events()
    
    async def get_prologue_001_events(self) -> List[StoryEvent]:
        """Get events for the first prologue mission"""
        return [
            StoryEvent(
                id="prologue_001_intro",
                event_type=StoryEventType.CUTSCENE,
                title="The World of Hunters",
                description="*You stand before a mysterious gate, its dark energy pulsing ominously. Other hunters around you prepare their weapons, but you can only grip your rusty dagger with trembling hands.*",
                speaker="Narrator",
                auto_continue=True,
                delay=3.0,
                color=WARNING_COLOR
            ),
            StoryEvent(
                id="prologue_001_dialogue1",
                event_type=StoryEventType.DIALOGUE,
                title="Team Leader's Warning",
                description="Listen up, rookies! This is just an E-rank gate, but don't get cocky. Even the weakest monsters can kill you if you're not careful.",
                speaker="Team Leader",
                choices=[
                    StoryChoice(
                        id="confident",
                        text="I'm ready for anything!",
                        description="Show confidence despite your fear",
                        choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                        emoji="💪",
                        consequences={"confidence": +1, "team_respect": +1}
                    ),
                    StoryChoice(
                        id="nervous",
                        text="I'll be careful...",
                        description="Admit your nervousness",
                        choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                        emoji="😰",
                        consequences={"caution": +1, "team_concern": +1}
                    ),
                    StoryChoice(
                        id="silent",
                        text="*Stay silent*",
                        description="Keep your thoughts to yourself",
                        choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                        emoji="🤐",
                        consequences={"mystery": +1}
                    )
                ]
            ),
            StoryEvent(
                id="prologue_001_exploration",
                event_type=StoryEventType.EXPLORATION,
                title="Entering the Dungeon",
                description="*The gate's energy washes over you as you step through. The dungeon is dark and damp, with the sound of dripping water echoing through the corridors.*",
                speaker="Narrator",
                choices=[
                    StoryChoice(
                        id="stay_back",
                        text="Stay at the back of the group",
                        description="Play it safe and let others lead",
                        choice_type=StoryChoiceType.ACTION_CHOICE,
                        emoji="🛡️",
                        consequences={"safety": +1, "experience": -1}
                    ),
                    StoryChoice(
                        id="middle_ground",
                        text="Stay in the middle",
                        description="Maintain a balanced position",
                        choice_type=StoryChoiceType.ACTION_CHOICE,
                        emoji="⚖️",
                        consequences={"balance": +1}
                    ),
                    StoryChoice(
                        id="scout_ahead",
                        text="Volunteer to scout ahead",
                        description="Take initiative despite the danger",
                        choice_type=StoryChoiceType.ACTION_CHOICE,
                        emoji="🔍",
                        requirements={"confidence": 1},
                        consequences={"courage": +1, "danger": +1, "experience": +1}
                    )
                ]
            ),
            StoryEvent(
                id="prologue_001_battle",
                event_type=StoryEventType.BATTLE,
                title="First Encounter",
                description="*Three goblins emerge from the shadows, their red eyes gleaming with malice. Your heart pounds as you realize this is your first real fight.*",
                speaker="System",
                color=ERROR_COLOR
            )
        ]
    
    async def get_double_dungeon_001_events(self) -> List[StoryEvent]:
        """Get events for the double dungeon mission"""
        return [
            StoryEvent(
                id="double_dungeon_intro",
                event_type=StoryEventType.CUTSCENE,
                title="The Mysterious Double Dungeon",
                description="*You stand before an unusual gate - one that seems to have another gate hidden within it. The other hunters look nervous, and even the experienced ones seem unsure.*",
                speaker="Narrator",
                auto_continue=True,
                delay=3.0,
                color=ERROR_COLOR
            ),
            StoryEvent(
                id="double_dungeon_warning",
                event_type=StoryEventType.DIALOGUE,
                title="Ominous Feeling",
                description="Something's not right about this place. The mana readings are all wrong. Maybe we should report this and come back with a stronger team.",
                speaker="Experienced Hunter",
                choices=[
                    StoryChoice(
                        id="agree_retreat",
                        text="I agree, let's retreat",
                        description="Support the cautious approach",
                        choice_type=StoryChoiceType.MORAL_CHOICE,
                        emoji="🚪",
                        consequences={"wisdom": +1, "missed_opportunity": True}
                    ),
                    StoryChoice(
                        id="press_forward",
                        text="We've come this far",
                        description="Encourage the team to continue",
                        choice_type=StoryChoiceType.MORAL_CHOICE,
                        emoji="⚔️",
                        consequences={"determination": +1, "fate_sealed": True}
                    ),
                    StoryChoice(
                        id="suggest_caution",
                        text="Let's be extra careful",
                        description="Propose a middle ground",
                        choice_type=StoryChoiceType.MORAL_CHOICE,
                        emoji="⚠️",
                        consequences={"caution": +1, "team_unity": +1}
                    )
                ]
            )
        ]
    
    async def get_reawakening_001_events(self) -> List[StoryEvent]:
        """Get events for the reawakening test mission"""
        return [
            StoryEvent(
                id="reawakening_intro",
                event_type=StoryEventType.CUTSCENE,
                title="The Hunter Association",
                description="*You stand in the pristine halls of the Hunter Association, surrounded by powerful hunters. The System has changed you, but now you need to prove it officially.*",
                speaker="Narrator",
                auto_continue=True,
                delay=3.0,
                color=SUCCESS_COLOR
            ),
            StoryEvent(
                id="reawakening_test_prep",
                event_type=StoryEventType.DIALOGUE,
                title="Test Administrator",
                description="Your previous rank was E, the lowest possible. But your recent dungeon reports suggest something has changed. Are you ready for the reawakening test?",
                speaker="Test Administrator",
                choices=[
                    StoryChoice(
                        id="confident_ready",
                        text="I'm ready to show my true power",
                        description="Display confidence in your new abilities",
                        choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                        emoji="💪",
                        consequences={"confidence": +2, "intimidation": +1}
                    ),
                    StoryChoice(
                        id="humble_ready",
                        text="I'll do my best",
                        description="Show humility despite your power",
                        choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                        emoji="🙏",
                        consequences={"humility": +1, "respect": +1}
                    ),
                    StoryChoice(
                        id="mysterious",
                        text="Let the test speak for itself",
                        description="Remain mysterious about your abilities",
                        choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                        emoji="🎭",
                        consequences={"mystery": +2, "intrigue": +1}
                    )
                ]
            )
        ]
    
    async def get_default_story_events(self) -> List[StoryEvent]:
        """Get default story events for missions without specific events"""
        return [
            StoryEvent(
                id="default_intro",
                event_type=StoryEventType.CUTSCENE,
                title="The Journey Continues",
                description="*Your adventure continues as you face new challenges and grow stronger.*",
                speaker="Narrator",
                auto_continue=True,
                delay=2.0
            )
        ]
    
    async def process_next_event(self):
        """Process the next story event"""
        if not self.session_active:
            return
        
        events = self.story_state.get("events", [])
        current_index = self.story_state.get("current_index", 0)
        
        if current_index >= len(events):
            await self.complete_story_session()
            return
        
        current_event = events[current_index]
        
        if current_event.event_type == StoryEventType.CUTSCENE:
            await self.process_cutscene_event(current_event)
        elif current_event.event_type == StoryEventType.DIALOGUE:
            await self.process_dialogue_event(current_event)
        elif current_event.event_type == StoryEventType.CHOICE:
            await self.process_choice_event(current_event)
        elif current_event.event_type == StoryEventType.BATTLE:
            await self.process_battle_event(current_event)
        elif current_event.event_type == StoryEventType.EXPLORATION:
            await self.process_exploration_event(current_event)
        else:
            # Default processing
            await self.advance_to_next_event()
    
    async def process_cutscene_event(self, event: StoryEvent):
        """Process a cutscene event"""
        embed = discord.Embed(
            title=f"📖 {event.title}",
            description=event.description,
            color=event.color
        )
        
        if event.speaker and event.speaker != "Narrator":
            embed.add_field(
                name=f"💬 {event.speaker}",
                value="*Speaking...*",
                inline=False
            )
        
        embed.set_footer(text="Click 'Continue Story' to proceed...")

        # Add continue button instead of auto-advancing
        view = ContinueStoryView(self)
        message = await self.ctx.send(embed=embed, view=view)
        self.story_message = message
    
    async def process_dialogue_event(self, event: StoryEvent):
        """Process a dialogue event with choices"""
        embed = discord.Embed(
            title=f"💬 {event.title}",
            description=event.description,
            color=event.color
        )
        
        if event.speaker:
            embed.add_field(
                name=f"🗣️ {event.speaker}",
                value="*Waiting for your response...*",
                inline=False
            )
        
        # Create choice view
        view = StoryChoiceView(self, event)
        message = await self.ctx.send(embed=embed, view=view)
    
    async def process_exploration_event(self, event: StoryEvent):
        """Process an exploration event with action choices"""
        embed = discord.Embed(
            title=f"🗺️ {event.title}",
            description=event.description,
            color=event.color
        )
        
        embed.add_field(
            name="🤔 What do you do?",
            value="Choose your action carefully...",
            inline=False
        )
        
        # Create choice view
        view = StoryChoiceView(self, event)
        message = await self.ctx.send(embed=embed, view=view)
    
    async def process_battle_event(self, event: StoryEvent):
        """Process a battle event"""
        # This will be implemented in the battle system
        embed = discord.Embed(
            title=f"⚔️ {event.title}",
            description=event.description,
            color=ERROR_COLOR
        )
        
        embed.add_field(
            name="🎮 Battle System",
            value="Interactive battle system will be implemented here",
            inline=False
        )
        
        # Add continue button instead of auto-advancing
        view = ContinueStoryView(self)
        message = await self.ctx.send(embed=embed, view=view)
        self.story_message = message
    
    async def advance_to_next_event_old(self):
        """Old advance method - deprecated"""
        # This method is deprecated, use the new advance_to_next_event method instead
        pass
    


    async def process_choice(self, choice: StoryChoice, interaction: discord.Interaction):
        """Process a player's story choice"""
        try:
            # Check requirements
            if not await self.check_choice_requirements(choice):
                await interaction.response.send_message(
                    f"❌ You don't meet the requirements for this choice!",
                    ephemeral=True
                )
                return

            # Record the choice
            self.player_choices[self.current_event_index] = {
                "choice_id": choice.id,
                "choice_text": choice.text,
                "consequences": choice.consequences
            }

            # Apply consequences
            await self.apply_choice_consequences(choice.consequences)

            # Create response embed
            embed = discord.Embed(
                title="✅ Choice Made",
                description=f"You chose: **{choice.text}**",
                color=SUCCESS_COLOR
            )

            if choice.description:
                embed.add_field(
                    name="📝 Description",
                    value=choice.description,
                    inline=False
                )

            # Show consequences if any
            if choice.consequences:
                consequences_text = []
                for key, value in choice.consequences.items():
                    if isinstance(value, (int, float)) and value != 0:
                        sign = "+" if value > 0 else ""
                        consequences_text.append(f"{key.title()}: {sign}{value}")
                    elif isinstance(value, bool) and value:
                        consequences_text.append(f"{key.replace('_', ' ').title()}")

                if consequences_text:
                    embed.add_field(
                        name="📊 Effects",
                        value="\n".join(consequences_text),
                        inline=False
                    )

            await interaction.response.edit_message(embed=embed, view=None)

            # Continue to next event after a short delay
            await asyncio.sleep(2.0)
            await self.advance_to_next_event()

        except Exception as e:
            print(f"Error processing choice: {e}")
            await interaction.response.send_message(
                "❌ An error occurred processing your choice.",
                ephemeral=True
            )

    async def check_choice_requirements(self, choice: StoryChoice) -> bool:
        """Check if player meets choice requirements"""
        if not choice.requirements:
            return True

        player = await Player.get(self.player_id)
        if not player:
            return False

        # Check level requirement
        if "level" in choice.requirements:
            if player.level < choice.requirements["level"]:
                return False

        # Check stat requirements
        for stat in ["strength", "agility", "intelligence", "vitality"]:
            if stat in choice.requirements:
                player_stat = getattr(player, stat, 0)
                if player_stat < choice.requirements[stat]:
                    return False

        # Check story state requirements (like previous choices)
        for key, required_value in choice.requirements.items():
            if key in self.story_state:
                if self.story_state[key] < required_value:
                    return False

        return True

    async def apply_choice_consequences(self, consequences: Dict[str, Any]):
        """Apply the consequences of a choice"""
        if not consequences:
            return

        # Update story state
        for key, value in consequences.items():
            if isinstance(value, (int, float)):
                # Add to existing value or create new
                current_value = self.story_state.get(key, 0)
                self.story_state[key] = current_value + value
            elif isinstance(value, bool):
                # Set boolean flags
                self.story_state[key] = value
            else:
                # Set other values directly
                self.story_state[key] = value

class StoryContinueView(discord.ui.View):
    """View for continuing story without choices"""

    def __init__(self, story_session: 'InteractiveStorySession'):
        super().__init__(timeout=300)
        self.story_session = story_session

    @discord.ui.button(label="Continue Story", style=discord.ButtonStyle.primary, emoji="▶️")
    async def continue_story(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != str(self.story_session.player_id):
            await interaction.response.send_message("❌ Only the story participant can continue.", ephemeral=True)
            return

        await interaction.response.defer()
        await self.story_session.advance_to_next_event()

    @discord.ui.button(label="Story Menu", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def return_to_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != str(self.story_session.player_id):
            await interaction.response.send_message("❌ Only the story participant can return to menu.", ephemeral=True)
            return

        await interaction.response.defer()
        self.story_session.session_active = False
        self.stop()

class StoryChoiceView(discord.ui.View):
    """View for story choices"""
    
    def __init__(self, story_session: InteractiveStorySession, event: StoryEvent):
        super().__init__(timeout=300)
        self.story_session = story_session
        self.event = event
        self.setup_choice_buttons()
    
    def setup_choice_buttons(self):
        """Setup buttons for story choices"""
        for i, choice in enumerate(self.event.choices[:5]):  # Max 5 choices per row
            button = StoryChoiceButton(choice, i)
            self.add_item(button)

class StoryChoiceButton(discord.ui.Button):
    """Button for individual story choices"""
    
    def __init__(self, choice: StoryChoice, index: int):
        self.choice = choice
        super().__init__(
            label=choice.text[:80],  # Discord button label limit
            emoji=choice.emoji,
            style=discord.ButtonStyle.primary,
            row=index // 5  # 5 buttons per row
        )
    
    async def callback(self, interaction: discord.Interaction):
        try:
            if interaction.user.id != int(self.view.story_session.player_id):
                await interaction.response.send_message("❌ This is not your story!", ephemeral=True)
                return

            # Process the choice
            await self.view.story_session.process_choice(self.choice, interaction)

        except Exception as e:
            print(f"Error in story choice callback: {e}")
            # Try to send error message to user
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ An error occurred processing your choice. The story will continue...", ephemeral=True)
                else:
                    await interaction.followup.send("❌ An error occurred processing your choice. The story will continue...", ephemeral=True)
            except:
                pass  # If we can't even send an error message, just continue

            # Try to advance the story anyway
            try:
                await self.view.story_session.advance_to_next_event()
            except:
                pass


class ContinueStoryView(discord.ui.View):
    """View for continuing story after boss battles"""

    def __init__(self, story_session):
        super().__init__(timeout=300)
        self.story_session = story_session

    @discord.ui.button(label="Continue Story", style=discord.ButtonStyle.primary, emoji="▶️")
    async def continue_story(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != str(self.story_session.player_id):
            await interaction.response.send_message("❌ Only the story participant can continue.", ephemeral=True)
            return

        await interaction.response.defer()
        await self.story_session.advance_to_next_event()

    @discord.ui.button(label="Return to Story Menu", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def return_to_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != str(self.story_session.player_id):
            await interaction.response.send_message("❌ Only the story participant can return to menu.", ephemeral=True)
            return

        # Return to story campaign menu
        from commands.story import StoryCampaignView
        from structure.player import Player

        # Get player data
        player = await Player.get(interaction.user.id)
        if not player:
            await interaction.response.send_message("❌ Player data not found.", ephemeral=True)
            return

        # Create a mock context object for StoryCampaignView
        class MockContext:
            def __init__(self, user):
                self.author = user

        mock_ctx = MockContext(interaction.user)
        view = StoryCampaignView(mock_ctx, player)
        embed = await view.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=view)


class StoryBattleChoiceView(discord.ui.View):
    """View for story battle strategy choices"""

    def __init__(self, story_session: InteractiveStorySession, event: StoryEvent, enemy_data: Dict):
        super().__init__(timeout=300)
        self.story_session = story_session
        self.event = event
        self.enemy_data = enemy_data

        # Add choice buttons
        for choice in event.choices:
            button = StoryBattleChoiceButton(choice, self)
            self.add_item(button)

    async def on_timeout(self):
        """Handle view timeout"""
        try:
            embed = discord.Embed(
                title="⏰ Choice Timeout",
                description="You took too long to decide. The battle begins with default strategy!",
                color=WARNING_COLOR
            )

            # Start battle with default strategy
            await self.story_session.start_direct_battle(self.enemy_data)

        except Exception as e:
            print(f"Error handling battle choice timeout: {e}")


class StoryBattleChoiceButton(discord.ui.Button):
    """Button for story battle strategy choices"""

    def __init__(self, choice: StoryChoice, view: StoryBattleChoiceView):
        self.choice = choice
        self.story_view = view  # Use different name to avoid conflict with discord.ui.Button.view

        super().__init__(
            label=choice.text,
            emoji=choice.emoji,
            style=discord.ButtonStyle.primary,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != int(self.story_view.story_session.player_id):
            await interaction.response.send_message("❌ This is not your story!", ephemeral=True)
            return

        # Apply choice consequences to battle
        battle_modifiers = {}
        if self.choice.consequences:
            for key, value in self.choice.consequences.items():
                if key == "battle_bonus":
                    battle_modifiers["damage_bonus"] = value
                elif key == "defense_bonus":
                    battle_modifiers["defense_bonus"] = value
                elif key == "team_support":
                    battle_modifiers["ally_assistance"] = True

        # Show choice result
        embed = discord.Embed(
            title="⚔️ Battle Strategy Chosen",
            description=f"You chose: **{self.choice.text}**",
            color=SUCCESS_COLOR
        )

        if self.choice.description:
            embed.add_field(
                name="📝 Strategy",
                value=self.choice.description,
                inline=False
            )

        await interaction.response.edit_message(embed=embed, view=None)

        # Apply consequences to story state
        await self.story_view.story_session.apply_choice_consequences(self.choice.consequences)

        # Start the battle with modifiers
        await asyncio.sleep(2.0)
        await self.story_view.story_session.start_direct_battle(self.story_view.enemy_data, battle_modifiers)


class StoryCompletionView(discord.ui.View):
    """View for story completion with home and continue options"""

    def __init__(self, ctx, player_id: str, next_mission=None, story_state=None):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player_id = player_id
        self.next_mission = next_mission
        self.story_state = story_state or {}

    @discord.ui.button(label="Go to Home", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def go_home(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to main menu"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this button.", ephemeral=True)
            return

        await interaction.response.defer()

        # Create a simple completion message
        embed = discord.Embed(
            title="📖 Story Session Complete",
            description="Thank you for playing the Solo Leveling interactive story!",
            color=SUCCESS_COLOR
        )

        embed.add_field(
            name="🎮 Continue Playing",
            value="Use `sl story` to access more story missions or other game features!",
            inline=False
        )

        await interaction.edit_original_response(embed=embed, view=None)

    @discord.ui.button(label="Character Development", style=discord.ButtonStyle.success, emoji="📊", row=1)
    async def view_character_development(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show detailed character development stats"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this button.", ephemeral=True)
            return

        if not self.story_state:
            await interaction.response.send_message("❌ No character development data available.", ephemeral=True)
            return

        # Create detailed character development embed
        embed = discord.Embed(
            title="📊 Character Development Details",
            description="Your choices have shaped Jin-Woo's personality and abilities:",
            color=INFO_COLOR
        )

        # Categorize stats
        combat_stats = []
        personality_traits = []
        relationships = []
        other_stats = []

        for stat, value in self.story_state.items():
            if isinstance(value, int) and value > 0 and stat not in ['player_hp', 'player_mp']:
                stat_display = stat.replace('_', ' ').title()
                stat_line = f"{stat_display}: +{value}"

                if stat.lower() in ['player_max_hp', 'player_max_mp', 'player_attack', 'player_defense', 'damage_bonus']:
                    combat_stats.append(stat_line)
                elif stat.lower() in ['family_bond', 'teamwork', 'relationships', 'protectiveness', 'trust']:
                    relationships.append(stat_line)
                elif stat.lower() in ['confidence', 'determination', 'courage', 'humility', 'caution', 'wisdom', 'hope', 'resolve', 'pride', 'focus', 'preparation']:
                    personality_traits.append(stat_line)
                else:
                    other_stats.append(stat_line)

        # Add fields for each category
        if combat_stats:
            embed.add_field(
                name="⚔️ Combat Enhancement",
                value="\n".join(combat_stats),
                inline=True
            )

        if personality_traits:
            embed.add_field(
                name="🧠 Personality Traits",
                value="\n".join(personality_traits),
                inline=True
            )

        if relationships:
            embed.add_field(
                name="👥 Relationships",
                value="\n".join(relationships),
                inline=True
            )

        if other_stats:
            embed.add_field(
                name="🌟 Other Development",
                value="\n".join(other_stats),
                inline=False
            )

        embed.add_field(
            name="💡 About Character Development",
            value="These stats reflect the choices you made during the story. They influence future story events, battle performance, and how other characters react to Jin-Woo.",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Continue Story", style=discord.ButtonStyle.primary, emoji="📚")
    async def continue_story(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Continue to the next story mission"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can use this button.", ephemeral=True)
            return

        if not self.next_mission:
            await interaction.response.send_message("❌ No more story missions available.", ephemeral=True)
            return

        # Don't defer here - let the story session handle the response

        # Start the next story mission
        story_session = InteractiveStorySession(
            self.player_id,
            self.next_mission.id,
            self.ctx,
            interaction.client
        )

        # Start the next story session - it will handle the interaction response
        success = await story_session.start_story_session(interaction=interaction)

        if success:
            # Story session started successfully, it handled the interaction
            return
        else:
            # Story session failed to start, we need to respond to the interaction
            await interaction.response.defer()

        if not success:
            # Fallback completion message
            embed = discord.Embed(
                title="📖 Story Complete!",
                description=f"Chapter **{self.next_mission.name}** completed!",
                color=SUCCESS_COLOR
            )
            await interaction.edit_original_response(embed=embed, view=None)

class StoryChapterContinueView(discord.ui.View):
    """View for continuing to the next story chapter"""

    def __init__(self, ctx, player_id, next_mission):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.player_id = player_id
        self.next_mission = next_mission

    @discord.ui.button(label="Continue Story", style=discord.ButtonStyle.primary, emoji="▶️")
    async def continue_story(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.player_id):
            await interaction.response.send_message("❌ This is not your story!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Start the next mission's interactive story
            from structure.player import Player
            player = await Player.get(self.player_id)

            # Create new story session for next mission
            story_session = InteractiveStorySession(
                self.player_id,
                self.next_mission.id,
                self.ctx,
                interaction.client
            )

            # Start the story session in the same message
            success = await story_session.start_story_session(interaction.message)

            if not success:
                # Fallback to mission completion
                from structure.story_campaign import StoryCampaign
                success, message, reward = await StoryCampaign.complete_mission(self.player_id, self.next_mission.id)

                embed = discord.Embed(
                    title="📖 Chapter Complete!",
                    description=f"Completed: **{self.next_mission.name}**",
                    color=SUCCESS_COLOR
                )

                if success:
                    embed.add_field(name="✅ Mission", value=message, inline=False)

                    # Show rewards
                    if reward:
                        reward_text = []
                        if reward.gold > 0:
                            reward_text.append(f"💰 **{reward.gold:,}** Gold")
                        if reward.xp > 0:
                            reward_text.append(f"⭐ **{reward.xp:,}** EXP")
                        if reward.diamonds > 0:
                            reward_text.append(f"💎 **{reward.diamonds:,}** Diamonds")
                        if reward.tickets > 0:
                            reward_text.append(f"🎫 **{reward.tickets:,}** Tickets")
                        if reward.stat_points > 0:
                            reward_text.append(f"📊 **{reward.stat_points:,}** Stat Points")
                        if reward.skill_points > 0:
                            reward_text.append(f"🎯 **{reward.skill_points:,}** Skill Points")
                        if reward.title:
                            reward_text.append(f"🏆 **{reward.title}** Title")
                        if hasattr(reward, 'items') and reward.items:
                            from structure.items import ItemManager
                            for item_id in reward.items:
                                # Get actual item from database to show proper name
                                item = await ItemManager.get(item_id)
                                if item:
                                    reward_text.append(f"🎁 **{item.name}**")
                                else:
                                    # Fallback for items not in database
                                    item_name = item_id.replace("_", " ").title()
                                    reward_text.append(f"🎁 **{item_name}** (Custom)")

                        if reward_text:
                            embed.add_field(
                                name="🎁 Chapter Rewards",
                                value="\n".join(reward_text),
                                inline=False
                            )

                await interaction.edit_original_response(embed=embed, view=None)

        except Exception as e:
            print(f"Error continuing story: {e}")
            await interaction.followup.send("❌ Error starting next chapter. Please try again.", ephemeral=True)

    @discord.ui.button(label="Return to Story Menu", style=discord.ButtonStyle.secondary, emoji="🏠")
    async def return_to_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.player_id):
            await interaction.response.send_message("❌ This is not your story!", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Show the story campaign menu
            from commands.story import show_story_campaign
            await show_story_campaign(self.ctx, interaction.client)

            # Edit the current message to show completion
            embed = discord.Embed(
                title="📚 Story Menu",
                description="Returned to story campaign menu. Use `sl story` to continue your journey!",
                color=INFO_COLOR
            )

            await interaction.edit_original_response(embed=embed, view=None)

        except Exception as e:
            print(f"Error returning to menu: {e}")
            await interaction.followup.send("❌ Error returning to menu. Use `sl story` to continue.", ephemeral=True)


# Import comprehensive story events and convert to proper format
try:
    from structure.complete_story_events import COMPLETE_STORY_EVENTS as IMPORTED_EVENTS

    # Convert imported events to use proper StoryEventType enums
    STORY_EVENTS = {}
    for mission_id, events in IMPORTED_EVENTS.items():
        converted_events = []
        for event in events:
            # Convert string event_type to StoryEventType enum
            event_type_mapping = {
                "NARRATIVE": StoryEventType.CUTSCENE,
                "DIALOGUE": StoryEventType.DIALOGUE,
                "BATTLE": StoryEventType.BATTLE,
                "EXPLORATION": StoryEventType.EXPLORATION,
                "EMOTIONAL": StoryEventType.DIALOGUE,
                "SYSTEM_MESSAGE": StoryEventType.SYSTEM_MESSAGE
            }

            # Convert choices to proper format
            converted_choices = []
            if hasattr(event, 'choices') and event.choices:
                choice_type_mapping = {
                    "HEROIC": StoryChoiceType.MORAL_CHOICE,
                    "CAUTIOUS": StoryChoiceType.ACTION_CHOICE,
                    "EMOTIONAL": StoryChoiceType.DIALOGUE_RESPONSE,
                    "PRACTICAL": StoryChoiceType.ACTION_CHOICE,
                    "DIALOGUE": StoryChoiceType.DIALOGUE_RESPONSE,
                    "ACTION": StoryChoiceType.ACTION_CHOICE,
                    "BATTLE": StoryChoiceType.BATTLE_STRATEGY,
                    "EXPLORATION": StoryChoiceType.EXPLORATION_CHOICE,
                    "SYSTEM": StoryChoiceType.SYSTEM_CHOICE
                }

                for choice in event.choices:
                    converted_choice = StoryChoice(
                        id=choice.id,
                        text=choice.text,
                        description=choice.description,
                        choice_type=choice_type_mapping.get(choice.choice_type, StoryChoiceType.DIALOGUE_RESPONSE),
                        requirements=choice.requirements if hasattr(choice, 'requirements') else {},
                        consequences=choice.consequences if hasattr(choice, 'consequences') else {},
                        emoji=choice.emoji if hasattr(choice, 'emoji') else "🔹"
                    )
                    converted_choices.append(converted_choice)

            # Create new StoryEvent with proper enum type
            converted_event = StoryEvent(
                id=event.id,
                event_type=event_type_mapping.get(event.event_type, StoryEventType.DIALOGUE),
                title=event.title,
                description=event.description,
                speaker=event.speaker,
                dialogue=event.dialogue,
                choices=converted_choices,
                battle_enemies=event.battle_enemies if hasattr(event, 'battle_enemies') else [],
                auto_continue=False,
                delay=2.0,
                color=INFO_COLOR
            )
            converted_events.append(converted_event)

        STORY_EVENTS[mission_id] = converted_events

    print(f"✅ Successfully loaded {len(STORY_EVENTS)} story missions with interactive events")

except ImportError as e:
    print(f"Warning: Could not import complete story events ({e}), using fallback")
    # Fallback to basic story events
    STORY_EVENTS = {
    # PROLOGUE - THE WEAKEST HUNTER
    "prologue_001": [
        StoryEvent(
            id="prologue_001_intro",
            event_type=StoryEventType.DIALOGUE,
            title="The Weakest Hunter",
            description="You stand before the entrance to your first dungeon as an E-rank hunter. The other hunters look at you with pity and disdain.",
            speaker="Narrator",
            dialogue="As the weakest hunter in all of Korea, Sung Jin-Woo has always been looked down upon. Today, like every other day, he enters a dungeon hoping to earn enough to pay for his mother's medical bills.",
            choices=[
                StoryChoice(
                    id="stay_confident",
                    text="I'll prove them wrong today!",
                    description="Show confidence despite being the weakest",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"confidence": 1},
                    emoji="💪"
                ),
                StoryChoice(
                    id="stay_humble",
                    text="I just need to do my best...",
                    description="Stay humble and focused on survival",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"humility": 1},
                    emoji="😌"
                ),
                StoryChoice(
                    id="stay_silent",
                    text="*Stay silent*",
                    description="Don't engage with the other hunters",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"caution": 1},
                    emoji="🤐"
                )
            ]
        ),
        StoryEvent(
            id="prologue_001_dungeon",
            event_type=StoryEventType.EXPLORATION,
            title="First Dungeon",
            description="You enter the dungeon with the other hunters. The air is thick with mana and danger lurks in every shadow.",
            speaker="System",
            dialogue="You have entered a D-rank dungeon. As an E-rank hunter, you are severely outclassed. Stay close to the others and try not to get in their way.",
            choices=[
                StoryChoice(
                    id="follow_closely",
                    text="Stay close to the stronger hunters",
                    description="Play it safe and follow the group",
                    choice_type=StoryChoiceType.ACTION_CHOICE,
                    consequences={"safety": 1},
                    emoji="🛡️"
                ),
                StoryChoice(
                    id="scout_ahead",
                    text="Scout ahead carefully",
                    description="Try to be useful by scouting",
                    choice_type=StoryChoiceType.ACTION_CHOICE,
                    consequences={"courage": 1},
                    requirements={"confidence": 1},
                    emoji="🔍"
                ),
                StoryChoice(
                    id="stay_back",
                    text="Stay at the back of the group",
                    description="Minimize risk by staying behind",
                    choice_type=StoryChoiceType.ACTION_CHOICE,
                    consequences={"caution": 2},
                    emoji="🚶"
                )
            ]
        ),
        StoryEvent(
            id="prologue_001_battle",
            event_type=StoryEventType.BATTLE,
            title="First Monster Encounter",
            description="A group of goblins appears! The other hunters spring into action, but one goblin breaks away toward you!",
            speaker="Hunter Leader",
            dialogue="Jin-Woo! There's one coming your way! Try not to die!",
            battle_enemies=[
                {"name": "Goblin", "level": 5, "hp": 150, "attack": 25, "defense": 10}
            ],
            choices=[
                StoryChoice(
                    id="fight_bravely",
                    text="Face the goblin head-on!",
                    description="Fight with everything you have",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"courage": 1, "battle_bonus": 0.1},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="fight_defensively",
                    text="Focus on defense and survival",
                    description="Prioritize staying alive",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"defense_bonus": 0.2},
                    emoji="🛡️"
                ),
                StoryChoice(
                    id="call_for_help",
                    text="Call for help from other hunters",
                    description="Ask the stronger hunters for assistance",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"team_support": 1},
                    emoji="📢"
                )
            ]
        )
    ],

    "prologue_002": [
        StoryEvent(
            id="prologue_002_intro",
            event_type=StoryEventType.DIALOGUE,
            title="Hunter's License",
            description="After barely surviving your first dungeon, you're at the Hunter Association to get your official license.",
            speaker="Association Staff",
            dialogue="Congratulations on surviving your first dungeon, Mr. Sung. Here's your official E-rank Hunter License. Try not to get yourself killed out there.",
            choices=[
                StoryChoice(
                    id="thank_politely",
                    text="Thank you for the opportunity",
                    description="Be polite and grateful",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"reputation": 1},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="ask_about_training",
                    text="Is there any training available?",
                    description="Inquire about improving your skills",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"knowledge": 1},
                    emoji="📚"
                ),
                StoryChoice(
                    id="express_determination",
                    text="I'll become stronger, no matter what",
                    description="Show your determination to improve",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"determination": 1},
                    emoji="🔥"
                )
            ]
        )
    ],

    "double_dungeon_001": [
        StoryEvent(
            id="double_dungeon_intro",
            event_type=StoryEventType.DIALOGUE,
            title="The Double Dungeon",
            description="You've been invited to join a raid on what appears to be a simple D-rank dungeon. But something feels wrong...",
            speaker="Raid Leader",
            dialogue="Alright everyone, this should be a straightforward D-rank clear. Jin-Woo, just stay back and try not to get in the way.",
            choices=[
                StoryChoice(
                    id="voice_concerns",
                    text="Something doesn't feel right about this place",
                    description="Express your unease about the dungeon",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"intuition": 1},
                    emoji="⚠️"
                ),
                StoryChoice(
                    id="stay_quiet",
                    text="*Nod silently and follow*",
                    description="Keep your concerns to yourself",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"caution": 1},
                    emoji="🤐"
                ),
                StoryChoice(
                    id="show_eagerness",
                    text="I'm ready to help however I can!",
                    description="Show enthusiasm despite the danger",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"team_spirit": 1},
                    emoji="💪"
                )
            ]
        ),
        StoryEvent(
            id="double_dungeon_temple",
            event_type=StoryEventType.EXPLORATION,
            title="The Hidden Temple",
            description="The raid team discovers a hidden temple within the dungeon. Ancient statues line the walls, and an ominous feeling fills the air.",
            speaker="Archaeologist Hunter",
            dialogue="These inscriptions... they're ancient. This isn't just a dungeon - it's some kind of temple. We should be careful.",
            choices=[
                StoryChoice(
                    id="examine_statues",
                    text="Examine the statues carefully",
                    description="Study the ancient statues for clues",
                    choice_type=StoryChoiceType.EXPLORATION_CHOICE,
                    consequences={"knowledge": 2, "danger": 1},
                    emoji="🗿"
                ),
                StoryChoice(
                    id="suggest_retreat",
                    text="Maybe we should leave...",
                    description="Suggest the team retreat from danger",
                    choice_type=StoryChoiceType.EXPLORATION_CHOICE,
                    consequences={"caution": 2},
                    requirements={"intuition": 1},
                    emoji="🚪"
                ),
                StoryChoice(
                    id="stay_alert",
                    text="Stay alert and watch for traps",
                    description="Focus on potential dangers",
                    choice_type=StoryChoiceType.EXPLORATION_CHOICE,
                    consequences={"alertness": 1},
                    emoji="👁️"
                )
            ]
        ),
        StoryEvent(
            id="double_dungeon_rules",
            event_type=StoryEventType.SYSTEM_MESSAGE,
            title="The Commandments",
            description="Ancient text appears on the temple walls, revealing three commandments that must be followed.",
            speaker="Ancient Voice",
            dialogue="COMMANDMENT ONE: Worship the God. COMMANDMENT TWO: Praise the God. COMMANDMENT THREE: Prove your faith to the God.",
            choices=[
                StoryChoice(
                    id="refuse_worship",
                    text="I won't worship some ancient statue!",
                    description="Refuse to follow the commandments",
                    choice_type=StoryChoiceType.MORAL_CHOICE,
                    consequences={"defiance": 2, "danger": 3},
                    emoji="✊"
                ),
                StoryChoice(
                    id="reluctant_compliance",
                    text="*Reluctantly follow the others*",
                    description="Go along with the group's decision",
                    choice_type=StoryChoiceType.MORAL_CHOICE,
                    consequences={"survival": 1},
                    emoji="😰"
                ),
                StoryChoice(
                    id="analyze_situation",
                    text="Try to understand what's happening",
                    description="Observe and analyze the situation",
                    choice_type=StoryChoiceType.MORAL_CHOICE,
                    consequences={"wisdom": 1},
                    emoji="🤔"
                )
            ]
        )
    ],

    # PROLOGUE - FIRST RAID
    "prologue_002": [
        StoryEvent(
            id="prologue_002_intro",
            event_type=StoryEventType.DIALOGUE,
            title="Hunter's License",
            description="After barely surviving your first dungeon, you're at the Hunter Association to get your official license.",
            speaker="Association Staff",
            dialogue="Congratulations on surviving your first dungeon, Mr. Sung. Here's your official E-rank Hunter License. Try not to get yourself killed out there.",
            choices=[
                StoryChoice(
                    id="thank_politely",
                    text="Thank you for the opportunity",
                    description="Be polite and grateful",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"reputation": 1},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="ask_about_training",
                    text="Is there any training available?",
                    description="Inquire about improving your skills",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"knowledge": 1},
                    emoji="📚"
                ),
                StoryChoice(
                    id="express_determination",
                    text="I'll become stronger, no matter what",
                    description="Show your determination to improve",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"determination": 1},
                    emoji="🔥"
                )
            ]
        )
    ],

    # PROLOGUE - FIRST STEPS
    "prologue_003": [
        StoryEvent(
            id="prologue_003_intro",
            event_type=StoryEventType.DIALOGUE,
            title="First Steps",
            description="You've received your hunter license and are ready to take on your first real mission as an official hunter.",
            speaker="Guild Representative",
            dialogue="Welcome to the guild, Hunter Sung. We have some basic missions available for new E-rank hunters. Nothing too dangerous, just some cleanup work.",
            choices=[
                StoryChoice(
                    id="eager_to_start",
                    text="I'm ready for any mission!",
                    description="Show enthusiasm for your new role",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"enthusiasm": 1},
                    emoji="💪"
                ),
                StoryChoice(
                    id="ask_about_safety",
                    text="What safety measures are in place?",
                    description="Inquire about safety protocols",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"caution": 1},
                    emoji="🛡️"
                ),
                StoryChoice(
                    id="request_details",
                    text="Can you tell me more about these missions?",
                    description="Gather more information first",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"preparation": 1},
                    emoji="📋"
                )
            ]
        )
    ],

    # DOUBLE DUNGEON - THE TEMPLE
    "double_dungeon_001": [
        StoryEvent(
            id="double_dungeon_intro",
            event_type=StoryEventType.DIALOGUE,
            title="The Double Dungeon",
            description="You've been invited to join a raid on what appears to be a simple D-rank dungeon. But something feels wrong...",
            speaker="Raid Leader",
            dialogue="Alright everyone, this should be a straightforward D-rank clear. Jin-Woo, just stay back and try not to get in the way.",
            choices=[
                StoryChoice(
                    id="voice_concerns",
                    text="Something doesn't feel right about this place",
                    description="Express your unease about the dungeon",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"intuition": 1},
                    emoji="⚠️"
                ),
                StoryChoice(
                    id="stay_quiet",
                    text="*Nod silently and follow*",
                    description="Keep your concerns to yourself",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"caution": 1},
                    emoji="🤐"
                ),
                StoryChoice(
                    id="show_eagerness",
                    text="I'm ready to help however I can!",
                    description="Show enthusiasm despite the danger",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"team_spirit": 1},
                    emoji="💪"
                )
            ]
        ),
        StoryEvent(
            id="double_dungeon_temple",
            event_type=StoryEventType.EXPLORATION,
            title="The Hidden Temple",
            description="The raid team discovers a hidden temple within the dungeon. Ancient statues line the walls, and an ominous feeling fills the air.",
            speaker="Archaeologist Hunter",
            dialogue="These inscriptions... they're ancient. This isn't just a dungeon - it's some kind of temple. We should be careful.",
            choices=[
                StoryChoice(
                    id="examine_statues",
                    text="Examine the statues carefully",
                    description="Study the ancient statues for clues",
                    choice_type=StoryChoiceType.EXPLORATION_CHOICE,
                    consequences={"knowledge": 2, "danger": 1},
                    emoji="🗿"
                ),
                StoryChoice(
                    id="suggest_retreat",
                    text="Maybe we should leave...",
                    description="Suggest the team retreat from danger",
                    choice_type=StoryChoiceType.EXPLORATION_CHOICE,
                    consequences={"caution": 2},
                    requirements={"intuition": 1},
                    emoji="🚪"
                ),
                StoryChoice(
                    id="stay_alert",
                    text="Stay alert and watch for traps",
                    description="Focus on potential dangers",
                    choice_type=StoryChoiceType.EXPLORATION_CHOICE,
                    consequences={"alertness": 1},
                    emoji="👁️"
                )
            ]
        ),
        StoryEvent(
            id="double_dungeon_rules",
            event_type=StoryEventType.SYSTEM_MESSAGE,
            title="The Commandments",
            description="Ancient text appears on the temple walls, revealing three commandments that must be followed.",
            speaker="Ancient Voice",
            dialogue="COMMANDMENT ONE: Worship the God. COMMANDMENT TWO: Praise the God. COMMANDMENT THREE: Prove your faith to the God.",
            choices=[
                StoryChoice(
                    id="refuse_worship",
                    text="I won't worship some ancient statue!",
                    description="Refuse to follow the commandments",
                    choice_type=StoryChoiceType.MORAL_CHOICE,
                    consequences={"defiance": 2, "danger": 3},
                    emoji="✊"
                ),
                StoryChoice(
                    id="reluctant_compliance",
                    text="*Reluctantly follow the others*",
                    description="Go along with the group's decision",
                    choice_type=StoryChoiceType.MORAL_CHOICE,
                    consequences={"survival": 1},
                    emoji="😰"
                ),
                StoryChoice(
                    id="analyze_situation",
                    text="Try to understand what's happening",
                    description="Observe and analyze the situation",
                    choice_type=StoryChoiceType.MORAL_CHOICE,
                    consequences={"wisdom": 1},
                    emoji="🤔"
                )
            ]
        ),
        StoryEvent(
            id="double_dungeon_massacre",
            event_type=StoryEventType.BATTLE,
            title="The Massacre",
            description="The statues come to life! The temple guardians begin slaughtering the raid team. You must survive!",
            speaker="Temple Guardian",
            dialogue="Those who do not follow the commandments... shall perish!",
            battle_enemies=[
                {"name": "Temple Guardian", "level": 15, "hp": 800, "attack": 60, "defense": 40}
            ],
            choices=[
                StoryChoice(
                    id="protect_others",
                    text="Try to protect the other hunters!",
                    description="Risk yourself to save others",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"heroism": 2, "danger": 2},
                    emoji="🛡️"
                ),
                StoryChoice(
                    id="focus_survival",
                    text="Focus on your own survival",
                    description="Prioritize staying alive",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"survival_instinct": 1},
                    emoji="🏃"
                ),
                StoryChoice(
                    id="find_weakness",
                    text="Look for the guardian's weakness",
                    description="Try to find a way to defeat it",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"tactical_thinking": 1, "damage_bonus": 0.2},
                    emoji="🎯"
                )
            ]
        )
    ],

    # DOUBLE DUNGEON - SYSTEM AWAKENING
    "double_dungeon_002": [
        StoryEvent(
            id="system_awakening",
            event_type=StoryEventType.SYSTEM_MESSAGE,
            title="System Awakening",
            description="After the temple incident, something has changed within you. A mysterious system has awakened!",
            speaker="System",
            dialogue="CONGRATULATIONS! You have been selected as a Player. You now have access to the System.",
            choices=[
                StoryChoice(
                    id="accept_system",
                    text="Accept the System's power",
                    description="Embrace this new ability",
                    choice_type=StoryChoiceType.SYSTEM_CHOICE,
                    consequences={"system_user": True, "power_level": 10},
                    emoji="✨"
                ),
                StoryChoice(
                    id="question_system",
                    text="What is this System?",
                    description="Try to understand what's happening",
                    choice_type=StoryChoiceType.SYSTEM_CHOICE,
                    consequences={"knowledge": 2, "system_user": True},
                    emoji="❓"
                ),
                StoryChoice(
                    id="fear_system",
                    text="This is too strange...",
                    description="Be wary of this new power",
                    choice_type=StoryChoiceType.SYSTEM_CHOICE,
                    consequences={"caution": 2, "system_user": True},
                    emoji="😰"
                )
            ]
        )
    ],

    # INSTANT DUNGEONS - FIRST QUEST
    "instant_dungeon_001": [
        StoryEvent(
            id="first_quest_intro",
            event_type=StoryEventType.SYSTEM_MESSAGE,
            title="Daily Quest",
            description="The System has given you your first Daily Quest. You must complete it or face severe penalties.",
            speaker="System",
            dialogue="DAILY QUEST: Complete 100 push-ups, 100 sit-ups, 100 squats, and run 10km. Failure to complete will result in punishment.",
            choices=[
                StoryChoice(
                    id="accept_quest",
                    text="I'll complete the quest",
                    description="Accept the System's challenge",
                    choice_type=StoryChoiceType.SYSTEM_CHOICE,
                    consequences={"discipline": 1},
                    emoji="💪"
                ),
                StoryChoice(
                    id="question_system",
                    text="What happens if I don't?",
                    description="Ask about the consequences",
                    choice_type=StoryChoiceType.SYSTEM_CHOICE,
                    consequences={"curiosity": 1},
                    emoji="❓"
                ),
                StoryChoice(
                    id="ignore_quest",
                    text="I'll ignore this for now",
                    description="Try to ignore the System",
                    choice_type=StoryChoiceType.SYSTEM_CHOICE,
                    consequences={"rebellion": 1, "penalty_incoming": True},
                    emoji="🚫"
                )
            ]
        ),
        StoryEvent(
            id="penalty_dungeon",
            event_type=StoryEventType.BATTLE,
            title="Penalty Zone",
            description="You ignored the Daily Quest and have been transported to a penalty dungeon filled with giant centipedes!",
            speaker="System",
            dialogue="PENALTY QUEST: Survive for 4 hours in the Penalty Zone. Current time remaining: 4:00:00",
            battle_enemies=[
                {"name": "Giant Centipede", "level": 8, "hp": 300, "attack": 35, "defense": 15}
            ],
            choices=[
                StoryChoice(
                    id="fight_desperately",
                    text="Fight with everything you have!",
                    description="Battle desperately for survival",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"desperation": 1, "damage_bonus": 0.3},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="find_hiding_spot",
                    text="Look for somewhere to hide",
                    description="Try to find a safe place to wait",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"stealth": 1, "defense_bonus": 0.2},
                    emoji="🫥"
                ),
                StoryChoice(
                    id="analyze_enemy",
                    text="Study the centipede's movements",
                    description="Look for patterns and weaknesses",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"tactical_mind": 1, "accuracy_bonus": 0.2},
                    emoji="🧠"
                )
            ]
        )
    ],

    # REAWAKENING TEST
    "reawakening_001": [
        StoryEvent(
            id="reawakening_test",
            event_type=StoryEventType.DIALOGUE,
            title="The Reawakening Test",
            description="You've grown incredibly strong. The Hunter Association wants to test your new abilities.",
            speaker="Association Official",
            dialogue="Mr. Sung, your recent performance has been... extraordinary. We'd like you to undergo a reawakening test.",
            choices=[
                StoryChoice(
                    id="accept_confidently",
                    text="I'm ready for the test",
                    description="Show confidence in your abilities",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"confidence": 2},
                    emoji="💪"
                ),
                StoryChoice(
                    id="accept_humbly",
                    text="I'll do my best",
                    description="Remain humble despite your power",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"humility": 2},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="ask_questions",
                    text="What exactly does the test involve?",
                    description="Gather more information first",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"wisdom": 1},
                    emoji="🤔"
                )
            ]
        ),
        StoryEvent(
            id="reawakening_battle",
            event_type=StoryEventType.BATTLE,
            title="Reawakening Combat Test",
            description="Face the combat portion of your reawakening test. Show them your true power!",
            speaker="Test Administrator",
            dialogue="Begin the combat test! Show us what you're truly capable of!",
            battle_enemies=[
                {"name": "Test Golem", "level": 25, "hp": 2000, "attack": 80, "defense": 60}
            ],
            choices=[
                StoryChoice(
                    id="hold_back",
                    text="Don't reveal your full power",
                    description="Keep some abilities secret",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"secrecy": 1, "damage_penalty": 0.3},
                    emoji="🤫"
                ),
                StoryChoice(
                    id="show_strength",
                    text="Demonstrate your true abilities",
                    description="Show them what you can really do",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"reputation": 2, "damage_bonus": 0.2},
                    emoji="⚡"
                ),
                StoryChoice(
                    id="balanced_approach",
                    text="Show impressive but not overwhelming power",
                    description="Strike a balance between secrecy and demonstration",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"wisdom": 1},
                    emoji="⚖️"
                )
            ]
        )
    ],

    # JOB CHANGE QUEST
    "job_change_001": [
        StoryEvent(
            id="job_change_intro",
            event_type=StoryEventType.SYSTEM_MESSAGE,
            title="Job Change Quest",
            description="The System offers you a chance to change your class. This will determine your future path as a hunter.",
            speaker="System",
            dialogue="JOB CHANGE QUEST AVAILABLE: Complete the trials to unlock your true potential. Warning: This quest is extremely dangerous.",
            choices=[
                StoryChoice(
                    id="accept_immediately",
                    text="I accept the quest!",
                    description="Take on the challenge without hesitation",
                    choice_type=StoryChoiceType.SYSTEM_CHOICE,
                    consequences={"courage": 2},
                    emoji="⚡"
                ),
                StoryChoice(
                    id="ask_details",
                    text="What exactly does this quest involve?",
                    description="Gather more information first",
                    choice_type=StoryChoiceType.SYSTEM_CHOICE,
                    consequences={"wisdom": 1},
                    emoji="📋"
                ),
                StoryChoice(
                    id="hesitate",
                    text="This sounds too dangerous...",
                    description="Express concern about the difficulty",
                    choice_type=StoryChoiceType.SYSTEM_CHOICE,
                    consequences={"caution": 1},
                    emoji="😰"
                )
            ]
        ),
        StoryEvent(
            id="job_change_trial",
            event_type=StoryEventType.BATTLE,
            title="The Trial of Strength",
            description="You face the first trial - a battle against a powerful knight construct that tests your combat abilities.",
            speaker="Knight of Trials",
            dialogue="Show me your resolve, challenger. Prove that you are worthy of power!",
            battle_enemies=[
                {"name": "Trial Knight", "level": 30, "hp": 3500, "attack": 100, "defense": 80}
            ],
            choices=[
                StoryChoice(
                    id="aggressive_assault",
                    text="Launch an all-out attack!",
                    description="Go on the offensive immediately",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"aggression": 1, "damage_bonus": 0.25},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="defensive_stance",
                    text="Focus on defense and counterattacks",
                    description="Play defensively and wait for openings",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"patience": 1, "defense_bonus": 0.3},
                    emoji="🛡️"
                ),
                StoryChoice(
                    id="balanced_approach",
                    text="Use a balanced fighting style",
                    description="Mix offense and defense strategically",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"balance": 1, "all_stats_bonus": 0.15},
                    emoji="⚖️"
                )
            ]
        )
    ],

    # CARTENON TEMPLE
    "cartenon_001": [
        StoryEvent(
            id="temple_entrance",
            event_type=StoryEventType.EXPLORATION,
            title="The Cartenon Temple",
            description="You stand before the ancient Cartenon Temple, a place of great magical power and danger.",
            speaker="Guild Master",
            dialogue="This temple has claimed many lives. Are you sure you're ready for this, Jin-Woo?",
            choices=[
                StoryChoice(
                    id="enter_boldly",
                    text="I'm ready. Let's go in.",
                    description="Enter the temple with confidence",
                    choice_type=StoryChoiceType.EXPLORATION_CHOICE,
                    consequences={"courage": 2},
                    emoji="🚪"
                ),
                StoryChoice(
                    id="suggest_caution",
                    text="We should be extremely careful",
                    description="Advise the team to proceed cautiously",
                    choice_type=StoryChoiceType.EXPLORATION_CHOICE,
                    consequences={"team_safety": 1, "caution": 1},
                    emoji="⚠️"
                ),
                StoryChoice(
                    id="study_temple",
                    text="Let me examine the temple first",
                    description="Study the temple's structure and magic",
                    choice_type=StoryChoiceType.EXPLORATION_CHOICE,
                    consequences={"knowledge": 2},
                    emoji="🔍"
                )
            ]
        ),
        StoryEvent(
            id="temple_guardian_battle",
            event_type=StoryEventType.BATTLE,
            title="Temple Guardian",
            description="The ancient guardian of the temple awakens to challenge intruders!",
            speaker="Temple Guardian",
            dialogue="Who dares disturb the sacred temple? Face the guardian's wrath!",
            battle_enemies=[
                {"name": "Stone Guardian", "level": 35, "hp": 4000, "attack": 120, "defense": 100}
            ],
            choices=[
                StoryChoice(
                    id="use_shadows",
                    text="Summon your shadow soldiers",
                    description="Use your shadow army in battle",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"shadow_mastery": 1, "damage_bonus": 0.3},
                    requirements={"system_user": True},
                    emoji="👤"
                ),
                StoryChoice(
                    id="solo_fight",
                    text="Fight the guardian alone",
                    description="Face the guardian in single combat",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"personal_growth": 2},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="team_coordination",
                    text="Coordinate with your team",
                    description="Work together with other hunters",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"teamwork": 2},
                    emoji="🤝"
                )
            ]
        )
    ],

    # RED GATE INCIDENT
    "red_gate_001": [
        StoryEvent(
            id="red_gate_intro",
            event_type=StoryEventType.DIALOGUE,
            title="The Red Gate",
            description="During a routine C-rank dungeon raid, the gate suddenly turns red, trapping everyone inside!",
            speaker="Panicked Hunter",
            dialogue="The gate... it's red! We're trapped! Red gates are at least B-rank difficulty!",
            choices=[
                StoryChoice(
                    id="take_charge",
                    text="Everyone stay calm! We can get through this!",
                    description="Take leadership of the panicked group",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"leadership": 2},
                    emoji="👑"
                ),
                StoryChoice(
                    id="assess_situation",
                    text="Let's figure out what we're dealing with",
                    description="Analyze the situation carefully",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"tactical_mind": 1},
                    emoji="🧠"
                ),
                StoryChoice(
                    id="comfort_others",
                    text="Don't worry, we'll find a way out",
                    description="Try to calm the other hunters",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"compassion": 1},
                    emoji="🤝"
                )
            ]
        ),
        StoryEvent(
            id="red_gate_boss",
            event_type=StoryEventType.BATTLE,
            title="Ice Bear Boss",
            description="You face the boss of the Red Gate - a massive Ice Bear that could kill you in one hit!",
            speaker="Ice Bear",
            dialogue="*ROOOOOAAAAAR!* The massive bear charges at you with deadly intent!",
            battle_enemies=[
                {"name": "Ice Bear", "level": 40, "hp": 8000, "attack": 200, "defense": 120}
            ],
            choices=[
                StoryChoice(
                    id="use_stealth",
                    text="Use stealth to avoid direct confrontation",
                    description="Try to outmaneuver the massive bear",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"stealth_mastery": 1, "evasion_bonus": 0.4},
                    emoji="👤"
                ),
                StoryChoice(
                    id="hit_and_run",
                    text="Use hit-and-run tactics",
                    description="Strike quickly and retreat",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"agility": 1, "speed_bonus": 0.3},
                    emoji="💨"
                ),
                StoryChoice(
                    id="find_weakness",
                    text="Look for the bear's weak points",
                    description="Study the enemy for vulnerabilities",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"analysis": 1, "critical_bonus": 0.5},
                    emoji="🎯"
                )
            ]
        )
    ],

    # DEMON CASTLE ARC
    "demon_castle_001": [
        StoryEvent(
            id="demon_castle_intro",
            event_type=StoryEventType.EXPLORATION,
            title="The Demon Castle",
            description="You discover a mysterious key that opens a portal to the Demon Castle - a place of immense danger and power.",
            speaker="System",
            dialogue="DEMON CASTLE DUNGEON UNLOCKED: This is an S-rank equivalent dungeon. Extreme caution advised.",
            choices=[
                StoryChoice(
                    id="enter_immediately",
                    text="Enter the Demon Castle now",
                    description="Face the challenge head-on",
                    choice_type=StoryChoiceType.EXPLORATION_CHOICE,
                    consequences={"reckless_courage": 1},
                    emoji="🏰"
                ),
                StoryChoice(
                    id="prepare_first",
                    text="Prepare thoroughly before entering",
                    description="Make sure you're ready for the challenge",
                    choice_type=StoryChoiceType.EXPLORATION_CHOICE,
                    consequences={"preparation": 1},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="study_castle",
                    text="Study the castle from outside first",
                    description="Gather information before entering",
                    choice_type=StoryChoiceType.EXPLORATION_CHOICE,
                    consequences={"intelligence": 1},
                    emoji="🔍"
                )
            ]
        ),
        StoryEvent(
            id="demon_castle_boss",
            event_type=StoryEventType.BATTLE,
            title="Baran, the Demon Noble",
            description="You face Baran, a powerful demon noble who rules this castle. This is your greatest challenge yet!",
            speaker="Baran",
            dialogue="A human dares to enter my domain? You will make an excellent addition to my undead army!",
            battle_enemies=[
                {"name": "Baran", "level": 50, "hp": 15000, "attack": 300, "defense": 200}
            ],
            choices=[
                StoryChoice(
                    id="shadow_army",
                    text="Summon your shadow soldiers",
                    description="Use your growing shadow army",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"necromancy": 2, "army_bonus": 0.4},
                    requirements={"system_user": True},
                    emoji="👥"
                ),
                StoryChoice(
                    id="solo_battle",
                    text="Face Baran in single combat",
                    description="Prove your individual strength",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"personal_power": 2, "damage_bonus": 0.3},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="tactical_combat",
                    text="Use strategy and the environment",
                    description="Fight smart, not just hard",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"tactical_genius": 1, "all_bonus": 0.2},
                    emoji="🧠"
                )
            ]
        )
    ],

    # JEJU ISLAND RAID
    "jeju_island_001": [
        StoryEvent(
            id="jeju_intro",
            event_type=StoryEventType.DIALOGUE,
            title="The Jeju Island Crisis",
            description="Jeju Island has been overrun by giant ants. You're invited to join the raid to reclaim it.",
            speaker="Go Gun-Hee",
            dialogue="Hunter Sung, we need your help. Jeju Island has fallen to the ants. Will you join the raid?",
            choices=[
                StoryChoice(
                    id="accept_mission",
                    text="I'll help reclaim Jeju Island",
                    description="Accept the dangerous mission",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"heroism": 2},
                    emoji="🏝️"
                ),
                StoryChoice(
                    id="ask_details",
                    text="Tell me more about the situation",
                    description="Gather intelligence first",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"strategic_thinking": 1},
                    emoji="📋"
                ),
                StoryChoice(
                    id="express_concern",
                    text="This sounds extremely dangerous",
                    description="Voice your concerns about the mission",
                    choice_type=StoryChoiceType.DIALOGUE_RESPONSE,
                    consequences={"caution": 1},
                    emoji="⚠️"
                )
            ]
        ),
        StoryEvent(
            id="ant_queen_battle",
            event_type=StoryEventType.BATTLE,
            title="The Ant Queen",
            description="You face the Ant Queen, the source of Jeju Island's ant infestation. This S-rank monster is incredibly powerful!",
            speaker="Ant Queen",
            dialogue="*Screeches* You dare challenge the Queen of this island?!",
            battle_enemies=[
                {"name": "Ant Queen", "level": 60, "hp": 25000, "attack": 400, "defense": 250}
            ],
            choices=[
                StoryChoice(
                    id="full_power",
                    text="Use your full power from the start",
                    description="Don't hold back against this threat",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"overwhelming_power": 2, "damage_bonus": 0.5},
                    emoji="💥"
                ),
                StoryChoice(
                    id="protect_team",
                    text="Focus on protecting your teammates",
                    description="Prioritize the safety of other hunters",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"protector": 2, "team_bonus": 0.3},
                    emoji="🛡️"
                ),
                StoryChoice(
                    id="strategic_assault",
                    text="Coordinate a strategic assault",
                    description="Work with the team for maximum effectiveness",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"leadership": 2, "coordination_bonus": 0.4},
                    emoji="🎯"
                )
            ]
        )
    ],

    # SHADOW MONARCH AWAKENING
    "shadow_monarch_001": [
        StoryEvent(
            id="monarch_awakening",
            event_type=StoryEventType.SYSTEM_MESSAGE,
            title="The Shadow Monarch Awakens",
            description="You finally understand your true nature. You are not just a hunter - you are the Shadow Monarch!",
            speaker="System",
            dialogue="CONGRATULATIONS: You have awakened as the Shadow Monarch. Your true journey begins now.",
            choices=[
                StoryChoice(
                    id="embrace_power",
                    text="Embrace your destiny as the Shadow Monarch",
                    description="Accept your role as one of the Monarchs",
                    choice_type=StoryChoiceType.SYSTEM_CHOICE,
                    consequences={"monarch_power": 3},
                    emoji="👑"
                ),
                StoryChoice(
                    id="stay_human",
                    text="I'm still human, no matter what power I have",
                    description="Hold onto your humanity",
                    choice_type=StoryChoiceType.SYSTEM_CHOICE,
                    consequences={"humanity": 2},
                    emoji="❤️"
                ),
                StoryChoice(
                    id="question_destiny",
                    text="What does this mean for the world?",
                    description="Consider the implications of your power",
                    choice_type=StoryChoiceType.SYSTEM_CHOICE,
                    consequences={"wisdom": 2},
                    emoji="🌍"
                )
            ]
        ),
        StoryEvent(
            id="final_battle",
            event_type=StoryEventType.BATTLE,
            title="The Final Confrontation",
            description="You face the ultimate enemy - the Architect of the System itself, in a battle that will determine the fate of all worlds!",
            speaker="The Architect",
            dialogue="So, the Shadow Monarch has finally awakened. Let us see if you can surpass your predecessor!",
            battle_enemies=[
                {"name": "The Architect", "level": 100, "hp": 100000, "attack": 1000, "defense": 500}
            ],
            choices=[
                StoryChoice(
                    id="shadow_army_ultimate",
                    text="Command your entire shadow army",
                    description="Use the full might of your shadow legion",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"shadow_mastery": 3, "army_ultimate": 1.0},
                    emoji="👥"
                ),
                StoryChoice(
                    id="monarch_power",
                    text="Unleash your full Monarch power",
                    description="Use your true power as a Monarch",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"monarch_mastery": 3, "power_ultimate": 1.0},
                    emoji="⚡"
                ),
                StoryChoice(
                    id="human_heart",
                    text="Fight with your human heart",
                    description="Let your humanity be your strength",
                    choice_type=StoryChoiceType.BATTLE_STRATEGY,
                    consequences={"human_strength": 3, "heart_power": 1.0},
                    emoji="❤️"
                )
            ]
        )
    ]
}
