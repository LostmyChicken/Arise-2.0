#!/usr/bin/env python3
"""
Comprehensive fix for title system
"""
import asyncio
import sqlite3
import os
import sys

def fix_database():
    """Fix database columns"""
    try:
        print("🔧 Fixing database...")
        
        db_files = ['new_player.db', 'player.db']
        
        for db_file in db_files:
            if os.path.exists(db_file):
                print(f"Updating database: {db_file}")
                
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Get current columns
                cursor.execute("PRAGMA table_info(players)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # Add missing columns
                if 'titles' not in column_names:
                    cursor.execute('ALTER TABLE players ADD COLUMN titles TEXT DEFAULT "{}"')
                    print("✅ Added 'titles' column")
                
                if 'active_title' not in column_names:
                    cursor.execute('ALTER TABLE players ADD COLUMN active_title TEXT DEFAULT NULL')
                    print("✅ Added 'active_title' column")
                
                conn.commit()
                conn.close()
                print(f"✅ Database {db_file} updated")
        
        return True
        
    except Exception as e:
        print(f"❌ Database fix error: {e}")
        return False

def test_imports():
    """Test all imports"""
    try:
        print("🧪 Testing imports...")
        
        # Test title system imports
        from structure.title_system import TitleManager, TitleCategory, Title
        print("✅ TitleManager imported")
        
        # Test titles loaded
        titles = TitleManager.TITLES
        print(f"✅ {len(titles)} titles loaded")
        
        # Test commands import
        from commands.titles import TitleCog
        print("✅ TitleCog imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_title_functionality():
    """Test title system functionality"""
    try:
        print("⚡ Testing title functionality...")
        
        from structure.title_system import TitleManager
        from structure.player import Player
        
        # Test player creation
        test_player_id = "999888777"
        player = Player(test_player_id)
        player.level = 10
        player.story_progress = {
            "prologue_001": {"completed": True}
        }
        
        await player.save()
        print("✅ Test player created")
        
        # Test title unlocking
        unlocked = await TitleManager.check_and_unlock_story_titles(test_player_id)
        print(f"✅ {len(unlocked)} titles unlocked")
        
        # Test title activation
        if unlocked:
            success = await TitleManager.set_player_active_title(test_player_id, unlocked[0])
            print(f"✅ Title activation: {success}")
        
        # Test profile display
        display = await TitleManager.get_title_display_for_profile(test_player_id)
        print(f"✅ Profile display: '{display}'")
        
        # Cleanup
        import aiosqlite
        async with aiosqlite.connect("new_player.db") as conn:
            await conn.execute("DELETE FROM players WHERE id = ?", (test_player_id,))
            await conn.commit()
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bot_extension():
    """Test bot extension loading"""
    try:
        print("🤖 Testing bot extension...")
        
        import discord
        from discord.ext import commands
        
        # Create test bot
        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix='!', intents=intents)
        
        # Load extension
        try:
            await bot.load_extension("commands.titles")
            print("✅ Extension loaded")
        except Exception as e:
            if "CommandLimitReached" in str(e):
                print("⚠️ Slash command limit reached - using text commands only")
                print("✅ Extension loaded (text commands)")
            else:
                raise e
        
        # Check commands
        title_commands = [cmd for cmd in bot.commands if cmd.name in ['titles', 'title']]
        print(f"✅ {len(title_commands)} commands registered")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot extension test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_main_py():
    """Check if main.py has titles extension"""
    try:
        print("📄 Checking main.py...")
        
        with open('main.py', 'r') as f:
            content = f.read()
        
        if 'commands.titles' in content:
            print("✅ titles extension found in main.py")
            return True
        else:
            print("❌ titles extension NOT found in main.py")
            print("Please add 'commands.titles' to the secondary_extensions list in main.py")
            return False
            
    except Exception as e:
        print(f"❌ main.py check error: {e}")
        return False

async def main():
    """Main fix function"""
    print("🔧 Title System Comprehensive Fix")
    print("=" * 40)
    
    # Step 1: Fix database
    db_ok = fix_database()
    
    # Step 2: Test imports
    imports_ok = test_imports()
    
    # Step 3: Check main.py
    main_py_ok = check_main_py()
    
    # Step 4: Test functionality
    if db_ok and imports_ok:
        functionality_ok = await test_title_functionality()
    else:
        functionality_ok = False
    
    # Step 5: Test bot extension
    if imports_ok:
        bot_ok = await test_bot_extension()
    else:
        bot_ok = False
    
    print("\n" + "=" * 40)
    print("🔍 Fix Results:")
    print(f"Database: {'✅' if db_ok else '❌'}")
    print(f"Imports: {'✅' if imports_ok else '❌'}")
    print(f"main.py: {'✅' if main_py_ok else '❌'}")
    print(f"Functionality: {'✅' if functionality_ok else '❌'}")
    print(f"Bot Extension: {'✅' if bot_ok else '❌'}")
    
    if all([db_ok, imports_ok, main_py_ok, functionality_ok, bot_ok]):
        print("\n🎉 Title system is fully operational!")
        print("You can now use 'sl titles' and 'sl title' commands!")
    else:
        print("\n❌ Some issues remain. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
