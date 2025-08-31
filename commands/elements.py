"""
Elemental System Commands
Commands for viewing and interacting with the elemental system
"""

import discord
from discord.ext import commands
from discord import app_commands
from structure.elements import ElementalSystem, Element
from structure.player import Player

class ElementalView(discord.ui.View):
    """Interactive view for the elemental system"""
    
    def __init__(self, ctx):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.current_view = "chart"  # chart, calculator, tips
        self.update_buttons()
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the command user can interact"""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Only the command user can interact with this menu!", ephemeral=True)
            return False
        return True
    
    def update_buttons(self):
        """Update buttons based on current view"""
        self.clear_items()
        
        # Main navigation buttons
        chart_style = discord.ButtonStyle.primary if self.current_view == "chart" else discord.ButtonStyle.secondary
        calc_style = discord.ButtonStyle.primary if self.current_view == "calculator" else discord.ButtonStyle.secondary
        tips_style = discord.ButtonStyle.primary if self.current_view == "tips" else discord.ButtonStyle.secondary
        
        chart_btn = discord.ui.Button(label="📊 Weakness Chart", style=chart_style)
        chart_btn.callback = self.show_chart
        self.add_item(chart_btn)
        
        calc_btn = discord.ui.Button(label="🧮 Damage Calculator", style=calc_style)
        calc_btn.callback = self.show_calculator
        self.add_item(calc_btn)
        
        tips_btn = discord.ui.Button(label="💡 Strategy Tips", style=tips_style)
        tips_btn.callback = self.show_tips
        self.add_item(tips_btn)
    
    async def show_chart(self, interaction: discord.Interaction):
        """Show the elemental weakness chart"""
        self.current_view = "chart"
        self.update_buttons()
        embed = ElementalSystem.create_weakness_chart_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def show_calculator(self, interaction: discord.Interaction):
        """Show the damage calculator"""
        self.current_view = "calculator"
        self.update_buttons()
        embed = self.create_calculator_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def show_tips(self, interaction: discord.Interaction):
        """Show strategy tips"""
        self.current_view = "tips"
        self.update_buttons()
        embed = self.create_tips_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    def create_calculator_embed(self):
        """Create damage calculator embed"""
        embed = discord.Embed(
            title="🧮 **ELEMENTAL DAMAGE CALCULATOR** 🧮",
            description="Calculate damage multipliers for different elemental matchups!",
            color=discord.Color.green()
        )
        
        # Show all possible matchups
        matchup_text = []
        for attacker in Element:
            if attacker == Element.NEUTRAL:
                continue
            
            attacker_emoji = ElementalSystem.get_element_emoji(attacker)
            attacker_name = ElementalSystem.get_element_name(attacker)
            
            for defender in Element:
                if defender == Element.NEUTRAL:
                    continue
                
                defender_emoji = ElementalSystem.get_element_emoji(defender)
                defender_name = ElementalSystem.get_element_name(defender)
                
                multiplier = ElementalSystem.calculate_damage_multiplier(attacker, defender)
                
                if multiplier > 1.0:
                    effectiveness = "💥 **SUPER**"
                elif multiplier < 1.0:
                    effectiveness = "💨 *Weak*"
                else:
                    effectiveness = "⚪ Normal"
                
                matchup_text.append(f"{attacker_emoji} vs {defender_emoji}: {effectiveness} ({multiplier}x)")
        
        # Split into chunks for multiple fields
        chunk_size = 8
        chunks = [matchup_text[i:i + chunk_size] for i in range(0, len(matchup_text), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            embed.add_field(
                name=f"⚔️ **Matchups {i+1}**" if i > 0 else "⚔️ **Damage Multipliers**",
                value="\n".join(chunk),
                inline=True
            )
        
        embed.add_field(
            name="📝 **How to Use**",
            value=(
                "• Find your attacker element (left side)\n"
                "• Find defender element (right side)\n"
                "• Check the multiplier for damage calculation\n"
                "• Plan your team composition accordingly!"
            ),
            inline=False
        )
        
        return embed
    
    def create_tips_embed(self):
        """Create strategy tips embed"""
        embed = discord.Embed(
            title="💡 **ELEMENTAL STRATEGY GUIDE** 💡",
            description="Master the elements to dominate in combat!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🎯 **Team Building Tips**",
            value=(
                "• **Diversify Elements**: Mix different elements in your team\n"
                "• **Counter Strategy**: Check enemy elements before battle\n"
                "• **Elemental Synergy**: Some combinations work better together\n"
                "• **Backup Plans**: Always have multiple element options"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚔️ **Combat Strategy**",
            value=(
                "• **Scout First**: Use reconnaissance to identify enemy elements\n"
                "• **Switch Tactics**: Change hunters mid-battle if needed\n"
                "• **Elemental Cubes**: Use cubes to enhance elemental attacks\n"
                "• **Timing Matters**: Save super effective attacks for key moments"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🏆 **Advanced Tactics**",
            value=(
                "• **Elemental Chains**: Combine elements for bonus effects\n"
                "• **Defensive Play**: Use resistant elements to tank damage\n"
                "• **Surprise Attacks**: Keep some elements hidden until needed\n"
                "• **Meta Knowledge**: Learn common enemy element patterns"
            ),
            inline=False
        )
        
        # Add element-specific tips
        element_tips = []
        for element in Element:
            if element == Element.NEUTRAL:
                continue
            
            emoji = ElementalSystem.get_element_emoji(element)
            name = ElementalSystem.get_element_name(element)
            
            tips_map = {
                Element.FIRE: "High damage, weak to Water & Earth",
                Element.WATER: "Balanced stats, counters Fire",
                Element.WIND: "High speed, great for hit-and-run",
                Element.EARTH: "High defense, slow but tanky",
                Element.LIGHT: "Healing abilities, counters Dark",
                Element.DARK: "Status effects, counters Light"
            }
            
            tip = tips_map.get(element, "Balanced element")
            element_tips.append(f"{emoji} **{name}**: {tip}")
        
        embed.add_field(
            name="🌟 **Element Specialties**",
            value="\n".join(element_tips),
            inline=False
        )
        
        embed.set_footer(text="Practice these strategies to become an elemental master!")
        
        return embed

class ElementCommands(commands.Cog):
    """Commands for the elemental system"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="elements", aliases=["elem", "elemental"], help="View the elemental weakness chart and combat system")
    async def elements(self, ctx):
        """Display the interactive elemental system interface"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # Create interactive elemental view
        view = ElementalView(ctx)
        embed = ElementalSystem.create_weakness_chart_embed()
        await ctx.reply(embed=embed, view=view, mention_author=False)
    
    @commands.command(name="element", help="Check the element of a specific hunter or weapon")
    async def check_element(self, ctx, *, item_name: str):
        """Check the element of a specific item"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ Not Started",
                description="You haven't started your adventure yet. Use `sl start` to begin!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed, mention_author=False)
            return
        
        # This would need to be implemented with actual item lookup
        # For now, show a placeholder
        embed = discord.Embed(
            title="🔍 **ELEMENT CHECK** 🔍",
            description=f"Checking element for: **{item_name}**",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="⚠️ Feature Coming Soon",
            value=(
                "Element checking for specific items is being implemented!\n"
                "For now, use the weakness chart to plan your strategy."
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Current Options",
            value=(
                "• Use `sl elements` to view the weakness chart\n"
                "• Check item descriptions for element info\n"
                "• Plan team compositions with elemental diversity"
            ),
            inline=False
        )
        
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(ElementCommands(bot))
