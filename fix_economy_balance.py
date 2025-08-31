#!/usr/bin/env python3
"""
Fix economy balance issues with gear costs and shard requirements
"""

def analyze_current_economy():
    """Analyze current economy balance"""
    print("📊 Current Economy Analysis")
    print("=" * 40)
    
    # Current shard requirements
    shard_requirements = [1, 1, 2, 2, 4]
    cube_requirements = [5, 10, 20, 40, 60]
    
    print("🌟 Limit Break Requirements:")
    for tier, (shards, cubes) in enumerate(zip(shard_requirements, cube_requirements)):
        print(f"  Tier {tier} → {tier+1}: {shards} shards, {cubes} cubes")
    
    # Current gear costs for level 10
    level = 10
    print(f"\n⚙️ Current Gear Costs (Level {level}):")
    
    # Hunter costs
    print("🏹 Hunters:")
    tier3_hunter = (3 * level) + ((level // 10) * 15)  # 30 + 15 = 45
    tier2_hunter = (4 * level) + ((level // 10) * 20)  # 40 + 20 = 60
    tier1_hunter = (5 * level) + ((level // 10) * 25)  # 50 + 25 = 75
    
    print(f"  Tier 3: {tier3_hunter} Gear III ⚠️ CHEAPEST")
    print(f"  Tier 2: {tier2_hunter} Gear II")
    print(f"  Tier 1: {tier1_hunter} Gear I ⚠️ MOST EXPENSIVE")
    
    # Weapon costs
    print("⚔️ Weapons:")
    tier3_weapon = (8 * level) + ((level // 15) * 30)  # 80
    tier2_weapon = (10 * level) + ((level // 15) * 25)  # 100
    tier1_weapon = 10 * level  # 100
    
    print(f"  Tier 3: {tier3_weapon} Gear III ⚠️ CHEAPEST")
    print(f"  Tier 2: {tier2_weapon} Gear II")
    print(f"  Tier 1: {tier1_weapon} Gear I ⚠️ TIED MOST EXPENSIVE")
    
    # Issues
    print("\n🚨 Issues Identified:")
    print("  1. Higher tier items cost LESS gear (should cost MORE)")
    print("  2. Tier 3 hunters are cheapest to upgrade (should be most expensive)")
    print("  3. Economic incentive is backwards - discourages high-tier items")
    
    return {
        'hunter_costs': [tier1_hunter, tier2_hunter, tier3_hunter],
        'weapon_costs': [tier1_weapon, tier2_weapon, tier3_weapon],
        'shard_requirements': shard_requirements,
        'cube_requirements': cube_requirements
    }

def propose_balanced_economy():
    """Propose a balanced economy"""
    print("\n💡 Proposed Balanced Economy")
    print("=" * 40)
    
    # Balanced shard requirements (keep current - they're reasonable)
    balanced_shards = [1, 2, 3, 4, 5]  # Slightly increased
    balanced_cubes = [5, 10, 20, 40, 80]  # Slightly increased top end
    
    print("🌟 Proposed Limit Break Requirements:")
    for tier, (shards, cubes) in enumerate(zip(balanced_shards, balanced_cubes)):
        print(f"  Tier {tier} → {tier+1}: {shards} shards, {cubes} cubes")
    
    # Balanced gear costs (higher tier = more expensive)
    level = 10
    print(f"\n⚙️ Proposed Gear Costs (Level {level}):")
    
    # Hunter costs (reversed and scaled)
    print("🏹 Hunters:")
    balanced_tier1_hunter = (3 * level) + ((level // 10) * 10)  # 30 + 10 = 40
    balanced_tier2_hunter = (5 * level) + ((level // 10) * 15)  # 50 + 15 = 65
    balanced_tier3_hunter = (8 * level) + ((level // 10) * 25)  # 80 + 25 = 105
    
    print(f"  Tier 1: {balanced_tier1_hunter} Gear I ✅ CHEAPEST")
    print(f"  Tier 2: {balanced_tier2_hunter} Gear II")
    print(f"  Tier 3: {balanced_tier3_hunter} Gear III ✅ MOST EXPENSIVE")
    
    # Weapon costs (properly scaled)
    print("⚔️ Weapons:")
    balanced_tier1_weapon = (5 * level) + ((level // 15) * 10)  # 50
    balanced_tier2_weapon = (8 * level) + ((level // 15) * 20)  # 80
    balanced_tier3_weapon = (12 * level) + ((level // 15) * 35)  # 120
    
    print(f"  Tier 1: {balanced_tier1_weapon} Gear I ✅ CHEAPEST")
    print(f"  Tier 2: {balanced_tier2_weapon} Gear II")
    print(f"  Tier 3: {balanced_tier3_weapon} Gear III ✅ MOST EXPENSIVE")
    
    print("\n✅ Benefits of Balanced Economy:")
    print("  1. Higher tier items cost MORE gear (economically logical)")
    print("  2. Players invest more in better items (proper progression)")
    print("  3. Gear types have clear value hierarchy")
    print("  4. Encourages strategic resource management")
    
    return {
        'hunter_formulas': {
            'tier1': '(3 * level) + ((level // 10) * 10)',
            'tier2': '(5 * level) + ((level // 10) * 15)', 
            'tier3': '(8 * level) + ((level // 10) * 25)'
        },
        'weapon_formulas': {
            'tier1': '(5 * level) + ((level // 15) * 10)',
            'tier2': '(8 * level) + ((level // 15) * 20)',
            'tier3': '(12 * level) + ((level // 15) * 35)'
        },
        'shard_requirements': balanced_shards,
        'cube_requirements': balanced_cubes
    }

def generate_fix_code():
    """Generate the code fixes needed"""
    print("\n🔧 Code Fixes Required")
    print("=" * 40)
    
    print("📁 File: commands/upgrade.py")
    print("\n🔄 Replace hunter gear cost calculations:")
    print("```python")
    print("# CURRENT (BROKEN):")
    print("if tier >= 3:")
    print("    gear_cost = (3 * level) + ((level // 10) * 15)  # CHEAPEST")
    print("elif tier >= 2:")
    print("    gear_cost = (4 * level) + ((level // 10) * 20)")
    print("else:")
    print("    gear_cost = (5 * level) + ((level // 10) * 25)  # MOST EXPENSIVE")
    print("")
    print("# FIXED (BALANCED):")
    print("if tier >= 3:")
    print("    gear_cost = (8 * level) + ((level // 10) * 25)  # MOST EXPENSIVE")
    print("elif tier >= 2:")
    print("    gear_cost = (5 * level) + ((level // 10) * 15)")
    print("else:")
    print("    gear_cost = (3 * level) + ((level // 10) * 10)  # CHEAPEST")
    print("```")
    
    print("\n🔄 Replace weapon gear cost calculations:")
    print("```python")
    print("# CURRENT (BROKEN):")
    print("if tier >= 3 or level >= 40:")
    print("    gear_cost = (8 * level) + ((level // 15) * 30)  # CHEAPEST")
    print("elif tier >= 2 or level >= 20:")
    print("    gear_cost = (10 * level) + ((level // 15) * 25)")
    print("else:")
    print("    gear_cost = 10 * level  # TIED MOST EXPENSIVE")
    print("")
    print("# FIXED (BALANCED):")
    print("if tier >= 3 or level >= 40:")
    print("    gear_cost = (12 * level) + ((level // 15) * 35)  # MOST EXPENSIVE")
    print("elif tier >= 2 or level >= 20:")
    print("    gear_cost = (8 * level) + ((level // 15) * 20)")
    print("else:")
    print("    gear_cost = (5 * level) + ((level // 15) * 10)  # CHEAPEST")
    print("```")
    
    print("\n📍 Locations to update in upgrade.py:")
    locations = [
        "Line ~218-231: Hunter gear costs in populate_items()",
        "Line ~236-249: Weapon gear costs in populate_items()",
        "Line ~936-949: Hunter gear costs in show_upgrade_details()",
        "Line ~1045-1058: Weapon gear costs in show_upgrade_details()",
        "Line ~1183-1187: Hunter gear costs in perform_upgrade()",
        "Line ~1191-1195: Weapon gear costs in perform_upgrade()",
        "Line ~1252-1256: Hunter gear costs in upgrade calculations",
        "Line ~1260-1264: Weapon gear costs in upgrade calculations"
    ]
    
    for location in locations:
        print(f"  • {location}")

def main():
    """Main analysis function"""
    print("💰 Economy Balance Analysis & Fix")
    print("=" * 50)
    
    # Analyze current economy
    current = analyze_current_economy()
    
    # Propose balanced economy
    balanced = propose_balanced_economy()
    
    # Generate fix code
    generate_fix_code()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print("❌ Current economy has backwards incentives")
    print("✅ Proposed fixes create proper progression")
    print("🔧 Code changes needed in 8 locations")
    print("\n💡 Apply these fixes to balance the economy!")

if __name__ == "__main__":
    main()
