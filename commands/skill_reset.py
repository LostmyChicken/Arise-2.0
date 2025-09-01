import discord
from discord.ext import commands
from discord import ui
import json
import aiosqlite
from datetime import datetime, timedelta
from structure.player import Player
from structure.skill_tree_system import SkillTreeSystem, SkillTreeType

def get_database_path():
    """Get the correct database path from configuration"""
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("player", "data/player.db")
    except Exception as e:
        return "data/player.db"

DATABASE_PATH = get_database_path()

class SkillResetCog(commands.Cog):
    """Skill reset system with 2-week cooldown"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="skillreset", help="Reset all skill points and skills (2-week cooldown)")
    async def skill_reset(self, ctx):
        """Reset all skill points and skills with confirmation"""
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(
                title="❌ **Player Not Found**",
                description="You don't have a profile yet. Use the bot to start your journey!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        # Check cooldown
        if player.last_skill_reset:
            try:
                last_reset = datetime.fromisoformat(player.last_skill_reset)
                cooldown_end = last_reset + timedelta(weeks=2)
                now = datetime.now()
                
                if now < cooldown_end:
                    time_left = cooldown_end - now
                    days_left = time_left.days
                    hours_left = time_left.seconds // 3600
                    
                    embed = discord.Embed(
                        title="⏰ **SKILL RESET ON COOLDOWN**",
                        description="You can only reset skills once every 2 weeks!",
                        color=discord.Color.orange()
                    )
                    
                    embed.add_field(
                        name="🕒 **Time Remaining**",
                        value=f"**{days_left}** days, **{hours_left}** hours",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="📅 **Next Reset Available**",
                        value=f"<t:{int(cooldown_end.timestamp())}:F>",
                        inline=True
                    )
                    
                    embed.add_field(
                        name="💡 **Why the Cooldown?**",
                        value="Skill resets are limited to prevent abuse and encourage thoughtful skill planning.",
                        inline=False
                    )
                    
                    embed.set_footer(text="◆ Skill System ◆ • Plan your builds carefully!")
                    await ctx.send(embed=embed)
                    return
                    
            except (ValueError, TypeError):
                # Invalid date format, allow reset
                pass

        # Show reset confirmation
        view = SkillResetConfirmView(ctx, player)
        embed = await view.create_confirmation_embed()
        await ctx.send(embed=embed, view=view)

class SkillResetConfirmView(discord.ui.View):
    """Confirmation view for skill reset"""
    
    def __init__(self, ctx, player):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.player = player
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.ctx.author.id
    
    async def create_confirmation_embed(self):
        """Create skill reset confirmation embed"""
        # Get current skill data
        total_skill_points_spent = 0
        unlocked_skills_count = 0
        
        for tree_type in SkillTreeType:
            tree_data = await SkillTreeSystem.get_player_skill_tree(str(self.player.id), tree_type)
            total_skill_points_spent += tree_data['total_points_spent']
            unlocked_skills_count += len(tree_data['unlocked_skills'])
        
        embed = discord.Embed(
            title="⚠️ **SKILL RESET CONFIRMATION**",
            description="**This will reset ALL your skill trees and refund skill points!**",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="🔄 **What Will Be Reset**",
            value=(
                f"• **All unlocked skills**: {unlocked_skills_count} skills\n"
                f"• **All skill upgrades**: Back to level 1\n"
                f"• **All skill trees**: Completely reset\n"
                f"• **Skill points refunded**: {total_skill_points_spent} ✥"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💰 **What You'll Get Back**",
            value=(
                f"• **{total_skill_points_spent}** ✥ skill points refunded\n"
                f"• **Fresh start** on all skill trees\n"
                f"• **Ability to respec** your entire build\n"
                f"• **Keep all other progress** (level, stats, items)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⏰ **Cooldown Information**",
            value=(
                "• **Next reset available**: 2 weeks from now\n"
                "• **One-time action**: Cannot be undone\n"
                "• **Plan carefully**: Choose your new build wisely"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 **Current Skill Points**",
            value=f"**Available**: {self.player.skillPoints} ✥\n**After Reset**: {self.player.skillPoints + total_skill_points_spent} ✥",
            inline=True
        )
        
        embed.set_footer(text="◆ Skill System ◆ • This action cannot be undone!")
        return embed
    
    @discord.ui.button(label="✅ CONFIRM RESET", style=discord.ButtonStyle.danger, row=0)
    async def confirm_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm and perform skill reset"""
        await interaction.response.defer()
        
        try:
            # Calculate total skill points to refund
            total_refund = 0
            reset_summary = {}
            
            for tree_type in SkillTreeType:
                tree_data = await SkillTreeSystem.get_player_skill_tree(str(self.player.id), tree_type)
                points_spent = tree_data['total_points_spent']
                skills_count = len(tree_data['unlocked_skills'])
                
                total_refund += points_spent
                reset_summary[tree_type.value] = {
                    'skills': skills_count,
                    'points': points_spent
                }
                
                # Reset the skill tree
                await SkillTreeSystem.reset_player_skill_tree(str(self.player.id), tree_type)
            
            # Refund skill points
            self.player.skillPoints += total_refund
            
            # Set reset cooldown
            self.player.last_skill_reset = datetime.now().isoformat()
            
            # Save player data
            await self.player.save()
            
            # Create success embed
            embed = discord.Embed(
                title="✅ **SKILL RESET COMPLETE**",
                description="All your skills have been reset and skill points refunded!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💰 **Skill Points Refunded**",
                value=f"**{total_refund}** ✥ skill points returned",
                inline=True
            )
            
            embed.add_field(
                name="🎯 **New Total**",
                value=f"**{self.player.skillPoints}** ✥ skill points available",
                inline=True
            )
            
            # Add reset summary
            summary_text = ""
            for tree_name, data in reset_summary.items():
                if data['skills'] > 0:
                    summary_text += f"**{tree_name}**: {data['skills']} skills, {data['points']} points\n"
            
            if summary_text:
                embed.add_field(
                    name="📊 **Reset Summary**",
                    value=summary_text,
                    inline=False
                )
            
            embed.add_field(
                name="⏰ **Next Reset Available**",
                value=f"<t:{int((datetime.now() + timedelta(weeks=2)).timestamp())}:F>",
                inline=False
            )
            
            embed.add_field(
                name="🎮 **What's Next?**",
                value=(
                    "• Use `sl skilltree` to access skill trees\n"
                    "• Plan your new build carefully\n"
                    "• Unlock skills that match your playstyle\n"
                    "• Remember: Next reset is in 2 weeks!"
                ),
                inline=False
            )
            
            embed.set_footer(text="◆ Skill System ◆ • Fresh start achieved!")
            await interaction.edit_original_response(embed=embed, view=None)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ **RESET FAILED**",
                description=f"An error occurred during skill reset: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=embed, view=None)
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary, row=0)
    async def cancel_reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel skill reset"""
        embed = discord.Embed(
            title="❌ **SKILL RESET CANCELLED**",
            description="Your skills remain unchanged.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="💡 **Tip**",
            value="Take time to plan your build before resetting. You can only reset once every 2 weeks!",
            inline=False
        )
        
        embed.set_footer(text="◆ Skill System ◆ • Reset cancelled")
        await interaction.response.edit_message(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(SkillResetCog(bot))
