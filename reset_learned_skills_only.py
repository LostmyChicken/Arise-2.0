#!/usr/bin/env python3
"""
Reset Learned Skills Only Script
Resets all players' learned skills but keeps their skill points intact.
Players already have the correct skill points (Level × 5) and can now re-learn skills properly.
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

async def backup_learned_skills():
    """Create a backup of all learned skills before reset"""
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
            skills_analysis = {}
            
            for player_id, level, skills_json, skill_points in players_with_skills:
                try:
                    skills = json.loads(skills_json) if skills_json else {}
                    backup_data.append({
                        'id': player_id,
                        'level': level,
                        'learned_skills': skills,
                        'current_skill_points': skill_points,
                        'skills_count': len(skills)
                    })
                    
                    # Analyze skill distribution
                    for skill_id in skills.keys():
                        if skill_id not in skills_analysis:
                            skills_analysis[skill_id] = 0
                        skills_analysis[skill_id] += 1
                        
                except json.JSONDecodeError:
                    logging.warning(f"Invalid skills JSON for player {player_id}")
            
            backup_file = f"learned_skills_backup_{int(asyncio.get_event_loop().time())}.json"
            with open(backup_file, 'w') as f:
                json.dump({
                    'players': backup_data,
                    'skill_analysis': skills_analysis,
                    'summary': {
                        'total_players_with_skills': len(backup_data),
                        'most_common_skills': sorted(skills_analysis.items(), key=lambda x: x[1], reverse=True)[:10]
                    }
                }, f, indent=2)
            
            logging.info(f"✅ Learned skills backup created: {backup_file}")
            logging.info(f"📊 Backed up skills for {len(backup_data)} players")
            logging.info(f"🎯 Most common skills: {list(skills_analysis.keys())[:5]}")
            return backup_file, len(backup_data)
            
    except Exception as e:
        logging.error(f"Error creating learned skills backup: {e}")
        return None, 0

async def reset_learned_skills_only():
    """Reset only learned skills, keeping skill points intact"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            logging.info(f"Connected to player database: {DATABASE_PATH}")
            
            # Get current state before reset
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_players,
                    COUNT(CASE WHEN skills IS NOT NULL AND skills != '{}' AND skills != '' THEN 1 END) as players_with_skills,
                    SUM(skillPoints) as total_skill_points
                FROM players
            """)
            before_stats = await cursor.fetchone()
            await cursor.close()
            
            total_players, players_with_skills, total_skill_points = before_stats
            
            logging.info(f"Before reset:")
            logging.info(f"  Total players: {total_players}")
            logging.info(f"  Players with skills: {players_with_skills}")
            logging.info(f"  Total skill points: {total_skill_points}")
            
            if players_with_skills == 0:
                logging.info("No players have learned skills to reset")
                return 0
            
            # Reset ONLY the skills column, keep skillPoints intact
            await db.execute("""
                UPDATE players 
                SET skills = '{}'
                WHERE skills IS NOT NULL AND skills != '{}' AND skills != ''
            """)
            
            await db.commit()
            
            # Verify skill points weren't touched
            cursor = await db.execute("SELECT SUM(skillPoints) FROM players")
            after_skill_points = (await cursor.fetchone())[0]
            await cursor.close()
            
            if after_skill_points != total_skill_points:
                logging.error(f"ERROR: Skill points changed! Before: {total_skill_points}, After: {after_skill_points}")
                return -1
            
            logging.info(f"✅ Reset learned skills for {players_with_skills} players")
            logging.info(f"✅ Skill points preserved: {total_skill_points}")
            return players_with_skills
            
    except Exception as e:
        logging.error(f"Error resetting learned skills: {e}")
        return -1

async def reset_skill_tree_progress_only():
    """Reset skill tree progress but don't touch skill points"""
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
                logging.info("No skill tree table found - players can start fresh")
                return 0
            
            # Get current skill tree progress count
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
        return -1

async def verify_skills_reset():
    """Verify that skills were reset but skill points preserved"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Check for any remaining learned skills
            cursor = await db.execute("""
                SELECT COUNT(*) FROM players
                WHERE skills IS NOT NULL AND skills != '{}' AND skills != ''
            """)
            remaining_skills = (await cursor.fetchone())[0]
            await cursor.close()
            
            # Check that skill points are still correct (Level × 5)
            cursor = await db.execute("""
                SELECT COUNT(*) FROM players
                WHERE skillPoints != (level * 5)
            """)
            incorrect_skill_points = (await cursor.fetchone())[0]
            await cursor.close()
            
            # Get final statistics
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_players,
                    SUM(skillPoints) as total_skill_points,
                    AVG(skillPoints) as avg_skill_points,
                    MIN(level) as min_level,
                    MAX(level) as max_level
                FROM players
            """)
            final_stats = await cursor.fetchone()
            await cursor.close()
            
            success = (remaining_skills == 0 and incorrect_skill_points == 0)
            
            if success:
                logging.info("✅ Skills reset verification PASSED")
                logging.info(f"  - No remaining learned skills: {remaining_skills == 0}")
                logging.info(f"  - All skill points correct: {incorrect_skill_points == 0}")
            else:
                logging.error("❌ Skills reset verification FAILED")
                logging.error(f"  - Remaining skills: {remaining_skills}")
                logging.error(f"  - Incorrect skill points: {incorrect_skill_points}")
            
            total, total_sp, avg_sp, min_lvl, max_lvl = final_stats
            logging.info("Final Statistics:")
            logging.info(f"  Total Players: {total:,}")
            logging.info(f"  Level Range: {min_lvl} - {max_lvl:,}")
            logging.info(f"  Total Skill Points: {total_sp:,}")
            logging.info(f"  Average Skill Points: {avg_sp:.1f}")
            
            return success
                
    except Exception as e:
        logging.error(f"Error verifying skills reset: {e}")
        return False

async def main():
    """Main function to run the learned skills reset"""
    logging.info("🚀 Starting Learned Skills Reset...")
    logging.info("This will reset ALL learned skills but preserve skill points")
    logging.info("Players keep their skill points (Level × 5) for re-learning skills")
    
    # Create backup first
    logging.info("Creating backup of learned skills...")
    backup_file, players_with_skills = await backup_learned_skills()
    
    if backup_file:
        logging.info(f"Backup saved to: {backup_file}")
    
    if players_with_skills == 0:
        logging.info("No players have learned skills - reset not needed")
        return
    
    # Reset learned skills only
    logging.info("Resetting learned skills (preserving skill points)...")
    skills_reset = await reset_learned_skills_only()
    
    if skills_reset == -1:
        logging.error("❌ Skills reset failed!")
        return
    
    # Reset skill tree progress
    logging.info("Resetting skill tree progress...")
    skill_tree_reset = await reset_skill_tree_progress_only()
    
    # Verify the reset
    logging.info("Verifying skills reset...")
    verification_success = await verify_skills_reset()
    
    # Final summary
    logging.info("=" * 60)
    logging.info("LEARNED SKILLS RESET COMPLETE!")
    logging.info("=" * 60)
    logging.info(f"✅ Players with skills reset: {skills_reset}")
    logging.info(f"✅ Skill tree entries reset: {skill_tree_reset}")
    logging.info(f"✅ Verification: {'PASSED' if verification_success else 'FAILED'}")
    logging.info("📊 All players now have:")
    logging.info("   - No learned skills (clean slate)")
    logging.info("   - Full skill points preserved (Level × 5)")
    logging.info("   - Can re-learn skills with proper point system")
    logging.info("=" * 60)
    
    if verification_success:
        logging.info("🎉 Learned skills reset completed successfully!")
        logging.info("Players can now re-learn skills using their skill points properly.")
    else:
        logging.error("❌ Skills reset verification failed!")
        logging.error("Please check the logs and investigate any issues.")

if __name__ == "__main__":
    asyncio.run(main())
