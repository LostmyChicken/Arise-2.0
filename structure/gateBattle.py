
import asyncio
import hashlib
import random
import discord
from structure.guild import Guild
from commands.dungeons import pbar
from structure.skills import SkillManager
from utilis.utilis import extractId, extractName, getStatWeapon
from structure.emoji import getEmoji
from structure.player import Player
import random
import asyncio
import discord
from discord.ui import Select
import time

import random
import asyncio
import discord
from discord.ui import Select

class GateBattle:
    def __init__(self, bot, user, enemy, channel):
        self.bot = bot
        self.user = user
        self.enemy = enemy
        self.p_name = None
        self.e_name = enemy['name']
        self.p_atk = None
        self.e_atk = enemy['atk']
        self.p_def = None
        self.e_def = enemy['atk'] * 2
        self.p_hp = None
        self.p_mhp = None
        self.e_hp = enemy['hp']
        self.e_mhp = enemy['hp']
        self.p_mp = None  # Player MP
        self.p_skills = None  # Player skills
        self.pmsg = None
        self.battle_result = None  # Store battle outcome
        self.turn = "player"  # Track whose turn it is
        self.o_img = enemy['image']
        self.last_damage_dealt = None  # Track last damage dealt by player
        self.enemy_damage = None  # Track last damage dealt by enemy
        self.channel = channel
        self.battle_result = asyncio.Future()  # Future that will hold the battle result (True for win, False for loss)


    async def async_init(self):
        player = await Player.get(self.user)
        self.p_name = await self.bot.fetch_user(self.user)
        self.p_atk = player.attack
        self.p_def = player.defense
        self.p_hp = max(1, player.hp)  # Ensure at least 1 HP
        self.p_mhp = player.hp
        self.p_mp = player.mp  # Initialize player MP
        self.p_skills = player.skills  # Initialize player skills

        # Add equipped weapon stats to player's base stats
        equipped_stats = {"attack": 0, "defense": 0, "hp": 0, "mp": 0}
        for slot, weapon_id in player.equipped.items():
            if weapon_id and slot in ["Weapon", "Weapon_2"]:
                weapon_level = player.inventory.get(weapon_id, {}).get("level", 1)
                weapon_stats = await getStatWeapon(weapon_id, weapon_level)
                equipped_stats["attack"] += weapon_stats['attack']
                equipped_stats["defense"] += weapon_stats['defense']
                equipped_stats["hp"] += weapon_stats['hp']
                equipped_stats["mp"] += weapon_stats['mp']

        self.p_atk += equipped_stats["attack"]
        self.p_def += equipped_stats["defense"]
        self.p_hp += equipped_stats["hp"]
        self.p_mp += equipped_stats["mp"]
        self.p_mhp = self.p_hp

    async def start_battle(self, interaction: discord.Interaction):
        await self.async_init()

        user = await self.bot.fetch_user(self.user)
        self.pmsg = await user.send(f"<@{user.id}>")

        class FakeInteraction:
            def __init__(self, user):
                self.user = user

            async def followup(self, **kwargs):
                return await user.send(kwargs.get("content", ""), embed=kwargs.get("embed"), view=kwargs.get("view"))

        fake_interaction = FakeInteraction(user)
        await self.display_battle(fake_interaction)
        return await self.battle_result 

    async def handle_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.user:
            await interaction.response.send_message("It's not your turn yet!", ephemeral=True)
            return

        action = interaction.data['values'][0]
        if action == "punch":
            await self.punch(interaction)
        else:
            skill_id = action
            await self.use_skill(interaction, skill_id)

    async def use_skill(self, interaction: discord.Interaction, skill_id: str):
        await interaction.response.defer()

        skill = await SkillManager.get(extractId(skill_id))
        if not skill:
            await interaction.followup.send("The selected skill is invalid!", ephemeral=True)
            return

        if self.p_mp < skill.mp_cost:
            await interaction.followup.send("Not enough MP to use this skill!", ephemeral=True)
            return

        # Player attacks
        damage = round((self.p_atk / self.e_def) * skill.damage)
        self.e_hp = max(0, self.e_hp - damage)
        self.p_mp -= skill.mp_cost
        self.last_damage_dealt = damage

        # Check if enemy is defeated
        if self.e_hp <= 0:
            await self.end_fight(interaction, winner=self.p_name.name)
            return

        # Enemy attacks back
        await self.enemy_turn(interaction)

    async def punch(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Player attacks
        damage = random.randint(30, 100)
        self.e_hp = max(0, self.e_hp - damage)
        self.last_damage_dealt = damage

        # Check if enemy is defeated
        if self.e_hp <= 0:
            await self.end_fight(interaction, winner=self.p_name.name)
            return

        # Enemy attacks back
        await self.enemy_turn(interaction)

    async def enemy_turn(self, interaction: discord.Interaction):
        """Handles the enemy's attack turn right after the player attacks."""
        damage = random.randint(30, 80)
        self.p_hp = max(0, self.p_hp - damage)
        self.enemy_damage = damage

        # Check if player is defeated
        if self.p_hp <= 0:
            await self.end_fight(interaction, winner=self.e_name)
            return

        # Keep the battle menu open
        await self.display_battle(interaction)

    async def end_fight(self, interaction: discord.Interaction, winner):
        """Ends the fight and announces the winner."""
        self.turn = None  # No more turns since battle is over
        
        # Ensure `self.battle_result` is a Future before setting it
        if isinstance(self.battle_result, asyncio.Future) and not self.battle_result.done():
            self.battle_result.set_result(winner == self.p_name.name)  # True if player wins, False otherwise

        await self.display_battle(interaction)

        color = discord.Color.green() if winner == self.p_name.name else discord.Color.red()
        await interaction.followup.send(f"<#{self.channel}> Continue your gate here.", ephemeral=True)


    async def display_battle(self, interaction):
        """Displays the battle UI with updated HP and attack details."""
        embed = discord.Embed(title="Dungeon Encounter!", description="> -# Defeat the **monster** to gain progress.")
        player_field_value = f"MP: **{self.p_mp}**\n{getEmoji('health')} Health: **{self.p_hp}/{self.p_mhp}**\n"
        enemy_field_value = f"{getEmoji('health')} Health: **{self.e_hp}/{self.e_mhp}**\n"

        if self.last_damage_dealt:
            player_field_value += f"> Player used **Skill** and dealt **{self.last_damage_dealt}** damage\n"
        if self.enemy_damage:
            enemy_field_value += f"> Enemy attacked and dealt **{self.enemy_damage}** damage\n"

        if self.p_hp <= 0:
            player_field_value += "> *Player Fainted!*"
        if self.e_hp <= 0:
            enemy_field_value += f"> *{self.e_name} Fainted!*"

        embed.add_field(name=f"{self.p_name.name}", value=player_field_value, inline=True)
        embed.add_field(name=f"{self.e_name}", value=enemy_field_value, inline=False)
        embed.set_image(url=self.o_img)

        if self.p_hp <= 0 or self.e_hp <= 0:
            embed.set_footer(text="Battle Over. You can move again.")
            view = None
        else:
            embed.set_footer(text="Choose your action from the menu below.")
            options = [discord.SelectOption(label="Punch", description="Basic attack", value="punch")]
            if self.p_skills:
                for skill_id, skill_data in self.p_skills.items():
                    skill = await SkillManager.get(skill_id)
                    if skill:
                        options.append(discord.SelectOption(
                            label=skill.name,
                            description=f"Level {skill_data.get('level', 'Unknown')} | {skill.damage}% Damage | MP Cost: {skill.mp_cost}",
                            value=skill_id
                        ))

            select_menu = Select(placeholder="Choose your action...", options=options)
            select_menu.callback = self.handle_select
            view = discord.ui.View()
            view.add_item(select_menu)

        if self.pmsg is None:
            self.pmsg = await interaction.followup.send(embed=embed, view=view)
        else:
            await self.pmsg.edit(embed=embed, view=view)


class CollaborativeBossBattle:
    def __init__(self, bot, participants, boss,guild):
        self.bot = bot
        self.participants = participants  # Dictionary of participants: {user_id: {"hp": x, "mp": y, "skills": z}}
        self.boss = boss  # Boss data: {"name": "Boss Name", "hp": 1000, "atk": 50, "def": 30}
        self.boss_hp = boss["hp"]
        self.boss_mhp = boss["hp"]
        self.battle_log = []  # Log of battle actions
        self.embed = None  # Battle embed
        self.message = None  # Battle message
        self.view = None  # Battle view
        self.last_attacker = None  # Track the last player who attacked the boss
        self.guild = guild

        # Initialize cooldown and total_damage for each participant
        for user_id in self.participants:
            self.participants[user_id]["last_action_time"] = 0  # Track the last time the player acted
            self.participants[user_id]["total_damage"] = 0  # Add this line

    async def start_battle(self, interaction: discord.Interaction):
        """Start the collaborative boss battle."""
        # Create the initial embed
        self.embed = self.create_battle_embed()
        self.view = self.create_battle_view()
        self.message = await interaction.followup.send(embed=self.embed, view=self.view)

        # Wait for players to make moves
        while self.boss_hp > 0 and any(player["hp"] > 0 for player in self.participants.values()):
            await asyncio.sleep(1)  # Prevent event loop blocking

        # End the battle
        await self.end_battle()

    def create_battle_embed(self):
        """Create the battle embed with player and boss health."""
        embed = discord.Embed(title="Collaborative Boss Battle", color=discord.Color.blue())
        down = getEmoji("down")
        # Add boss health
        boss_hp_bar = self.create_hp_bar(self.boss_hp, self.boss_mhp)
        embed.add_field(
            name=f"{self.boss['name']}",
            value=f"{getEmoji('health')} {self.boss_hp}/{self.boss_mhp}\n{boss_hp_bar}",
            inline=False
        )
        embed.set_image(url=self.boss['image'])

        # Add player health and MP
        for user_id, player in self.participants.items():
            user = self.bot.get_user(user_id)
            
            embed.add_field(
                name=f"{user.name if user else f'Unknown ({user_id})'}",
                value=f"{getEmoji('mp')} {player['mp']} {getEmoji('attack')} {player['atk']} {getEmoji('defense')} {player['def']}\n"
                f"{getEmoji('health')} Health: `[{player['hp']}/{player['mhp']}]`",
                inline=False
            )

        # Add battle log
        if self.battle_log:
            embed.add_field(name="Battle Log", value="> "+"\n> ".join(self.battle_log[-3:]), inline=False)

        return embed

    def create_hp_bar(self, current_hp, max_hp):
        """Create a visual HP bar."""
        bar_length = 24
        filled = int((current_hp / max_hp) * bar_length)
        return f"`[{'█' * filled}{'░' * (bar_length - filled)}]`"

    def create_battle_view(self):
        """Create the battle view with Move and Leave buttons."""
        view = discord.ui.View()

        # Move Button
        move_button = discord.ui.Button(label="Moves", style=discord.ButtonStyle.primary)
        move_button.callback = self.move_button_callback
        view.add_item(move_button)

        
        return view

    async def move_button_callback(self, interaction: discord.Interaction):
        """Handle the Move button click."""
        if interaction.user.id not in self.participants:
            await interaction.response.send_message("❌ You are not part of this battle!", ephemeral=True)
            return

        player = self.participants[interaction.user.id]

        # Check if the player is on cooldown
        current_time = time.time()
        if current_time - player["last_action_time"] < 5:  # 5-second cooldown
            remaining_cooldown = 5 - (current_time - player["last_action_time"])
            await interaction.response.send_message(f"❌ You are on cooldown for {remaining_cooldown:.1f} seconds!", ephemeral=True)
            return

        # Create a select menu with the player's skills
        options = [
            discord.SelectOption(label="Punch", description="Basic attack | MP Cost: 0", value="punch")
        ]
        if player["skills"]:
            for skill_id, skill_data in player["skills"].items():
                skill = await SkillManager.get(skill_id)
                if skill:
                    options.append(discord.SelectOption(
                        label=skill.name,
                        description=f"{skill.damage}% Damage | MP Cost: {skill.mp_cost}",
                        value=skill_id
                    ))

        select_menu = Select(placeholder="Choose your action...", options=options)
        select_menu.callback = lambda i: self.handle_skill_select(i, interaction.user.id)
        view = discord.ui.View()
        view.add_item(select_menu)

        await interaction.response.send_message("Choose your move:", view=view, ephemeral=True)

    async def handle_skill_select(self, interaction: discord.Interaction, user_id):
        """Handle skill selection from the select menu."""
        await interaction.response.defer()
        action = interaction.data["values"][0]

        player = self.participants[user_id]
        if action == "punch":
            damage = random.randint(30, 100)
            self.boss_hp = max(0, self.boss_hp - damage)
            player["total_damage"] += damage  # Update total damage
            self.battle_log.append(f"{interaction.user.name} used Punch and dealt **{damage}** damage!")
        else:
            skill = await SkillManager.get(extractId(action))
            if not skill:
                await interaction.followup.send("❌ Invalid skill!", ephemeral=True)
                return

            if player["mp"] < skill.mp_cost:
                await interaction.followup.send("❌ Not enough MP!", ephemeral=True)
                return

            # Calculate skill damage
            damage = round((player["atk"] / self.boss["def"]) * skill.damage)
            self.boss_hp = max(0, self.boss_hp - damage)
            player["mp"] -= skill.mp_cost
            player["total_damage"] += damage  # Update total damage
            self.battle_log.append(f"{interaction.user.name} used {skill.name} and dealt **{damage}** damage!")

        # Set the last attacker
        self.last_attacker = user_id
        player["last_action_time"] = time.time()

        # Boss retaliates after the player's move
        await self.boss_retaliate(interaction)

        # Update the embed
        self.embed = self.create_battle_embed()
        await self.message.edit(embed=self.embed)

    async def boss_retaliate(self, interaction: discord.Interaction):
        """Boss attacks a random player after a player's move."""
        if self.boss_hp <= 0:
            return

        # Boss attacks a random player
        alive_players = [user_id for user_id, player in self.participants.items() if player["hp"] > 0]
        if not alive_players:
            return

        target_id = random.choice(alive_players)
        target = self.participants[target_id]
        damage = random.randint(30, 80)
        target["hp"] = max(0, target["hp"] - damage)
        self.battle_log.append(f"{self.boss['name']} attacked {self.bot.get_user(target_id).name} for **{damage}** damage!")

        # Update the embed
        self.embed = self.create_battle_embed()
        await self.message.edit(embed=self.embed)

    async def leave_button_callback(self, interaction: discord.Interaction):
        """Handle the Leave button click."""
        if interaction.user.id not in self.participants:
            await interaction.response.send_message("❌ You are not part of this battle!", ephemeral=True)
            return

        del self.participants[interaction.user.id]
        self.turn_order.remove(interaction.user.id)
        self.battle_log.append(f"🚪 {interaction.user.name} left the battle!")

        # Update the embed
        self.embed = self.create_battle_embed()
        await self.message.edit(embed=self.embed)

        await interaction.response.send_message("✅ You left the battle!", ephemeral=True)
    
    async def end_battle(self):
        """End the battle and declare the result by sending a new embed."""
        result_embed = discord.Embed(color=discord.Color.blue())
        gk = getEmoji("gate_key")
        mana_crystal_emoji = getEmoji("stone")  # Replace with the actual emoji ID
        down = getEmoji("down")

        # Define Mana Crystal rewards based on rank
        mana_rewards = {
            "E": 1000,
            "D": 1250,
            "C": 1500,
            "B": 1750,
            "A": 2000,
            "S": 2500
        }
        boss_rank = self.boss['rank']
        total_mana_crystals = mana_rewards.get(boss_rank, 0)
        guild = await Guild.get(self.guild)
        
        # Calculate total kills by all players
        total_kills = sum(player['kills'] for player in self.participants.values())
        total_dmg = sum(player['total_damage'] for player in self.participants.values())

        # Determine the outcome of the battle
        if self.boss_hp <= 0:
            result_embed.title = "The boss was defeated!"
            result_embed.description = (
                f"{gk} {boss_rank}-Rank\nGate Cleared ☑️\nGuild: **{extractName(self.guild)}**\n"
                f"> The guild has earned **{total_mana_crystals}** points.\n"
            )
            guild.points += total_mana_crystals
            guild.gates += 1
            for user_id in self.participants.keys():
                guild.update_member_gc(user_id)
            await guild.save()
            result_embed.color = discord.Color.dark_green()

            # Distribute Mana Crystals based on kill contribution
            damage_summary = []
            for user_id, player in self.participants.items():
                user = self.bot.get_user(user_id)
                player_mana = round((player['kills'] / total_kills) * total_mana_crystals)  # Proportional reward based on kills
                damage_bonus = round((player['total_damage'] / total_dmg) * 300)
                total_mana = player_mana + damage_bonus

                damage_summary.append(
                    f"**{user.name if user else f'Unknown ({user_id})'}**\n"
                    f"{getEmoji('attack')} Kills: {player['kills']}\n🩸 Total Damage: `{player['total_damage']}`\n"
                    f"<:rightee:1343260049505779831> Obtained **{total_mana}** Mana Crystals  {mana_crystal_emoji}"
                )

                # Update player's mana crystals in the database
                p = await Player.get(user_id)
                p.mIncrease("gate")
                p.stone += total_mana
                p.trade = False
                await p.save()
                
            result_embed.add_field(name="Hunters Participated", value="\n".join(damage_summary), inline=False)
        else:
            result_embed.title = "💀 Defeat!"
            result_embed.description = "The boss has overwhelmed the players."
            result_embed.color = discord.Color.dark_red()

            # Only show damage summary but still give kill bonuses
            damage_summary = []
            for user_id, player in self.participants.items():
                user = self.bot.get_user(user_id)
                kill_bonus = player['kills'] * 10  # 10 Mana Crystals per kill
                damage_bonus = player['total_damage'] * 0.1  # 10% of total damage as bonus essence stones
                total_mana = kill_bonus + damage_bonus

                damage_summary.append(
                    f"**{user.name if user else f'Unknown ({user_id})'}**\n"
                    f"{getEmoji('attack')} Kills: {player['kills']}\n🩸 Total Damage: `{player['total_damage']}`\n"
                )

                p = await Player.get(user_id)
                p.trade = False
                await p.save()
                
            result_embed.add_field(name="Hunters Participated", value="\n".join(damage_summary), inline=False)
        
        await self.message.channel.send(embed=result_embed)

        self.view.disable_all_items()
        await self.message.edit(view=self.view)
