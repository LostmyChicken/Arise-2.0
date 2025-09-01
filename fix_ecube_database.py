#!/usr/bin/env python3
"""
Fix Earth Cube Database Migration
Manually adds the ecube column to existing player databases
"""

import asyncio
import aiosqlite
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_database_path():
    """Get the database path from db.json"""
    try:
        with open("db.json", "r") as f:
            return json.load(f).get("player", "data/player.db")
    except Exception:
        return "data/player.db"

async def fix_ecube_column():
    """Add ecube column to existing player database"""
    database_path = get_database_path()
    logging.info(f"🔧 Fixing ecube column in database: {database_path}")
    
    try:
        async with aiosqlite.connect(database_path) as conn:
            # Check if ecube column exists
            cursor = await conn.execute("PRAGMA table_info(players)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            logging.info(f"📊 Current columns: {column_names}")
            
            if 'ecube' not in column_names:
                logging.info("➕ Adding ecube column...")
                await conn.execute("ALTER TABLE players ADD COLUMN ecube INTEGER DEFAULT 0")
                await conn.commit()
                logging.info("✅ Successfully added ecube column!")
                
                # Verify the column was added
                cursor = await conn.execute("PRAGMA table_info(players)")
                columns = await cursor.fetchall()
                new_column_names = [col[1] for col in columns]
                logging.info(f"📊 Updated columns: {new_column_names}")
                
                # Update all existing players to have 0 ecube
                await conn.execute("UPDATE players SET ecube = 0 WHERE ecube IS NULL")
                await conn.commit()
                logging.info("✅ Initialized all existing players with 0 ecube")
                
            else:
                logging.info("✅ ecube column already exists!")
            
            # Verify cube columns are all present
            expected_cubes = ['fcube', 'icube', 'wcube', 'ecube', 'dcube', 'lcube']
            missing_cubes = [cube for cube in expected_cubes if cube not in column_names]
            
            if missing_cubes:
                logging.warning(f"⚠️ Missing cube columns: {missing_cubes}")
                for cube in missing_cubes:
                    try:
                        await conn.execute(f"ALTER TABLE players ADD COLUMN {cube} INTEGER DEFAULT 0")
                        logging.info(f"➕ Added missing {cube} column")
                    except Exception as e:
                        logging.error(f"❌ Failed to add {cube} column: {e}")
                
                await conn.commit()
                logging.info("✅ All cube columns verified/added")
            else:
                logging.info("✅ All cube columns present!")
            
            # Show sample of player data to verify
            cursor = await conn.execute("SELECT id, fcube, icube, wcube, ecube, dcube, lcube FROM players LIMIT 5")
            sample_data = await cursor.fetchall()

            if sample_data:
                logging.info("📋 Sample player cube data:")
                for row in sample_data:
                    user_id, fcube, icube, wcube, ecube, dcube, lcube = row
                    logging.info(f"   User {user_id}: F={fcube}, I={icube}, W={wcube}, E={ecube}, D={dcube}, L={lcube}")
            else:
                logging.info("📋 No player data found in database")
                
    except Exception as e:
        logging.error(f"❌ Error fixing ecube column: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_player_save():
    """Test that player saving works with ecube"""
    logging.info("🧪 Testing player save with ecube...")
    
    try:
        # Import player class
        import sys
        sys.path.append('.')
        from structure.player import Player
        
        # Create a test player
        test_player = Player({
            'id': 999999999999999999,  # Test user ID
            'name': 'Test Player',
            'level': 1,
            'fcube': 10,
            'icube': 20,
            'wcube': 30,
            'ecube': 40,  # Test Earth cubes
            'dcube': 50,
            'lcube': 60
        })
        
        # Try to save the player
        await test_player.save()
        logging.info("✅ Test player save successful!")
        
        # Load the player back
        loaded_player = await Player.load(999999999999999999)
        if loaded_player:
            logging.info(f"✅ Test player loaded: ecube = {loaded_player.ecube}")
            
            # Clean up test player
            await loaded_player.delete()
            logging.info("✅ Test player cleaned up")
        else:
            logging.warning("⚠️ Could not load test player back")
            
    except Exception as e:
        logging.error(f"❌ Error testing player save: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Main function"""
    logging.info("🚀 Starting Earth Cube Database Fix...")
    
    # Fix the database
    success = await fix_ecube_column()
    if not success:
        logging.error("❌ Database fix failed!")
        return
    
    # Test player saving
    success = await test_player_save()
    if not success:
        logging.error("❌ Player save test failed!")
        return
    
    logging.info("🎉 Earth Cube Database Fix Complete!")
    logging.info("✅ All players can now use Earth cubes (ecube)")
    logging.info("✅ Database is ready for Earth element system")

if __name__ == "__main__":
    asyncio.run(main())
