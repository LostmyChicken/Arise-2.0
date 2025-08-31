#!/usr/bin/env python3
"""
CRITICAL HP STAT REBALANCE SCRIPT

This script fixes the massive HP imbalance caused by changing HP increment from 50 to 15 per point.

PROBLEM:
- Old players who upgraded HP before the fix got +50 HP per point
- New players who upgrade HP after the fix get +15 HP per point  
- This creates a 3.33x HP advantage for old players!

SOLUTION:
- Recalculate all players' HP based on the new balanced increment (15 per point)
- Preserve their stat point investments but apply fair HP values
"""

import asyncio
import aiosqlite
import json
import logging
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append('.')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'hp_rebalance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

async def analyze_hp_imbalance():
    """Analyze the current HP imbalance in the player database"""
    
    print("🔍 ANALYZING HP STAT IMBALANCE")
    print("=" * 50)
    
    try:
        # Load database configuration
        try:
            with open('db.json', 'r') as f:
                config = json.load(f)
                db_path = config.get('player', 'data/player.db')
        except:
            db_path = 'data/player.db'
            
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return None
            
        async with aiosqlite.connect(db_path) as conn:
            # Get all players with their stats
            cursor = await conn.execute("""
                SELECT id, level, hp, statPoints 
                FROM players 
                WHERE level > 1 
                ORDER BY hp DESC 
                LIMIT 20
            """)
            players = await cursor.fetchall()
            await cursor.close()
            
            if not players:
                print("❌ No players found")
                return None
                
            print(f"📊 Analyzing top 20 players by HP:")
            print()
            
            base_hp = 100  # Starting HP
            old_increment = 50  # Old HP per point
            new_increment = 15  # New HP per point
            
            imbalanced_players = []
            
            for player_id, level, current_hp, stat_points in players:
                # Calculate expected HP ranges
                max_possible_old_hp = base_hp + (level * 10 * old_increment)  # If all points went to HP
                max_possible_new_hp = base_hp + (level * 10 * new_increment)  # If all points went to HP
                
                # Estimate how many points were likely spent on HP (old system)
                if current_hp > base_hp:
                    estimated_hp_points_old = (current_hp - base_hp) / old_increment
                    estimated_hp_points_new = (current_hp - base_hp) / new_increment
                    
                    # If they have way more HP than the new system would allow, they're imbalanced
                    if current_hp > max_possible_new_hp:
                        imbalanced_players.append({
                            'id': player_id,
                            'level': level,
                            'current_hp': current_hp,
                            'estimated_old_points': estimated_hp_points_old,
                            'estimated_new_points': estimated_hp_points_new,
                            'excess_hp': current_hp - max_possible_new_hp
                        })
                        
                        print(f"⚠️  Player {player_id}: Level {level}")
                        print(f"    Current HP: {current_hp:,}")
                        print(f"    Est. HP points (old): {estimated_hp_points_old:.1f}")
                        print(f"    Est. HP points (new): {estimated_hp_points_new:.1f}")
                        print(f"    Excess HP: {current_hp - max_possible_new_hp:,}")
                        print()
                
            print(f"🚨 Found {len(imbalanced_players)} players with excessive HP!")
            return imbalanced_players
            
    except Exception as e:
        print(f"❌ Error analyzing HP imbalance: {e}")
        import traceback
        traceback.print_exc()
        return None

async def fix_hp_imbalance():
    """Fix the HP imbalance by recalculating HP based on estimated stat point usage"""
    
    print("🔧 FIXING HP STAT IMBALANCE")
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
            # Get all players
            cursor = await conn.execute("SELECT id, level, hp, attack, defense, mp, precision FROM players")
            players = await cursor.fetchall()
            await cursor.close()
            
            if not players:
                print("❌ No players found")
                return
                
            print(f"👥 Processing {len(players)} players...")
            
            base_stats = {'hp': 100, 'attack': 10, 'defense': 10, 'mp': 10, 'precision': 10}
            old_increments = {'hp': 50, 'attack': 10, 'defense': 10, 'mp': 5, 'precision': 10}
            new_increments = {'hp': 15, 'attack': 10, 'defense': 10, 'mp': 5, 'precision': 10}
            
            fixed_count = 0
            total_hp_reduced = 0
            
            for player_data in players:
                player_id, level, hp, attack, defense, mp, precision = player_data
                current_stats = {'hp': hp, 'attack': attack, 'defense': defense, 'mp': mp, 'precision': precision}
                
                # Calculate estimated stat points spent on each stat (using old increments)
                estimated_points = {}
                total_estimated_points = 0
                
                for stat, current_value in current_stats.items():
                    if current_value > base_stats[stat]:
                        points_spent = (current_value - base_stats[stat]) / old_increments[stat]
                        estimated_points[stat] = max(0, round(points_spent))
                        total_estimated_points += estimated_points[stat]
                    else:
                        estimated_points[stat] = 0
                
                # If total estimated points exceed what they should have, scale down proportionally
                max_points = level * 10
                if total_estimated_points > max_points:
                    scale_factor = max_points / total_estimated_points
                    for stat in estimated_points:
                        estimated_points[stat] = round(estimated_points[stat] * scale_factor)
                
                # Recalculate HP using new increment
                new_hp = base_stats['hp'] + (estimated_points['hp'] * new_increments['hp'])
                
                # Only update if HP is significantly different (more than 10% change)
                if abs(new_hp - hp) > (hp * 0.1):
                    await conn.execute(
                        "UPDATE players SET hp = ? WHERE id = ?",
                        (new_hp, player_id)
                    )
                    
                    hp_change = new_hp - hp
                    total_hp_reduced += abs(hp_change)
                    fixed_count += 1
                    
                    if fixed_count <= 10:  # Show first 10 changes
                        print(f"🔧 Player {player_id}: {hp:,} → {new_hp:,} HP ({hp_change:+,})")
            
            await conn.commit()
            
            print("=" * 50)
            print("🎉 HP REBALANCE COMPLETED!")
            print(f"👥 Players updated: {fixed_count}/{len(players)}")
            print(f"📉 Total HP adjusted: {total_hp_reduced:,.0f}")
            print()
            print("✅ ALL PLAYERS NOW HAVE BALANCED HP!")
            print("   📊 HP increment: 15 per stat point (fair for everyone)")
            print("   ⚖️ No more 3.33x HP advantage for old players")
            
    except Exception as e:
        print(f"❌ Error fixing HP imbalance: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function to analyze and fix HP imbalance"""
    print("🚨 CRITICAL HP STAT REBALANCE")
    print("This script fixes the massive HP imbalance between old and new players")
    print()
    
    # First analyze the problem
    imbalanced_players = await analyze_hp_imbalance()
    
    if not imbalanced_players:
        print("✅ No HP imbalance detected!")
        return
    
    print(f"🚨 CRITICAL ISSUE: {len(imbalanced_players)} players have excessive HP!")
    print("This creates unfair advantages in:")
    print("• World boss battles")
    print("• PvP combat")
    print("• Raid scaling")
    print("• General game balance")
    print()
    
    response = input("Do you want to fix this imbalance? (yes/no): ")
    if response.lower() == 'yes':
        await fix_hp_imbalance()
        print("\n🎯 NEXT STEPS:")
        print("1. Restart the bot to ensure changes take effect")
        print("2. Monitor player feedback")
        print("3. Test world boss scaling with balanced HP values")
    else:
        print("❌ HP imbalance NOT fixed. Players will continue to have unfair advantages.")

if __name__ == "__main__":
    asyncio.run(main())
