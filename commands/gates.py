import discord
from discord.ext import commands
from discord import ui, app_commands
import random
import time
import asyncio
import logging
from datetime import datetime
from collections import deque
from typing import Optional

# Assuming these imports are correct and the files exist
from structure.guild import Guild
from structure.skills import SkillManager
from utilis.utilis import extractName, getStatWeapon, randM
from structure.player import Player
from structure.emoji import getEmoji
from commands.missions import track_mission_progress

def pbar(current, max_val, divs=10):
    """Creates a stylish, emoji-based progress bar like other systems."""
    if max_val <= 0: return ""
    progress = max(0, min(1, current / max_val))
    fill = {'s': getEmoji("GSTART"), 'm': getEmoji("GMID"), 'e': getEmoji("GEND")}
    empty = {'s': getEmoji("EGSTART"), 'm': getEmoji("EGMIDDLE"), 'e': getEmoji("EGEND")}
    filled_len = round(divs * progress)
    if divs <= 1: return fill['s'] if filled_len > 0 else empty['s']
    bar = [fill['s'] if filled_len > 0 else empty['s']]
    for i in range(1, divs - 1): bar.append(fill['m'] if i < filled_len else empty['m'])
    bar.append(fill['e'] if filled_len == divs else empty['e'])
    return "".join(bar) + f" `[{int(current)}/{int(max_val)}]`"

BOSS_DATA = {
    "E": {"name": "Blue Venom-Fanged Kasaka", "hp_multiplier": 2000, "atk": 80, "def": 50, "rank": "E", "image": "https://static.wikia.nocookie.net/solo-leveling/images/e/ec/Anime_Episode_4_Kasaka_Snake.jpg/revision/latest/scale-to-width-down/1000?cb=20240127204652"},
    "D": {"name": "Stone Golem", "hp_multiplier": 3000, "atk": 120, "def": 75, "rank": "D", "image": "https://static.wikia.nocookie.net/solo-leveling/images/4/47/StoneGolem1.jpg/revision/latest?cb=20210628163114"},
    "C": {"name": "Giant Arachnid Buryura", "hp_multiplier": 4000, "atk": 160, "def": 75, "rank": "C", "image": "https://static.wikia.nocookie.net/solo-leveling/images/e/e1/Buryura1.jpg/revision/latest?cb=20210627232921"},
    "B": {"name": "Armored Minotaur", "hp_multiplier": 5000, "atk": 200, "def": 175, "rank": "B", "image": "https://i.pinimg.com/736x/79/86/92/798692258253a028b98975ea765d1d80.jpg"},
    "A": {"name": "Kargalan", "hp_multiplier": 7000, "atk": 280, "def": 200, "rank": "A", "image": "https://static.wikia.nocookie.net/solo-leveling/images/f/fd/Kargalgan1.jpg/revision/latest?cb=20210624152303"},
    "S": {"name": "Kamish", "hp_multiplier": 10000, "atk": 400, "def": 300, "rank": "S", "image": "https://static.wikia.nocookie.net/solo-leveling/images/7/72/Kamish2.jpg/revision/latest?cb=20210406203322"}
}
# Player directional emojis - using the correct ones from emojis.json
PLAYER_DIRECTIONAL_EMOJIS = {
    "p1": {"up": getEmoji("p1u"), "down": getEmoji("p1d"), "left": getEmoji("p1l"), "right": getEmoji("p1r")},
    "p2": {"up": getEmoji("p2u"), "down": getEmoji("p2d"), "left": getEmoji("p2l"), "right": getEmoji("p2r")},
    "p3": {"up": getEmoji("p3u"), "down": getEmoji("p3d"), "left": getEmoji("p3l"), "right": getEmoji("p3r")},
    "p4": {"up": getEmoji("p4u"), "down": getEmoji("p4d"), "left": getEmoji("p4l"), "right": getEmoji("p4r")},
}

# Default player emojis (facing down)
PLAYER_EMOJI = [getEmoji("p1d"), getEmoji("p2d"), getEmoji("p3d"), getEmoji("p4d")]
QUEST_DURATION = 600  # 10 minutes
MONSTERS_TO_DEFEAT = 10
BOSS_ROOM_CHANCE = 0.15  # 15% chance per monster kill to reveal boss room
MIN_KILLS_FOR_BOSS = 5   # Minimum kills before boss room can appear

class Gate:
    def __init__(self, bot, rank, start_time_unix, guild, cog):
        self.bot, self.rank, self.start_time_unix, self.guild, self.cog = bot, rank, start_time_unix, guild, cog
        self.participants, self.enemies, self.tk_enemies = {}, {}, 0
        self.logs = deque(maxlen=6)
        self.boss_battle, self.finished, self._boss_spawn_lock = None, False, asyncio.Lock()
        self.message, self.quest_timer_task = None, None
        self.boss_room_revealed = False
        self.boss_room_position = None
        self.boss_warnings_sent = 0
        self.boss_defeated = False  # Prevent re-fighting boss
        self.monster_movement_task = None  # Task for moving monsters

    async def start_quest_timer(self):
        self.quest_timer_task = asyncio.create_task(self._quest_timer())

    async def start_monster_movement(self):
        """Start the monster movement task"""
        self.monster_movement_task = asyncio.create_task(self._monster_movement_loop())

    async def _monster_movement_loop(self):
        """Move monsters every 8 seconds"""
        try:
            while not self.finished:
                await asyncio.sleep(8)  # Wait 8 seconds
                if not self.finished:
                    await self.move_monsters()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in monster movement loop: {e}")

    async def move_monsters(self):
        """Move all living monsters to new positions"""
        if self.finished:
            return

        new_positions = {}
        grid_size = 10

        for (x, y), enemy in list(self.enemies.items()):
            # All enemies in self.enemies are living (defeated ones are removed)
            # Try to find a new position for this living monster
            attempts = 0
            while attempts < 20:  # Prevent infinite loops
                # Move in a random direction
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
                dx, dy = random.choice(directions)
                new_x, new_y = x + dx, y + dy

                # Keep within bounds
                if 0 <= new_x < grid_size and 0 <= new_y < grid_size:
                    # Check if new position is free
                    if ((new_x, new_y) not in new_positions and
                        not self.is_player_position(new_x, new_y) and
                        (new_x, new_y) != self.boss_room_position):
                        new_positions[(new_x, new_y)] = enemy
                        break

                attempts += 1
            else:
                # If no valid position found, keep current position
                new_positions[(x, y)] = enemy

        # Update enemy positions
        self.enemies = new_positions

        # Update the gate display if there's a message
        if self.message:
            try:
                await self.cog.update_gate_display(self)
                # Add movement log
                self.logs.append("👹 The monsters have moved to new positions!")
            except Exception as e:
                print(f"Error updating gate display after monster movement: {e}")

    async def _quest_timer(self):
        await asyncio.sleep(QUEST_DURATION)
        if not self.finished:
            await self.handle_quest_failure()

    async def handle_quest_failure(self):
        if self.finished: return
        self.finished = True

        # Create failure summary
        participants_info = []
        for user_id, p_data in self.participants.items():
            kills = p_data.get('kills', 0)
            status = "💀 Dead" if p_data.get('dead', False) else "❤️ Alive"
            participants_info.append(f"{p_data['emoji']} <@{user_id}> - {kills} kills ({status})")

        embed = discord.Embed(
            title="⏰ Gate Failed - Time Expired!",
            description=f"> The hunters failed to clear the {self.rank}-rank gate within 10 minutes.\n\n**Final Results:**\n- Monsters Defeated: **{self.tk_enemies}/{MONSTERS_TO_DEFEAT}**\n- Boss Room: **{'🏛️ Revealed' if self.boss_room_revealed else '❓ Hidden'}**",
            color=discord.Color.red()
        )

        if participants_info:
            embed.add_field(name="👥 Participants", value="\n".join(participants_info), inline=False)

        embed.set_footer(text="Better luck next time! Gates require teamwork and strategy.")

        # Clean up and notify
        await self.cog.cleanup_gate(self)

        if self.message:
            try:
                await self.message.edit(embed=embed, view=None)
            except (discord.HTTPException, discord.NotFound) as e:
                # Handle webhook token expiration or message not found
                logging.error(f"Failed to edit gate failure message: {e}")
                # Try to send a new message to the channel if possible
                try:
                    if hasattr(self.message, 'channel'):
                        await self.message.channel.send(embed=embed)
                except Exception:
                    pass

    def place_enemies(self, num_enemies):
        grid_size = 10
        for _ in range(num_enemies):
            while True:
                # Place enemies away from the edges for a better experience
                x, y = random.randint(1, grid_size - 2), random.randint(1, grid_size - 2)
                if (x, y) not in self.enemies and not self.is_player_position(x, y):
                    enemy_data = randM(self.rank)
                    enemy_name_key = enemy_data["name"].replace(" ", "_").lower()
                    enemy_emoji = getEmoji(enemy_name_key)
                    self.enemies[(x, y)] = {"revealed": False, "type": enemy_data, "emoji": enemy_emoji}
                    break

    def is_player_position(self, x, y):
        return any(data["x"] == x and data["y"] == y for data in self.participants.values())

    def generate_grid(self, highlight_user_id=None, show_movement_preview=False, movement_direction=None, movement_type="walk"):
        grid_size = 10
        grid = [["⬛" for _ in range(grid_size)] for _ in range(grid_size)]

        # Place players first
        for user_id, data in self.participants.items():
            if not data.get('dead', False):  # Only show alive players
                grid[data["y"]][data["x"]] = data["emoji"]

        # Place revealed enemies (defeated enemies are removed from self.enemies)
        for (x, y), enemy in self.enemies.items():
            if enemy["revealed"]:
                # Only living enemies are in self.enemies now
                grid[y][x] = enemy["emoji"]

        # Place boss room if revealed and not defeated
        if self.boss_room_revealed and self.boss_room_position and not self.boss_defeated:
            bx, by = self.boss_room_position
            grid[by][bx] = "🏛️"  # Boss room emoji

        # Highlight adjacent spaces for selected user
        if highlight_user_id and highlight_user_id in self.participants:
            px, py = self.participants[highlight_user_id]["x"], self.participants[highlight_user_id]["y"]

            # Show possible movement directions
            directions = {
                "up": (0, -1),
                "down": (0, 1),
                "left": (-1, 0),
                "right": (1, 0)
            }

            if show_movement_preview and movement_direction in directions:
                # Show movement path preview
                dx, dy = directions[movement_direction]
                movement_distances = {
                    "step": 1,    # Single step
                    "walk": 3,    # Max 3 spaces
                    "run": 7,     # Max 7 spaces
                    "sprint": 10  # Until boundary
                }
                max_distance = movement_distances.get(movement_type, 3)

                for step in range(1, max_distance + 1):
                    nx, ny = px + (dx * step), py + (dy * step)

                    # Check boundaries
                    if nx < 0 or nx > 9 or ny < 0 or ny > 9:
                        break

                    # Check for obstacles
                    if self.is_player_position(nx, ny) or (nx, ny) in self.enemies:
                        # Show obstacle and stop
                        if grid[ny][nx] == "⬛":
                            grid[ny][nx] = "🔴"  # Obstacle marker
                        break

                    # Show movement path
                    if grid[ny][nx] == "⬛":
                        grid[ny][nx] = "🟢"  # Movement path
            else:
                # Show adjacent spaces for general movement
                for direction, (dx, dy) in directions.items():
                    nx, ny = px + dx, py + dy
                    if (0 <= nx < grid_size and 0 <= ny < grid_size and
                        not self.is_player_position(nx, ny) and
                        grid[ny][nx] == "⬛"):
                        grid[ny][nx] = "🟦"

        return "\n".join(" ".join(row) for row in grid)

    def check_boss_room_revelation(self):
        """Check if boss room should be revealed after monster kill"""
        if (self.boss_room_revealed or
            self.tk_enemies < MIN_KILLS_FOR_BOSS or
            self.finished):
            return False

        # Chance increases with more kills
        base_chance = BOSS_ROOM_CHANCE
        kill_bonus = (self.tk_enemies - MIN_KILLS_FOR_BOSS) * 0.05
        total_chance = min(base_chance + kill_bonus, 0.8)  # Max 80% chance

        if random.random() < total_chance:
            self.reveal_boss_room()
            return True
        return False

    def reveal_boss_room(self):
        """Reveal the boss room at a strategic location"""
        if self.boss_room_revealed:
            return

        # Place boss room away from players and enemies
        grid_size = 10
        attempts = 0
        while attempts < 50:  # Prevent infinite loop
            x, y = random.randint(2, grid_size - 3), random.randint(2, grid_size - 3)

            # Check if position is clear and not too close to players
            if ((x, y) not in self.enemies and
                not self.is_player_position(x, y) and
                self.is_good_boss_room_location(x, y)):

                self.boss_room_position = (x, y)
                self.boss_room_revealed = True

                # Add ominous log message
                self.logs.append("⚠️ **A powerful presence stirs deeper in the dungeon...**")
                break
            attempts += 1

    def is_good_boss_room_location(self, x, y):
        """Check if location is good for boss room (not too close to players)"""
        min_distance = 3
        for player_data in self.participants.values():
            if not player_data.get('dead', False):
                px, py = player_data['x'], player_data['y']
                distance = abs(x - px) + abs(y - py)  # Manhattan distance
                if distance < min_distance:
                    return False
        return True

    async def start_collaborative_boss_battle(self, interaction: discord.Interaction):
        async with self._boss_spawn_lock:
            if self.finished: return
            self.finished = True
            if self.quest_timer_task: self.quest_timer_task.cancel()
            if self.monster_movement_task: self.monster_movement_task.cancel()

            boss_info = BOSS_DATA.get(self.rank, BOSS_DATA["E"])
            boss = {"name": boss_info["name"], "hp": boss_info["hp_multiplier"] * len(self.participants), "atk": boss_info["atk"], "def": boss_info["def"], "rank": boss_info["rank"], "image": boss_info["image"]}
            
            participants_data = {}
            for user_id, data in self.participants.items():
                if data.get('dead', False): continue
                player = await Player.get(user_id)
                total_atk, total_def, total_hp, total_mp = player.attack, player.defense, player.hp, player.mp
                
                for slot in ["Weapon", "Weapon_2"]:
                    if weapon_id := player.equipped.get(slot):
                        if weapon_id in player.inventory:
                            weapon_stats = await getStatWeapon(weapon_id, player.inventory[weapon_id].get("level", 1))
                            if weapon_stats:
                                total_atk += weapon_stats.get('attack', 0); total_def += weapon_stats.get('defense', 0)
                                total_hp += weapon_stats.get('hp', 0); total_mp += weapon_stats.get('mp', 0)

                participants_data[user_id] = {"hp": total_hp, "mhp": total_hp, "mp": total_mp, "atk": total_atk, "def": total_def, "skills": player.skills, "kills": data['kills'], "name": data['name'], "total_damage": 0}

            self.boss_battle = BossBattleView(self.bot, self, participants_data, boss, self.cog)
            await self.boss_battle.start(interaction)

class GateCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_gates = {}
        self.player_gate_map = {}

    async def send_response(self, ctx, embed=None, content=None, view=None, ephemeral=False):
        """Helper function to send responses for both interactions and regular commands"""
        if hasattr(ctx, 'interaction') and ctx.interaction:
            if ctx.interaction.response.is_done():
                return await ctx.interaction.followup.send(embed=embed, content=content, view=view, ephemeral=ephemeral)
            else:
                return await ctx.interaction.response.send_message(embed=embed, content=content, view=view, ephemeral=ephemeral)
        else:
            return await ctx.send(embed=embed, content=content, view=view)

    async def cleanup_gate(self, gate):
        """Removes a gate and its participants from tracking."""
        if gate.message and gate.message.id in self.active_gates:
            del self.active_gates[gate.message.id]

        # Cancel monster movement task
        if gate.monster_movement_task and not gate.monster_movement_task.done():
            gate.monster_movement_task.cancel()
            try:
                await gate.monster_movement_task
            except asyncio.CancelledError:
                pass

        for user_id in list(gate.participants.keys()):
            if user_id in self.player_gate_map:
                del self.player_gate_map[user_id]
            player = await Player.get(user_id)
            if player:
                try:
                    player.inc = False
                    await player.save()
                except Exception as e:
                    print(f"Error saving player {user_id} after gate cleanup: {e}")
                    # Continue without saving to prevent blocking

    def create_gate_battle_view(self, gate, player_id, enemy, original_interaction):
        return GateBattleView(self.bot, gate, player_id, enemy, original_interaction, self)

    def create_boss_battle_view(self, gate, participants_data, boss):
        return BossBattleView(self.bot, gate, participants_data, boss, self)

    @commands.hybrid_command(name="gate", description="Spawns a gate for your guild to conquer.")
    async def spawn_gate(self, ctx: commands.Context):
        # Defer only if it's an interaction
        if ctx.interaction:
            await ctx.defer()

        try:
            # Check if player is already in an active gate
            if ctx.author.id in self.player_gate_map:
                message_id = self.player_gate_map.get(ctx.author.id)
                if message_id:
                    gate = self.active_gates.get(message_id)
                    if gate and not gate.finished:
                        view = ui.View()
                        view.add_item(ui.Button(label="Go to Your Active Gate", style=discord.ButtonStyle.link, url=gate.message.jump_url))
                        await self.send_response(ctx, content="You are already in an active gate. Click the button to return to it.", view=view, ephemeral=True)
                        return
                    else:
                        # The gate data is gone or finished, so the mapping is stale. Remove it.
                        del self.player_gate_map[ctx.author.id]

            # Get player data
            player = await Player.get(ctx.author.id)
            if not player:
                await self.send_response(ctx, embed=discord.Embed(title="Error", description="You haven't started the bot yet. Use `/start` to register.", color=discord.Color.red()), ephemeral=True)
                return
            if not player.guild:
                await self.send_response(ctx, embed=discord.Embed(title="<:guild:1329840946975604837> No Guild", description="You need to be in a guild to spawn a gate.", color=discord.Color.orange()))
                return
            if player.key < 1:
                await self.send_response(ctx, embed=discord.Embed(title=f"{getEmoji('gate_key')} No Keys", description="You need at least **1** key to spawn a gate.", color=discord.Color.orange()))
                return

            # Consume key and create gate
            player.key -= 1
            try:
                await player.save()
            except Exception as e:
                print(f"Error saving player {ctx.author.id} after key consumption: {e}")
                # Continue without saving to prevent blocking gate creation

            gate_rank = random.choices(["E", "D", "C", "B", "A", "S"], weights=[40, 25, 15, 10, 7, 3], k=1)[0]
            start_time_unix = int(time.time() + 90)
            gate = Gate(self.bot, gate_rank, start_time_unix, player.guild, self)
            gate.place_enemies(MONSTERS_TO_DEFEAT)

            # Create spawn embed
            embed = discord.Embed(title="🌀 A Gate Has Spawned!", description="> Hunters from the guild must clear it before it becomes unstable.", color=discord.Color.blurple())
            embed.set_image(url="https://imgs.search.brave.com/hU-dNmKSPWmHYJewD3-1xJrZaM5hZAFyafCBs2kp9wc/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9zdGF0/aWMxLmNicmltYWdl/cy5jb20vd29yZHBy/ZXNzL3dwLWNvbnRl/bnQvdXBsb2Fkcy8y/MDI0LzA0L2dhdGUt/c29sby1sZXZlbGlu/Zy0xLmpwZWc")
            embed.add_field(name="🏛️ Gate Information", value=f"**Rank:** {gate.rank}-Rank\n**Starting:** <t:{start_time_unix}:R>\n**Guild:** {extractName(player.guild)}", inline=False)
            embed.add_field(name="👥 Hunters", value="No hunters have joined yet.", inline=False)
            embed.set_footer(text="⚠️ Join quickly before the gate starts! Maximum 4 hunters allowed.")

            view = self.create_join_view()
            message = await self.send_response(ctx, embed=embed, view=view)
            gate.message = message
            self.active_gates[message.id] = gate

            # Wait for gate to start
            sleep_time = max(0, start_time_unix - time.time())
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        except Exception as e:
            # Error handling
            error_embed = discord.Embed(
                title="❌ Gate Spawn Error",
                description=f"An error occurred while spawning the gate: {str(e)}",
                color=discord.Color.red()
            )
            await self.send_response(ctx, embed=error_embed, ephemeral=True)
            return

        # Continue with gate start logic (moved outside try-except)
        try:
            if message.id in self.active_gates:
                gate_data = self.active_gates[message.id]

                if not gate_data.participants:
                    await message.edit(embed=discord.Embed(title="❌ Gate Closed!", description="The gate disappeared as no one joined.", color=discord.Color.red()), view=None)
                    await self.cleanup_gate(gate_data)
                    return

            d_embed = discord.Embed(
                title="Gate Entered!",
                description=(
                    f"> Explore the dungeon and defeat monsters to reveal the boss room!\n\n"
                    f"**Quest Objectives:**\n"
                    f"- Defeat monsters to gain strength: **{gate_data.tk_enemies}/{MONSTERS_TO_DEFEAT}**\n"
                    f"- Find the hidden boss room: **{'🏛️ Revealed' if gate_data.boss_room_revealed else '❓ Hidden'}**\n"
                    f"- Challenge the {gate_data.rank}-Rank boss and clear the gate!\n\n"
                    f"*Time Limit: **{int(QUEST_DURATION/60)}** minutes*"
                ),
                color=discord.Color.blurple()
            )

            participants_info = "\n".join(f"{p_data['emoji']} <@{user_id}>" for user_id, p_data in gate_data.participants.items())
            d_embed.add_field(name="Hunters", value=participants_info, inline=False)
            d_embed.add_field(name="Grid", value=gate_data.generate_grid(), inline=False)

            main_view = self.create_main_buttons(gate_data)
            await message.edit(embed=d_embed, view=main_view)
            gate_data.message = message
            await gate_data.start_quest_timer()
            await gate_data.start_monster_movement()
        except Exception as e:
            # Handle any errors during gate start
            error_embed = discord.Embed(
                title="❌ Gate Start Error",
                description=f"An error occurred while starting the gate: {str(e)}",
                color=discord.Color.red()
            )
            try:
                await message.edit(embed=error_embed, view=None)
            except:
                pass  # Message might be deleted

    def create_join_view(self):
        view = ui.View(timeout=90)
        join_button = ui.Button(label="Join", style=discord.ButtonStyle.blurple)
        
        async def join_callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)

            gate = self.active_gates.get(interaction.message.id)
            if not gate or gate.finished or time.time() > gate.start_time_unix:
                await interaction.followup.send("This gate is no longer active or has already started.", ephemeral=True)
                return

            if interaction.user.id in self.player_gate_map and self.player_gate_map.get(interaction.user.id) != interaction.message.id:
                other_gate_msg_id = self.player_gate_map[interaction.user.id]
                other_gate = self.active_gates.get(other_gate_msg_id)
                if other_gate and not other_gate.finished:
                    btn_view = ui.View()
                    btn_view.add_item(ui.Button(label="Go to Your Active Gate", style=discord.ButtonStyle.link, url=other_gate.message.jump_url))
                    await interaction.followup.send("You are already in another active gate.", view=btn_view, ephemeral=True)
                    return
                else:
                    del self.player_gate_map[interaction.user.id]

            player = await Player.get(interaction.user.id)
            if not player:
                await interaction.followup.send("You haven't started the bot yet. Use `/start` to register.", ephemeral=True)
                return

            # Check guild membership or alliance permission
            from guild_integration_manager import GuildIntegrationManager
            gate_guild = await GuildIntegrationManager.get_unified_guild(gate.guild)
            if player.guild != gate.guild:
                if not gate_guild or not gate_guild.allow_alliances:
                    await interaction.followup.send("You must be in the correct guild to join this gate, or the guild must allow alliances.", ephemeral=True)
                    return
                else:
                    # Player is from allied guild - show alliance message
                    player_guild = await GuildIntegrationManager.get_unified_guild(player.guild) if player.guild else None
                    guild_name = player_guild.name if player_guild else "Unknown Guild"
                    await interaction.followup.send(f"🤝 You joined as an allied hunter from **{guild_name}**!", ephemeral=True)
            if interaction.user.id in gate.participants:
                await interaction.followup.send("You have already joined this gate.", ephemeral=True)
                return
            if len(gate.participants) >= 4:
                await interaction.followup.send("This gate is full.", ephemeral=True)
                return

            player_number = len(gate.participants) + 1  # p1, p2, p3, p4
            player_key = f"p{player_number}"
            initial_direction = "down"  # Start facing down
            player_emoji = PLAYER_DIRECTIONAL_EMOJIS[player_key][initial_direction]

            gate.participants[interaction.user.id] = {
                "x": random.randint(0, 9),
                "y": random.randint(0, 9),
                "mp": player.mp,
                "mhp": player.hp,
                "hp": player.hp,
                "cooldown": 0,
                "dead": False,
                "kills": 0,
                "dir": initial_direction,
                "name": interaction.user.name,
                "emoji": player_emoji,
                "player_key": player_key,  # Store which player they are (p1, p2, etc.)
                "stamina": 100,
                "max_stamina": 100
            }
            self.player_gate_map[interaction.user.id] = interaction.message.id

            new_embed = interaction.message.embeds[0]
            participants_info = "\n".join(f"{p_data['emoji']} <@{user_id}> ❤️`{p_data.get('hp', 0)}/{p_data.get('mhp', 0)}` ⚡`{p_data.get('stamina', 100)}/{p_data.get('max_stamina', 100)}`" for user_id, p_data in gate.participants.items())
            
            field_index = -1
            for i, field in enumerate(new_embed.fields):
                if field.name == "Hunters":
                    field_index = i
                    break
            
            if field_index != -1:
                new_embed.set_field_at(field_index, name="Hunters", value=participants_info, inline=False)
            
            await interaction.message.edit(embed=new_embed)
            await interaction.followup.send("You have successfully joined the gate!", ephemeral=True)

        join_button.callback = join_callback
        view.add_item(join_button)
        return view

    def create_main_buttons(self, gate):
        view = ui.View(timeout=QUEST_DURATION)

        async def move_callback(interaction: discord.Interaction):
            # Check if gate is finished
            if gate.finished or gate.boss_defeated:
                await interaction.response.send_message("❌ This gate has been completed. The boss has been defeated!", ephemeral=True)
                return

            player = gate.participants.get(interaction.user.id)
            if not player or player.get('dead'):
                await interaction.response.send_message("You cannot move.", ephemeral=True)
                return

            # Check cooldown
            if time.time() < player.get('cooldown', 0):
                remaining_cooldown = max(0, player.get('cooldown', 0) - time.time())
                await interaction.response.send_message(f"You are on cooldown for {remaining_cooldown:.1f} seconds!", ephemeral=True)
                return

            move_view = self.create_move_buttons(gate, interaction)
            move_embed = discord.Embed(
                title="Move",
                description=f"**Mode: 👣 Stepping**\n\nChoose your movement type and direction.\n\n**Grid**\n{gate.generate_grid(interaction.user.id)}",
                color=discord.Color.blurple()
            )
            move_embed.add_field(
                name="Movement Types",
                value="👣 **Step:** 1 space precisely\n🚶 **Walk:** 1-3 spaces safely\n🏃 **Run:** 4-7 spaces quickly\n💨 **Sprint:** Until obstacle (fastest)",
                inline=False
            )
            await interaction.response.send_message(embed=move_embed, view=move_view, ephemeral=True)

        async def stats_callback(interaction: discord.Interaction):
            player_data = gate.participants.get(interaction.user.id)
            if not player_data:
                await interaction.response.send_message("You are not in this gate.", ephemeral=True)
                return
            
            status = "`Dead`" if player_data.get('dead') else "`Alive`"
            stats_embed = discord.Embed(title=f"{interaction.user.name}'s Stats", color=discord.Color.green())
            stats_embed.add_field(name="Status", value=f"**Kills**: {player_data['kills']}\n**Health**: {player_data['hp']}/{player_data['mhp']} ({status})")
            await interaction.response.send_message(embed=stats_embed, ephemeral=True)

        async def logs_callback(interaction: discord.Interaction):
            await interaction.response.send_message(f"**Dungeon Logs:**\n" + "\n".join(list(gate.logs)), ephemeral=True)

        async def leave_callback(interaction: discord.Interaction):
            if interaction.user.id in gate.participants:
                del gate.participants[interaction.user.id]
                if interaction.user.id in self.player_gate_map:
                    del self.player_gate_map[interaction.user.id]
                
                await interaction.response.send_message("You have left the gate.", ephemeral=True)
                
                new_embed = gate.message.embeds[0]
                participants_info = "\n".join(f"{p_data['emoji']} <@{user_id}> ❤️`{p_data.get('hp', 0)}/{p_data.get('mhp', 0)}` ⚡`{p_data.get('stamina', 100)}/{p_data.get('max_stamina', 100)}`" for user_id, p_data in gate.participants.items()) or "No hunters."
                
                field_index = -1
                for i, field in enumerate(new_embed.fields):
                    if field.name == "Hunters":
                        field_index = i
                        break
                if field_index != -1:
                    new_embed.set_field_at(field_index, name="Hunters", value=participants_info, inline=False)
                
                grid_field_index = -1
                for i, field in enumerate(new_embed.fields):
                    if field.name == "Grid":
                        grid_field_index = i
                        break
                if grid_field_index != -1:
                    new_embed.set_field_at(grid_field_index, name="Grid", value=gate.generate_grid(), inline=False)
                await gate.message.edit(embed=new_embed)

        move_button = ui.Button(label="Move", style=discord.ButtonStyle.primary)
        move_button.callback = move_callback
        stats_button = ui.Button(label="Stats", style=discord.ButtonStyle.secondary)
        stats_button.callback = stats_callback
        logs_button = ui.Button(label="Logs", style=discord.ButtonStyle.success)
        logs_button.callback = logs_callback
        leave_button = ui.Button(label="Leave", style=discord.ButtonStyle.danger)
        leave_button.callback = leave_callback

        view.add_item(move_button)
        view.add_item(stats_button)
        view.add_item(logs_button)
        view.add_item(leave_button)
        return view

    def create_move_buttons(self, gate, original_interaction: discord.Interaction):
        view = ui.View(timeout=180)

        async def move_action(interaction: discord.Interaction, direction: str, movement_type: str = "walk"):
            player = gate.participants.get(interaction.user.id)
            if not player or player.get('dead') or time.time() < player.get('cooldown', 0):
                remaining_cooldown = max(0, player.get('cooldown', 0) - time.time())
                try:
                    from utilis.interaction_handler import InteractionHandler
                    await InteractionHandler.safe_response(
                        interaction,
                        content=f"You cannot move right now. Cooldown: {remaining_cooldown:.1f}s",
                        ephemeral=True,
                        delete_after=5
                    )
                except discord.InteractionResponded:
                    pass
                return

            # Check stamina and adjust movement type if necessary
            current_stamina = player.get('stamina', 100)
            stamina_costs = {
                "step": 5,
                "walk": 10,
                "run": 25,
                "sprint": 40
            }

            # Force step movement if not enough stamina
            if current_stamina < stamina_costs.get(movement_type, 10):
                if current_stamina >= stamina_costs["step"]:
                    movement_type = "step"
                    await interaction.followup.send("⚡ **Low stamina!** Forced to step movement.", ephemeral=True)
                else:
                    try:
                        from utilis.interaction_handler import InteractionHandler
                        await InteractionHandler.safe_response(
                            interaction,
                            content="💨 **No stamina!** Rest to recover stamina.",
                            ephemeral=True,
                            delete_after=5
                        )
                    except discord.InteractionResponded:
                        pass
                    return

            # Determine movement distance based on type
            movement_distances = {
                "step": 1,                       # Single step
                "walk": random.randint(1, 3),    # 1-3 spaces
                "run": random.randint(4, 7),     # 4-7 spaces
                "sprint": 10                     # Until boundary/obstacle
            }

            max_distance = movement_distances.get(movement_type, 1)

            # Calculate movement path
            px, py = player['x'], player['y']
            path = []
            distance_moved = 0

            # Direction vectors
            directions = {
                "up": (0, -1),
                "down": (0, 1),
                "left": (-1, 0),
                "right": (1, 0)
            }

            dx, dy = directions.get(direction, (0, 0))

            # Calculate path until obstacle or max distance
            current_x, current_y = px, py
            for step in range(1, max_distance + 1):
                nx, ny = current_x + dx, current_y + dy

                # Check boundaries
                if nx < 0 or nx > 9 or ny < 0 or ny > 9:
                    break

                # Check for other players
                if self.is_occupied(gate, nx, ny):
                    break

                # Check for enemies
                if (nx, ny) in gate.enemies:
                    # Only living enemies are in gate.enemies now (defeated ones removed)
                    enemy = gate.enemies[(nx, ny)]
                    # Reveal living enemy and stop here
                    enemy['revealed'] = True
                    path.append((nx, ny))
                    distance_moved = step
                    break

                # Check for boss room
                if gate.boss_room_revealed and (nx, ny) == gate.boss_room_position:
                    path.append((nx, ny))
                    distance_moved = step
                    break

                path.append((nx, ny))
                distance_moved = step
                current_x, current_y = nx, ny  # Update position for next step

                # Random loot chance while exploring (like original) - TEMPORARILY DISABLED
                # if random.random() < 0.15:  # 15% chance per step
                #     await self.handle_loot_discovery(interaction, gate, nx, ny)

            # If no movement possible
            if distance_moved == 0:
                try:
                    from utilis.interaction_handler import InteractionHandler
                    await InteractionHandler.safe_response(
                        interaction,
                        content="Cannot move in that direction!",
                        ephemeral=True,
                        delete_after=5
                    )
                except discord.InteractionResponded:
                    pass
                return

            # Update player position to final location
            final_x, final_y = path[-1]
            player['x'], player['y'], player['dir'] = final_x, final_y, direction

            # Update player emoji based on direction
            player_key = player.get('player_key', 'p1')  # Default to p1 if not set
            if player_key in PLAYER_DIRECTIONAL_EMOJIS and direction in PLAYER_DIRECTIONAL_EMOJIS[player_key]:
                player['emoji'] = PLAYER_DIRECTIONAL_EMOJIS[player_key][direction]

            # Consume stamina
            stamina_cost = stamina_costs.get(movement_type, 10)
            player['stamina'] = max(0, player.get('stamina', 100) - stamina_cost)

            # Optimized cooldowns - much shorter for better gameplay
            cooldown_times = {
                "step": 0.5,    # Very fast single steps
                "walk": 1.0,    # Quick walking
                "run": 1.5,     # Moderate running
                "sprint": 2.0   # Longer sprint cooldown
            }
            player['cooldown'] = time.time() + cooldown_times.get(movement_type, 1.0)

            # Create movement description
            movement_desc = f"You {movement_type} {direction} for {distance_moved} space{'s' if distance_moved > 1 else ''}."

            # Check if final position has enemy (only living enemies are in gate.enemies now)
            if (final_x, final_y) in gate.enemies:
                enemy = gate.enemies[(final_x, final_y)]

                # Living enemy - start battle
                gate.logs.append(f"{player['emoji']} moved {direction} and encountered {enemy['type']['name']}")

                # Update main gate display first
                await self.update_gate_display(gate)

                # Show movement result then start battle
                move_embed = discord.Embed(
                    title="Movement & Encounter!",
                    description=f"{movement_desc}\n\n{getEmoji('attack')} **Enemy Encountered!**\nPreparing for battle...",
                    color=discord.Color.orange()
                )
                try:
                    if interaction.response.is_done():
                        await interaction.edit_original_response(embed=move_embed, view=None)
                    else:
                        await interaction.response.edit_message(embed=move_embed, view=None)
                except discord.InteractionResponded:
                    await interaction.followup.edit_message(interaction.message.id, embed=move_embed, view=None)

                # Small delay then start battle
                await asyncio.sleep(1)
                await self.handle_battle(interaction, gate, (final_x, final_y))
            elif gate.boss_room_revealed and (final_x, final_y) == gate.boss_room_position:
                # Boss room encounter!
                gate.logs.append(f"{player['emoji']} discovered the Boss Room!")

                # Update main gate display first
                await self.update_gate_display(gate)

                # Show dramatic boss room discovery
                await self.handle_boss_room_encounter(interaction, gate)
            else:
                gate.logs.append(f"{player['emoji']} moved {direction} ({distance_moved} spaces)")

                # Update main gate display
                await self.update_gate_display(gate)

                move_embed = discord.Embed(
                    title="Movement Complete",
                    description=f"{movement_desc}\n\n**Current Position:** ({final_x}, {final_y})\n\n**Grid**\n{gate.generate_grid(interaction.user.id)}",
                    color=discord.Color.green()
                )
                move_embed.add_field(
                    name="Next Actions",
                    value="• Move again in any direction\n• Check your stats\n• View dungeon logs",
                    inline=False
                )

                try:
                    if interaction.response.is_done():
                        await interaction.edit_original_response(embed=move_embed, view=view)
                    else:
                        await interaction.response.edit_message(embed=move_embed, view=view)
                except discord.InteractionResponded:
                    await interaction.followup.edit_message(interaction.message.id, embed=move_embed, view=view)

        async def back_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            if original_interaction:
                 await original_interaction.delete_original_response()

        # Movement type selector with optimized options
        movement_select = ui.Select(
            placeholder="Choose movement type...",
            options=[
                discord.SelectOption(label="👣 Step", description="Move 1 space precisely", value="step"),
                discord.SelectOption(label="🚶 Walk", description="Move 1-3 spaces safely", value="walk"),
                discord.SelectOption(label="🏃 Run", description="Move 4-7 spaces quickly", value="run"),
                discord.SelectOption(label="💨 Sprint", description="Move until obstacle", value="sprint")
            ]
        )

        current_movement_type = "step"  # Default to precise movement

        async def movement_type_callback(interaction: discord.Interaction):
            nonlocal current_movement_type
            current_movement_type = interaction.data['values'][0]
            type_names = {"step": "👣 Stepping", "walk": "🚶 Walking", "run": "🏃 Running", "sprint": "💨 Sprinting"}

            move_embed = discord.Embed(
                title="Move",
                description=f"**Mode: {type_names[current_movement_type]}**\n\nSelect a direction to move.\n\n**Grid**\n{gate.generate_grid(interaction.user.id)}",
                color=discord.Color.blurple()
            )
            move_embed.add_field(
                name="Movement Types",
                value="👣 **Step:** 1 space precisely\n🚶 **Walk:** 1-3 spaces safely\n🏃 **Run:** 4-7 spaces quickly\n💨 **Sprint:** Until obstacle (fastest)",
                inline=False
            )
            await interaction.response.edit_message(embed=move_embed, view=view)

        movement_select.callback = movement_type_callback
        view.add_item(movement_select)

        # Direction buttons with preview
        async def direction_with_preview(interaction: discord.Interaction, direction: str):
            # Directly execute the move without confirmation
            try:
                await interaction.response.defer()
                await move_action(interaction, direction, current_movement_type)
            except Exception as e:
                try:
                    await interaction.followup.send(f"❌ Movement error: {str(e)}", ephemeral=True)
                except:
                    pass

        for emoji, direction in {"⬆️": "up", "⬇️": "down", "⬅️": "left", "➡️": "right"}.items():
            button = ui.Button(emoji=emoji, style=discord.ButtonStyle.primary, row=1)
            button.callback = lambda i, d=direction: direction_with_preview(i, d)
            view.add_item(button)

        # Rest button to recover stamina
        async def rest_action(interaction: discord.Interaction):
            player = gate.participants.get(interaction.user.id)
            if not player or player.get('dead'):
                await interaction.response.send_message("You cannot rest.", ephemeral=True)
                return

            # Check cooldown
            if time.time() < player.get('cooldown', 0):
                remaining_cooldown = max(0, player.get('cooldown', 0) - time.time())
                await interaction.response.send_message(f"You are on cooldown for {remaining_cooldown:.1f} seconds!", ephemeral=True)
                return

            # Restore stamina
            current_stamina = player.get('stamina', 100)
            max_stamina = player.get('max_stamina', 100)
            stamina_restored = min(30, max_stamina - current_stamina)  # Restore up to 30 stamina
            player['stamina'] = min(max_stamina, current_stamina + stamina_restored)
            player['cooldown'] = time.time() + 3.0  # 3 second cooldown for resting

            gate.logs.append(f"{player['emoji']} rested and recovered {stamina_restored} stamina")
            await self.update_gate_display(gate)

            await interaction.response.send_message(f"💤 **Rested!** Recovered {stamina_restored} stamina. Current: {player['stamina']}/{max_stamina}", ephemeral=True)

        rest_button = ui.Button(label="💤 Rest", style=discord.ButtonStyle.success, row=1)
        rest_button.callback = rest_action
        view.add_item(rest_button)

        # Quick movement buttons (no preview)
        async def quick_move(interaction: discord.Interaction, direction: str):
            await move_action(interaction, direction, current_movement_type)

        quick_move_select = ui.Select(
            placeholder="Quick Move (no preview)...",
            options=[
                discord.SelectOption(label="⬆️ Quick Up", description="Move up instantly", value="up"),
                discord.SelectOption(label="⬇️ Quick Down", description="Move down instantly", value="down"),
                discord.SelectOption(label="⬅️ Quick Left", description="Move left instantly", value="left"),
                discord.SelectOption(label="➡️ Quick Right", description="Move right instantly", value="right")
            ],
            row=2
        )

        async def quick_move_callback(interaction: discord.Interaction):
            direction = interaction.data['values'][0]
            await quick_move(interaction, direction)

        quick_move_select.callback = quick_move_callback
        view.add_item(quick_move_select)

        back_button = ui.Button(label="Back", style=discord.ButtonStyle.secondary, row=3)
        back_button.callback = back_callback
        view.add_item(back_button)

        return view

    def is_occupied(self, gate, x, y):
        return any(p['x'] == x and p['y'] == y for p in gate.participants.values())

    async def handle_loot_discovery(self, interaction, gate, x, y):
        """Handle random loot discovery while exploring"""
        from structure.player import Player

        # Loot table for gate exploration
        loot_table = [
            {"type": "gold", "amount": random.randint(50, 200), "weight": 40},
            {"type": "xp", "amount": random.randint(25, 100), "weight": 30},
            {"type": "key", "amount": 1, "weight": 10},
            {"type": "potion", "amount": random.randint(1, 3), "weight": 15},
            {"type": "rare_material", "amount": 1, "weight": 5}
        ]

        # Weighted random selection
        total_weight = sum(item["weight"] for item in loot_table)
        rand_num = random.randint(1, total_weight)
        current_weight = 0

        selected_loot = None
        for item in loot_table:
            current_weight += item["weight"]
            if rand_num <= current_weight:
                selected_loot = item
                break

        if not selected_loot:
            return

        # Award loot to player
        player = await Player.get(interaction.user.id)
        if not player:
            return

        loot_message = ""
        if selected_loot["type"] == "gold":
            player.gold += selected_loot["amount"]
            loot_message = f"💰 Found **{selected_loot['amount']:,}** Gold!"
        elif selected_loot["type"] == "xp":
            player.xp += selected_loot["amount"]
            loot_message = f"⭐ Found **{selected_loot['amount']:,}** XP!"
        elif selected_loot["type"] == "key":
            player.key += selected_loot["amount"]
            loot_message = f"{getEmoji('gate_key')} Found **{selected_loot['amount']}** Gate Key!"
        elif selected_loot["type"] == "potion":
            # Add to inventory (simplified)
            loot_message = f"🧪 Found **{selected_loot['amount']}** Health Potion(s)!"
        elif selected_loot["type"] == "rare_material":
            loot_message = f"💎 Found **Rare Crafting Material**!"

        try:
            await player.save()
        except Exception as e:
            print(f"Error saving player {interaction.user.id} after loot: {e}")
            # Continue without saving to prevent blocking gameplay

        # Add to gate logs
        gate.logs.append(f"🎁 {interaction.user.display_name} found loot at ({x}, {y})")

        # Send loot notification
        try:
            # Send as DM to avoid interaction conflicts
            await interaction.user.send(f"🎁 **Loot Found in Gate!**\n{loot_message}")
        except:
            pass

    async def update_gate_display(self, gate):
        """Update the main gate message with current grid state"""
        if not gate.message:
            return

        try:
            embed = gate.message.embeds[0]

            # Find and update the grid field
            for i, field in enumerate(embed.fields):
                if field.name == "Grid":
                    embed.set_field_at(i, name="Grid", value=gate.generate_grid(), inline=False)
                    break

            # Update quest progress with boss room status
            if gate.boss_room_revealed:
                embed.description = (
                    f"> The boss room has been revealed! Find and enter it to face the final challenge.\n\n"
                    f"**Progress:**\n"
                    f"- Monsters Defeated: **{gate.tk_enemies}/{MONSTERS_TO_DEFEAT}**\n"
                    f"- 🏛️ **Boss Room:** Available\n\n"
                    f"*Time Remaining: **{int(QUEST_DURATION/60)}** minutes*"
                )
            else:
                embed.description = (
                    f"> Explore the dungeon and defeat monsters to reveal the boss room!\n\n"
                    f"**Progress:**\n"
                    f"- Monsters Defeated: **{gate.tk_enemies}/{MONSTERS_TO_DEFEAT}**\n"
                    f"- 🏛️ **Boss Room:** Hidden\n\n"
                    f"*Time Remaining: **{int(QUEST_DURATION/60)}** minutes*"
                )

            await gate.message.edit(embed=embed)
        except (discord.NotFound, discord.HTTPException):
            pass  # Message might be deleted or inaccessible

    async def handle_battle(self, interaction: discord.Interaction, gate, pos):
        player_data = gate.participants[interaction.user.id]
        enemy_data = gate.enemies[pos]
        enemy_data['revealed'] = True

        gate.logs.append(f"{gate.participants[interaction.user.id]['emoji']} encountered {enemy_data['type']['name']}")

        # Create encounter embed
        encounter_embed = discord.Embed(
            title=f"{getEmoji('attack')} Enemy Encounter!",
            description=f"You have encountered a **{enemy_data['type']['name']}**!\n\nPrepare for battle!",
            color=discord.Color.red()
        )
        encounter_embed.set_image(url=enemy_data['type']['image'])
        encounter_embed.add_field(
            name="Enemy Stats",
            value=f"**HP:** {enemy_data['type']['hp']}\n**Attack:** {enemy_data['type']['atk']}\n**Defense:** {enemy_data['type'].get('def', 'Unknown')}",
            inline=True
        )

        # Update the movement message to show encounter
        try:
            await interaction.edit_original_response(embed=encounter_embed, view=None)
        except (discord.NotFound, discord.HTTPException):
            pass

        # Start battle in a new message
        battle_view = self.create_gate_battle_view(gate, interaction.user.id, enemy_data['type'], interaction)
        await battle_view.start(interaction)

    async def handle_boss_room_encounter(self, interaction: discord.Interaction, gate):
        """Handle dramatic boss room encounter like Solo Leveling"""
        # Check if boss is already defeated or gate is finished
        if gate.boss_defeated or gate.finished:
            defeated_embed = discord.Embed(
                title="✅ Gate Completed!",
                description="🏆 **Congratulations!** This gate has been successfully cleared!\n\n💀 The boss has been defeated and the gate is now closed.\n\n🎉 Thank you for your participation in clearing this gate!",
                color=discord.Color.green()
            )
            try:
                await interaction.edit_original_response(embed=defeated_embed, view=None)
            except (discord.NotFound, discord.HTTPException):
                pass
            return

        boss_info = BOSS_DATA.get(gate.rank, BOSS_DATA["E"])

        # Phase 1: Discovery
        discovery_embed = discord.Embed(
            title="🏛️ Boss Room Discovered!",
            description=(
                f"You have found the **Boss Room**!\n\n"
                f"*The air grows heavy with malevolent energy...*\n"
                f"*Ancient runes glow ominously on the walls...*\n"
                f"*Something powerful lurks within...*"
            ),
            color=discord.Color.dark_purple()
        )
        discovery_embed.set_image(url="https://imgs.search.brave.com/hU-dNmKSPWmHYJewD3-1xJrZaM5hZAFyafCBs2kp9wc/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9zdGF0aWMxLmNicmltYWdlcy5jb20vd29yZHByZXNzL3dwLWNvbnRlbnQvdXBsb2Fkcy8yMDI0LzA0L2dhdGUtc29sby1sZXZlbGluZy0xLmpwZWc")

        try:
            await interaction.edit_original_response(embed=discovery_embed, view=None)
        except (discord.NotFound, discord.HTTPException):
            pass

        await asyncio.sleep(3)

        # Phase 2: Warning
        warning_embed = discord.Embed(
            title="⚠️ DANGER WARNING ⚠️",
            description=(
                f"**{gate.rank}-Rank Gate Boss Detected!**\n\n"
                f"🔥 **{boss_info['name']}**\n"
                f"💀 **Threat Level:** {gate.rank}-Rank\n"
                f"{getEmoji('attack')} **Estimated Power:** {boss_info['atk']} ATK\n"
                f"🛡️ **Defense:** {boss_info['def']} DEF\n\n"
                f"*All hunters in the gate will be summoned for the final battle!*"
            ),
            color=discord.Color.red()
        )
        warning_embed.set_footer(text="Prepare yourself... The real fight begins now!")

        try:
            await interaction.followup.send(embed=warning_embed)
        except (discord.NotFound, discord.HTTPException):
            pass

        await asyncio.sleep(4)

        # Phase 3: Boss Entrance
        entrance_embed = discord.Embed(
            title="👹 THE BOSS AWAKENS!",
            description=(
                f"***{boss_info['name']} emerges from the shadows!***\n\n"
                f"*The ground trembles beneath its presence...*\n"
                f"*Its eyes burn with ancient fury...*\n"
                f"*The final battle for the gate begins!*"
            ),
            color=discord.Color.dark_red()
        )
        entrance_embed.set_image(url=boss_info['image'])

        try:
            await interaction.followup.send(embed=entrance_embed)
        except (discord.NotFound, discord.HTTPException):
            pass

        await asyncio.sleep(3)

        # Start the collaborative boss battle
        await gate.start_collaborative_boss_battle(interaction)

class GateBattleView(ui.View):
    def __init__(self, bot, gate, player_id, enemy, original_interaction, cog):
        super().__init__(timeout=180)
        self.bot = bot
        self.gate = gate
        self.player_id = player_id
        self.enemy = enemy
        self.original_interaction = original_interaction
        self.cog = cog
        self.player_stats = {}
        self.enemy_hp = enemy['hp']
        self.enemy_mhp = enemy['hp']
        self.log = []
        self.turn = "player"

    async def start(self, interaction: discord.Interaction):
        player = await Player.get(self.player_id)
        self.player_stats = {
            "name": self.original_interaction.user.name,
            "hp": player.hp,
            "mhp": player.hp,
            "mp": player.mp,
            "atk": player.attack,
            "def": player.defense,
            "skills": player.skills,
            "last_action_time": 0
        }
        
        for slot in ["Weapon", "Weapon_2"]:
            weapon_id = player.equipped.get(slot)
            if weapon_id and weapon_id in player.inventory:
                weapon_stats = await getStatWeapon(weapon_id, player.inventory[weapon_id].get("level", 1))
                if weapon_stats:
                    self.player_stats['atk'] += weapon_stats.get('attack', 0); self.player_stats['def'] += weapon_stats.get('defense', 0)
                    self.player_stats['hp'] += weapon_stats.get('hp', 0); self.player_stats['mp'] += weapon_stats.get('mp', 0)
        self.player_stats['mhp'] = self.player_stats['hp']

        await self.update_battle_ui(interaction, first_time=True)

    async def update_battle_ui(self, interaction: discord.Interaction, first_time=False):
        embed = self.create_embed()
        self.clear_items()

        if self.player_stats['hp'] > 0 and self.enemy_hp > 0:
            await self.add_action_buttons()

        try:
            if first_time:
                # For first time, send a new message instead of editing
                await interaction.response.send_message(embed=embed, view=self, ephemeral=True)
            else:
                await interaction.edit_original_response(embed=embed, view=self)
        except discord.InteractionResponded:
            # If interaction already responded, try to edit the original response
            try:
                await interaction.edit_original_response(embed=embed, view=self)
            except:
                # If that fails, send a followup
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self)

    def create_embed(self):
        embed = discord.Embed(title="Dungeon Encounter!", description=f"> Defeat the **{self.enemy['name']}** to continue.", color=discord.Color.red())
        embed.set_image(url=self.enemy['image'])

        player_hp_bar = pbar(self.player_stats['hp'], self.player_stats['mhp'])
        enemy_hp_bar = pbar(self.enemy_hp, self.enemy_mhp)

        embed.add_field(name=f"{self.player_stats['name']}", value=f"HP: {self.player_stats['hp']}/{self.player_stats['mhp']}\n{player_hp_bar}\nMP: {self.player_stats['mp']}", inline=True)
        embed.add_field(name=f"{self.enemy['name']}", value=f"HP: {self.enemy_hp}/{self.enemy_mhp}\n{enemy_hp_bar}", inline=True)
        
        if self.log:
            embed.add_field(name="Battle Log", value="\n".join(self.log[-3:]), inline=False)

        if self.player_stats['hp'] <= 0:
            embed.description = f"You have been defeated by the {self.enemy['name']}!"
            embed.color = discord.Color.dark_red()
        elif self.enemy_hp <= 0:
            embed.description = f"You have defeated the {self.enemy['name']}!"
            embed.color = discord.Color.green()

        return embed

    async def add_action_buttons(self):
        punch_button = ui.Button(label="Punch", style=discord.ButtonStyle.primary, disabled=(self.turn != 'player'))
        punch_button.callback = self.punch
        self.add_item(punch_button)

        if self.player_stats['skills']:
            options = []
            for skill_id, skill_data in self.player_stats['skills'].items():
                # Get skill with player's current level applied
                skill = await SkillManager.get_skill_with_player_level(skill_id, str(self.player_id))
                if skill and self.player_stats['mp'] >= skill.mp_cost:
                    options.append(discord.SelectOption(
                        label=f"{skill.name} Lv.{skill.level} (MP: {skill.mp_cost}, DMG: {skill.damage}%)",
                        value=skill_id,
                        emoji="⚡"
                    ))
            if options:
                skill_select = ui.Select(placeholder="Use a skill...", options=options, disabled=(self.turn != 'player'))
                skill_select.callback = self.use_skill
                self.add_item(skill_select)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("This is not your battle.", ephemeral=True)
            return False
        if self.turn != 'player':
            await interaction.response.send_message("It's not your turn.", ephemeral=True)
            return False
        return True

    async def punch(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # Balanced damage calculation with random variance
        base_damage = max(1, self.player_stats['atk'] - self.enemy.get('def', 0))
        damage = random.randint(max(1, base_damage - 5), base_damage + 10)
        self.enemy_hp -= damage
        self.log.append(f"{getEmoji('attack')} You punched and dealt {damage} damage.")
        self.turn = "enemy"
        await self.check_battle_status(interaction)

    async def use_skill(self, interaction: discord.Interaction):
        await interaction.response.defer()
        skill_id = interaction.data['values'][0]
        # Get skill with player's current level applied
        skill = await SkillManager.get_skill_with_player_level(skill_id, str(interaction.user.id))

        if not skill:
            await interaction.followup.send("❌ **Skill not found.**", ephemeral=True)
            return

        self.player_stats['mp'] -= skill.mp_cost
        # Balanced skill damage with random variance
        base_damage = max(1, int((self.player_stats['atk'] * (skill.damage / 100)) - self.enemy.get('def', 0)))
        damage = random.randint(max(1, base_damage - 3), base_damage + 8)
        self.enemy_hp -= damage
        self.log.append(f"✨ You used {skill.name} (Lv.{skill.level}) and dealt {damage} damage.")
        self.turn = "enemy"
        await self.check_battle_status(interaction)

    async def check_battle_status(self, interaction: discord.Interaction):
        if self.enemy_hp <= 0:
            self.enemy_hp = 0
            await self.end_battle(interaction, True)
            return

        await self.update_battle_ui(interaction)
        await asyncio.sleep(1.5)
        await self.enemy_turn(interaction)
        
        if self.player_stats['hp'] <= 0:
            self.player_stats['hp'] = 0
            await self.end_battle(interaction, False)
            return
        
        self.turn = "player"
        await self.update_battle_ui(interaction)

    async def enemy_turn(self, interaction: discord.Interaction):
        # Balanced enemy damage (not overpowered)
        base_damage = max(1, self.enemy['atk'] - self.player_stats['def'])
        # Reduce enemy damage to be more balanced
        balanced_damage = max(1, int(base_damage * 0.7))  # 30% damage reduction
        damage = random.randint(max(1, balanced_damage - 3), balanced_damage + 5)
        self.player_stats['hp'] -= damage
        self.log.append(f"🩸 The enemy attacked and dealt {damage} damage.")

    async def end_battle(self, interaction: discord.Interaction, won: bool):
        player_data = self.gate.participants[self.player_id]
        
        if won:
            self.gate.tk_enemies += 1
            player_data['kills'] += 1
            pos = (player_data['x'], player_data['y'])
            enemy_name = self.gate.enemies[pos]['type']['name']
            self.gate.logs.append(f"{player_data['emoji']} defeated {enemy_name}")

            # Remove defeated enemy from the grid completely
            del self.gate.enemies[pos]

            # Check if boss room should be revealed (Solo Leveling style)
            if self.gate.check_boss_room_revelation():
                self.gate.logs.append("🌟 **The boss room has been revealed!**")
                await self.cog.update_gate_display(self.gate)

                # Send dramatic revelation message to all participants
                revelation_embed = discord.Embed(
                    title="🏛️ Boss Room Revealed!",
                    description=(
                        f"After defeating the **{enemy_name}**, a hidden passage has opened!\n\n"
                        f"*A dark energy emanates from deeper within the dungeon...*\n"
                        f"*The true challenge awaits those brave enough to enter...*\n\n"
                        f"🏛️ **Boss Room Location:** Look for the temple icon on the grid!"
                    ),
                    color=discord.Color.gold()
                )

                # Notify all participants
                for user_id in self.gate.participants.keys():
                    try:
                        user = await self.bot.fetch_user(user_id)
                        await user.send(embed=revelation_embed)
                    except (discord.NotFound, discord.HTTPException):
                        pass
        else:
            player_data['dead'] = True
            pos = (player_data['x'], player_data['y'])
            self.gate.logs.append(f"{player_data['emoji']} was defeated by {self.gate.enemies[pos]['type']['name']}")

        await self.update_battle_ui(interaction)
        await asyncio.sleep(3)

        # Boss battle now only starts when boss room is discovered and entered
        # Return to main gate interface
        main_view = self.cog.create_main_buttons(self.gate)
        embed = self.gate.message.embeds[0]
        embed.title = "Gate Entered!"

        # Update description based on boss room status
        if self.gate.boss_room_revealed:
            embed.description = f"> The boss room has been revealed! Find and enter it to face the final challenge.\n\n**Progress**\n- Monsters Defeated: **{self.gate.tk_enemies}/{MONSTERS_TO_DEFEAT}**\n- 🏛️ **Boss Room:** Available"
        else:
            embed.description = f"> Continue exploring to find the boss room.\n\n**Progress**\n- Monsters Defeated: **{self.gate.tk_enemies}/{MONSTERS_TO_DEFEAT}**\n- 🏛️ **Boss Room:** Hidden"

        # Find and update the grid field
        for i, field in enumerate(embed.fields):
            if field.name == "Grid":
                embed.set_field_at(i, name="Grid", value=self.gate.generate_grid(), inline=False)
                break

        await self.original_interaction.edit_original_response(embed=embed, view=main_view)

class BossBattleView(ui.View):
    def __init__(self, bot, gate, participants_data, boss, cog):
        super().__init__(timeout=600)
        self.bot = bot
        self.gate = gate
        self.participants = participants_data
        self.boss = boss
        self.boss_hp = boss['hp']
        self.boss_mhp = boss['hp']
        self.log = deque(maxlen=5)
        self.turn_order = list(participants_data.keys())
        random.shuffle(self.turn_order)
        self.current_turn_index = 0
        self.turn_lock = asyncio.Lock()
        self.cog = cog

    async def start(self, interaction: discord.Interaction):
        self.log.append(f"The {self.boss['name']} has appeared!")
        try:
            await self.update_boss_ui(interaction, first_time=True)
            self.bot.loop.create_task(self.boss_turn_handler(interaction))
        except Exception as e:
            print(f"Error starting boss battle: {e}")
            # Fallback: send new message if editing fails
            embed = self.create_embed()
            await interaction.followup.send(embed=embed, view=self)
            self.bot.loop.create_task(self.boss_turn_handler(interaction))

    async def update_boss_ui(self, interaction: discord.Interaction, first_time=False):
        embed = self.create_embed()
        self.clear_items()

        if self.boss_hp > 0 and any(p['hp'] > 0 for p in self.participants.values()):
            await self.add_action_buttons()

        try:
            if first_time:
                if interaction.response.is_done():
                    await interaction.followup.send(embed=embed, view=self)
                else:
                    await interaction.response.send_message(embed=embed, view=self)
            else:
                await interaction.edit_original_response(embed=embed, view=self)
        except discord.InteractionResponded:
            # Fallback if interaction already responded
            await interaction.followup.send(embed=embed, view=self)
        except Exception as e:
            print(f"Error updating boss UI: {e}")
            # Final fallback
            try:
                await interaction.followup.send(embed=embed, view=self)
            except:
                pass

    def create_embed(self):
        embed = discord.Embed(title=f"Boss Battle: {self.boss['name']}", color=discord.Color.purple())
        embed.set_image(url=self.boss['image'])
        
        boss_hp_bar = pbar(self.boss_hp, self.boss_mhp)
        embed.description = f"**HP: {self.boss_hp}/{self.boss_mhp}**\n{boss_hp_bar}"

        current_turn_id = self.turn_order[self.current_turn_index]

        for user_id, data in self.participants.items():
            user = self.bot.get_user(user_id)
            player_hp_bar = pbar(data['hp'], data['mhp'])
            status = "💀" if data['hp'] <= 0 else "❤️"
            turn_indicator = "▶️" if user_id == current_turn_id and self.boss_hp > 0 else ""
            embed.add_field(name=f"{turn_indicator}{status} {user.name if user else data['name']}", value=f"HP: {data['hp']}/{data['mhp']}\n{player_hp_bar}", inline=False)

        if self.log:
            embed.add_field(name="Battle Log", value="\n".join(self.log), inline=False)
        
        return embed

    async def add_action_buttons(self):
        attack_button = ui.Button(label="Attack", style=discord.ButtonStyle.danger)
        attack_button.callback = self.attack
        self.add_item(attack_button)

        skill_button = ui.Button(label="Skills", style=discord.ButtonStyle.primary)
        skill_button.callback = self.show_skills
        self.add_item(skill_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        user_id = interaction.user.id
        if user_id not in self.participants or self.participants[user_id]['hp'] <= 0:
            await interaction.response.send_message("You are not in this battle or have been defeated.", ephemeral=True)
            return False
        
        if user_id != self.turn_order[self.current_turn_index]:
            await interaction.response.send_message("It's not your turn.", ephemeral=True)
            return False
            
        if self.turn_lock.locked():
            await interaction.response.send_message("An action is already being processed.", ephemeral=True)
            return False

        return True

    async def attack(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with self.turn_lock:
            user_id = interaction.user.id
            player = self.participants[user_id]
            damage = max(1, player['atk'] - self.boss['def'])
            self.boss_hp -= damage
            player['total_damage'] = player.get('total_damage', 0) + damage
            self.log.append(f"{getEmoji('attack')} {player['name']} attacked for {damage} damage.")
            await self.advance_turn(interaction)

    async def show_skills(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        player = self.participants[user_id]
        options = []
        if player['skills']:
            for skill_id, skill_data in player['skills'].items():
                skill = await SkillManager.get(skill_id)
                if skill and player['mp'] >= skill.mp_cost:
                    options.append(discord.SelectOption(label=f"{skill.name} (MP: {skill.mp_cost})", value=skill_id))
        
        if not options:
            await interaction.response.send_message("You have no usable skills.", ephemeral=True)
            return

        skill_select = ui.Select(placeholder="Choose a skill...", options=options)
        
        async def skill_callback(i: discord.Interaction):
            await i.response.defer()
            async with self.turn_lock:
                skill_id = i.data['values'][0]
                await self.use_skill(i, skill_id)
            try:
                await i.delete_original_response()
            except (discord.NotFound, discord.HTTPException):
                pass

        skill_select.callback = skill_callback
        view = ui.View().add_item(skill_select)
        await interaction.response.send_message("Select your skill:", view=view, ephemeral=True)

    async def use_skill(self, interaction: discord.Interaction, skill_id: str):
        user_id = interaction.user.id
        player = self.participants[user_id]
        skill = await SkillManager.get(skill_id)

        player['mp'] -= skill.mp_cost
        damage = max(1, int((player['atk'] * (skill.damage / 100)) - self.boss['def']))
        self.boss_hp -= damage
        player['total_damage'] = player.get('total_damage', 0) + damage
        self.log.append(f"✨ {player['name']} used {skill.name} for {damage} damage.")
        
        await self.advance_turn(interaction)

    async def advance_turn(self, interaction: discord.Interaction):
        if self.boss_hp <= 0:
            self.boss_hp = 0
            await self.end_boss_battle(interaction, True)
            return

        self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
        
        # Skip dead players
        while self.participants[self.turn_order[self.current_turn_index]]['hp'] <= 0:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
            if all(p['hp'] <= 0 for p in self.participants.values()):
                await self.end_boss_battle(interaction, False)
                return

        await self.update_boss_ui(interaction)

    async def boss_turn_handler(self, interaction: discord.Interaction):
        while self.boss_hp > 0 and any(p['hp'] > 0 for p in self.participants.values()):
            await asyncio.sleep(20) # Boss acts every 20 seconds
            async with self.turn_lock:
                if self.boss_hp <= 0: break # Check again after acquiring lock
                
                alive_players = [p for p in self.participants.values() if p['hp'] > 0]
                if not alive_players: break
                
                target_data = random.choice(alive_players)
                damage = max(1, self.boss['atk'] - target_data['def'])
                target_data['hp'] -= damage
                self.log.append(f"🩸 {self.boss['name']} attacked {target_data['name']} for {damage} damage.")

                if all(p['hp'] <= 0 for p in self.participants.values()):
                    await self.end_boss_battle(interaction, False)
                    break
                
                await self.update_boss_ui(interaction)

    async def end_boss_battle(self, interaction: discord.Interaction, won: bool):
        self.stop() # Stop the view from listening to interactions

        # Create final result embed
        result_embed = discord.Embed(title="Gate Boss Battle Complete!", color=discord.Color.gold())

        if won:
            result_embed.title = "🏆 Victory!"
            result_embed.description = f"The guild has successfully defeated **{self.boss['name']}**!"
            result_embed.color = discord.Color.dark_green()

            # Mark boss as defeated and gate as finished to prevent re-fighting
            self.gate.boss_defeated = True
            self.gate.finished = True
            # Remove boss room from the grid
            self.gate.boss_room_position = None
            self.gate.boss_room_revealed = False

            # Track mission progress for all participants
            for user_id in self.participants.keys():
                await track_mission_progress(user_id, "gate", 1)

            # Calculate rewards based on old system
            total_kills = sum(player['kills'] for player in self.participants.values())
            total_dmg = sum(player['total_damage'] for player in self.participants.values())
            total_mana_crystals = 500  # Base reward

            # Update guild stats
            from structure.guild import Guild
            guild_name = None
            for user_id in self.participants.keys():
                player = await Player.get(user_id)
                if player and player.guild:
                    guild = await Guild.get(player.guild)
                    if guild:
                        guild.gates += 1
                        guild.points += 100
                        await guild.save()
                        guild_name = guild.name
                        break

            # Distribute rewards based on contribution
            damage_summary = []
            for user_id, player_data in self.participants.items():
                user = self.bot.get_user(user_id)
                if not user:
                    continue

                # Calculate rewards
                kill_contribution = (player_data['kills'] / max(1, total_kills)) if total_kills > 0 else 0
                damage_contribution = (player_data['total_damage'] / max(1, total_dmg)) if total_dmg > 0 else 0

                player_mana = round(kill_contribution * total_mana_crystals)
                damage_bonus = round(damage_contribution * 300)
                total_mana = player_mana + damage_bonus

                damage_summary.append(
                    f"**{user.name}**\n"
                    f"{getEmoji('sword')} Kills: {player_data['kills']}\n"
                    f"🩸 Total Damage: `{player_data['total_damage']}`\n"
                    f"{getEmoji('rightee')} Obtained **{total_mana}** Mana Crystals"
                )

                # Update player rewards
                player = await Player.get(user_id)
                if player:
                    try:
                        player.mIncrease("gate")
                        player.stone += total_mana
                        player.trade = False
                        await player.save()
                    except Exception as e:
                        print(f"Error saving player {user_id} rewards: {e}")
                        # Continue without saving to prevent blocking

            result_embed.add_field(name="🏆 Hunters Participated", value="\n".join(damage_summary), inline=False)

            if guild_name:
                result_embed.add_field(name="🏰 Guild Bonus", value=f"**{guild_name}** gained +1 Gate Clear and +100 Guild Points!", inline=False)

        else:
            result_embed.title = "💀 Defeat!"
            result_embed.description = f"The guild has been defeated by **{self.boss['name']}**."
            result_embed.color = discord.Color.dark_red()

            # Still give participation rewards
            damage_summary = []
            for user_id, player_data in self.participants.items():
                user = self.bot.get_user(user_id)
                if not user:
                    continue

                kill_bonus = player_data['kills'] * 10  # 10 Mana Crystals per kill
                damage_bonus = int(player_data['total_damage'] * 0.1)  # 10% of damage as bonus
                total_mana = kill_bonus + damage_bonus

                damage_summary.append(
                    f"**{user.name}**\n"
                    f"{getEmoji('sword')} Kills: {player_data['kills']}\n"
                    f"🩸 Total Damage: `{player_data['total_damage']}`\n"
                    f"{getEmoji('rightee')} Consolation: **{total_mana}** Mana Crystals"
                )

                # Update player with consolation rewards
                player = await Player.get(user_id)
                if player:
                    try:
                        player.stone += total_mana
                        player.trade = False
                        await player.save()
                    except Exception as e:
                        print(f"Error saving player {user_id} consolation rewards: {e}")
                        # Continue without saving to prevent blocking

            result_embed.add_field(name="💀 Hunters Participated", value="\n".join(damage_summary), inline=False)

        # Send final result
        await interaction.edit_original_response(embed=result_embed, view=None)
        await self.cog.cleanup_gate(self.gate)

class GateAllianceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_response(self, ctx, embed=None, content=None, view=None, ephemeral=False):
        """Helper function to send responses for both interactions and regular commands"""
        # Filter out None values to avoid TypeError
        kwargs = {}
        if embed is not None:
            kwargs['embed'] = embed
        if content is not None:
            kwargs['content'] = content
        if view is not None:
            kwargs['view'] = view
        if ephemeral:
            kwargs['ephemeral'] = ephemeral

        if hasattr(ctx, 'interaction') and ctx.interaction:
            if ctx.interaction.response.is_done():
                return await ctx.interaction.followup.send(**kwargs)
            else:
                return await ctx.interaction.response.send_message(**kwargs)
        else:
            # Remove ephemeral for regular commands as it's not supported
            kwargs.pop('ephemeral', None)
            return await ctx.send(**kwargs)

    @commands.hybrid_command(name="gatealliance", description="Toggle whether other guilds can join your guild's gates (Guild Leader only)")
    async def gate_alliance(self, ctx: commands.Context):
        """Toggle alliance setting for gates"""
        if ctx.interaction:
            await ctx.defer()

        player = await Player.get(ctx.author.id)
        if not player:
            await self.send_response(ctx, embed=discord.Embed(title="Error", description="You haven't started the bot yet. Use `/start` to register.", color=discord.Color.red()), ephemeral=True)
            return

        if not player.guild:
            await self.send_response(ctx, embed=discord.Embed(title="<:guild:1329840946975604837> No Guild", description="You need to be in a guild to use this command.", color=discord.Color.orange()))
            return

        # Try to get guild from both systems
        from guild_integration_manager import GuildIntegrationManager
        guild = await GuildIntegrationManager.get_unified_guild(player.guild)
        if not guild:
            await self.send_response(ctx, embed=discord.Embed(title="Error", description="Guild not found.", color=discord.Color.red()), ephemeral=True)
            return



        if guild.owner != ctx.author.id:
            await self.send_response(ctx, embed=discord.Embed(
                title="🚫 Permission Denied",
                description=f"Only the guild leader can change alliance settings.\n\nGuild Owner: {guild.owner}\nYour ID: {ctx.author.id}",
                color=discord.Color.red()
            ), ephemeral=True)
            return

        # Toggle alliance setting
        guild.allow_alliances = not guild.allow_alliances
        await guild.save()

        status = "**enabled**" if guild.allow_alliances else "**disabled**"
        color = discord.Color.green() if guild.allow_alliances else discord.Color.red()

        embed = discord.Embed(
            title="🤝 Gate Alliance Settings Updated",
            description=f"Gate alliances have been {status} for **{guild.name}**.",
            color=color
        )

        if guild.allow_alliances:
            embed.add_field(
                name="✅ Alliances Enabled",
                value="• Other guilds can now join your gates\n• Great for partnerships and helping smaller guilds\n• Promotes cooperation between guilds",
                inline=False
            )
        else:
            embed.add_field(
                name="❌ Alliances Disabled",
                value="• Only your guild members can join gates\n• Traditional guild-exclusive gameplay\n• Maintains guild boundaries",
                inline=False
            )

        await self.send_response(ctx, embed=embed)

    @commands.hybrid_command(name="gatestatus", description="View your guild's gate alliance status")
    async def gate_status(self, ctx: commands.Context):
        """View guild gate alliance status"""
        if ctx.interaction:
            await ctx.defer()

        player = await Player.get(ctx.author.id)
        if not player:
            await self.send_response(ctx, embed=discord.Embed(title="Error", description="You haven't started the bot yet. Use `/start` to register.", color=discord.Color.red()), ephemeral=True)
            return

        if not player.guild:
            await self.send_response(ctx, embed=discord.Embed(title="<:guild:1329840946975604837> No Guild", description="You need to be in a guild to use this command.", color=discord.Color.orange()))
            return

        # Try to get guild from both systems
        from guild_integration_manager import GuildIntegrationManager
        guild = await GuildIntegrationManager.get_unified_guild(player.guild)
        if not guild:
            await self.send_response(ctx, embed=discord.Embed(title="Error", description="Guild not found.", color=discord.Color.red()), ephemeral=True)
            return

        status = "✅ Enabled" if guild.allow_alliances else "❌ Disabled"
        color = discord.Color.green() if guild.allow_alliances else discord.Color.red()

        embed = discord.Embed(
            title=f"🏛️ Gate Alliance Status - {guild.name}",
            description=f"**Alliance Status:** {status}",
            color=color
        )

        if guild.allow_alliances:
            embed.add_field(
                name="🤝 Alliance Benefits",
                value="• Other guilds can join your gates\n• Your members can join allied gates\n• Increased cooperation opportunities\n• Faster progression for smaller guilds",
                inline=False
            )
        else:
            embed.add_field(
                name="🔒 Guild Exclusive",
                value="• Only guild members can join gates\n• Traditional guild-only gameplay\n• Maintains guild exclusivity",
                inline=False
            )

        if guild.owner == ctx.author.id:
            embed.add_field(
                name="⚙️ Guild Leader Options",
                value="Use `/gatealliance` to toggle alliance settings",
                inline=False
            )

        await self.send_response(ctx, embed=embed)

async def setup(bot):
    await bot.add_cog(GateCommands(bot))
    await bot.add_cog(GateAllianceCommands(bot))
