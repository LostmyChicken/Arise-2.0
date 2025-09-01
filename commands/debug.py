import discord
from discord.ext import commands
from discord import app_commands
import json
import sys
from typing import Optional
from structure.player import Player
from structure.emoji import getEmoji
from utilis.utilis import create_embed, INFO_COLOR, ERROR_COLOR, WARNING_COLOR

class DebugCog(commands.Cog):
    """Debug commands for analyzing database issues and player data."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="debug_size", help="Analyze player data size to find database blob issues.")
    @commands.is_owner()
    async def debug_player_size(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Debug command to analyze player data size and identify large fields."""
        
        target_user = user or ctx.author
        player = await Player.get(target_user.id)
        
        if not player:
            embed = create_embed(
                "Player Not Found", 
                f"No player data found for {target_user.display_name}",
                ERROR_COLOR,
                ctx.author
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Analyze data sizes
        data_analysis = {}
        total_size = 0
        
        # Check each field size
        fields_to_check = [
            'inventory', 'hunters', 'equipped', 'shadows', 'quests', 
            'skills', 'mission', 'loot', 'market', 'defeated_bosses'
        ]
        
        for field in fields_to_check:
            field_data = getattr(player, field, {})
            if field_data:
                json_str = json.dumps(field_data)
                size_bytes = len(json_str.encode('utf-8'))
                data_analysis[field] = {
                    'size_bytes': size_bytes,
                    'size_kb': round(size_bytes / 1024, 2),
                    'item_count': len(field_data) if isinstance(field_data, dict) else 1,
                    'json_length': len(json_str)
                }
                total_size += size_bytes

        # Sort by size
        sorted_fields = sorted(data_analysis.items(), key=lambda x: x[1]['size_bytes'], reverse=True)
        
        # Create embed
        embed = discord.Embed(
            title=f"🔍 Player Data Size Analysis",
            description=f"**Player**: {target_user.display_name}\n**Total Size**: `{round(total_size / 1024, 2)} KB`",
            color=WARNING_COLOR if total_size > 500000 else INFO_COLOR  # Warn if > 500KB
        )
        
        # Add field analysis
        analysis_text = []
        for field, data in sorted_fields[:10]:  # Top 10 largest fields
            size_kb = data['size_kb']
            item_count = data['item_count']
            
            # Add warning emoji for large fields
            warning = "⚠️" if size_kb > 50 else "📊" if size_kb > 10 else "📝"
            
            analysis_text.append(
                f"{warning} **{field.title()}**: `{size_kb} KB` ({item_count} items)"
            )
        
        embed.add_field(
            name="📈 Field Size Analysis",
            value="\n".join(analysis_text) if analysis_text else "No data found",
            inline=False
        )
        
        # Check for potential issues
        issues = []
        if total_size > 1000000:  # 1MB
            issues.append("🚨 **CRITICAL**: Total data size exceeds 1MB")
        elif total_size > 500000:  # 500KB
            issues.append("⚠️ **WARNING**: Total data size exceeds 500KB")
            
        for field, data in data_analysis.items():
            if data['size_kb'] > 100:
                issues.append(f"🔴 **{field}** is very large ({data['size_kb']} KB)")
            elif data['size_kb'] > 50:
                issues.append(f"🟡 **{field}** is large ({data['size_kb']} KB)")
        
        if issues:
            embed.add_field(
                name="🚨 Potential Issues",
                value="\n".join(issues),
                inline=False
            )
        else:
            embed.add_field(
                name="✅ Status",
                value="No size issues detected",
                inline=False
            )
        
        # Add recommendations
        recommendations = []
        if data_analysis.get('inventory', {}).get('size_kb', 0) > 50:
            recommendations.append("• Consider cleaning up old inventory items")
        if data_analysis.get('hunters', {}).get('size_kb', 0) > 50:
            recommendations.append("• Hunter data might need optimization")
        if data_analysis.get('shadows', {}).get('size_kb', 0) > 50:
            recommendations.append("• Shadow data might be corrupted or too large")
        
        if recommendations:
            embed.add_field(
                name="💡 Recommendations",
                value="\n".join(recommendations),
                inline=False
            )
        
        embed.set_footer(text="Use this data to identify what's causing database size errors")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="debug_inventory", help="Analyze inventory data in detail.")
    @commands.is_owner()
    async def debug_inventory(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Debug command to analyze inventory data in detail."""
        
        target_user = user or ctx.author
        player = await Player.get(target_user.id)
        
        if not player:
            embed = create_embed(
                "Player Not Found", 
                f"No player data found for {target_user.display_name}",
                ERROR_COLOR,
                ctx.author
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        inventory = player.inventory
        if not inventory:
            embed = create_embed(
                "Empty Inventory", 
                f"{target_user.display_name} has no inventory data",
                INFO_COLOR,
                ctx.author
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Analyze inventory items
        item_analysis = {}
        total_items = len(inventory)
        
        for item_id, item_data in inventory.items():
            item_json = json.dumps({item_id: item_data})
            size_bytes = len(item_json.encode('utf-8'))
            
            item_analysis[item_id] = {
                'size_bytes': size_bytes,
                'data_type': type(item_data).__name__,
                'data_preview': str(item_data)[:100] + "..." if len(str(item_data)) > 100 else str(item_data)
            }

        # Sort by size
        sorted_items = sorted(item_analysis.items(), key=lambda x: x[1]['size_bytes'], reverse=True)
        
        # Create embed
        embed = discord.Embed(
            title=f"🎒 Inventory Analysis",
            description=f"**Player**: {target_user.display_name}\n**Total Items**: `{total_items}`",
            color=INFO_COLOR
        )
        
        # Show largest items
        large_items = []
        for item_id, data in sorted_items[:15]:  # Top 15 largest items
            size_bytes = data['size_bytes']
            data_type = data['data_type']
            preview = data['data_preview']
            
            large_items.append(
                f"**{item_id}** ({data_type}): `{size_bytes}B`\n└ `{preview}`"
            )
        
        if large_items:
            embed.add_field(
                name="📦 Largest Items",
                value="\n".join(large_items),
                inline=False
            )
        
        # Check for problematic items
        problems = []
        for item_id, data in item_analysis.items():
            if data['size_bytes'] > 1000:  # Items over 1KB
                problems.append(f"🔴 **{item_id}**: {data['size_bytes']} bytes")
            elif data['data_type'] not in ['dict', 'int', 'str']:
                problems.append(f"🟡 **{item_id}**: Unusual data type ({data['data_type']})")
        
        if problems:
            embed.add_field(
                name="⚠️ Potential Issues",
                value="\n".join(problems[:10]),  # Limit to 10 issues
                inline=False
            )
        
        embed.set_footer(text=f"Showing analysis for {min(15, len(sorted_items))} items")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="debug_cleanup", help="Clean up player data to reduce size.")
    @commands.is_owner()
    async def debug_cleanup(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Debug command to clean up player data and reduce size."""
        
        target_user = user or ctx.author
        player = await Player.get(target_user.id)
        
        if not player:
            embed = create_embed(
                "Player Not Found", 
                f"No player data found for {target_user.display_name}",
                ERROR_COLOR,
                ctx.author
            )
            await ctx.reply(embed=embed, mention_author=False)
            return

        # Perform cleanup operations
        cleanup_report = []
        
        # Clean up inventory - remove invalid entries
        if player.inventory:
            original_count = len(player.inventory)
            # Remove None values and empty strings
            player.inventory = {k: v for k, v in player.inventory.items() if v is not None and v != ""}
            new_count = len(player.inventory)
            if original_count != new_count:
                cleanup_report.append(f"🧹 Cleaned inventory: {original_count} → {new_count} items")
        
        # Clean up hunters - remove invalid entries
        if player.hunters:
            original_count = len(player.hunters)
            player.hunters = {k: v for k, v in player.hunters.items() if v is not None and v != ""}
            new_count = len(player.hunters)
            if original_count != new_count:
                cleanup_report.append(f"🧹 Cleaned hunters: {original_count} → {new_count} items")
        
        # Clean up shadows - remove invalid entries
        if player.shadows:
            original_count = len(player.shadows)
            player.shadows = {k: v for k, v in player.shadows.items() if v is not None and v != ""}
            new_count = len(player.shadows)
            if original_count != new_count:
                cleanup_report.append(f"🧹 Cleaned shadows: {original_count} → {new_count} items")
        
        # Save the cleaned data
        try:
            await player.save()
            cleanup_report.append("✅ Player data saved successfully")
        except Exception as e:
            cleanup_report.append(f"❌ Failed to save: {str(e)}")
        
        # Create result embed
        embed = discord.Embed(
            title=f"🧹 Data Cleanup Complete",
            description=f"**Player**: {target_user.display_name}",
            color=INFO_COLOR
        )
        
        if cleanup_report:
            embed.add_field(
                name="📋 Cleanup Report",
                value="\n".join(cleanup_report),
                inline=False
            )
        else:
            embed.add_field(
                name="📋 Cleanup Report",
                value="No cleanup needed - data is already clean",
                inline=False
            )
        
        await ctx.reply(embed=embed, mention_author=False)

async def setup(bot):
    await bot.add_cog(DebugCog(bot))
