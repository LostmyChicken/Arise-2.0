#!/usr/bin/env python3
"""
Verify Final Player State Script
Verifies that all players have the correct points and clean skill state after the reset.
"""

import asyncio
import aiosqlite
import json
import logging

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

async def verify_player_state():
    """Verify the final state of all players"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            logging.info(f"Connected to database: {DATABASE_PATH}")
            
            # Get comprehensive player statistics
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_players,
                    COUNT(CASE WHEN statPoints = (level * 10) THEN 1 END) as correct_stat_points,
                    COUNT(CASE WHEN skillPoints = (level * 5) THEN 1 END) as correct_skill_points,
                    COUNT(CASE WHEN skills IS NULL OR skills = '{}' OR skills = '' THEN 1 END) as clean_skills,
                    SUM(statPoints) as total_stat_points,
                    SUM(skillPoints) as total_skill_points,
                    AVG(level) as avg_level,
                    MIN(level) as min_level,
                    MAX(level) as max_level
                FROM players
            """)
            stats = await cursor.fetchone()
            await cursor.close()
            
            if not stats:
                logging.error("No player data found!")
                return False
            
            (total_players, correct_stat_points, correct_skill_points, clean_skills,
             total_stat_points, total_skill_points, avg_level, min_level, max_level) = stats
            
            # Check for any issues
            stat_point_issues = total_players - correct_stat_points
            skill_point_issues = total_players - correct_skill_points
            skill_cleanup_issues = total_players - clean_skills
            
            # Display results
            logging.info("=" * 60)
            logging.info("FINAL PLAYER STATE VERIFICATION")
            logging.info("=" * 60)
            
            logging.info(f"📊 Total Players: {total_players:,}")
            logging.info(f"📈 Level Range: {min_level} - {max_level:,} (avg: {avg_level:.1f})")
            
            logging.info("\n🎯 STAT POINTS VERIFICATION:")
            if stat_point_issues == 0:
                logging.info(f"  ✅ ALL {correct_stat_points:,} players have correct stat points (Level × 10)")
                logging.info(f"  📊 Total stat points: {total_stat_points:,}")
            else:
                logging.error(f"  ❌ {stat_point_issues} players have incorrect stat points!")
            
            logging.info("\n⚡ SKILL POINTS VERIFICATION:")
            if skill_point_issues == 0:
                logging.info(f"  ✅ ALL {correct_skill_points:,} players have correct skill points (Level × 5)")
                logging.info(f"  ✥ Total skill points: {total_skill_points:,}")
            else:
                logging.error(f"  ❌ {skill_point_issues} players have incorrect skill points!")
            
            logging.info("\n🧹 SKILLS CLEANUP VERIFICATION:")
            if skill_cleanup_issues == 0:
                logging.info(f"  ✅ ALL {clean_skills:,} players have clean skill states (no learned skills)")
            else:
                logging.error(f"  ❌ {skill_cleanup_issues} players still have learned skills!")
            
            # Show examples of different level players
            logging.info("\n📋 PLAYER EXAMPLES:")
            cursor = await db.execute("""
                SELECT id, level, statPoints, skillPoints, 
                       CASE WHEN skills IS NULL OR skills = '{}' OR skills = '' THEN 'Clean' ELSE 'Has Skills' END as skill_state
                FROM players
                WHERE level IN (1, 10, 50, 100, 500, 1000)
                ORDER BY level
                LIMIT 10
            """)
            examples = await cursor.fetchall()
            await cursor.close()
            
            for player_id, level, stat_points, skill_points, skill_state in examples:
                expected_stat = level * 10
                expected_skill = level * 5
                stat_ok = "✅" if stat_points == expected_stat else "❌"
                skill_ok = "✅" if skill_points == expected_skill else "❌"
                clean_ok = "✅" if skill_state == "Clean" else "❌"
                
                logging.info(f"  Level {level:3}: {stat_ok} {stat_points:4} stat, {skill_ok} {skill_points:3} skill, {clean_ok} {skill_state}")
            
            # Overall success check
            overall_success = (stat_point_issues == 0 and skill_point_issues == 0 and skill_cleanup_issues == 0)
            
            logging.info("\n" + "=" * 60)
            if overall_success:
                logging.info("🎉 VERIFICATION PASSED - ALL SYSTEMS READY!")
                logging.info("✅ All players have correct points and clean skill states")
                logging.info("✅ Players can now use the new point system properly")
            else:
                logging.error("❌ VERIFICATION FAILED - ISSUES FOUND!")
                logging.error("Please investigate and fix the reported issues")
            logging.info("=" * 60)
            
            return overall_success
            
    except Exception as e:
        logging.error(f"Error verifying player state: {e}")
        return False

async def show_system_status():
    """Show the status of the point systems"""
    logging.info("\n🎮 SYSTEM STATUS:")
    logging.info("📊 Stat Points System:")
    logging.info("   - Formula: Level × 10")
    logging.info("   - Purpose: Upgrading base stats (Attack, Defense, Health, MP, Precision)")
    logging.info("   - Commands: sl stats, sl su")
    
    logging.info("✥ Skill Points System:")
    logging.info("   - Formula: Level × 5")
    logging.info("   - Purpose: Learning skills and skill tree progression")
    logging.info("   - Commands: skill tree, skill learning")
    
    logging.info("🔄 Level Up Rewards:")
    logging.info("   - +10 stat points per level")
    logging.info("   - +5 skill points per level")
    
    logging.info("🧹 Skills State:")
    logging.info("   - All learned skills reset")
    logging.info("   - Clean skill tree progression")
    logging.info("   - Players can re-learn skills with their skill points")

async def main():
    """Main verification function"""
    logging.info("🔍 Starting Final Player State Verification...")
    
    success = await verify_player_state()
    await show_system_status()
    
    if success:
        logging.info("\n🎊 COMPLETE SUCCESS!")
        logging.info("All players are ready to use the new standardized point system!")
    else:
        logging.error("\n⚠️ ISSUES DETECTED!")
        logging.error("Please review the verification results and fix any problems.")

if __name__ == "__main__":
    asyncio.run(main())
