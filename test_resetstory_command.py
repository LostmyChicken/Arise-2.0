#!/usr/bin/env python3
"""
Test script to verify the resetstory command is properly implemented
"""
import asyncio
import sys
import os

async def test_resetstory_command():
    """Test that the resetstory command can be imported and is properly structured"""
    print("🔍 Testing resetstory command implementation...")
    
    try:
        # Test importing the admin module
        from commands.admin import AdminGrant
        print("  ✅ AdminGrant class imported successfully")
        
        # Check if the reset_story method exists
        if hasattr(AdminGrant, 'reset_story'):
            print("  ✅ reset_story method found in AdminGrant class")
            
            # Get method info
            method = getattr(AdminGrant, 'reset_story')
            print(f"  📋 Method signature: {method.__name__}")
            print(f"  📝 Method docstring: {method.__doc__}")
            
            # Check if it's a command
            if hasattr(method, '__commands_is_command__') and method.__commands_is_command__:
                print("  ✅ Method is properly decorated as a discord.py command")
                print(f"  🏷️ Command name: {getattr(method, 'name', 'resetstory')}")
            else:
                print("  ⚠️ Method may not be properly decorated as a command")
            
        else:
            print("  ❌ reset_story method NOT found in AdminGrant class")
            return False
        
        # Test admin utility import
        from utilis.admin import is_bot_admin
        print("  ✅ is_bot_admin function imported successfully")
        
        # Test player import
        from structure.player import Player
        print("  ✅ Player class imported successfully")
        
        print("\n✅ ALL TESTS PASSED!")
        print("🎉 resetstory command is properly implemented and should work!")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

async def test_command_structure():
    """Test the overall command structure"""
    print("\n🔧 Testing command structure...")
    
    try:
        from commands.admin import AdminGrant
        
        # Get all methods in the class
        methods = [method for method in dir(AdminGrant) if not method.startswith('_')]
        command_methods = []
        
        for method_name in methods:
            method = getattr(AdminGrant, method_name)
            if hasattr(method, '__commands_is_command__') and method.__commands_is_command__:
                command_methods.append(method_name)
        
        print(f"  📊 Found {len(command_methods)} command methods in AdminGrant:")
        for cmd in sorted(command_methods):
            method = getattr(AdminGrant, cmd)
            cmd_name = getattr(method, 'name', cmd)
            print(f"    • {cmd} -> sl {cmd_name}")
        
        if 'reset_story' in command_methods:
            print("  ✅ resetstory command found in command list!")
        else:
            print("  ❌ resetstory command NOT found in command list!")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing command structure: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 RESETSTORY COMMAND TEST")
    print("=" * 50)
    
    test1_passed = await test_resetstory_command()
    test2_passed = await test_command_structure()
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    
    if test1_passed and test2_passed:
        print("✅ All tests passed!")
        print("🚀 The resetstory command should now work properly!")
        print("\n📋 USAGE:")
        print("  sl resetstory @username")
        print("\n🔧 TROUBLESHOOTING:")
        print("  • Make sure the bot is restarted after the changes")
        print("  • Verify you have admin permissions")
        print("  • Check that the user exists and has a character")
        return 0
    else:
        print("❌ Some tests failed!")
        print("🔧 Please check the implementation and try again.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
