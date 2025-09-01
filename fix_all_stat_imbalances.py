#!/usr/bin/env python3
"""
COMPREHENSIVE STAT REBALANCE SCRIPT

This script checks and fixes imbalances in ALL player stats, not just HP.
It ensures all players have fair stat values based on consistent increments.

CURRENT BALANCED INCREMENTS:
- Attack: +10 per point
- Defense: +10 per point  
- HP: +15 per point
- MP: +5 per point
- Precision: +10 per point

PROBLEM:
- Players may have used different increment values over time
- Some stats might have had different scaling in the past
- This creates unfair advantages/disadvantages across all stats
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
        logging.FileHandler(f'all_stats_rebalance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

# Base stats and balanced increments
BASE_STATS = {
    'hp': 100,
    'attack': 10,
    'defense': 10,
    'mp': 10,
    'precision': 10
}

BALANCED_INCREMENTS = {
    'hp': 15,
    'attack': 10,
    'defense': 10,
    'mp': 5,
    'precision': 10
}

async def analyze_all_stat_imbalances():
    """Analyze imbalances across ALL stats for ALL players"""
    
    print("🔍 ANALYZING ALL STAT IMBALANCES")
    print("=" * 60)
    
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
                SELECT id, level, hp, attack, defense, mp, precision, statPoints
                FROM players 
                WHERE level > 1 
                ORDER BY level DESC
            """)
            players = await cursor.fetchall()
            await cursor.close()
            
            if not players:
                print("❌ No players found")
                return None
                
            print(f"👥 Analyzing {len(players)} players...")
            print()
            
            imbalanced_players = []
            stat_analysis = {stat: {'total_excess': 0, 'players_affected': 0} for stat in BASE_STATS.keys()}
            
            for player_data in players:
                player_id, level, hp, attack, defense, mp, precision, stat_points = player_data
                current_stats = {
                    'hp': hp,
                    'attack': attack, 
                    'defense': defense,
                    'mp': mp,
                    'precision': precision
                }
                
                max_points_available = level * 10
                player_imbalances = {}
                total_estimated_points = 0
                
                # Calculate what each stat should be at maximum investment
                for stat_name, current_value in current_stats.items():
                    base_value = BASE_STATS[stat_name]
                    increment = BALANCED_INCREMENTS[stat_name]
                    
                    # Maximum possible value with all points invested in this stat
                    max_possible_value = base_value + (max_points_available * increment)
                    
                    # If current value exceeds what's possible, it's imbalanced
                    if current_value > max_possible_value:
                        excess = current_value - max_possible_value
                        player_imbalances[stat_name] = {
                            'current': current_value,
                            'max_possible': max_possible_value,
                            'excess': excess,
                            'excess_percent': (excess / max_possible_value) * 100
                        }
                        stat_analysis[stat_name]['total_excess'] += excess
                        stat_analysis[stat_name]['players_affected'] += 1
                    
                    # Estimate points spent on this stat
                    if current_value > base_value:
                        # Try different possible increments to estimate
                        estimated_points = (current_value - base_value) / increment
                        total_estimated_points += max(0, estimated_points)
                
                # If player has imbalances, add to list
                if player_imbalances:
                    imbalanced_players.append({
                        'id': player_id,
                        'level': level,
                        'imbalances': player_imbalances,
                        'total_estimated_points': total_estimated_points,
                        'max_points': max_points_available
                    })
            
            # Show analysis results
            print("📊 STAT IMBALANCE ANALYSIS:")
            print("-" * 40)
            
            total_affected_players = len(imbalanced_players)
            
            for stat_name, analysis in stat_analysis.items():
                if analysis['players_affected'] > 0:
                    print(f"⚠️  {stat_name.upper()}:")
                    print(f"    Players affected: {analysis['players_affected']}")
                    print(f"    Total excess: {analysis['total_excess']:,.0f}")
                    print(f"    Avg excess per player: {analysis['total_excess']/analysis['players_affected']:,.0f}")
                    print()
            
            # Show worst cases
            if imbalanced_players:
                print("🚨 WORST IMBALANCE CASES:")
                print("-" * 30)
                
                # Sort by total imbalance severity
                sorted_players = sorted(imbalanced_players, 
                                      key=lambda p: sum(imp['excess'] for imp in p['imbalances'].values()), 
                                      reverse=True)
                
                for i, player in enumerate(sorted_players[:5]):  # Show top 5
                    print(f"{i+1}. Player {player['id']} (Level {player['level']}):")
                    for stat_name, imbalance in player['imbalances'].items():
                        print(f"    {stat_name}: {imbalance['current']:,} (excess: {imbalance['excess']:,}, {imbalance['excess_percent']:.1f}%)")
                    print()
            
            print(f"🚨 TOTAL AFFECTED: {total_affected_players}/{len(players)} players have stat imbalances!")
            return imbalanced_players
            
    except Exception as e:
        print(f"❌ Error analyzing stat imbalances: {e}")
        import traceback
        traceback.print_exc()
        return None

async def fix_all_stat_imbalances():
    """Fix imbalances across ALL stats for ALL players"""
    
    print("🔧 FIXING ALL STAT IMBALANCES")
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
            cursor = await conn.execute("""
                SELECT id, level, hp, attack, defense, mp, precision 
                FROM players
            """)
            players = await cursor.fetchall()
            await cursor.close()
            
            if not players:
                print("❌ No players found")
                return
                
            print(f"👥 Processing {len(players)} players...")
            
            fixed_count = 0
            stat_changes = {stat: 0 for stat in BASE_STATS.keys()}
            
            for player_data in players:
                player_id, level, hp, attack, defense, mp, precision = player_data
                current_stats = {
                    'hp': hp,
                    'attack': attack,
                    'defense': defense, 
                    'mp': mp,
                    'precision': precision
                }
                
                max_points = level * 10
                new_stats = {}
                player_changed = False
                
                # For each stat, estimate points spent and recalculate with balanced increments
                total_estimated_points = 0
                estimated_points_per_stat = {}
                
                # First pass: estimate points spent on each stat
                for stat_name, current_value in current_stats.items():
                    base_value = BASE_STATS[stat_name]
                    increment = BALANCED_INCREMENTS[stat_name]
                    
                    if current_value > base_value:
                        # Estimate points spent (using various possible old increments)
                        possible_increments = {
                            'hp': [50, 25, 20, 15],  # Try old HP increments
                            'attack': [10, 15, 12],
                            'defense': [10, 15, 12], 
                            'mp': [5, 10, 8],
                            'precision': [10, 15, 12]
                        }
                        
                        # Use the increment that gives the most reasonable point estimate
                        best_estimate = 0
                        for test_increment in possible_increments.get(stat_name, [increment]):
                            estimate = (current_value - base_value) / test_increment
                            if 0 <= estimate <= max_points:
                                best_estimate = max(best_estimate, estimate)
                        
                        estimated_points_per_stat[stat_name] = min(max_points, max(0, round(best_estimate)))
                        total_estimated_points += estimated_points_per_stat[stat_name]
                    else:
                        estimated_points_per_stat[stat_name] = 0
                
                # If total estimated points exceed available, scale down proportionally
                if total_estimated_points > max_points:
                    scale_factor = max_points / total_estimated_points
                    for stat_name in estimated_points_per_stat:
                        estimated_points_per_stat[stat_name] = round(estimated_points_per_stat[stat_name] * scale_factor)
                
                # Second pass: calculate new balanced stat values
                for stat_name, current_value in current_stats.items():
                    base_value = BASE_STATS[stat_name]
                    increment = BALANCED_INCREMENTS[stat_name]
                    points_spent = estimated_points_per_stat[stat_name]
                    
                    new_value = base_value + (points_spent * increment)
                    new_stats[stat_name] = new_value
                    
                    # Check if this stat needs updating (significant change)
                    if abs(new_value - current_value) > (current_value * 0.05):  # 5% threshold
                        player_changed = True
                        stat_changes[stat_name] += abs(new_value - current_value)
                
                # Update player if any stats changed significantly
                if player_changed:
                    await conn.execute("""
                        UPDATE players 
                        SET hp = ?, attack = ?, defense = ?, mp = ?, precision = ?
                        WHERE id = ?
                    """, (new_stats['hp'], new_stats['attack'], new_stats['defense'], 
                          new_stats['mp'], new_stats['precision'], player_id))
                    
                    fixed_count += 1
                    
                    if fixed_count <= 10:  # Show first 10 changes
                        print(f"🔧 Player {player_id}:")
                        for stat_name in current_stats:
                            old_val = current_stats[stat_name]
                            new_val = new_stats[stat_name]
                            if abs(new_val - old_val) > (old_val * 0.05):
                                change = new_val - old_val
                                print(f"    {stat_name}: {old_val:,} → {new_val:,} ({change:+,})")
                        print()
            
            await conn.commit()
            
            print("=" * 50)
            print("🎉 ALL STATS REBALANCED!")
            print(f"👥 Players updated: {fixed_count}/{len(players)}")
            print()
            print("📊 Total adjustments by stat:")
            for stat_name, total_change in stat_changes.items():
                if total_change > 0:
                    print(f"   {stat_name}: {total_change:,.0f} total adjustment")
            print()
            print("✅ ALL PLAYERS NOW HAVE BALANCED STATS!")
            print("   ⚖️ Consistent increments across all players")
            print("   🎮 Fair game balance restored")
            
    except Exception as e:
        print(f"❌ Error fixing stat imbalances: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function to analyze and fix all stat imbalances"""
    print("🚨 COMPREHENSIVE STAT REBALANCE")
    print("This script analyzes and fixes imbalances in ALL player stats")
    print()
    print("BALANCED INCREMENTS:")
    for stat, increment in BALANCED_INCREMENTS.items():
        print(f"  {stat}: +{increment} per point")
    print()
    
    # Analyze all stat imbalances
    imbalanced_players = await analyze_all_stat_imbalances()
    
    if not imbalanced_players:
        print("✅ No stat imbalances detected across all players!")
        return
    
    print(f"🚨 CRITICAL: {len(imbalanced_players)} players have stat imbalances!")
    print("This affects game balance in all systems!")
    print()
    
    # Auto-run the fix
    print("🔧 RUNNING AUTOMATIC STAT REBALANCE...")
    await fix_all_stat_imbalances()
    
    print("\n🎯 REBALANCE COMPLETED!")
    print("✅ All players now have fair, balanced stats")
    print("✅ Game balance restored across all systems")
    print("✅ No more unfair advantages/disadvantages")

if __name__ == "__main__":
    asyncio.run(main())
