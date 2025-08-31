import discord
from discord.ext import commands
from structure.items import ItemManager
from structure.heroes import HeroManager
from structure.boss import Boss
from structure.shadow import Shadow
from utilis.utilis import extractId
from structure.emoji import getEmoji, getClassEmoji, getRarityEmoji
from utilis.admin import is_bot_admin

class ViewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="view", aliases=["info", "show"])
    async def view_content(self, ctx, *, name: str):
        """View detailed information about any item, hero, boss, or shadow"""
        if not name:
            await ctx.send("❌ **Please provide a name to search for!**\nUsage: `sl view <name>`")
            return

        # Search in all content types
        results = await self.search_all_content(name)
        
        if not results:
            await ctx.send(f"❌ **No content found matching '{name}'**\nTry checking the spelling or use `sl gallery` to see available content.")
            return
        
        if len(results) == 1:
            # Single result - show detailed view
            content_type, content = results[0]
            embed = await self.create_detailed_embed(content_type, content)
            await ctx.send(embed=embed)
        else:
            # Multiple results - show selection
            embed = await self.create_selection_embed(name, results)
            await ctx.send(embed=embed)

    async def search_all_content(self, name: str):
        """Search for content across all types"""
        results = []
        search_id = extractId(name)
        
        # Search items
        try:
            items = await ItemManager.get_all()
            for item in items:
                if (name.lower() in item.name.lower() or 
                    search_id == item.id or 
                    item.name.lower() == name.lower()):
                    results.append(("item", item))
        except Exception as e:
            print(f"Error searching items: {e}")
        
        # Search heroes
        try:
            heroes = await HeroManager.get_all()
            for hero in heroes:
                if (name.lower() in hero.name.lower() or 
                    search_id == hero.id or 
                    hero.name.lower() == name.lower()):
                    results.append(("hero", hero))
        except Exception as e:
            print(f"Error searching heroes: {e}")
        
        # Search bosses
        try:
            bosses = await Boss.get_all()
            for boss in bosses:
                if (name.lower() in boss.name.lower() or 
                    search_id == boss.id or 
                    boss.name.lower() == name.lower()):
                    results.append(("boss", boss))
        except Exception as e:
            print(f"Error searching bosses: {e}")
        
        # Search shadows
        try:
            shadows = await Shadow.get_all()
            for shadow in shadows:
                if (name.lower() in shadow.name.lower() or 
                    search_id == shadow.id or 
                    shadow.name.lower() == name.lower()):
                    results.append(("shadow", shadow))
        except Exception as e:
            print(f"Error searching shadows: {e}")
        
        return results

    async def create_detailed_embed(self, content_type: str, content):
        """Create detailed embed for a single piece of content"""
        # Get custom emoji or fallback
        custom_emoji = getattr(content, 'custom_emoji', '')
        fallback_emoji = getEmoji(content.id)
        display_emoji = custom_emoji or fallback_emoji
        
        if content_type == "item":
            embed = discord.Embed(
                title=f"{display_emoji} **{content.name}**",
                description=f"*{content.description}*" if content.description else "*No description available*",
                color=self.get_rarity_color(content.rarity)
            )
            
            embed.add_field(name="📋 **Item Details**", value=(
                f"**Type**: {content.type}\n"
                f"**Class**: {getClassEmoji(content.classType)} {content.classType}\n"
                f"**Rarity**: {getRarityEmoji(content.rarity)} {content.rarity}\n"
                f"**ID**: `{content.id}`"
            ), inline=True)
            
            embed.add_field(name="📊 **Stats**", value=(
                f"⚔️ **Attack**: {content.attack}\n"
                f"🛡️ **Defense**: {content.defense}\n"
                f"❤️ **Health**: {content.health}\n"
                f"💙 **MP**: {content.mp}\n"
                f"⚡ **Speed**: {content.speed}\n"
                f"🎯 **Precision**: {content.precision}"
            ), inline=True)
            
        elif content_type == "hero":
            embed = discord.Embed(
                title=f"{display_emoji} **{content.name}**",
                description=f"*{content.description}*" if content.description else "*No description available*",
                color=self.get_rarity_color(content.rarity)
            )
            
            embed.add_field(name="👤 **Hero Details**", value=(
                f"**Type**: {content.type}\n"
                f"**Class**: {getClassEmoji(content.classType)} {content.classType}\n"
                f"**Rarity**: {getRarityEmoji(content.rarity)} {content.rarity}\n"
                f"**Rank**: {content.rank}\n"
                f"**ID**: `{content.id}`"
            ), inline=True)
            
            embed.add_field(name="📊 **Stats**", value=(
                f"⚔️ **Attack**: {content.attack}\n"
                f"🛡️ **Defense**: {content.defense}\n"
                f"❤️ **Health**: {content.health}\n"
                f"💙 **MP**: {content.mp}\n"
                f"⚡ **Speed**: {content.speed}"
            ), inline=True)
            
            embed.add_field(name="🌍 **Background**", value=(
                f"**Age**: {content.age}\n"
                f"**Gender**: {content.gender}\n"
                f"**Country**: {content.country}\n"
                f"**Weapon**: {content.weapon}\n"
                f"**Guild**: {content.guild}"
            ), inline=False)
            
        elif content_type == "boss":
            embed = discord.Embed(
                title=f"{display_emoji} **{content.name}**",
                description=f"*{content.description}*" if content.description else "*No description available*",
                color=discord.Color.dark_red()
            )
            
            embed.add_field(name="👹 **Boss Details**", value=(
                f"**Element**: {getClassEmoji(content.boss_class)} {content.boss_class}\n"
                f"**Weakness**: {getClassEmoji(content.weakness_class)} {content.weakness_class}\n"
                f"**Rarity**: {getRarityEmoji(content.rarity)} {content.rarity}\n"
                f"**ID**: `{content.id}`"
            ), inline=True)
            
            embed.add_field(name="📊 **Stats**", value=(
                f"⚔️ **Attack**: {content.attack:,}\n"
                f"🛡️ **Defense**: {content.defense:,}\n"
                f"❤️ **Health**: {content.health:,}\n"
                f"⚡ **Speed**: {content.speed:,}\n"
                f"🎯 **Precision**: {content.precision:,}"
            ), inline=True)
            
        elif content_type == "shadow":
            embed = discord.Embed(
                title=f"{display_emoji} **{content.name}**",
                description=f"*{content.description}*" if content.description else "*No description available*",
                color=discord.Color.purple()
            )
            
            embed.add_field(name="👤 **Shadow Details**", value=(
                f"**Price**: {content.price:,} TOS\n"
                f"**ID**: `{content.id}`"
            ), inline=True)
            
            embed.add_field(name="📊 **Stat Boosts**", value=(
                f"⚔️ **Attack Boost**: +{content.attack}%\n"
                f"🛡️ **Defense Boost**: +{content.defense}%"
            ), inline=True)
        
        # Set image
        if hasattr(content, 'image') and content.image:
            embed.set_image(url=content.image)
        
        # Set footer
        embed.set_footer(text=f"Solo Leveling Bot • {content_type.title()} Information")
        
        return embed

    async def create_selection_embed(self, search_term: str, results):
        """Create selection embed when multiple results found"""
        embed = discord.Embed(
            title=f"🔍 **Multiple Results Found for '{search_term}'**",
            description="Here are all the matches:",
            color=discord.Color.blue()
        )
        
        for i, (content_type, content) in enumerate(results[:10], 1):  # Limit to 10 results
            custom_emoji = getattr(content, 'custom_emoji', '')
            fallback_emoji = getEmoji(content.id)
            display_emoji = custom_emoji or fallback_emoji
            
            embed.add_field(
                name=f"{i}. {display_emoji} **{content.name}**",
                value=f"**Type**: {content_type.title()}\n**ID**: `{content.id}`",
                inline=True
            )
        
        if len(results) > 10:
            embed.add_field(
                name="📋 **Note**",
                value=f"Showing first 10 of {len(results)} results. Be more specific to narrow down.",
                inline=False
            )
        
        embed.set_footer(text="Use 'sl view <exact name>' to see detailed information")
        return embed

    def get_rarity_color(self, rarity: str):
        """Get color based on rarity"""
        colors = {
            'UR': discord.Color.from_rgb(255, 0, 128),  # Pink for UR
            'SSR': discord.Color.gold(),
            'Super Rare': discord.Color.purple(),
            'Rare': discord.Color.blue(),  # Keep for badge display only
            'Common': discord.Color.light_grey(),
            'Epic': discord.Color.purple(),
            'Legendary': discord.Color.gold(),
            'Mythic': discord.Color.red()
        }
        return colors.get(rarity, discord.Color.default())

async def setup(bot):
    await bot.add_cog(ViewCog(bot))
