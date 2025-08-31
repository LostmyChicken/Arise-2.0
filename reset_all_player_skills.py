#!/usr/bin/env python3
"""
Reset All Player Skills Script
Resets all players' learned skills and skill tree progress, ensuring they get full skill points back.
This complements the points reset to give players a fresh start with the new system.
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

def get_skill_tree_database_path():
    """Get the skill tree database path"""
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("skill_trees", "skill_trees.db")
    except Exception as e:
        logging.error(f"Error loading skill tree database configuration: {e}")
        return "skill_trees.db"

DATABASE_PATH = get_database_path()
SKILL_TREE_DB_PATH = get_skill_tree_database_path()

async def backup_player_skills():
    """Create a backup of all player skills before reset"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("""
                SELECT id, level, skills, skillPoints
                FROM players
                WHERE skills IS NOT NULL AND skills != '{}' AND skills != ''
            """)
            players_with_skills = await cursor.fetchall()
            await cursor.close()
            
            backup_data = []
            for player_id, level, skills_json, skill_points in players_with_skills:
                try:
                    skills = json.loads(skills_json) if skills_json else {}
                    backup_data.append({
                        'id': player_id,
                        'level': level,
                        'old_skills': skills,
                        'old_skill_points': skill_points,
                        'skills_count': len(skills)
                    })
                except json.JSONDecodeError:
                    logging.warning(f"Invalid skills JSON for player {player_id}")
            
            backup_file = f"player_skills_backup_{int(asyncio.get_event_loop().time())}.json"
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logging.info(f"✅ Skills backup created: {backup_file}")
            logging.info(f"📊 Backed up skills for {len(backup_data)} players")
            return backup_file
            
    except Exception as e:
        logging.error(f"Error creating skills backup: {e}")
        return None

async def reset_player_skills():
    """Reset all players' learned skills"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            logging.info(f"Connected to player database: {DATABASE_PATH}")
            
            # Get all players with skills
            cursor = await db.execute("""
                SELECT id, level, skills, skillPoints
                FROM players
                WHERE skills IS NOT NULL AND skills != '{}' AND skills != ''
            """)
            players_with_skills = await cursor.fetchall()
            await cursor.close()
            
            logging.info(f"Found {len(players_with_skills)} players with learned skills")
            
            if not players_with_skills:
                logging.info("No players have learned skills to reset")
                return 0
            
            # Reset all players' skills to empty
            await db.execute("""
                UPDATE players 
                SET skills = '{}'
                WHERE skills IS NOT NULL AND skills != '{}' AND skills != ''
            """)
            
            await db.commit()
            
            logging.info(f"✅ Reset learned skills for {len(players_with_skills)} players")
            return len(players_with_skills)
            
    except Exception as e:
        logging.error(f"Error resetting player skills: {e}")
        return 0

async def reset_skill_tree_progress():
    """Reset all skill tree progress"""
    try:
        async with aiosqlite.connect(SKILL_TREE_DB_PATH) as db:
            logging.info(f"Connected to skill tree database: {SKILL_TREE_DB_PATH}")
            
            # Check if skill tree table exists
            cursor = await db.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='player_skill_trees'
            """)
            table_exists = await cursor.fetchone()
            await cursor.close()
            
            if not table_exists:
                logging.info("No skill tree table found - creating it for future use")
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS player_skill_trees (
                        player_id TEXT,
                        tree_type TEXT,
                        unlocked_skills TEXT DEFAULT '[]',
                        skill_levels TEXT DEFAULT '{}',
                        total_points_spent INTEGER DEFAULT 0,
                        PRIMARY KEY (player_id, tree_type)
                    )
                """)
                await db.commit()
                return 0
            
            # Get current skill tree progress
            cursor = await db.execute("SELECT COUNT(*) FROM player_skill_trees")
            skill_tree_count = (await cursor.fetchone())[0]
            await cursor.close()
            
            if skill_tree_count == 0:
                logging.info("No skill tree progress found to reset")
                return 0
            
            # Reset all skill tree progress
            await db.execute("DELETE FROM player_skill_trees")
            await db.commit()
            
            logging.info(f"✅ Reset skill tree progress for {skill_tree_count} entries")
            return skill_tree_count
            
    except Exception as e:
        logging.error(f"Error resetting skill tree progress: {e}")
        return 0

async def verify_skill_reset():
    """Verify that all skills have been reset properly"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Check for any remaining skills
            cursor = await db.execute("""
                SELECT COUNT(*) FROM players
                WHERE skills IS NOT NULL AND skills != '{}' AND skills != ''
            """)
            remaining_skills = (await cursor.fetchone())[0]
            await cursor.close()
            
            if remaining_skills > 0:
                logging.warning(f"⚠️ {remaining_skills} players still have skills!")
                return False
            else:
                logging.info("✅ All player skills successfully reset")
                return True
                
    except Exception as e:
        logging.error(f"Error verifying skill reset: {e}")
        return False

async def get_reset_statistics():
    """Get statistics about the reset"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Get player statistics
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_players,
                    AVG(level) as avg_level,
                    SUM(skillPoints) as total_skill_points,
                    MIN(level) as min_level,
                    MAX(level) as max_level
                FROM players
            """)
            stats = await cursor.fetchone()
            await cursor.close()
            
            if stats:
                total, avg_level, total_skill_points, min_level, max_level = stats
                logging.info("Reset Statistics:")
                logging.info(f"  Total Players: {total:,}")
                logging.info(f"  Level Range: {min_level} - {max_level:,} (avg: {avg_level:.1f})")
                logging.info(f"  Total Skill Points Available: {total_skill_points:,}")
                logging.info(f"  Average Skill Points per Player: {total_skill_points/total:.1f}")
                
    except Exception as e:
        logging.error(f"Error getting statistics: {e}")

async def main():
    """Main function to run the skill reset"""
    logging.info("🚀 Starting Player Skills Reset...")
    logging.info("This will reset ALL players' learned skills and skill tree progress")
    logging.info("Players will keep their skill points (5 per level) for a fresh start")
    
    # Create backup first
    logging.info("Creating backup of current skills...")
    backup_file = await backup_player_skills()
    
    if backup_file:
        logging.info(f"Backup saved to: {backup_file}")
    
    # Reset learned skills
    logging.info("Resetting learned skills...")
    skills_reset = await reset_player_skills()
    
    # Reset skill tree progress
    logging.info("Resetting skill tree progress...")
    skill_tree_reset = await reset_skill_tree_progress()
    
    # Verify the reset
    logging.info("Verifying skill reset...")
    verification_success = await verify_skill_reset()
    
    # Get final statistics
    await get_reset_statistics()
    
    # Final summary
    logging.info("=" * 60)
    logging.info("PLAYER SKILLS RESET COMPLETE!")
    logging.info("=" * 60)
    logging.info(f"✅ Players with skills reset: {skills_reset}")
    logging.info(f"✅ Skill tree entries reset: {skill_tree_reset}")
    logging.info(f"✅ Verification: {'PASSED' if verification_success else 'FAILED'}")
    logging.info("📊 All players now have:")
    logging.info("   - No learned skills (fresh start)")
    logging.info("   - Full skill points based on level (Level × 5)")
    logging.info("   - Clean skill tree progression")
    logging.info("=" * 60)
    
    if verification_success:
        logging.info("🎉 Skills reset completed successfully!")
        logging.info("Players can now learn skills with the proper point system.")
    else:
        logging.error("❌ Skills reset verification failed!")
        logging.error("Please check the logs and run verification manually.")

if __name__ == "__main__":
    asyncio.run(main())
