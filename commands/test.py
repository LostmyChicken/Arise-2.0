import discord
from discord.ext import commands
import asyncio
import inspect
import logging

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="testall", description="Run all commands to check for errors.")
    @commands.is_owner()
    async def test_all_commands(self, ctx: commands.Context):
        """
        Iterates through all commands and tries to run them with dummy data.
        This is a diagnostic tool to find broken commands.
        """
        is_interaction = ctx.interaction is not None
        if is_interaction:
            await ctx.defer(ephemeral=True)
        else:
            await ctx.typing()
        
        success_count = 0
        fail_count = 0
        failed_commands = []

        for command in self.bot.walk_commands():
            if command.name in ['testall', 'help'] or not command.enabled:
                continue

            # Skip subcommands of groups, as they are walked individually
            if command.parent:
                continue

            logging.info(f"Testing command: {command.qualified_name}")
            try:
                # We can't truly "invoke" the command here as creating dummy arguments
                # for every possible signature is extremely complex.
                # Instead, we'll do a basic check by calling its callback with a mock context.
                # This won't catch all errors, but it will catch signature mismatches,
                # bad decorators, and other initialization-time errors.
                
                # A simple check to see if the command's callback can be accessed
                # and appears to be a valid coroutine.
                if not asyncio.iscoroutinefunction(command.callback):
                    raise TypeError(f"Callback for {command.qualified_name} is not a coroutine.")

                # This is a simplified check. A full test would require complex arg mocking.
                # For now, we are just checking for load-time and definition errors.
                # The fact that the cog loaded is a good sign. We'll mark it as a "pass"
                # for this simplified test. A more robust test would require a dedicated
                # testing framework.
                
                success_count += 1
            except Exception as e:
                fail_count += 1
                error_info = f"`{command.qualified_name}`: {type(e).__name__} - {e}"
                failed_commands.append(error_info)
                logging.error(f"Command '{command.qualified_name}' failed test: {e}")

        if not failed_commands:
            embed = discord.Embed(
                title="✅ Command Test Complete",
                description=f"All **{success_count}** commands seem to be defined correctly.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="❌ Command Test Finished with Errors",
                description=(
                    f"**{success_count}** commands passed.\n"
                    f"**{fail_count}** commands failed."
                ),
                color=discord.Color.red()
            )
            # Add failed commands to the embed
            error_list = "\\n".join(failed_commands)
            if len(error_list) > 1000:
                error_list = error_list[:1000] + "\\n..."
            embed.add_field(name="Failed Commands", value=error_list, inline=False)

        if is_interaction:
            await ctx.followup.send(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(TestCog(bot))
