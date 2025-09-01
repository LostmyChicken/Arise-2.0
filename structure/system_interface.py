import logging
import discord
import asyncio
import random
from typing import List, Dict, Optional
from structure.emoji import getEmoji

class SystemInterface:
    """
    Sung Jin-Woo style System Interface for notifications and interactions
    """
    
    @staticmethod
    def create_system_embed(title: str, description: str, color: discord.Color = discord.Color.blue()) -> discord.Embed:
        """Create a System-style embed with consistent formatting"""
        embed = discord.Embed(
            title=f"📱 **[SYSTEM]** {title}",
            description=description,
            color=color
        )
        embed.set_footer(text="◆ The System ◆")
        return embed
    
    @staticmethod
    def create_level_up_notification(old_level: int, new_level: int, stat_points: int) -> discord.Embed:
        """Create Sung Jin-Woo style level up notification"""
        embed = discord.Embed(
            title="📱 **[SYSTEM NOTIFICATION]**",
            description="**LEVEL UP!**",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🎉 **Congratulations!**",
            value=f"You have reached **Level {new_level}**!",
            inline=False
        )
        
        embed.add_field(
            name="📊 **Level Progress**",
            value=f"**Level {old_level}** → **Level {new_level}**",
            inline=True
        )
        
        embed.add_field(
            name="⭐ **Stat Points Gained**",
            value=f"+{stat_points} Stat Points",
            inline=True
        )
        
        embed.add_field(
            name="💡 **System Message**",
            value="*Your power grows stronger. Continue your journey, Hunter.*",
            inline=False
        )
        
        embed.set_footer(text="◆ The System ◆ • Use 'sl stats' to allocate your stat points")
        return embed
    
    @staticmethod
    def create_rank_up_notification(old_rank: str, new_rank: str) -> discord.Embed:
        """Create rank up notification"""
        rank_colors = {
            'E': discord.Color.light_grey(),
            'D': discord.Color.green(),
            'C': discord.Color.blue(),
            'B': discord.Color.purple(),
            'A': discord.Color.red(),
            'S': discord.Color.gold(),
            'National': discord.Color.from_rgb(255, 215, 0)
        }
        
        embed = discord.Embed(
            title="📱 **[SYSTEM NOTIFICATION]**",
            description="**RANK UP ACHIEVED!**",
            color=rank_colors.get(new_rank, discord.Color.gold())
        )
        
        embed.add_field(
            name="🏆 **Hunter Rank Promotion**",
            value=f"**{old_rank}-Rank** → **{new_rank}-Rank Hunter**",
            inline=False
        )
        
        rank_messages = {
            'D': "You have proven yourself capable. New opportunities await.",
            'C': "Your skills are developing well. Continue your training.",
            'B': "You are becoming a formidable hunter. Stay vigilant.",
            'A': "Few reach this level. Your power is exceptional.",
            'S': "You have joined the elite. The world recognizes your strength.",
            'National': "You stand among legends. Your name will be remembered."
        }
        
        embed.add_field(
            name="💬 **System Message**",
            value=f"*{rank_messages.get(new_rank, 'Your journey continues, Hunter.')}*",
            inline=False
        )
        
        embed.set_footer(text="◆ The System ◆ • New content and challenges are now available")
        return embed
    
    @staticmethod
    def create_achievement_notification(achievement_name: str, achievement_desc: str, reward: str) -> discord.Embed:
        """Create achievement unlock notification"""
        embed = discord.Embed(
            title="📱 **[SYSTEM NOTIFICATION]**",
            description="**ACHIEVEMENT UNLOCKED!**",
            color=discord.Color.from_rgb(255, 215, 0)
        )
        
        embed.add_field(
            name="🏅 **Achievement**",
            value=f"**{achievement_name}**",
            inline=False
        )
        
        embed.add_field(
            name="📝 **Description**",
            value=achievement_desc,
            inline=False
        )
        
        if reward:
            embed.add_field(
                name="🎁 **Reward**",
                value=reward,
                inline=False
            )
        
        embed.add_field(
            name="💬 **System Message**",
            value="*Your dedication has been recognized. Well done, Hunter.*",
            inline=False
        )
        
        embed.set_footer(text="◆ The System ◆ • Check 'sl achievements' for more challenges")
        return embed
    
    @staticmethod
    def create_skill_unlock_notification(skill_name: str, skill_type: str) -> discord.Embed:
        """Create skill unlock notification"""
        embed = discord.Embed(
            title="📱 **[SYSTEM NOTIFICATION]**",
            description="**NEW SKILL ACQUIRED!**",
            color=discord.Color.from_rgb(138, 43, 226)
        )
        
        embed.add_field(
            name="🌟 **Skill Unlocked**",
            value=f"**{skill_name}**",
            inline=False
        )
        
        embed.add_field(
            name="⚡ **Skill Type**",
            value=skill_type,
            inline=True
        )
        
        embed.add_field(
            name="💬 **System Message**",
            value="*New power flows through you. Master it well, Hunter.*",
            inline=False
        )
        
        embed.set_footer(text="◆ The System ◆ • Use 'sl skills' to manage your abilities")
        return embed
    
    @staticmethod
    def create_daily_quest_notification(quests: Dict) -> discord.Embed:
        """Create daily quest assignment notification"""
        embed = discord.Embed(
            title="📱 **[SYSTEM NOTIFICATION]**",
            description="**DAILY QUESTS ASSIGNED**",
            color=discord.Color.blue()
        )
        
        quest_text = ""
        for quest_name, quest_data in quests.items():
            required = quest_data.get('required', 0)
            quest_text += f"• **{quest_name.title()}**: 0/{required}\n"
        
        embed.add_field(
            name="📋 **Today's Quests**",
            value=quest_text,
            inline=False
        )
        
        embed.add_field(
            name="💬 **System Message**",
            value="*Complete your daily training to grow stronger, Hunter.*",
            inline=False
        )
        
        embed.set_footer(text="◆ The System ◆ • Use 'sl train' to make progress")
        return embed
    
    @staticmethod
    def create_emergency_quest_notification(quest_name: str, description: str, time_limit: str) -> discord.Embed:
        """Create emergency quest notification"""
        embed = discord.Embed(
            title="📱 **[SYSTEM ALERT]**",
            description="**EMERGENCY QUEST DETECTED!**",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="🚨 **Emergency Quest**",
            value=f"**{quest_name}**",
            inline=False
        )
        
        embed.add_field(
            name="📝 **Objective**",
            value=description,
            inline=False
        )
        
        embed.add_field(
            name="⏰ **Time Limit**",
            value=time_limit,
            inline=True
        )
        
        embed.add_field(
            name="💬 **System Message**",
            value="*Urgent situation detected. Immediate action required, Hunter.*",
            inline=False
        )
        
        embed.set_footer(text="◆ The System ◆ • Emergency quests offer exceptional rewards")
        return embed
    
    @staticmethod
    async def send_system_notification(channel: discord.TextChannel, embed: discord.Embed, delay: float = 0.5):
        """Send a system notification with typing effect"""
        try:
            if delay > 0:
                try:
                    async with channel.typing():
                        await asyncio.sleep(delay)
                except discord.Forbidden:
                    # No typing permission, just wait without typing
                    await asyncio.sleep(delay)
                except Exception:
                    # Any other error with typing, skip it
                    pass

            return await channel.send(embed=embed)
        except discord.Forbidden:
            # No send message permission, silently fail
            logging.warning(f"Missing permission to send message in channel {channel.id}")
            return None
        except discord.HTTPException as e:
            # Other Discord API errors
            logging.error(f"Discord API error sending system notification: {e}")
            return None
        except Exception as e:
            # Any other unexpected error
            logging.error(f"Unexpected error sending system notification: {e}")
            return None
    
    @staticmethod
    def get_system_response(message_type: str) -> str:
        """Get random system response messages"""
        responses = {
            'level_up': [
                "Your power grows stronger, Hunter.",
                "You have overcome your limits.",
                "The System acknowledges your progress.",
                "Your potential continues to unfold.",
                "Well done. Continue your journey."
            ],
            'rank_up': [
                "You have proven your worth.",
                "Your skills have been recognized.",
                "A new chapter begins, Hunter.",
                "Your dedication has paid off.",
                "The System is pleased with your progress."
            ],
            'achievement': [
                "Your efforts have been noted.",
                "Excellence deserves recognition.",
                "You have surpassed expectations.",
                "The System commends your achievement.",
                "Your determination is admirable."
            ],
            'quest_complete': [
                "Quest completed successfully.",
                "Your training bears fruit.",
                "The System is satisfied.",
                "Well executed, Hunter.",
                "Your skills continue to develop."
            ]
        }
        
        return random.choice(responses.get(message_type, ["The System observes your progress."]))
