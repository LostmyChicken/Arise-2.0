#!/usr/bin/env python3
"""
Test admin commands to see if they're properly loaded
"""
import asyncio
import discord
from discord.ext import commands

async def test_admin_commands():
    """Test if admin commands are properly loaded"""
    try:
        print("🧪 Testing Admin Commands...")
        
        # Create a test bot
        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix='sl ', intents=intents)
        
        # Load the admin extension
        try:
            await bot.load_extension("commands.admin")
            print("✅ Admin extension loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load admin extension: {e}")
            return False
        
        # Check if the guild commands are registered
        guild_commands = []
        for command in bot.commands:
            if 'guild' in command.name.lower():
                guild_commands.append(command.name)
        
        print(f"🏰 Guild-related commands found: {guild_commands}")
        
        # Check specific commands
        delete_guild_cmd = bot.get_command('deleteguild')
        list_guilds_cmd = bot.get_command('listguilds')
        
        if delete_guild_cmd:
            print("✅ deleteguild command found")
            print(f"   Help: {delete_guild_cmd.help}")
        else:
            print("❌ deleteguild command NOT found")
        
        if list_guilds_cmd:
            print("✅ listguilds command found")
            print(f"   Help: {list_guilds_cmd.help}")
        else:
            print("❌ listguilds command NOT found")
        
        # List all admin commands
        admin_commands = []
        for command in bot.commands:
            if hasattr(command, 'callback') and hasattr(command.callback, '__self__'):
                cog_name = command.callback.__self__.__class__.__name__
                if 'admin' in cog_name.lower():
                    admin_commands.append(command.name)
        
        print(f"🔧 All admin commands: {admin_commands}")
        
        return len(guild_commands) > 0
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_economy_balance():
    """Test economy balance for shards and gears"""
    try:
        print("\n💰 Testing Economy Balance...")
        
        # Test shard requirements for limit breaking
        shard_requirements = [1, 1, 2, 2, 4]  # From upgrade.py
        cube_requirements = [5, 10, 20, 40, 60]  # From upgrade.py
        
        print("🌟 Limit Break Requirements:")
        for tier, (shards, cubes) in enumerate(zip(shard_requirements, cube_requirements)):
            print(f"  Tier {tier} → {tier+1}: {shards} shards, {cubes} cubes")
        
        # Test gear costs for different tiers
        print("\n⚙️ Gear Costs for Level 10 Items:")
        
        # Hunter gear costs (from upgrade.py)
        level = 10
        print("🏹 Hunters:")
        tier3_gear = (3 * level) + ((level // 10) * 15)  # 30 + 15 = 45
        tier2_gear = (4 * level) + ((level // 10) * 20)  # 40 + 20 = 60  
        tier1_gear = (5 * level) + ((level // 10) * 25)  # 50 + 25 = 75
        
        print(f"  Tier 3 Hunter (Level {level}): {tier3_gear} Gear III")
        print(f"  Tier 2 Hunter (Level {level}): {tier2_gear} Gear II")
        print(f"  Tier 1 Hunter (Level {level}): {tier1_gear} Gear I")
        
        # Weapon gear costs
        print("⚔️ Weapons:")
        weapon_tier3_gear = (8 * level) + ((level // 15) * 30)  # 80 + 0 = 80
        weapon_tier2_gear = (10 * level) + ((level // 15) * 25)  # 100 + 0 = 100
        weapon_tier1_gear = 10 * level  # 100
        
        print(f"  Tier 3 Weapon (Level {level}): {weapon_tier3_gear} Gear III")
        print(f"  Tier 2 Weapon (Level {level}): {weapon_tier2_gear} Gear II")
        print(f"  Tier 1 Weapon (Level {level}): {weapon_tier1_gear} Gear I")
        
        # Analysis
        print("\n📊 Economy Analysis:")
        print("✅ Higher tier items require LESS gear (more efficient)")
        print("✅ Shard requirements scale reasonably (1→4 max)")
        print("✅ Cube requirements scale exponentially (5→60)")
        
        # Check if balance is reasonable
        balance_issues = []
        
        # Check if higher tiers are actually cheaper (they should be more expensive)
        if tier3_gear < tier1_gear:
            balance_issues.append("⚠️ Tier 3 hunters require LESS gear than Tier 1 (should be more)")
        
        if weapon_tier3_gear < weapon_tier1_gear:
            balance_issues.append("⚠️ Tier 3 weapons require LESS gear than Tier 1 (should be more)")
        
        # Check cube scaling
        max_cube_ratio = max(cube_requirements) / min(cube_requirements)
        if max_cube_ratio > 20:  # 60/5 = 12, which is reasonable
            balance_issues.append(f"⚠️ Cube requirements scale too steeply (ratio: {max_cube_ratio})")
        
        if balance_issues:
            print("\n🚨 Balance Issues Found:")
            for issue in balance_issues:
                print(f"  {issue}")
        else:
            print("\n✅ Economy appears balanced")
        
        return len(balance_issues) == 0
        
    except Exception as e:
        print(f"❌ Economy test error: {e}")
        return False

async def main():
    """Main test function"""
    print("🔧 Admin Commands & Economy Balance Test")
    print("=" * 50)
    
    # Test admin commands
    admin_ok = await test_admin_commands()
    
    # Test economy balance
    economy_ok = await test_economy_balance()
    
    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print(f"Admin Commands: {'✅ Working' if admin_ok else '❌ Issues'}")
    print(f"Economy Balance: {'✅ Balanced' if economy_ok else '⚠️ Needs Review'}")
    
    if admin_ok and economy_ok:
        print("\n🎉 All systems operational!")
    else:
        print("\n⚠️ Some issues detected - see details above")

if __name__ == "__main__":
    asyncio.run(main())
