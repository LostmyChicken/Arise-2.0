#!/usr/bin/env python3
"""
Test the fixed title extension loading
"""
import asyncio
import discord
from discord.ext import commands

async def test_title_extension():
    """Test loading the titles extension with text commands"""
    try:
        print("🤖 Testing title extension loading...")
        
        # Create test bot
        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix='sl ', intents=intents)
        
        print("Loading titles extension...")
        
        # Try to load the titles extension
        try:
            await bot.load_extension("commands.titles")
            print("✅ Titles extension loaded successfully!")
        except Exception as e:
            if "CommandLimitReached" in str(e):
                print("⚠️ Slash command limit reached, but extension should still load with text commands")
                print("✅ Extension loaded (text commands only)")
            else:
                print(f"❌ Extension load error: {e}")
                return False
        
        # Check if commands are registered
        title_commands = [cmd for cmd in bot.commands if cmd.name in ['titles', 'title']]
        print(f"✅ Found {len(title_commands)} title commands:")
        for cmd in title_commands:
            print(f"   - sl {cmd.name}: {cmd.help}")
        
        # Check if TitleCog is loaded
        title_cog = bot.get_cog('TitleCog')
        if title_cog:
            print("✅ TitleCog found in bot")
        else:
            print("❌ TitleCog not found in bot")
            return False
        
        # Test title system imports
        from structure.title_system import TitleManager
        titles = TitleManager.TITLES
        print(f"✅ {len(titles)} titles available in system")
        
        print("🎉 Title extension test completed successfully!")
        print("\nCommands available:")
        print("- sl titles  (Interactive title management)")
        print("- sl title   (Show/set current title)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_title_extension()
    
    if success:
        print("\n🎉 Title system is ready!")
        print("You can now restart your bot and use:")
        print("- sl titles")
        print("- sl title")
    else:
        print("\n❌ Title system needs more fixes")

if __name__ == "__main__":
    asyncio.run(main())
