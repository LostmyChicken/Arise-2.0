import time
import discord
import random
import json
from discord.ui import Button, View
from discord.ext import commands
from discord import app_commands
from typing import List, Dict, Any
from utilis.utilis import PremiumCheck
from structure.emoji import getEmoji
from structure.player import Player

class TriviaView(View):
    def __init__(self, cog: 'Trivia', author: discord.User, questions: List[Dict[str, Any]]):
        super().__init__(timeout=60.0)
        self.cog = cog
        self.author = author
        self.questions = questions
        self.current_question_index = 0
        self.correct_answers = 0
        self.attempt_log: List[bool] = []
        self.message: discord.Message = None

    async def start(self, ctx: commands.Context):
        """Starts the trivia session by sending the first question."""
        embed = self._create_question_embed()
        self._setup_buttons()
        self.message = await ctx.send(embed=embed, view=self)

    def _create_question_embed(self) -> discord.Embed:
        """Creates the embed for the current question."""
        question_data = self.questions[self.current_question_index]
        log_display = " ".join(["☑️" if correct else "❌" for correct in self.attempt_log])
        
        embed = discord.Embed(
            title=f"Trivia Question {self.current_question_index + 1}/{len(self.questions)}",
            description=f"**{question_data['question']}**\n\n{log_display}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url="https://i.redd.it/official-solo-leveling-emotes-from-koreas-kakaotalk-app-v0-2bpm0xaae92e1.png?width=210&format=png&auto=webp&s=820a6c8d3b493bced141812ea0836072864df857")
        embed.set_footer(text=f"Time remaining...")
        return embed

    def _setup_buttons(self):
        """Sets up the answer buttons for the current question."""
        self.clear_items()
        question_data = self.questions[self.current_question_index]
        options = question_data['options']
        correct_answer = question_data['answer']
        
        shuffled_options = options[:]
        random.shuffle(shuffled_options)
        
        for option in shuffled_options:
            is_correct = (option == correct_answer)
            button = Button(label=option, style=discord.ButtonStyle.secondary)
            button.callback = self.create_callback(is_correct)
            self.add_item(button)

    def create_callback(self, is_correct: bool):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.author.id:
                await interaction.response.send_message("This isn't your trivia session!", ephemeral=True)
                return

            self.attempt_log.append(is_correct)
            if is_correct:
                self.correct_answers += 1
            
            self.current_question_index += 1
            if self.current_question_index < len(self.questions):
                embed = self._create_question_embed()
                self._setup_buttons()
                await interaction.response.edit_message(embed=embed, view=self)
            else:
                await self.end_trivia(interaction)
        return callback

    async def end_trivia(self, interaction: discord.Interaction = None):
        """Ends the trivia, calculates rewards, and shows the final result."""
        self.stop()
        
        player = await Player.get(self.author.id)
        if not player: return

        reward_data = self.cog.rewards.get(self.correct_answers, self.cog.rewards[0])
        gold = random.randint(*reward_data["gold"])
        xp = random.randint(*reward_data["xp"])
        
        bonus_msg = ""
        if random.randint(1, self.cog.bonus_chance) == 1:
            bonus_xp = random.randint(2000, 5000)
            xp += bonus_xp
            bonus_msg = f"\n\n✨ **BONUS!** You got lucky and earned an extra `{bonus_xp}` {getEmoji('xp')}!"

        player.gold += gold
        await player.add_xp(self.cog.bot, xp, interaction.channel if interaction else self.message.channel)
        await player.save()

        log_display = " | ".join(["☑️" if correct else "❌" for correct in self.attempt_log])
        
        embed = discord.Embed(
            title="Trivia Complete!",
            description=(
                f"{self.cog.funny_responses[self.correct_answers]}\n\n"
                f"You got **{self.correct_answers}/{len(self.questions)}** correct!\n`{log_display}`\n\n"
                f"**Rewards:**\n"
                f"• Obtained `{gold}` {getEmoji('gold')} Gold\n"
                f"• Obtained `{xp}` {getEmoji('xp')} Experience"
                f"{bonus_msg}"
            ),
            color=discord.Color.green() if self.correct_answers > 2 else discord.Color.orange()
        )
        
        thumbnail_url = "https://files.catbox.moe/axkqha.webp" if self.correct_answers == 5 else "https://media.stickerswiki.app/solo_leveling_sticker/6522420.512.webp"
        embed.set_thumbnail(url=thumbnail_url)
        
        # Check if interaction is still valid before responding
        if interaction and not interaction.response.is_done():
            try:
                await interaction.response.edit_message(embed=embed, view=None)
            except (discord.NotFound, discord.HTTPException) as e:
                # Interaction expired or invalid, try to edit the message directly
                if self.message:
                    try:
                        await self.message.edit(embed=embed, view=None)
                    except (discord.NotFound, discord.HTTPException):
                        pass
        elif self.message:
            try:
                await self.message.edit(embed=embed, view=None)
            except (discord.NotFound, discord.HTTPException):
                pass
            
        self.cog.active_trivias.discard(self.author.id)

    async def on_timeout(self):
        await self.end_trivia()

class Trivia(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open('trivia.json', 'r', encoding='utf-8') as f:
            self.questions = json.load(f)["questions"]
        
        self.rewards = {
            5: {"gold": (1000, 1200), "xp": (300, 350)}, 4: {"gold": (800, 1000), "xp": (200, 300)},
            3: {"gold": (400, 800), "xp": (150, 200)}, 2: {"gold": (400, 600), "xp": (100, 150)},
            1: {"gold": (200, 400), "xp": (50, 100)}, 0: {"gold": (100, 200), "xp": (10, 50)}
        }
        self.funny_responses = {
            0: "Even a rock would've done better!", 1: "Did you guess randomly? Because it shows...",
            2: "Well... at least you tried?", 3: "Not terrible! But not great either...",
            4: "Almost perfect! Just one more!", 5: "Perfect! Are you a genius?"
        }
        self.bonus_chance = 100
        self.active_trivias = set()

    @commands.hybrid_command(name="trivia", aliases=["tr"], help="Start a trivia session to earn rewards.")
    async def trivia(self, ctx: commands.Context):
        if ctx.author.id in self.active_trivias:
            embed = discord.Embed(title="SYSTEM MESSAGE", description="**[ERROR] Active Session**\nYou already have an active trivia session.", color=discord.Color.red())
            await ctx.send(embed=embed, ephemeral=True)
            return
            
        player = await Player.get(ctx.author.id)
        if not player:
            embed = discord.Embed(title="SYSTEM MESSAGE", description="**[ERROR] Player Not Found**\nYou don't have a profile yet. Use `sl start`.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
            
        if player.trade:
            embed = discord.Embed(title="SYSTEM MESSAGE", description="**[ERROR] Action Blocked**\nYou are in a trade. Please complete it first.", color=discord.Color.red())
            await ctx.send(embed=embed)
            return
            
        cooldown = int(120 * PremiumCheck(player))
        if player.trivia and (time.time() - float(player.trivia) < cooldown):
            remaining = cooldown - (time.time() - float(player.trivia))
            minutes, seconds = divmod(int(remaining), 60)
            embed = discord.Embed(
                title="SYSTEM MESSAGE",
                description=f"**[COOLDOWN]**\nYou can play trivia again in **{minutes}m {seconds}s**.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
            
        player.setTriviaCooldown()
        await player.save()
        self.active_trivias.add(ctx.author.id)

        selected_questions = random.sample(self.questions, min(5, len(self.questions)))
        
        # To ensure the correct answer string is passed, we need to process the questions
        processed_questions = []
        for q in selected_questions:
            correct_answer_text = q['options'][q['answer'] - 1]
            processed_questions.append({
                "question": q["question"],
                "options": q["options"],
                "answer": correct_answer_text
            })

        view = TriviaView(self, ctx.author, processed_questions)
        await view.start(ctx)

async def setup(bot):
    await bot.add_cog(Trivia(bot))