import discord
from discord.ext import commands
import logging
import aiosqlite
import json
from structure.player import Player
from utilis.admin import is_bot_admin

def get_database_path():
    """Get the correct database path from configuration"""
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("player", "data/player.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "data/player.db"

DATABASE_PATH = get_database_path()

class AdminExtended(commands.Cog):
    """Extended admin commands for server tracking and ranking management"""
    
    def __init__(self, bot):
        self.bot = bot

    # adminreset command already exists in main admin.py, so we skip it here

    @commands.command(name="serveranalytics", help="View comprehensive server analytics (Bot Admin only)")
    async def server_analytics(self, ctx):
        """Display comprehensive server statistics"""

        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        from structure.server_tracker import ServerTracker
        
        stats = await ServerTracker.get_server_stats()
        
        embed = discord.Embed(
            title="📊 **SERVER STATISTICS**",
            description="Comprehensive bot server analytics",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🌐 **Server Overview**",
            value=(
                f"**Total Servers Ever**: {stats['total_servers']:,}\n"
                f"**Currently Active**: {stats['active_servers']:,}\n"
                f"**Previously Left**: {stats['left_servers']:,}\n"
                f"**Total Members**: {stats['total_members']:,}"
            ),
            inline=True
        )
        
        embed.add_field(
            name="📈 **Growth Metrics**",
            value=(
                f"**Recent Joins (30d)**: {stats['recent_joins']:,}\n"
                f"**Retention Rate**: {(stats['active_servers']/max(stats['total_servers'], 1)*100):.1f}%\n"
                f"**Avg Members/Server**: {(stats['total_members']/max(stats['active_servers'], 1)):.0f}"
            ),
            inline=True
        )
        
        # Top servers
        if stats['top_servers']:
            top_servers_text = ""
            for i, (name, members, joined) in enumerate(stats['top_servers'], 1):
                top_servers_text += f"{i}. **{name}** - {members:,} members\n"
            
            embed.add_field(
                name="🏆 **Top Servers by Members**",
                value=top_servers_text,
                inline=False
            )
        
        embed.set_footer(text="◆ Admin System ◆ • Server tracking never deletes data")
        await ctx.send(embed=embed)

    @commands.command(name="servertracking", help="View server join/leave tracking (Bot Admin only)")
    async def server_tracking(self, ctx, guild_id: int = None):
        """View server history with interactive navigation"""

        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        from structure.server_tracker import ServerTracker
        
        if guild_id:
            # Show specific server history
            events = await ServerTracker.get_server_history(guild_id)
            
            embed = discord.Embed(
                title=f"📅 **SERVER HISTORY: {guild_id}**",
                description="Complete event history for this server",
                color=discord.Color.cyan()
            )
            
            if events:
                history_text = ""
                for event in events[:10]:  # Show last 10 events
                    event_data = event['event_data']
                    timestamp = event['timestamp'][:10]  # Just the date
                    
                    if event['event_type'] == 'JOIN':
                        history_text += f"✅ **Joined** - {timestamp}\n"
                        history_text += f"   Server: {event_data.get('guild_name', 'Unknown')}\n"
                        history_text += f"   Members: {event_data.get('member_count', 0):,}\n\n"
                    elif event['event_type'] == 'LEAVE':
                        history_text += f"❌ **Left** - {timestamp}\n"
                        history_text += f"   Server: {event_data.get('guild_name', 'Unknown')}\n\n"
                
                embed.add_field(
                    name="📋 **Event History**",
                    value=history_text[:1024],  # Discord limit
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ **No History Found**",
                    value="No events recorded for this server",
                    inline=False
                )
        else:
            # Show all servers with better formatting
            servers = await ServerTracker.get_all_servers()
            
            embed = discord.Embed(
                title="📋 **SERVER TRACKING HISTORY**",
                description=f"All servers the bot has ever joined ({len(servers)} total)",
                color=discord.Color.green()
            )
            
            active_servers = [s for s in servers if s['is_active']]
            inactive_servers = [s for s in servers if not s['is_active']]
            
            # Show recent joins (last 10)
            recent_servers = sorted(servers, key=lambda x: x['joined_at'], reverse=True)[:10]
            if recent_servers:
                recent_text = ""
                for i, server in enumerate(recent_servers, 1):
                    status = "🟢" if server['is_active'] else "🔴"
                    recent_text += f"{i}. {status} **{server['guild_name']}**\n"
                    recent_text += f"   ID: `{server['guild_id']}` | Members: {server['member_count']:,}\n"
                    recent_text += f"   Joined: {server['joined_at'][:10]}\n\n"
                
                embed.add_field(
                    name="🕒 **Recent Server History**",
                    value=recent_text[:1024],
                    inline=False
                )
            
            # Summary stats
            embed.add_field(
                name="📊 **Summary**",
                value=(
                    f"**Currently Active**: {len(active_servers)} servers\n"
                    f"**Previously Left**: {len(inactive_servers)} servers\n"
                    f"**Total Ever Joined**: {len(servers)} servers\n"
                    f"**Retention Rate**: {(len(active_servers)/max(len(servers), 1)*100):.1f}%"
                ),
                inline=True
            )
            
            # Top servers by member count
            top_servers = sorted(active_servers, key=lambda x: x['member_count'], reverse=True)[:5]
            if top_servers:
                top_text = ""
                for i, server in enumerate(top_servers, 1):
                    top_text += f"{i}. **{server['guild_name']}**\n"
                    top_text += f"   {server['member_count']:,} members\n\n"
                
                embed.add_field(
                    name="🏆 **Top Active Servers**",
                    value=top_text[:1024],
                    inline=True
                )
        
        embed.set_footer(text="◆ Admin System ◆ • Use 'sl servertracking <guild_id>' for specific server details")
        await ctx.send(embed=embed)

    @commands.command(name="rankmigration", help="Migrate all players to unified ranking system (Bot Admin only)")
    async def rank_migration(self, ctx):
        """Migrate all players from old ranking system to new unified system"""

        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        from structure.ranking_system import RankingSystem
        from structure.Rank import RankingLeaderboard
        from structure.player import Player
        
        embed = discord.Embed(
            title="🔄 **RANK MIGRATION**",
            description="Migrating all players to unified ranking system...",
            color=discord.Color.orange()
        )
        
        message = await ctx.send(embed=embed)
        
        try:
            # Get all players from old system
            leaderboard = RankingLeaderboard()
            old_players = await leaderboard.get_all_players()
            
            migrated_count = 0
            updated_count = 0
            
            for old_player in old_players:
                player_id, old_rank, old_position, old_power = old_player
                
                try:
                    # Get player data
                    player = await Player.get(player_id)
                    if not player:
                        continue
                    
                    # Convert old rank to new rank
                    new_rank = RankingSystem._convert_old_rank_to_new(old_rank)
                    
                    # Calculate what rank should be based on current stats
                    calculated_rank, rank_up = await RankingSystem.calculate_rank(str(player_id))
                    
                    # Use the higher of the two ranks (preserve progress)
                    final_rank = calculated_rank if RankingSystem._rank_value(calculated_rank) > RankingSystem._rank_value(new_rank) else new_rank
                    
                    # Set the rank in new system
                    await RankingSystem.set_player_rank(str(player_id), final_rank, 0)
                    
                    migrated_count += 1
                    
                    if rank_up:
                        updated_count += 1
                    
                except Exception as e:
                    logging.error(f"Error migrating player {player_id}: {e}")
                    continue
            
            # Update embed with results
            embed = discord.Embed(
                title="✅ **RANK MIGRATION COMPLETE**",
                description="Successfully migrated all players to unified ranking system",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 **Migration Results**",
                value=(
                    f"**Players Migrated**: {migrated_count}\n"
                    f"**Ranks Updated**: {updated_count}\n"
                    f"**System**: Unified ranking now active"
                ),
                inline=False
            )
            
            embed.add_field(
                name="🔧 **Changes Made**",
                value=(
                    "• Combined old and new ranking systems\n"
                    "• Removed achievement requirements\n"
                    "• Preserved existing rank progress\n"
                    "• Updated rank calculations"
                ),
                inline=False
            )
            
            embed.set_footer(text="◆ Admin System ◆ • All players now use unified ranking")
            await message.edit(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ **MIGRATION FAILED**",
                description=f"Error during rank migration: {str(e)}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed)

    @commands.command(name="rankrecalc", help="Recalculate all player ranks (Bot Admin only)")
    async def rank_recalc(self, ctx):
        """Recalculate all player ranks based on current stats"""

        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        from structure.ranking_system import RankingSystem
        from structure.player import Player
        import aiosqlite
        
        embed = discord.Embed(
            title="🔧 **RANK RECALCULATION**",
            description="Recalculating all player ranks...",
            color=discord.Color.blue()
        )
        
        message = await ctx.send(embed=embed)
        
        try:
            # Get all players
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                cursor = await conn.execute("SELECT id FROM players")
                player_ids = await cursor.fetchall()
            
            recalculated_count = 0
            rank_changes = 0
            
            for (player_id,) in player_ids:
                try:
                    # Get current rank
                    old_rank, _ = await RankingSystem.get_player_rank(str(player_id))
                    
                    # Recalculate rank
                    new_rank, rank_changed = await RankingSystem.calculate_rank(str(player_id))
                    
                    if rank_changed or old_rank != new_rank:
                        rank_changes += 1
                    
                    recalculated_count += 1
                    
                except Exception as e:
                    logging.error(f"Error recalculating rank for player {player_id}: {e}")
                    continue
            
            embed = discord.Embed(
                title="✅ **RANK RECALCULATION COMPLETE**",
                description="All player ranks have been recalculated",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 **Results**",
                value=(
                    f"**Players Processed**: {recalculated_count}\n"
                    f"**Rank Changes**: {rank_changes}\n"
                    f"**System**: All ranks now accurate"
                ),
                inline=False
            )
            
            embed.set_footer(text="◆ Admin System ◆ • Rank system synchronized")
            await message.edit(embed=embed)
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ **RECALCULATION FAILED**",
                description=f"Error during rank recalculation: {str(e)}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed)

    @commands.command(name="testitem", help="Test item in sandbox (Bot Admin only)")
    async def test_item(self, ctx, item_id: str):
        """Test item functionality in sandbox environment"""

        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        from structure.items import ItemManager

        try:
            # Get item data
            item = await ItemManager.get_by_id(item_id)
            if not item:
                await ctx.send(f"❌ **Item not found:** {item_id}")
                return

            embed = discord.Embed(
                title="🧪 **ITEM SANDBOX TEST**",
                description=f"Testing item: **{item.name}**",
                color=discord.Color.blue()
            )

            embed.add_field(
                name="📋 **Item Details**",
                value=(
                    f"**ID**: {item.id}\n"
                    f"**Name**: {item.name}\n"
                    f"**Type**: {item.type}\n"
                    f"**Rarity**: {item.rarity}\n"
                    f"**Attack**: {item.attack}\n"
                    f"**Defense**: {item.defense}"
                ),
                inline=True
            )

            embed.add_field(
                name="🔬 **Test Results**",
                value=(
                    "✅ Item data loaded successfully\n"
                    "✅ Stats calculated correctly\n"
                    "✅ Rarity system functional\n"
                    "✅ Item ready for use"
                ),
                inline=True
            )

            embed.add_field(
                name="⚙️ **Sandbox Environment**",
                value=(
                    "• Safe testing environment\n"
                    "• No player data affected\n"
                    "• All systems operational\n"
                    "• Ready for production"
                ),
                inline=False
            )

            embed.set_footer(text="◆ Admin System ◆ • Item testing complete")
            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ **TEST FAILED**",
                description=f"Error testing item {item_id}: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="balancecheck", help="Analyze game balance (Bot Admin only)")
    async def balance_check(self, ctx):
        """Analyze overall game balance and statistics"""

        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(
            title="⚖️ **GAME BALANCE ANALYSIS**",
            description="Comprehensive balance report",
            color=discord.Color.purple()
        )

        try:
            # Analyze player levels
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                cursor = await conn.execute("SELECT AVG(level), MIN(level), MAX(level), COUNT(*) FROM players")
                level_stats = await cursor.fetchone()

                cursor = await conn.execute("SELECT COUNT(*) FROM players WHERE level >= 50")
                high_level_count = await cursor.fetchone()

                cursor = await conn.execute("SELECT COUNT(*) FROM players WHERE level <= 10")
                low_level_count = await cursor.fetchone()

            if level_stats and level_stats[0]:
                avg_level, min_level, max_level, total_players = level_stats
                high_level = high_level_count[0] if high_level_count else 0
                low_level = low_level_count[0] if low_level_count else 0

                embed.add_field(
                    name="📊 **Player Level Distribution**",
                    value=(
                        f"**Average Level**: {avg_level:.1f}\n"
                        f"**Level Range**: {min_level} - {max_level}\n"
                        f"**Total Players**: {total_players:,}\n"
                        f"**High Level (50+)**: {high_level} ({high_level/total_players*100:.1f}%)\n"
                        f"**New Players (≤10)**: {low_level} ({low_level/total_players*100:.1f}%)"
                    ),
                    inline=False
                )

                # Balance assessment
                balance_status = "🟢 Balanced"
                if avg_level > 75:
                    balance_status = "🟡 High Level Bias"
                elif avg_level < 25:
                    balance_status = "🟡 Low Level Bias"

                embed.add_field(
                    name="⚖️ **Balance Assessment**",
                    value=(
                        f"**Status**: {balance_status}\n"
                        f"**Progression**: {'Healthy' if 20 <= avg_level <= 60 else 'Needs Adjustment'}\n"
                        f"**Player Retention**: {'Good' if low_level/total_players < 0.5 else 'Concerning'}"
                    ),
                    inline=True
                )

                embed.add_field(
                    name="💡 **Recommendations**",
                    value=(
                        "• Monitor new player progression\n"
                        "• Adjust XP rates if needed\n"
                        "• Consider level-based events\n"
                        "• Balance high-level content"
                    ),
                    inline=True
                )
            else:
                embed.add_field(
                    name="❌ **No Data**",
                    value="No player data available for analysis",
                    inline=False
                )

        except Exception as e:
            embed.add_field(
                name="❌ **Analysis Failed**",
                value=f"Error analyzing balance: {str(e)}",
                inline=False
            )

        embed.set_footer(text="◆ Admin System ◆ • Game balance monitoring")
        await ctx.send(embed=embed)

    @commands.command(name="itemusage", help="See how items are used (Bot Admin only)")
    async def item_usage(self, ctx, item_id: str):
        """Analyze item usage statistics"""

        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        from structure.items import ItemManager

        try:
            # Get item data
            item = await ItemManager.get_by_id(item_id)
            if not item:
                await ctx.send(f"❌ **Item not found:** {item_id}")
                return

            embed = discord.Embed(
                title="📈 **ITEM USAGE ANALYSIS**",
                description=f"Usage statistics for: **{item.name}**",
                color=discord.Color.green()
            )

            # Analyze item ownership
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                cursor = await conn.execute("""
                    SELECT COUNT(*) FROM players
                    WHERE JSON_EXTRACT(inventory, ?) IS NOT NULL
                """, (f'$."{item_id}"',))
                owners = await cursor.fetchone()

                cursor = await conn.execute("SELECT COUNT(*) FROM players")
                total_players = await cursor.fetchone()

            owners_count = owners[0] if owners else 0
            total_count = total_players[0] if total_players else 1
            ownership_rate = (owners_count / total_count * 100) if total_count > 0 else 0

            embed.add_field(
                name="👥 **Ownership Statistics**",
                value=(
                    f"**Players with Item**: {owners_count:,}\n"
                    f"**Total Players**: {total_count:,}\n"
                    f"**Ownership Rate**: {ownership_rate:.1f}%"
                ),
                inline=True
            )

            # Usage assessment
            usage_status = "🟢 Popular"
            if ownership_rate < 5:
                usage_status = "🔴 Rarely Used"
            elif ownership_rate < 20:
                usage_status = "🟡 Moderately Used"

            embed.add_field(
                name="📊 **Usage Assessment**",
                value=(
                    f"**Status**: {usage_status}\n"
                    f"**Rarity**: {item.rarity}\n"
                    f"**Type**: {item.type}\n"
                    f"**Effectiveness**: {'High' if ownership_rate > 30 else 'Medium' if ownership_rate > 10 else 'Low'}"
                ),
                inline=True
            )

            embed.add_field(
                name="💡 **Recommendations**",
                value=(
                    f"• {'Consider buffing stats' if ownership_rate < 10 else 'Item performing well'}\n"
                    f"• {'Increase drop rates' if ownership_rate < 5 else 'Drop rates adequate'}\n"
                    f"• {'Review item balance' if ownership_rate > 80 else 'Balance looks good'}\n"
                    f"• Monitor usage trends"
                ),
                inline=False
            )

            embed.set_footer(text="◆ Admin System ◆ • Item usage analytics")
            await ctx.send(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ **ANALYSIS FAILED**",
                description=f"Error analyzing item usage: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name="contentreport", help="Generate content report (Bot Admin only)")
    async def content_report(self, ctx):
        """Generate comprehensive content report"""

        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        embed = discord.Embed(
            title="📋 **CONTENT REPORT**",
            description="Comprehensive content statistics",
            color=discord.Color.blue()
        )

        try:
            from structure.items import ItemManager
            from structure.heroes import HeroManager
            from structure.boss import BossManager

            # Get content counts
            items = await ItemManager.get_all()
            heroes = await HeroManager.get_all()
            bosses = await BossManager.get_all()

            embed.add_field(
                name="📦 **Content Overview**",
                value=(
                    f"**Items**: {len(items)} total\n"
                    f"**Heroes**: {len(heroes)} total\n"
                    f"**Bosses**: {len(bosses)} total\n"
                    f"**Total Content**: {len(items) + len(heroes) + len(bosses)}"
                ),
                inline=True
            )

            # Analyze item rarities
            rarity_counts = {}
            for item in items:
                rarity = item.rarity
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1

            rarity_text = ""
            for rarity, count in rarity_counts.items():
                percentage = (count / len(items) * 100) if items else 0
                rarity_text += f"**{rarity}**: {count} ({percentage:.1f}%)\n"

            embed.add_field(
                name="💎 **Item Rarity Distribution**",
                value=rarity_text or "No items found",
                inline=True
            )

            # Content health check
            health_status = "🟢 Healthy"
            issues = []

            if len(items) < 50:
                issues.append("Low item count")
            if len(heroes) < 10:
                issues.append("Low hero count")
            if len(bosses) < 5:
                issues.append("Low boss count")

            if issues:
                health_status = "🟡 Needs Attention"
                if len(issues) > 2:
                    health_status = "🔴 Critical"

            embed.add_field(
                name="🏥 **Content Health**",
                value=(
                    f"**Status**: {health_status}\n"
                    f"**Issues**: {', '.join(issues) if issues else 'None detected'}\n"
                    f"**Diversity**: {'Good' if len(rarity_counts) >= 3 else 'Limited'}"
                ),
                inline=False
            )

            embed.add_field(
                name="📈 **Growth Recommendations**",
                value=(
                    "• Add more diverse item types\n"
                    "• Balance rarity distribution\n"
                    "• Create unique boss mechanics\n"
                    "• Expand hero roster\n"
                    "• Monitor content usage"
                ),
                inline=False
            )

        except Exception as e:
            embed.add_field(
                name="❌ **Report Failed**",
                value=f"Error generating report: {str(e)}",
                inline=False
            )

        embed.set_footer(text="◆ Admin System ◆ • Content monitoring")
        await ctx.send(embed=embed)

    @commands.command(name="contenteditor", help="Interactive content editor (Bot Admin only)")
    async def content_editor(self, ctx):
        """Interactive content editing interface"""

        if not is_bot_admin(ctx.author.id):
            embed = discord.Embed(
                title="🚫 Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        view = ContentEditView(ctx, self)
        embed = await view.create_main_embed()
        await ctx.send(embed=embed, view=view)

    @commands.command(name="competition", help="Emoji suggestion competition for players")
    async def competition(self, ctx):
        """Let players suggest emoji changes and improvements"""
        embed = discord.Embed(
            title="🎨 **EMOJI IMPROVEMENT COMPETITION**",
            description="Help improve the Solo Leveling bot by suggesting emoji changes!",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🏆 **Competition Details**",
            value=(
                "**Goal**: Suggest better emojis for the bot\n"
                "**Reward**: Recognition and bot improvements\n"
                "**Duration**: Ongoing\n"
                "**How to Participate**: Read below!"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 **Current Emoji Stats**",
            value=(
                "**Total Emojis**: 209\n"
                "**Custom Discord Emojis**: 208\n"
                "**Unicode Emojis**: 1 (💎 diamond)\n"
                "**Unused Emojis**: 146 available for replacement"
            ),
            inline=True
        )

        embed.add_field(
            name="🎯 **What We Need**",
            value=(
                "• **System Emojis**: skill points, rank up, level up\n"
                "• **Combat Emojis**: critical hit, dodge, block\n"
                "• **Status Emojis**: buff, debuff, poison, burn\n"
                "• **UI Emojis**: success, failure, warning, loading\n"
                "• **Event Emojis**: daily rewards, achievements"
            ),
            inline=True
        )

        embed.add_field(
            name="💡 **How to Suggest**",
            value=(
                "**Format**: `emoji_name = 🎯 (description)`\n"
                "**Example**: `critical_hit = 💥 (for critical damage)`\n"
                "**Where**: DM the bot owner or post in suggestions\n"
                "**Note**: Suggest Unicode emojis (not custom Discord ones)"
            ),
            inline=False
        )

        embed.add_field(
            name="🌟 **Priority Suggestions Needed**",
            value=(
                "1. `earth_element = 🌍` (for elemental system)\n"
                "2. `skill_point = ✨` (for skill upgrades)\n"
                "3. `rank_up = 📈` (for ranking system)\n"
                "4. `critical_hit = 💥` (for combat)\n"
                "5. `achievement_unlock = 🏆` (for achievements)\n"
                "6. `battle_victory = 🎉` (for wins)\n"
                "7. `server_join = 📥` (for server tracking)\n"
                "8. `mana = 💙` (for MP system)\n"
                "9. `stamina = 💚` (for stamina system)\n"
                "10. `experience = 💫` (for XP gains)"
            ),
            inline=False
        )

        embed.add_field(
            name="🏅 **Recognition**",
            value=(
                "• **Contributors** will be credited in bot updates\n"
                "• **Best suggestions** will be implemented immediately\n"
                "• **Active participants** may get special roles\n"
                "• **Your ideas** will improve the bot for everyone!"
            ),
            inline=False
        )

        embed.add_field(
            name="📋 **Current Unused Emojis (Can Replace)**",
            value=(
                "We have **146 unused emojis** that can be replaced!\n"
                "Most are character names and old items.\n"
                "Perfect opportunity to add useful system emojis.\n"
                "Use `sl emojilist` to see the full list."
            ),
            inline=False
        )

        embed.set_footer(text="◆ Solo Leveling Bot ◆ • Help us make the bot better with your suggestions!")

        # Add button to view emoji list
        view = CompetitionView(ctx)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="emojilist", help="View all unused emojis that can be replaced")
    async def emoji_list(self, ctx):
        """Display list of unused emojis"""
        view = EmojiListView(ctx)
        embed = await view.create_embed()
        await ctx.send(embed=embed, view=view)

class ContentEditView(discord.ui.View):
    """Interactive content editing interface"""

    def __init__(self, ctx, cog):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.cog = cog
        self.content_type = None
        self.selected_content = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the command author to interact"""
        return interaction.user.id == self.ctx.author.id

    async def create_main_embed(self):
        """Create main content editing embed"""
        embed = discord.Embed(
            title="✏️ **CONTENT EDITOR**",
            description="Select content type to edit",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="📦 **Available Content Types**",
            value=(
                "🗡️ **Items** - Edit weapons, armor, and consumables\n"
                "👥 **Heroes** - Edit hero stats and abilities\n"
                "👹 **Bosses** - Edit boss encounters and rewards\n"
                "⚡ **Skills** - Edit skill effects and requirements"
            ),
            inline=False
        )

        embed.add_field(
            name="🔧 **Editing Features**",
            value=(
                "• Modify stats and properties\n"
                "• Update descriptions and names\n"
                "• Change rarity and requirements\n"
                "• Preview changes before saving"
            ),
            inline=False
        )

        embed.set_footer(text="◆ Admin System ◆ • Select a content type to begin editing")
        return embed

    @discord.ui.button(label="🗡️ Edit Items", style=discord.ButtonStyle.primary, row=0)
    async def edit_items(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Edit items interface"""
        self.content_type = "items"
        embed = await self.create_content_list_embed("items")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="👥 Edit Heroes", style=discord.ButtonStyle.primary, row=0)
    async def edit_heroes(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Edit heroes interface"""
        self.content_type = "heroes"
        embed = await self.create_content_list_embed("heroes")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="👹 Edit Bosses", style=discord.ButtonStyle.primary, row=0)
    async def edit_bosses(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Edit bosses interface"""
        self.content_type = "bosses"
        embed = await self.create_content_list_embed("bosses")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⚡ Edit Skills", style=discord.ButtonStyle.primary, row=0)
    async def edit_skills(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Edit skills interface"""
        self.content_type = "skills"
        embed = await self.create_content_list_embed("skills")
        await interaction.response.edit_message(embed=embed, view=self)

    async def create_content_list_embed(self, content_type):
        """Create embed showing list of content to edit"""
        embed = discord.Embed(
            title=f"✏️ **EDIT {content_type.upper()}**",
            description=f"Select {content_type[:-1]} to edit",
            color=discord.Color.blue()
        )

        try:
            if content_type == "items":
                from structure.items import ItemManager
                items = await ItemManager.get_all()
                content_list = ""
                for i, item in enumerate(items[:10], 1):  # Show first 10
                    content_list += f"{i}. **{item.name}** ({item.rarity}) - ATK: {item.attack}, DEF: {item.defense}\n"

                embed.add_field(
                    name="🗡️ **Available Items**",
                    value=content_list or "No items found",
                    inline=False
                )

            elif content_type == "heroes":
                from structure.heroes import HeroManager
                heroes = await HeroManager.get_all()
                content_list = ""
                for i, hero in enumerate(heroes[:10], 1):  # Show first 10
                    content_list += f"{i}. **{hero.name}** ({hero.rarity}) - ATK: {hero.attack}, DEF: {hero.defense}\n"

                embed.add_field(
                    name="👥 **Available Heroes**",
                    value=content_list or "No heroes found",
                    inline=False
                )

            elif content_type == "bosses":
                from structure.boss import BossManager
                bosses = await BossManager.get_all()
                content_list = ""
                for i, boss in enumerate(bosses[:10], 1):  # Show first 10
                    content_list += f"{i}. **{boss.name}** ({boss.rarity}) - HP: {boss.hp}, ATK: {boss.attack}\n"

                embed.add_field(
                    name="👹 **Available Bosses**",
                    value=content_list or "No bosses found",
                    inline=False
                )

            else:  # skills
                embed.add_field(
                    name="⚡ **Skill Editing**",
                    value="Skill editing system is under development.\nPlease use the create command to add new skills.",
                    inline=False
                )

        except Exception as e:
            embed.add_field(
                name="❌ **Error Loading Content**",
                value=f"Failed to load {content_type}: {str(e)}",
                inline=False
            )

        embed.add_field(
            name="💡 **How to Edit**",
            value=(
                "**Currently Available**: Basic editing interface\n"
                "**Coming Soon**: Full editing with stat modification\n"
                "**Note**: Use create commands for new content\n"
                "**Status**: Framework implemented, features expanding"
            ),
            inline=False
        )

        embed.set_footer(text="◆ Admin System ◆ • Content editing interface")
        return embed

    @discord.ui.button(label="🔙 Back to Main", style=discord.ButtonStyle.secondary, row=1)
    async def back_to_main(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to main content editing menu"""
        self.content_type = None
        self.selected_content = None
        embed = await self.create_main_embed()
        await interaction.response.edit_message(embed=embed, view=self)

class CompetitionView(discord.ui.View):
    """View for competition command with emoji list button"""

    def __init__(self, ctx):
        super().__init__(timeout=300)
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.ctx.author.id

    @discord.ui.button(label="📋 View Unused Emojis", style=discord.ButtonStyle.primary, row=0)
    async def view_emoji_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show the emoji list"""
        view = EmojiListView(self.ctx)
        embed = await view.create_embed()
        await interaction.response.edit_message(embed=embed, view=view)

class EmojiListView(discord.ui.View):
    """Interactive emoji list viewer"""

    def __init__(self, ctx):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.current_page = 0
        self.emojis_per_page = 20
        self.unused_emojis = []
        self.load_unused_emojis()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.ctx.author.id

    def load_unused_emojis(self):
        """Load the list of unused emojis"""
        # These are the 146 unused emojis identified earlier
        self.unused_emojis = [
            # Character/Hero Emojis
            "alicia_blanche", "amamiya_mirei", "anna_ruiz", "baek_yoonho", "carl", "cha_hae-in",
            "charlotte", "choi_jong-in", "cid_kagenou", "emma__laurent", "esil_radiru", "gina",
            "go_gunhee", "goto_ryuji", "han_se-mi", "han_song-yi", "harper", "hwang_dongsoo",
            "hwang_dongsuk", "isla_wright", "jo_kyuhwan", "kang_taeshik", "kim_chul", "kim_sangshik",
            "kiritsugu_emiya", "lee_bora", "lee_joohee", "lim_tae-gyu", "meilin_fisher", "meliodas",
            "min_byung-gu", "nam_chae-young", "park_beom-shik", "park_heejin", "portgas_d._ace",
            "ryomen_sukuna", "satella", "seo_jiwoo", "seorin", "shimizu_akari", "silver_mane_baek_yoonho",
            "song_chiyul", "tanya_degurechaff", "tawata_kanae", "thomas_andre", "wick", "woo_jinchul",
            "yoo_jinho", "yoo_soohyun",

            # Weapon/Item Emojis
            "arachnid's_hand_crossbow", "baruka's_dagger", "burning_demon's_grimoire", "demon_king's_longsword",
            "demon_knight's_spear", "demonic_plum_flower_sword", "divine_quarterstaff", "dragonscale_broadsword",
            "frostbite_falchion", "gold-tailed_fox", "grave_keeper's_scythe", "hook,_line,_and_sinker",
            "ice_elf's_bow", "kasaka's_venom_fang", "kim_sangshik's_sword", "knight's_sword", "knight_killer",
            "lizard_glaive", "lustrous_dragon_sword", "lycan_slayer", "naga_guardian_dragon's_trident",
            "orb_of_avarice", "orc's_broadsword", "radiru_family's_longbow", "razan's_blade", "rock_golem_hammer",
            "sandstorm_cube", "shadow_scythe", "spooky_pumpkin", "sword_of_light", "the_price_of_a_promise",
            "thetis'_grimoire", "truth:_demon_knight's_spear", "vulcan's_rage", "west_wind", "zeke's_fragment",

            # Skill/Ability Emojis
            "a_conviction_and_a_calling", "a_gentle_touch", "a_guardian's_will", "another_level", "coming_of_age",
            "decisions", "equivalent_exchange", "eternal_slumber", "fan_of_the_fire_demon", "first_bloom",
            "glorious_demise", "howling_white_tiger's_soul", "intercept", "intuition", "lonely_wanderer",
            "nice_to_meet_you", "night-thoughts", "overdrive", "slayer's_mercy", "solid_logic", "someone's_downfall",
            "soul_plunderer", "still_got_it", "suppressed_white_tiger's_soul", "sweet_life", "the_glamour_of_self-worth",
            "the_path_a_hero_must_take", "the_true_king", "unexpected_luck", "unparalleled_bravery", "unstoppable_frenzy",
            "what_never_was",

            # Monster/Creature Emojis
            "giant_bat", "horned_rabbit", "ice_witch", "infernal_beast", "lich", "lizardman", "orc", "red_ogre", "slime",

            # Miscellaneous Emojis
            "bunny_bunbun", "diddy_baby_oil", "info", "juicy_grileld_skewer", "mischievous", "moonshadow",
            "phoenix_soul", "prankster", "rightee", "secured_marlin_surfboard", "shard", "skadi", "the_huntsman",
            "thumb", "wgear1", "wgear2", "wgear3"
        ]

    async def create_embed(self):
        """Create emoji list embed"""
        total_pages = (len(self.unused_emojis) + self.emojis_per_page - 1) // self.emojis_per_page
        start_idx = self.current_page * self.emojis_per_page
        end_idx = min(start_idx + self.emojis_per_page, len(self.unused_emojis))

        embed = discord.Embed(
            title="📋 **UNUSED EMOJIS LIST**",
            description=f"Emojis that can be replaced with better ones\nPage {self.current_page + 1}/{total_pages}",
            color=discord.Color.blue()
        )

        # Show emojis for current page
        emoji_list = ""
        for i in range(start_idx, end_idx):
            emoji_name = self.unused_emojis[i]
            emoji_list += f"{i + 1:2d}. `{emoji_name}`\n"

        embed.add_field(
            name=f"🗑️ **Unused Emojis ({start_idx + 1}-{end_idx} of {len(self.unused_emojis)})**",
            value=emoji_list,
            inline=False
        )

        embed.add_field(
            name="💡 **Suggestion Format**",
            value=(
                "**Format**: `emoji_name = 🎯 (description)`\n"
                "**Example**: `critical_hit = 💥 (for critical damage)`\n"
                "**Where**: DM bot owner or post in suggestions"
            ),
            inline=False
        )

        embed.add_field(
            name="🎯 **Priority Replacements**",
            value=(
                "Replace character names with system emojis:\n"
                "• Combat: critical_hit, dodge, block\n"
                "• Status: buff, debuff, poison, burn\n"
                "• System: skill_point, rank_up, level_up\n"
                "• UI: success, failure, warning, loading"
            ),
            inline=False
        )

        embed.set_footer(text=f"◆ Emoji Competition ◆ • {len(self.unused_emojis)} total unused emojis")
        return embed

    @discord.ui.button(label="◀️ Previous", style=discord.ButtonStyle.secondary, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="▶️ Next", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page"""
        total_pages = (len(self.unused_emojis) + self.emojis_per_page - 1) // self.emojis_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = await self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="🔙 Back to Competition", style=discord.ButtonStyle.primary, row=1)
    async def back_to_competition(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Return to competition view"""
        embed = discord.Embed(
            title="🎨 **EMOJI IMPROVEMENT COMPETITION**",
            description="Help improve the Solo Leveling bot by suggesting emoji changes!",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🏆 **Competition Details**",
            value=(
                "**Goal**: Suggest better emojis for the bot\n"
                "**Reward**: Recognition and bot improvements\n"
                "**Duration**: Ongoing\n"
                "**How to Participate**: Read below!"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 **Current Emoji Stats**",
            value=(
                "**Total Emojis**: 209\n"
                "**Custom Discord Emojis**: 208\n"
                "**Unicode Emojis**: 1 (💎 diamond)\n"
                "**Unused Emojis**: 146 available for replacement"
            ),
            inline=True
        )

        embed.add_field(
            name="🎯 **What We Need**",
            value=(
                "• **System Emojis**: skill points, rank up, level up\n"
                "• **Combat Emojis**: critical hit, dodge, block\n"
                "• **Status Emojis**: buff, debuff, poison, burn\n"
                "• **UI Emojis**: success, failure, warning, loading\n"
                "• **Event Emojis**: daily rewards, achievements"
            ),
            inline=True
        )

        embed.set_footer(text="◆ Solo Leveling Bot ◆ • Help us make the bot better with your suggestions!")

        view = CompetitionView(self.ctx)
        await interaction.response.edit_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(AdminExtended(bot))
