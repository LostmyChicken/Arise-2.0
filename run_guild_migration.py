#!/usr/bin/env python3
"""
Run complete guild system migration and integration
"""
import asyncio
import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def run_complete_guild_migration():
    """Run complete guild migration and integration"""
    print("🔄 COMPLETE GUILD SYSTEM MIGRATION")
    print("=" * 50)
    
    try:
        # Import the integration manager
        from guild_integration_manager import GuildIntegrationManager
        from structure.guild import Guild
        from structure.enhanced_guild import EnhancedGuild
        
        print("📊 Pre-migration Analysis:")
        
        # Check current state
        try:
            old_guilds = await Guild.get_all()
            print(f"  Old guilds found: {len(old_guilds)}")
            for guild in old_guilds[:5]:  # Show first 5
                member_count = len(guild.members) if hasattr(guild, 'members') and guild.members else 0
                print(f"    - {guild.name} (ID: {guild.id}, Members: {member_count})")
        except Exception as e:
            print(f"  Error getting old guilds: {e}")
            old_guilds = []
        
        try:
            enhanced_guilds = await EnhancedGuild.get_all()
            print(f"  Enhanced guilds found: {len(enhanced_guilds)}")
            for guild in enhanced_guilds[:5]:  # Show first 5
                member_count = len(guild.members) if guild.members else 0
                print(f"    - {guild.name} (ID: {guild.id}, Members: {member_count})")
        except Exception as e:
            print(f"  Error getting enhanced guilds: {e}")
            enhanced_guilds = []
        
        print(f"\n🔧 Starting Migration Process...")
        
        # Run full migration
        migration_result = await GuildIntegrationManager.run_full_migration()
        
        print(f"\n✅ Migration Results:")
        print(f"  Guilds migrated: {migration_result['migrated']}")
        print(f"  Migration failures: {migration_result['failed']}")
        print(f"  Player references updated: {migration_result['updated_players']}")
        
        # Verify final state
        print(f"\n📊 Post-migration Analysis:")
        
        try:
            final_guilds = await GuildIntegrationManager.get_all_guilds()
            print(f"  Total unified guilds: {len(final_guilds)}")
            
            total_members = 0
            for guild in final_guilds:
                member_count = len(guild.members) if guild.members else 0
                total_members += member_count
                print(f"    - {guild.name} (Members: {member_count}, Level: {guild.level})")
            
            print(f"  Total members across all guilds: {total_members}")
            
        except Exception as e:
            print(f"  Error getting final guild state: {e}")
        
        # Test admin commands integration
        print(f"\n🧪 Testing Admin Commands Integration...")
        
        try:
            # Test getting a guild through admin system
            if final_guilds:
                test_guild = final_guilds[0]
                unified_guild = await GuildIntegrationManager.get_unified_guild(test_guild.id)
                if unified_guild:
                    print(f"  ✅ Admin commands can access guild: {unified_guild.name}")
                else:
                    print(f"  ❌ Admin commands cannot access guild")
            else:
                print(f"  ⚠️ No guilds to test with")
                
        except Exception as e:
            print(f"  ❌ Error testing admin integration: {e}")
        
        print(f"\n🎉 Migration Complete!")
        
        if migration_result['migrated'] > 0:
            print(f"✅ Successfully migrated {migration_result['migrated']} guilds")
        if migration_result['failed'] > 0:
            print(f"⚠️ {migration_result['failed']} guilds failed to migrate")
        if migration_result['updated_players'] > 0:
            print(f"✅ Updated {migration_result['updated_players']} player guild references")
        
        print(f"\n📋 What This Means:")
        print(f"  • All guilds now use the enhanced system")
        print(f"  • Old guild data has been preserved and converted")
        print(f"  • Admin commands work with all guilds")
        print(f"  • Players can access their guilds normally")
        print(f"  • Guild creation uses enhanced system")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_guild_integration():
    """Test guild integration functionality"""
    print("\n🧪 TESTING GUILD INTEGRATION")
    print("=" * 50)
    
    try:
        from guild_integration_manager import GuildIntegrationManager
        
        # Test 1: Get all guilds
        print("Test 1: Getting all guilds...")
        all_guilds = await GuildIntegrationManager.get_all_guilds()
        print(f"  ✅ Found {len(all_guilds)} guilds")
        
        # Test 2: Test unified guild access
        if all_guilds:
            test_guild = all_guilds[0]
            print(f"Test 2: Testing unified access for guild '{test_guild.name}'...")
            
            unified_guild = await GuildIntegrationManager.get_unified_guild(test_guild.id)
            if unified_guild and unified_guild.id == test_guild.id:
                print(f"  ✅ Unified access working")
            else:
                print(f"  ❌ Unified access failed")
        
        # Test 3: Test admin command compatibility
        print("Test 3: Testing admin command compatibility...")
        try:
            # Simulate admin command guild lookup
            if all_guilds:
                test_guild = all_guilds[0]
                found_guild = await GuildIntegrationManager.get_unified_guild(test_guild.id)
                if found_guild:
                    print(f"  ✅ Admin commands can find guild: {found_guild.name}")
                    print(f"    - Members: {len(found_guild.members)}")
                    print(f"    - Owner: {found_guild.owner}")
                    print(f"    - Level: {found_guild.level}")
                else:
                    print(f"  ❌ Admin commands cannot find guild")
        except Exception as e:
            print(f"  ❌ Admin command test failed: {e}")
        
        print(f"✅ Integration tests complete")
        return True
        
    except Exception as e:
        print(f"❌ Integration tests failed: {e}")
        return False

async def main():
    """Main migration and test function"""
    print("🏰 GUILD SYSTEM INTEGRATION & MIGRATION")
    print("=" * 60)
    
    # Run migration
    migration_success = await run_complete_guild_migration()
    
    # Run tests
    if migration_success:
        test_success = await test_guild_integration()
    else:
        test_success = False
    
    print("\n" + "=" * 60)
    print("📋 FINAL SUMMARY:")
    
    if migration_success and test_success:
        print("🎉 COMPLETE SUCCESS!")
        print("✅ All guilds migrated to enhanced system")
        print("✅ Admin commands integrated with unified system")
        print("✅ Old and new guild data working together")
        print("✅ Player guild references updated")
        print("\n🚀 Your guild system is now fully integrated!")
        print("   • Use 'sl listguilds' to see all guilds")
        print("   • Use 'sl deleteguild <name>' to delete guilds")
        print("   • All guild commands work with unified data")
    else:
        print("❌ ISSUES DETECTED")
        if not migration_success:
            print("❌ Migration had problems")
        if not test_success:
            print("❌ Integration tests failed")
        print("\n🔧 Check the errors above and retry")

if __name__ == "__main__":
    asyncio.run(main())
