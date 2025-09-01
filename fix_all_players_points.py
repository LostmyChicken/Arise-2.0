#!/usr/bin/env python3
"""
CRITICAL FIX SCRIPT: Reset all players' stat and skill points to correct values

This script fixes the major issue where:
- Stat points should be 10 per level (for upgrading base stats)
- Skill points should be 5 per level (for skill tree progression)

The previous system was incorrectly giving:
- 5 stat points per level (should be 10)
- 2 skill points per level + bonus (should be 5)
"""

import asyncio
import aiosqlite
import json
import logging
import sys
import os

# Add the project root to the path
sys.path.append('.')

async def fix_all_players():
    """Fix all players' stat and skill points to correct values"""
    
    print("🔧 CRITICAL FIX: Resetting all players' stat and skill points")
    print("=" * 60)
    
    try:
        # Load database configuration
        try:
            with open('db.json', 'r') as f:
                config = json.load(f)
                db_path = config.get('player', 'data/player.db')
        except:
            db_path = 'data/player.db'
            
        print(f"📊 Database path: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return
            
        async with aiosqlite.connect(db_path) as conn:
            # Get all players
            cursor = await conn.execute("SELECT id, level, statPoints, skillPoints FROM players")
            players = await cursor.fetchall()
            await cursor.close()
            
            if not players:
                print("❌ No players found in database")
                return
                
            print(f"👥 Found {len(players)} players to fix")
            print()
            
            fixed_count = 0
            total_stat_points_added = 0
            total_skill_points_removed = 0
            
            for player_id, level, current_stat_points, current_skill_points in players:
                # Calculate correct points
                correct_stat_points = level * 10  # 10 per level
                correct_skill_points = level * 5   # 5 per level
                
                # Calculate differences
                stat_diff = correct_stat_points - (current_stat_points or 0)
                skill_diff = correct_skill_points - (current_skill_points or 0)
                
                # Only update if there's a difference
                if stat_diff != 0 or skill_diff != 0:
                    await conn.execute(
                        "UPDATE players SET statPoints = ?, skillPoints = ? WHERE id = ?",
                        (correct_stat_points, correct_skill_points, player_id)
                    )
                    
                    fixed_count += 1
                    total_stat_points_added += stat_diff
                    total_skill_points_removed += abs(skill_diff) if skill_diff < 0 else -skill_diff
                    
                    print(f"🔧 Player {player_id} (Level {level}):")
                    print(f"   📊 Stat Points: {current_stat_points or 0} → {correct_stat_points} ({stat_diff:+d})")
                    print(f"   ✨ Skill Points: {current_skill_points or 0} → {correct_skill_points} ({skill_diff:+d})")
                    print()
            
            await conn.commit()
            
            print("=" * 60)
            print("🎉 CRITICAL FIX COMPLETED!")
            print(f"👥 Players fixed: {fixed_count}/{len(players)}")
            print(f"📊 Total stat points added: {total_stat_points_added:+d}")
            print(f"✨ Total skill points adjusted: {total_skill_points_removed:+d}")
            print()
            print("✅ CORRECTED SYSTEM:")
            print("   📊 Stat Points: 10 per level (for base stat upgrades)")
            print("   ✨ Skill Points: 5 per level (for skill tree progression)")
            print()
            print("🔧 All players now have the correct point allocations!")
            
    except Exception as e:
        print(f"❌ Error fixing players: {e}")
        import traceback
        traceback.print_exc()

async def verify_fix():
    """Verify that the fix was applied correctly"""
    
    print("\n🔍 VERIFICATION: Checking if fix was applied correctly")
    print("=" * 50)
    
    try:
        # Load database configuration
        try:
            with open('db.json', 'r') as f:
                config = json.load(f)
                db_path = config.get('player', 'data/player.db')
        except:
            db_path = 'data/player.db'
            
        async with aiosqlite.connect(db_path) as conn:
            # Check a sample of players
            cursor = await conn.execute(
                "SELECT id, level, statPoints, skillPoints FROM players ORDER BY level DESC LIMIT 10"
            )
            sample_players = await cursor.fetchall()
            await cursor.close()
            
            print("📊 Sample of fixed players:")
            print()
            
            all_correct = True
            for player_id, level, stat_points, skill_points in sample_players:
                expected_stat = level * 10
                expected_skill = level * 5
                
                stat_correct = stat_points == expected_stat
                skill_correct = skill_points == expected_skill
                
                status = "✅" if (stat_correct and skill_correct) else "❌"
                
                print(f"{status} Player {player_id} (Level {level}):")
                print(f"   📊 Stat Points: {stat_points} (expected: {expected_stat}) {'✅' if stat_correct else '❌'}")
                print(f"   ✨ Skill Points: {skill_points} (expected: {expected_skill}) {'✅' if skill_correct else '❌'}")
                print()
                
                if not (stat_correct and skill_correct):
                    all_correct = False
            
            if all_correct:
                print("🎉 VERIFICATION PASSED: All sampled players have correct points!")
            else:
                print("❌ VERIFICATION FAILED: Some players still have incorrect points!")
                
    except Exception as e:
        print(f"❌ Error during verification: {e}")

async def main():
    """Main function to run the fix"""
    print("🚨 CRITICAL SYSTEM FIX")
    print("This script will fix the stat/skill points confusion for ALL players")
    print()
    print("CHANGES:")
    print("• Stat Points: Will be set to 10 per level (for base stat upgrades)")
    print("• Skill Points: Will be set to 5 per level (for skill tree progression)")
    print()
    
    # Run the fix
    await fix_all_players()
    
    # Verify the fix
    await verify_fix()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Restart the bot to ensure all changes take effect")
    print("2. Test stat upgrades with 'sl stats' command")
    print("3. Test skill upgrades with skill tree commands")
    print("4. Monitor for any remaining issues")

if __name__ == "__main__":
    asyncio.run(main())
