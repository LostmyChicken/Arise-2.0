import discord
from discord.ext import commands
from discord import app_commands
from rapidfuzz import process, fuzz

from structure.heroes import HeroManager
from structure.items import ItemManager
from structure.player import Player
from structure.emoji import getClassEmoji, getEmoji
from utilis.utilis import getStatHunter, getStatWeapon, get_emoji_url, player_hunter_autocomplete

async def getPartyTotalPower(player):
    total_power = 0
    for slot_key in ["Party_1", "Party_2", "Party_3"]:
        hunter_id = player.equipped.get(slot_key)
        if hunter_id and hunter_id in player.hunters:
            hunter = player.hunters[hunter_id]
            char = await HeroManager.get(hunter_id)
            if char:
                level = hunter.get("level", 1)
                stat = await getStatHunter(char.id, level)
                
                weapon_id = hunter.get("weapon")
                if weapon_id and weapon_id in player.inventory:
                    w_level = player.inventory[weapon_id].get("level", 1)
                    weapon_stat = await getStatWeapon(weapon_id, w_level)
                    if weapon_stat:
                        stat.total_power += weapon_stat.get("total_power", 0)
                
                total_power += stat.total_power
    return total_power

class PartyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="team", invoke_without_command=True, aliases=["party"], help="Commands for managing your party/team.")
    async def team(self, ctx: commands.Context):
        await self.party_view(ctx)
    
    @team.command(name="view", aliases=["v"], help="View your current party setup.")
    async def party_view(self, ctx: commands.Context):
        player = await Player.get(ctx.author.id)
        if not player:
            await ctx.reply("You haven't started yet. Use `sl start`.", mention_author=False)
            return

        embed = discord.Embed(title=f"{ctx.author.name}'s Party", color=discord.Color.dark_purple())
        
        total_p = await getPartyTotalPower(player)
        embed.description = f"**Total Power:** {total_p:,} ⚔️"
        
        for i, slot_key in enumerate(["Party_1", "Party_2", "Party_3"], start=1):
            hunter_id = player.equipped.get(slot_key)
            if hunter_id and player.hunters and hunter_id in player.hunters:
                hunter_data = player.hunters.get(hunter_id)
                if not hunter_data:
                    embed.add_field(name=f"Slot {i}", value=f"Empty {getEmoji('slot')}", inline=False)
                    continue
                
                char = await HeroManager.get(hunter_id)
                if not char:
                    embed.add_field(name=f"Slot {i}", value=f"Unknown Hunter {getEmoji('slot')}", inline=False)
                    continue

                level = hunter_data.get("level", 1)
                tier = hunter_data.get("tier", 0)
                stat = await getStatHunter(char.id, level)

                weapon_text = f"Empty {getEmoji('slot')}"
                weapon_id = hunter_data.get("weapon")
                if weapon_id and player.inventory and weapon_id in player.inventory:
                    weapon_data = player.inventory.get(weapon_id)
                    if weapon_data:
                        w_level = weapon_data.get("level", 1)
                        weapon_stat = await getStatWeapon(weapon_id, w_level)
                        if weapon_stat:
                            stat.attack += weapon_stat.get("attack", 0)
                            stat.defense += weapon_stat.get("defense", 0)
                            stat.hp += weapon_stat.get("hp", 0)
                            stat.mp += weapon_stat.get("mp", 0)
                        
                        weapon = await ItemManager.get(weapon_id)
                        if weapon:
                            weapon_text = f"{weapon.name} | Level: `{w_level}`"

                tier_stars = "★" * tier + "☆" * (5 - tier)
                field_value = (
                    f"Level: `{level}` | Tier: {tier_stars}\n"
                    f"ATK: `{stat.attack}` | DEF: `{stat.defense}` | HP: `{stat.hp}` | MP: `{stat.mp}`\n"
                    f"**Weapon:** {weapon_text}"
                )
                embed.add_field(name=f"Slot {i}: {getClassEmoji(char.classType)} {char.name}", value=field_value, inline=False)
            else:
                embed.add_field(name=f"Slot {i}", value=f"Empty {getEmoji('slot')}", inline=False)
        
        embed.set_footer(text="Use /team add [slot] [hunter] to add hunters")
        await ctx.reply(embed=embed, mention_author=False)

    @team.command(name="add", aliases=['a'], help="Add a hunter to a party slot.")
    @app_commands.describe(slot="The party slot to add the hunter to (1, 2, or 3).", hunter="The name of the hunter to add.")
    @app_commands.autocomplete(hunter=player_hunter_autocomplete)
    async def party_add(self, ctx: commands.Context, slot, *, hunter: str):
        try:
            # Convert and validate slot parameter
            try:
                slot_num = int(slot)
                if slot_num not in [1, 2, 3]:
                    await ctx.send("❌ Invalid slot! Please use slot 1, 2, or 3.", ephemeral=True)
                    return
                slot = slot_num
            except (ValueError, TypeError):
                await ctx.send("❌ Invalid slot! Please use slot 1, 2, or 3.", ephemeral=True)
                return

            player = await Player.get(ctx.author.id)
            if not player:
                await ctx.send("Player data not found. Please register first.", ephemeral=True)
                return
            if player.trade:
                await ctx.send(f"<@{player.id}> is in a trade. Please complete it first.", ephemeral=True)
                return

            available_hunters = { (await HeroManager.get(h_id)).name: h_id for h_id in player.hunters.keys() if await HeroManager.get(h_id) }

            best_match = process.extractOne(hunter, available_hunters.keys(), scorer=fuzz.ratio)
            if not best_match or best_match[1] < 60:
                await ctx.reply(f"Could not find a hunter matching `{hunter}`.", mention_author=False)
                return

            hunter_name, hunter_id = best_match[0], available_hunters[best_match[0]]

            if hunter_id in player.equipped.values():
                await ctx.reply(f"**{hunter_name}** is already equipped.", mention_author=False)
                return

            slot_key = f"Party_{slot}"
            player.equipped[slot_key] = hunter_id
            await player.save()

            h = await HeroManager.get(hunter_id)
            embed = discord.Embed(title=f"Slot {slot} Updated", description=f"Successfully added **{h.name}** to your party.", color=discord.Color.green())
            embed.set_thumbnail(url=get_emoji_url(getEmoji(h.id)))
            await ctx.reply(embed=embed, mention_author=False)

        except Exception as e:
            print(f"Error in party_add: {e}")
            try:
                await ctx.send("❌ An error occurred while adding the hunter to your party.", ephemeral=True)
            except:
                pass  # Ignore if we can't send error message

async def setup(bot):
    await bot.add_cog(PartyCog(bot))