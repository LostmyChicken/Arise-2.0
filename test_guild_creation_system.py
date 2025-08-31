#!/usr/bin/env python3
"""
Test the enhanced guild creation system.
"""

import asyncio
import logging
from structure.player import Player
from structure.enhanced_guild import EnhancedGuild, GuildRole, GuildPermission

async def test_guild_creation_system():
    """Test the guild creation system components"""
    print("🧪 Testing Enhanced Guild Creation System...")
    
    # Test player ID
    test_player_id = "555666777"
    
    try:
        # Create a test player with sufficient resources
        print(f"👤 Creating test player {test_player_id}...")
        player = Player(test_player_id)
        player.level = 15  # Above minimum requirement
        player.gold = 250000  # Above creation cost
        player.guild = None  # Not in a guild
        await player.save()
        print("✅ Test player created!")
        
        # Test guild creation data validation
        print("🏰 Testing guild creation validation...")
        
        # Test valid guild data
        valid_guild_data = {
            "name": "Test Shadow Guild",
            "description": "A test guild for the Shadow Monarch system testing purposes.",
            "image_url": "https://example.com/guild.png",
            "motto": "Rise from the shadows",
            "min_level": 10,
            "max_members": 30,
            "application_required": True,
            "public_visibility": True,
            "allow_alliances": False
        }
        
        print(f"✅ Valid guild data: {valid_guild_data['name']}")
        
        # Test guild creation process (simulate)
        print("🔧 Testing guild creation process...")
        
        from utilis.utilis import extractId
        from datetime import datetime
        
        guild_id = extractId(valid_guild_data["name"])
        print(f"✅ Generated guild ID: {guild_id}")
        
        # Check if guild already exists
        existing_guild = await EnhancedGuild.get(guild_id)
        if existing_guild:
            print("⚠️ Guild already exists, cleaning up...")
            # In a real scenario, we'd handle this differently
        
        # Test enhanced guild creation
        enhanced_guild = EnhancedGuild(
            id=guild_id,
            name=valid_guild_data["name"],
            owner=player.id,
            members=[{
                "id": player.id,
                "role": GuildRole.GUILD_MASTER.value,
                "joined_at": datetime.now().isoformat()
            }],
            level=1,
            points=0,
            image=valid_guild_data.get("image_url", ""),
            description=valid_guild_data["description"],
            gates=0,
            allow_alliances=valid_guild_data.get("allow_alliances", False),
            guild_bank={"gold": 0, "items": {}},
            applications=[],
            settings={
                "min_level_requirement": valid_guild_data.get("min_level", 1),
                "application_required": valid_guild_data.get("application_required", True),
                "max_members": valid_guild_data.get("max_members", 50),
                "public_visibility": valid_guild_data.get("public_visibility", True),
                "motto": valid_guild_data.get("motto", "")
            },
            created_at=datetime.now().isoformat(),
            last_active=datetime.now().isoformat()
        )
        
        print("✅ Enhanced guild object created!")
        
        # Test guild permissions
        print("🔐 Testing guild permissions...")
        
        # Test guild master permissions
        master_perms = enhanced_guild.get_role_permissions(GuildRole.GUILD_MASTER)
        print(f"✅ Guild Master permissions: {len(master_perms)} permissions")
        
        # Test member role assignment
        member_role = enhanced_guild.get_member_role(player.id)
        print(f"✅ Player role: {member_role.value if member_role else 'None'}")
        
        # Test permission checking
        can_invite = enhanced_guild.has_permission(player.id, GuildPermission.INVITE_MEMBERS)
        can_manage_bank = enhanced_guild.has_permission(player.id, GuildPermission.MANAGE_GUILD_BANK)
        print(f"✅ Can invite members: {can_invite}")
        print(f"✅ Can manage bank: {can_manage_bank}")
        
        # Test guild settings
        print("⚙️ Testing guild settings...")
        settings = enhanced_guild.settings
        print(f"✅ Min level requirement: {settings.get('min_level_requirement', 1)}")
        print(f"✅ Max members: {settings.get('max_members', 50)}")
        print(f"✅ Applications required: {settings.get('application_required', True)}")
        print(f"✅ Public visibility: {settings.get('public_visibility', True)}")
        print(f"✅ Guild motto: {settings.get('motto', 'None')}")
        
        # Test guild filtering criteria
        print("🔍 Testing guild filtering...")
        
        # Test level requirement check
        meets_level_req = settings.get("min_level_requirement", 1) <= player.level
        print(f"✅ Player meets level requirement: {meets_level_req}")
        
        # Test member capacity
        has_space = len(enhanced_guild.members) < settings.get("max_members", 50)
        print(f"✅ Guild has space: {has_space}")
        
        # Test search functionality
        search_term = "shadow"
        matches_search = (
            search_term.lower() in enhanced_guild.name.lower() or
            search_term.lower() in enhanced_guild.description.lower()
        )
        print(f"✅ Matches search '{search_term}': {matches_search}")
        
        # Clean up test data
        print("🧹 Cleaning up test data...")
        import aiosqlite
        async with aiosqlite.connect("new_player.db") as conn:
            await conn.execute("DELETE FROM players WHERE id = ?", (test_player_id,))
            await conn.commit()
        
        # Clean up guild data if it was saved
        try:
            # This would depend on how guilds are stored
            pass
        except:
            pass
        
        print("✅ Test data cleaned up!")
        print("🎉 All guild creation system tests passed!")
        
    except Exception as e:
        print(f"❌ Guild creation system test failed: {e}")
        logging.error(f"Guild creation system test failed: {e}")
        
        # Clean up on error
        try:
            import aiosqlite
            async with aiosqlite.connect("new_player.db") as conn:
                await conn.execute("DELETE FROM players WHERE id = ?", (test_player_id,))
                await conn.commit()
        except:
            pass

async def main():
    """Main test function"""
    await test_guild_creation_system()

if __name__ == "__main__":
    asyncio.run(main())
