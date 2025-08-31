import discord
from discord.ext import commands
from rapidfuzz import process

from structure.emoji import getEmoji
from utilis.utilis import extractId
from structure.player import Player
from structure.skills import SkillManager, Skill

class Skills(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="skills", help="Show the player's skills and their levels.")
    async def skills(self, ctx):
        player_id = ctx.author.id

        player = await Player.get(player_id)
        if not player:
            await ctx.send("You don't have a profile yet. Use `sl start` to create one.")
            return

        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Skills",
            description=f"**✥** Skill Points: **{player.skillPoints}**\n-# You get +5 ✥ every level you gain\n-# `sl learn [name]` to learn a new skill.\n-# `sl codex skill [name]` for more detail.",
            color=discord.Color.dark_red()
        )

        # Initialize fields for each skill type
        skills_by_type = {
            "Basic": [],
            "QTE": [],
            "Ultimate": []
        }

        if hasattr(player, "skills") and player.skills:
            for skill_id, skill_data in player.skills.items():
                skill = await SkillManager.get(skill_id)
                if skill:
                    skill_level = skill_data.get("level", "Unknown")
                    # Add skill to the appropriate category
                    skill_type = skill.skill_type.value
                    skills_by_type[skill_type].append(f"┗ {skill.name} | Level: **{skill_level}**")
        else:
            embed.description = "You haven't unlocked any skills yet."

        down = getEmoji("down")
        slot = getEmoji("slot")
        # Add fields to the embed
        for skill_type, skills in skills_by_type.items():
            if skills:
                embed.add_field(name=f"{skill_type} Skills", value=f"\n".join(skills), inline=False)
            else:
                embed.add_field(name=f"{skill_type} Skills", value=f"┗ None {slot}", inline=False)

        embed.set_footer(text="Keep leveling up to unlock more skills!")
        await ctx.send(embed=embed)

    @commands.command(name="learn", help="Learn a new skill by ID or name.")
    async def skill_learn(self, ctx, *, name: str):
        player_id = ctx.author.id
        player = await Player.get(player_id)

        if not player:
            await ctx.send("You don't have a profile yet. Use `sl start` to create one.")
            return

        # Check story lock for advanced skills
        from structure.story_campaign import check_story_lock
        from utilis.utilis import create_embed, WARNING_COLOR
        can_access, lock_message = await check_story_lock(ctx.author.id, "double_dungeon_002", "Skill Learning")
        if not can_access:
            embed = create_embed("🔒 Feature Locked", lock_message, WARNING_COLOR, ctx.author)
            await ctx.reply(embed=embed, mention_author=False)
            return

        all_skills = await SkillManager.get_all()
        skill_names = [skill.name for skill in all_skills]

        best_match = process.extractOne(name, skill_names)
        if not best_match or best_match[1] < 80:  # 80 is the threshold for a good match
            await ctx.send(f"No skill found matching `{name}`. Please try again with a more accurate name.")
            return

        skill_name = best_match[0]
        skill = None
        for s in all_skills:
            if s.name == skill_name:
                skill = s
                break

        if not skill:
            await ctx.send(f"Skill `{skill_name}` not found.")
            return

        if skill.id in player.skills:
            await ctx.send(f"You already know the skill `{skill.name}`.")
            return

        if skill.level > player.level:
            await ctx.send(f"Sung Jinwoo should be level **{skill.level}** to learn **{skill.name}**")
            return

        player.add_skill(skill.id)
        await player.save()

        await ctx.send(f"Congratulations! You have learned the skill `{skill.name}`.")

async def setup(bot):
    await bot.add_cog(Skills(bot))