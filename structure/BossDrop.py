import asyncio
import random
import discord
from discord.ui import Button, View,Select
from discord import Embed
from structure.stats import getStat
from structure.skills import SkillManager
from structure.emoji import getEmoji
from structure.player import Player
from collections import deque


class BossDrop(View):
    def __init__(self, boss, embed, level, gold, xp):
        super().__init__(timeout=300)  # No timeout for this interaction
        self.boss = boss
        self.embed = embed
        self.level = level
        self.gold = gold
        self.xp = xp
        self.hp = 0
        self.mhp = 0
        self.mp = 0
        base_stats = {
            "HP": self.boss.health,
            "Attack": self.boss.attack,
            "Defense": self.boss.defense,
            "Precision": self.boss.precision
        }
        stats = getStat(["HP", "Attack", "Defense", "Precision"], level=self.level, base_stats=base_stats)
        self.bhp = stats.HP
        self.MBhp = stats.HP
        self.log = deque(maxlen=3)
        self.round = 1
        self.message = None  # Will be set when the view is sent
    async def on_timeout(self):
        self.embed.set_footer(text="This challenge has timed out.")
        if self.message:
            try:
                await self.message.edit(embed=self.embed, view=None)
            except:
                pass  # Message might be deleted or inaccessible

    def update_embed(self, player, stats):
        down = getEmoji("down")
        qx = getEmoji("qx")
        mp = getEmoji("mp")
        bossBar = pbar(self.bhp, self.MBhp, 9)
        playerBar = pbar(self.hp, self.mhp, 9)
        self.hp = max(self.hp,0)
        self.bhp = max(self.bhp,0)
        
        self.embed.title = f"▬▬ Round {self.round} ▬▬"
        
        self.embed.set_field_at(
            0, 
            name=f"{self.boss.name}", 
            value=f"**MP** remaining: `∞`\n**ATK:** `{stats.Attack}` | **DEF:** `{stats.Defense}`\n-# {bossBar}", 
            inline=False
        )
        self.embed.set_field_at(
            1, 
            name=f"Sung Jinwoo", 
            value=f"**MP** remaining: `{self.mp}`\n**ATK:** `{player.attack}` | **DEF:** `{player.defense}`\n-# {playerBar}", 
            inline=False
        )
        self.embed.description = f"Level: **{self.level}**\nPower Level: **{self.level * 75}**"
        self.embed.set_field_at(2,name="Battle Logs",value="\n".join(self.log),inline=False)
        self.embed.set_image(url=self.boss.image)
        self.embed.set_author(name="Boss Battle", icon_url="https://files.catbox.moe/2f0938.png")
        if self.hp==0:
            self.embed.set_footer(text=f"Player ({player.id}) lost against the boss.")
        elif self.bhp==0:
            self.embed.set_footer(text=f"Player ({player.id}) took down the boss.")
        else:
            self.embed.set_footer(text="use /codex skill info to get info about your skill")
        
        self.embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/pfTmp02lQ0Wglq3n2_MTdDvJnOqg3Swsw8qymAHYLao/%3Fcb%3D20241202155341/https/static.wikia.nocookie.net/solo-leveling-arise/images/2/23/Sung_Jin_Woo_Full_Body.png/revision/latest/scale-to-width-down/1000?format=webp&width=349&height=622")

    @discord.ui.button(label="Fight", style=discord.ButtonStyle.red)
    async def fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the fight interaction."""
        await interaction.response.defer()
        player = await Player.get(interaction.user.id)
        if not player:
            await interaction.followup.send("You haven't started the bot yet.", ephemeral=True)
            return

        msg = await interaction.original_response()

        base_stats = {
            "HP": self.boss.health,
            "Attack": self.boss.attack,
            "Defense": self.boss.defense,
            "Precision": self.boss.precision
        }
        stats = getStat(["HP", "Attack", "Defense", "Precision"], level=self.level, base_stats=base_stats)

        self.hp = player.hp
        self.mhp = player.hp
        self.mp = player.mp

        if stats.Precision > player.precision:
            
            self.log.append("Boss takes the first turn (speed)")
            boss_turn = True
        else:
            self.log.append("Sung Jinwoo takes the first turn")
            boss_turn = False
            
        self.embed.add_field(name="Battle Logs",value=f"{self.log}")
        self.update_embed(player, stats)

        skill_options = [
            {"name": "Punch", "description": "Level 1 | 100% Damage | MP Cost: 0"}
        ]
        if hasattr(player, "skills") and player.skills:
            for skill_id, skill_data in player.skills.items():
                skill = await SkillManager.get(skill_id)
                if skill:
                    skill_options.append({
                        "name": skill.name,
                        "description": f"Level {skill_data.get('level', 'Unknown')} | {skill.damage}% Damage | MP Cost: {skill.mp_cost}"
                    })

        class SkillSelect(Select):
            def __init__(self, parent: 'BossDrop', options):
                super().__init__(
                    placeholder="Select your skill...",
                    min_values=1,
                    max_values=1,
                    options=[
                        discord.SelectOption(label=opt["name"], description=opt["description"])
                        for opt in options
                    ]
                )
                self.parent = parent  # Reference to the BossDrop instance

            async def callback(self, interaction):
                selected_skill = self.values[0]
                await interaction.response.defer()
                skill_data = next((opt for opt in skill_options if opt["name"] == selected_skill), None)
                if skill_data:
                    skill_damage = int(skill_data["description"].split('|')[1].split('%')[0].strip())
                    mp_cost = int(skill_data["description"].split('MP Cost: ')[1])
                    s_D = round((skill_damage / 100) * player.attack)
                    self.parent.bhp = max(0, self.parent.bhp - s_D)
                    
                    self.parent.mp -= mp_cost
                    down = getEmoji("down")
                    sn = skill_data["name"]
                    self.parent.log.append(f"{getEmoji('attack')} Sung Jinwoo used **{sn}** and dealt **{s_D}** Damage.\n{down} **Mana** Consumed: **{mp_cost}**")
                    
                    # Check if the boss is defeated
                    if self.parent.bhp <= 0:
                        self.parent.log.append("Boss defeated! You win!")
                        self.parent.embed.color = discord.Color.dark_magenta()
                        self.parent.embed.set_footer(text=f"{interaction.user.global_name} defeated the boss!")
                        self.parent.update_embed(player, stats)
                        await msg.edit(embed=self.parent.embed, view=None)
                        
                        v_embed = Embed(title=f"{self.parent.boss.name} Defeated!")
                        v_embed.set_author(name="Victory", icon_url="https://files.catbox.moe/2f0938.png")

                        xp = getEmoji("xp")
                        gold = getEmoji("gold")
                        qx = getEmoji("qx")
                        down = getEmoji("down")
                        v_embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/pfTmp02lQ0Wglq3n2_MTdDvJnOqg3Swsw8qymAHYLao/%3Fcb%3D20241202155341/https/static.wikia.nocookie.net/solo-leveling-arise/images/2/23/Sung_Jin_Woo_Full_Body.png/revision/latest/scale-to-width-down/1000?format=webp&width=349&height=622")

                        v_embed.color = discord.Color.dark_green()
                        v_embed.description = f"**You've Obtained the Following Rewards:**\n- {gold} Gold: `x{self.parent.gold}`\n- {xp} Expereince: `x{self.parent.xp}`\n-# {down} Check /inventory to see the updated balance."
                        player.xp += self.parent.xp
                        player.gold += self.parent.gold
                        await player.save()
                        await interaction.channel.send(embed=v_embed)
                        self.parent.stop()
                        return
                    for item in self.parent.children:
                        if isinstance(item, discord.ui.Select):
                            item.disabled = True
                    self.parent.update_embed(player, stats)

                    await msg.edit(embed=self.parent.embed, view=self.parent)
                    await asyncio.sleep(1.5)
                    # Boss attacks (balanced damage calculation)
                    base_damage = max(1, stats.Attack - player.defense)
                    boss_damage = random.randint(max(1, base_damage - 5), base_damage + 10)
                    self.parent.hp = max(0, self.parent.hp - boss_damage)

                    self.parent.log.append(f"{getEmoji('attack')} The boss attacked and dealt **{boss_damage}** Damage to Sung Jinwoo.")
                    for item in self.parent.children:
                        if isinstance(item, discord.ui.Select):
                            item.disabled = False
                    # Check if the player is defeated
                    if self.parent.hp <= 0:
                        self.parent.log.append("💀 You were defeated by the boss. Game over.")
                        self.parent.embed.color = discord.Color.dark_red()
                        self.parent.update_embed(player, stats)
                        await msg.edit(embed=self.parent.embed, view=None)
                        self.parent.stop()
                        return
                    
                    # Update the embed after both turns
                    self.parent.round += 1
                    self.parent.update_embed(player, stats)
                    await msg.edit(embed=self.parent.embed,view=self.parent)

        # Add the skill selection menu to the view
        skill_menu = SkillSelect(self, skill_options)
        self.add_item(skill_menu)
        for item in list(self.children):
            if isinstance(item, discord.ui.Button):
                self.remove_item(item)
        await msg.edit(embed=self.embed, view=self)

        # Boss attacks first if boss_turn is True
        if boss_turn:
            # Balanced first turn damage
            base_damage = max(1, stats.Attack - player.defense)
            boss_damage = random.randint(max(1, base_damage - 5), base_damage + 10)
            self.hp = max(0, self.hp - boss_damage)
            self.log.append(f"{getEmoji('attack')} The boss attacked and dealt **{boss_damage}** Damage to Sung Jinwoo.")

            # Check if the player is defeated
            if self.hp <= 0:
                self.log.append("💀 You were defeated by the boss. Game over.")
                self.embed.color = discord.Color.dark_red()
                self.embed.set_footer(text=f"({player.id}) lost against the boss!")
                self.update_embed(player, stats)
                await msg.edit(embed=self.embed, view=None)
                self.stop()
                return

            self.update_embed(player, stats)
            await msg.edit(embed=self.embed)


def pbar(current, max, divs):
    progress = current / max
    fill = {
        'start': getEmoji("GSTART"),
        'middle': getEmoji("GMID"),
        'end': getEmoji("GEND")
    }
    empty = {
        'start': getEmoji("EGSTART"),
        'middle': getEmoji("EGMIDDLE"),
        'end': getEmoji("EGEND")
    }

    icons = []
    progress_bar_length = divs
    filled_length = round(progress_bar_length * progress)

    # Add the start icon
    if filled_length > 0:
        icons.append(fill['start'])
    else:
        icons.append(empty['start'])

    # Add the middle icons
    for i in range(1, divs - 1):
        if i < filled_length:
            icons.append(fill['middle'])
        else:
            icons.append(empty['middle'])

    # Add the end icon
    if filled_length == progress_bar_length:
        icons.append(fill['end'])
    else:
        icons.append(empty['end'])

    return "".join(icons)+f" `[{current}/{max}]`"
