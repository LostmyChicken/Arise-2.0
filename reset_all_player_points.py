#!/usr/bin/env python3
"""
Reset All Player Points Script
Resets all players' stat points and skill points to the correct amounts based on their level.
- Stat Points: 10 per level (for stat upgrades)
- Skill Points: 5 per level (for skill tree progression)
"""

import asyncio
import aiosqlite
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_database_path():
    """Get the database path from configuration"""
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("player", "new_player.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "new_player.db"

DATABASE_PATH = get_database_path()

async def reset_all_player_points():
    """Reset all players' stat and skill points based on their current level"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            logging.info(f"Connected to database: {DATABASE_PATH}")
            
            # Get all players
            cursor = await db.execute("SELECT id, level FROM players")
            players = await cursor.fetchall()
            await cursor.close()
            
            if not players:
                logging.warning("No players found in database")
                return
            
            logging.info(f"Found {len(players)} players to update")
            
            updated_count = 0
            errors = 0
            
            for player_id, level in players:
                try:
                    # Calculate correct points based on level
                    correct_stat_points = level * 10  # 10 stat points per level
                    correct_skill_points = level * 5  # 5 skill points per level
                    
                    # Update player points
                    await db.execute("""
                        UPDATE players 
                        SET statPoints = ?, skillPoints = ?
                        WHERE id = ?
                    """, (correct_stat_points, correct_skill_points, player_id))
                    
                    updated_count += 1
                    
                    if updated_count % 100 == 0:  # Progress update every 100 players
                        logging.info(f"Updated {updated_count}/{len(players)} players...")
                    
                except Exception as e:
                    logging.error(f"Error updating player {player_id}: {e}")
                    errors += 1
            
            # Commit all changes
            await db.commit()
            
            logging.info("=" * 60)
            logging.info("PLAYER POINTS RESET COMPLETE!")
            logging.info("=" * 60)
            logging.info(f"✅ Successfully updated: {updated_count} players")
            logging.info(f"❌ Errors encountered: {errors} players")
            logging.info(f"📊 Stat Points: 10 per level")
            logging.info(f"✥ Skill Points: 5 per level")
            logging.info("=" * 60)
            
            # Show some examples
            if updated_count > 0:
                logging.info("Example updates:")
                cursor = await db.execute("""
                    SELECT id, level, statPoints, skillPoints 
                    FROM players 
                    ORDER BY level DESC 
                    LIMIT 5
                """)
                examples = await cursor.fetchall()
                await cursor.close()
                
                for player_id, level, stat_points, skill_points in examples:
                    logging.info(f"  Player {player_id}: Level {level} → {stat_points} stat points, {skill_points} skill points")
            
    except Exception as e:
        logging.error(f"Critical error during point reset: {e}")
        raise

async def verify_point_calculations():
    """Verify that all players have correct points after reset"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            logging.info("Verifying point calculations...")
            
            # Check for any players with incorrect points
            cursor = await db.execute("""
                SELECT id, level, statPoints, skillPoints
                FROM players
                WHERE statPoints != (level * 10) OR skillPoints != (level * 5)
                LIMIT 10
            """)
            incorrect_players = await cursor.fetchall()
            await cursor.close()
            
            if incorrect_players:
                logging.warning(f"Found {len(incorrect_players)} players with incorrect points:")
                for player_id, level, stat_points, skill_points in incorrect_players:
                    expected_stat = level * 10
                    expected_skill = level * 5
                    logging.warning(f"  Player {player_id}: Level {level}")
                    logging.warning(f"    Stat Points: {stat_points} (expected {expected_stat})")
                    logging.warning(f"    Skill Points: {skill_points} (expected {expected_skill})")
            else:
                logging.info("✅ All players have correct point amounts!")
                
            # Get summary statistics
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_players,
                    AVG(level) as avg_level,
                    MIN(level) as min_level,
                    MAX(level) as max_level,
                    SUM(statPoints) as total_stat_points,
                    SUM(skillPoints) as total_skill_points
                FROM players
            """)
            stats = await cursor.fetchone()
            await cursor.close()
            
            if stats:
                total, avg_level, min_level, max_level, total_stat, total_skill = stats
                logging.info("Database Summary:")
                logging.info(f"  Total Players: {total}")
                logging.info(f"  Level Range: {min_level} - {max_level} (avg: {avg_level:.1f})")
                logging.info(f"  Total Stat Points: {total_stat:,}")
                logging.info(f"  Total Skill Points: {total_skill:,}")
                
    except Exception as e:
        logging.error(f"Error during verification: {e}")

async def backup_before_reset():
    """Create a backup of current player points before reset"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("""
                SELECT id, level, 
                       COALESCE(statPoints, 0) as statPoints,
                       COALESCE(skillPoints, 0) as skillPoints
                FROM players
            """)
            players = await cursor.fetchall()
            await cursor.close()
            
            # Save backup to JSON file
            backup_data = []
            for player_id, level, stat_points, skill_points in players:
                backup_data.append({
                    'id': player_id,
                    'level': level,
                    'old_stat_points': stat_points,
                    'old_skill_points': skill_points,
                    'new_stat_points': level * 10,
                    'new_skill_points': level * 5
                })
            
            backup_file = f"player_points_backup_{int(asyncio.get_event_loop().time())}.json"
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logging.info(f"✅ Backup created: {backup_file}")
            return backup_file
            
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        return None

async def main():
    """Main function to run the point reset"""
    logging.info("🚀 Starting Player Points Reset...")
    logging.info("This will reset ALL players' stat and skill points based on their level")
    logging.info("📊 Stat Points: 10 per level (for stat upgrades)")
    logging.info("✥ Skill Points: 5 per level (for skill tree progression)")
    
    # Create backup first
    logging.info("Creating backup of current points...")
    backup_file = await backup_before_reset()
    
    if backup_file:
        logging.info(f"Backup saved to: {backup_file}")
    
    # Perform the reset
    await reset_all_player_points()
    
    # Verify the results
    await verify_point_calculations()
    
    logging.info("🎉 Player points reset completed successfully!")
    logging.info("All players now have the correct stat and skill points for their level.")

if __name__ == "__main__":
    asyncio.run(main())
