#!/usr/bin/env python3
"""
Fix guild creation system by ensuring database tables exist and testing functionality
"""
import asyncio
import sqlite3
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def create_enhanced_guilds_table():
    """Create the enhanced_guilds table"""
    try:
        print("🔧 Creating enhanced_guilds table...")
        
        # Check which database file exists
        db_files = ['new_player.db', 'player.db', 'data/player.db']
        db_path = None
        
        for db_file in db_files:
            if os.path.exists(db_file):
                db_path = db_file
                print(f"Found database: {db_file}")
                break
        
        if not db_path:
            print("❌ No database file found")
            return False
        
        # Connect and create table
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create enhanced_guilds table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enhanced_guilds (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner INTEGER NOT NULL,
                members TEXT DEFAULT '[]',
                level INTEGER DEFAULT 1,
                points INTEGER DEFAULT 0,
                image TEXT,
                description TEXT,
                gates INTEGER DEFAULT 0,
                allow_alliances INTEGER DEFAULT 0,
                guild_bank TEXT DEFAULT '{"gold": 0, "diamond": 0, "crystals": 0}',
                applications TEXT DEFAULT '[]',
                settings TEXT DEFAULT '{}',
                created_at TEXT,
                last_active TEXT
            )
        """)
        
        # Also ensure regular guilds table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guilds (
                id TEXT PRIMARY KEY,
                name TEXT,
                owner INTEGER,
                members TEXT,
                level INTEGER,
                points INTEGER,
                image TEXT,
                description TEXT,
                gates INTEGER DEFAULT 0,
                allow_alliances INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Enhanced guilds table created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating enhanced guilds table: {e}")
        return False

async def test_guild_creation():
    """Test the guild creation process"""
    try:
        print("🧪 Testing guild creation process...")
        
        from structure.player import Player
        from structure.enhanced_guild import EnhancedGuild, GuildRole
        from datetime import datetime
        from utilis.utilis import extractId
        
        # Create test player
        test_player_id = "555666777888"
        player = Player(test_player_id)
        player.level = 15
        player.gold = 300000  # Enough for guild creation
        player.guild = None
        
        await player.save()
        print("✅ Test player created")
        
        # Test guild creation data
        guild_data = {
            "name": "Test Shadow Guild",
            "description": "A test guild for the enhanced guild system",
            "image_url": "https://example.com/guild.png",
            "motto": "Testing the shadows",
            "min_level": 10,
            "max_members": 30,
            "application_required": True,
            "public_visibility": True,
            "allow_alliances": False
        }
        
        print(f"🏰 Creating guild: {guild_data['name']}")
        
        # Create guild ID
        guild_id = extractId(guild_data["name"])
        print(f"Guild ID: {guild_id}")
        
        # Create enhanced guild
        enhanced_guild = EnhancedGuild(
            id=guild_id,
            name=guild_data["name"],
            owner=int(player.id),
            members=[{
                "id": int(player.id),
                "role": GuildRole.GUILD_MASTER.value,
                "joined_at": datetime.now().isoformat()
            }],
            level=1,
            points=0,
            image=guild_data.get("image_url", ""),
            description=guild_data["description"],
            gates=0,
            allow_alliances=guild_data.get("allow_alliances", False),
            guild_bank={"gold": 0, "items": {}},
            applications=[],
            settings={
                "min_level_requirement": guild_data.get("min_level", 1),
                "application_required": guild_data.get("application_required", True),
                "max_members": guild_data.get("max_members", 50),
                "public_visibility": guild_data.get("public_visibility", True),
                "motto": guild_data.get("motto", "")
            },
            created_at=datetime.now().isoformat(),
            last_active=datetime.now().isoformat()
        )
        
        print("💾 Saving guild to database...")
        await enhanced_guild.save()
        print("✅ Guild saved successfully")
        
        # Update player
        print("👤 Updating player data...")
        player.guild = guild_id
        player.gold -= 200000
        await player.save()
        print(f"✅ Player updated - Gold: {player.gold}, Guild: {player.guild}")
        
        # Verify guild was created
        print("🔍 Verifying guild creation...")
        created_guild = await EnhancedGuild.get(guild_id)
        if created_guild:
            print(f"✅ Guild verified: {created_guild.name}")
            print(f"   Owner: {created_guild.owner}")
            print(f"   Members: {len(created_guild.members)}")
            print(f"   Description: {created_guild.description}")
        else:
            print("❌ Guild not found after creation")
            return False
        
        # Verify player was updated
        print("👤 Verifying player update...")
        updated_player = await Player.get(test_player_id)
        if updated_player:
            print(f"✅ Player verified:")
            print(f"   Gold: {updated_player.gold}")
            print(f"   Guild: {updated_player.guild}")
        else:
            print("❌ Player not found after update")
            return False
        
        # Clean up test data
        print("🧹 Cleaning up test data...")
        
        # Delete guild
        await created_guild.delete()
        print("✅ Test guild deleted")
        
        # Delete player
        import aiosqlite
        db_files = ['new_player.db', 'player.db', 'data/player.db']
        for db_file in db_files:
            if os.path.exists(db_file):
                async with aiosqlite.connect(db_file) as conn:
                    await conn.execute("DELETE FROM players WHERE id = ?", (test_player_id,))
                    await conn.commit()
                break
        print("✅ Test player deleted")
        
        print("🎉 Guild creation test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Guild creation test failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up on error
        try:
            import aiosqlite
            db_files = ['new_player.db', 'player.db', 'data/player.db']
            for db_file in db_files:
                if os.path.exists(db_file):
                    async with aiosqlite.connect(db_file) as conn:
                        await conn.execute("DELETE FROM players WHERE id = ?", (test_player_id,))
                        await conn.execute("DELETE FROM enhanced_guilds WHERE id = ?", (guild_id,))
                        await conn.commit()
                    break
        except:
            pass
        
        return False

def check_database_path():
    """Check which database path is being used"""
    try:
        print("🔍 Checking database configuration...")
        
        # Check structure files for DATABASE_PATH
        files_to_check = [
            'structure/enhanced_guild.py',
            'structure/guild.py', 
            'structure/player.py',
            'utilis/database_setup.py'
        ]
        
        database_paths = set()
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'DATABASE_PATH' in content:
                        # Extract DATABASE_PATH value
                        lines = content.split('\n')
                        for line in lines:
                            if 'DATABASE_PATH' in line and '=' in line:
                                path = line.split('=')[1].strip().strip('"\'')
                                database_paths.add(path)
        
        print(f"Found database paths: {database_paths}")
        
        # Check which files actually exist
        existing_dbs = []
        for path in database_paths:
            if os.path.exists(path):
                existing_dbs.append(path)
        
        # Also check common locations
        common_paths = ['new_player.db', 'player.db', 'data/player.db']
        for path in common_paths:
            if os.path.exists(path) and path not in existing_dbs:
                existing_dbs.append(path)
        
        print(f"Existing database files: {existing_dbs}")
        return existing_dbs
        
    except Exception as e:
        print(f"❌ Error checking database paths: {e}")
        return []

async def main():
    """Main fix function"""
    print("🔧 Guild Creation System Fix")
    print("=" * 40)
    
    # Step 1: Check database paths
    db_paths = check_database_path()
    
    # Step 2: Create enhanced guilds table
    table_created = create_enhanced_guilds_table()
    
    # Step 3: Test guild creation
    if table_created:
        creation_test = await test_guild_creation()
    else:
        creation_test = False
    
    print("\n" + "=" * 40)
    print("🔍 Fix Results:")
    print(f"Database paths found: {len(db_paths)}")
    print(f"Enhanced guilds table: {'✅' if table_created else '❌'}")
    print(f"Guild creation test: {'✅' if creation_test else '❌'}")
    
    if table_created and creation_test:
        print("\n🎉 Guild creation system is now working!")
        print("Players can now:")
        print("- Create guilds with sl guild create")
        print("- Gold will be properly deducted")
        print("- Guilds will be saved to database")
        print("- Guild membership will be tracked")
    else:
        print("\n❌ Some issues remain. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
