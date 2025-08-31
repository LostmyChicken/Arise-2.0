#!/usr/bin/env python3
"""
Test loading the titles extension in a bot
"""
import asyncio
import discord
from discord.ext import commands

async def test_extension_load():
    """Test loading the titles extension"""
    try:
        print("Creating test bot...")
        
        # Create a minimal bot for testing
        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix='!', intents=intents)
        
        print("Loading titles extension...")
        
        # Try to load the titles extension
        await bot.load_extension("commands.titles")
        print("✅ Titles extension loaded successfully!")
        
        # Check if commands are registered
        title_commands = [cmd for cmd in bot.commands if cmd.name in ['titles', 'title']]
        print(f"✅ Found {len(title_commands)} title commands:")
        for cmd in title_commands:
            print(f"   - {cmd.name}: {cmd.help}")
        
        # Test TitleCog
        title_cog = bot.get_cog('TitleCog')
        if title_cog:
            print("✅ TitleCog found in bot")
        else:
            print("❌ TitleCog not found in bot")
        
        print("🎉 Extension test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Extension load error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    await test_extension_load()

if __name__ == "__main__":
    asyncio.run(main())
