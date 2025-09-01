#!/usr/bin/env python3
"""
Comprehensive analysis of the entire economy system
"""

def analyze_income_sources():
    """Analyze all sources of income for players"""
    print("💰 INCOME SOURCES ANALYSIS")
    print("=" * 50)
    
    # Daily Login Rewards
    print("📅 Daily Login Rewards:")
    base_gold = (1000, 10000)  # Random range
    base_stone = 500
    base_tickets = 10
    base_keys = (2, 3)  # Random range
    
    print(f"  Base Gold: {base_gold[0]}-{base_gold[1]} per day")
    print(f"  Base Stone: {base_stone} per day")
    print(f"  Base Tickets: {base_tickets} per day")
    print(f"  Base Keys: {base_keys[0]}-{base_keys[1]} per day")
    print(f"  Streak Bonus: Up to 2x (10 day streak)")
    print(f"  Max Daily Gold: {base_gold[1] * 2} gold")
    
    # AFK Rewards
    print("\n💤 AFK Rewards:")
    afk_gold_per_min = "10 + (afk_level - 1) * 2"
    afk_xp_per_min = "5 + (afk_level - 1) * 1"
    max_afk_hours = 24
    print(f"  Gold per minute: {afk_gold_per_min}")
    print(f"  XP per minute: {afk_xp_per_min}")
    print(f"  Max AFK time: {max_afk_hours} hours")
    print(f"  Level 1 AFK (24h): {10 * 60 * 24} gold")
    print(f"  Level 10 AFK (24h): {(10 + 9*2) * 60 * 24} gold")
    
    # Achievement Rewards
    print("\n🏆 Achievement Rewards:")
    achievement_rewards = [
        ("First Steps (Lv5)", 1000),
        ("Rising Hunter (Lv25)", 5000),
        ("Veteran Hunter (Lv50)", 15000),
        ("Elite Hunter (Lv100)", 50000),
        ("Shadow Monarch", 100000),
        ("Lucky Hunter", 200000)
    ]
    
    total_achievement_gold = sum(reward[1] for reward in achievement_rewards)
    for name, gold in achievement_rewards:
        print(f"  {name}: {gold} gold")
    print(f"  Total Achievement Gold: {total_achievement_gold}")
    
    # Trivia Rewards
    print("\n🧠 Trivia Rewards:")
    trivia_rewards = {
        5: (1000, 1200),
        4: (800, 1000),
        3: (400, 800),
        2: (400, 600),
        1: (200, 400),
        0: (100, 200)
    }
    print(f"  Perfect Score: {trivia_rewards[5][0]}-{trivia_rewards[5][1]} gold")
    print(f"  Average Score: {trivia_rewards[3][0]}-{trivia_rewards[3][1]} gold")
    
    # Gate Rewards
    print("\n🚪 Gate Rewards:")
    print("  Stone rewards based on damage contribution")
    print("  Base: 500 mana crystals per gate")
    print("  Guild bonuses: +100 guild points")
    
    return {
        'daily_max': base_gold[1] * 2,
        'afk_24h_lv1': 10 * 60 * 24,
        'afk_24h_lv10': (10 + 9*2) * 60 * 24,
        'achievement_total': total_achievement_gold,
        'trivia_max': trivia_rewards[5][1]
    }

def analyze_expenses():
    """Analyze all ways players spend resources"""
    print("\n💸 EXPENSE ANALYSIS")
    print("=" * 50)
    
    # Upgrade Costs
    print("⚡ Upgrade Costs:")
    print("  Hunters:")
    print("    Gold: (150 * level) + ((level // 10) * 500)")
    print("    Level 10: 150*10 + 500 = 2000 gold")
    print("    Level 50: 150*50 + 2500 = 10000 gold")
    print("    Level 100: 150*100 + 5000 = 20000 gold")
    
    print("  Weapons:")
    print("    Gold: 2000 * (2 ** (level // 20))")
    print("    Level 10: 2000 * 1 = 2000 gold")
    print("    Level 20: 2000 * 2 = 4000 gold")
    print("    Level 40: 2000 * 4 = 8000 gold")
    print("    Level 60: 2000 * 8 = 16000 gold")
    print("    Level 80: 2000 * 16 = 32000 gold")
    print("    Level 100: 2000 * 32 = 64000 gold")
    
    # Gear Costs (Fixed)
    print("\n⚙️ Gear Costs (Fixed):")
    level = 50
    print(f"  Level {level} Hunter Upgrades:")
    tier1_hunter = (3 * level) + ((level // 10) * 10)
    tier2_hunter = (5 * level) + ((level // 10) * 15)
    tier3_hunter = (8 * level) + ((level // 10) * 25)
    print(f"    Tier 1: {tier1_hunter} Gear I")
    print(f"    Tier 2: {tier2_hunter} Gear II")
    print(f"    Tier 3: {tier3_hunter} Gear III")
    
    print(f"  Level {level} Weapon Upgrades:")
    tier1_weapon = (5 * level) + ((level // 15) * 10)
    tier2_weapon = (8 * level) + ((level // 15) * 20)
    tier3_weapon = (12 * level) + ((level // 15) * 35)
    print(f"    Tier 1: {tier1_weapon} Gear I")
    print(f"    Tier 2: {tier2_weapon} Gear II")
    print(f"    Tier 3: {tier3_weapon} Gear III")
    
    # Limit Break Costs
    print("\n🌟 Limit Break Costs:")
    shard_requirements = [1, 1, 2, 2, 4]
    cube_requirements = [5, 10, 20, 40, 60]
    for tier, (shards, cubes) in enumerate(zip(shard_requirements, cube_requirements)):
        print(f"  Tier {tier} → {tier+1}: {shards} shards, {cubes} cubes")
    
    # Guild Creation
    print("\n🏰 Guild Creation:")
    print("  Cost: 200,000 gold")
    print("  Requirements: Level 10+")
    
    return {
        'hunter_lv10': 2000,
        'hunter_lv50': 10000,
        'hunter_lv100': 20000,
        'weapon_lv10': 2000,
        'weapon_lv50': 16000,
        'weapon_lv100': 64000,
        'guild_creation': 200000
    }

def analyze_balance():
    """Analyze overall economic balance"""
    print("\n⚖️ BALANCE ANALYSIS")
    print("=" * 50)
    
    income = analyze_income_sources()
    expenses = analyze_expenses()
    
    # Daily income vs expenses
    print("📊 Daily Income vs Upgrade Costs:")
    daily_income = income['daily_max'] + income['afk_24h_lv10']  # Max daily + AFK
    print(f"  Max Daily Income: {daily_income} gold")
    print(f"  Hunter Lv10 Upgrade: {expenses['hunter_lv10']} gold ({expenses['hunter_lv10']/daily_income*100:.1f}% of daily)")
    print(f"  Hunter Lv50 Upgrade: {expenses['hunter_lv50']} gold ({expenses['hunter_lv50']/daily_income*100:.1f}% of daily)")
    print(f"  Weapon Lv100 Upgrade: {expenses['weapon_lv100']} gold ({expenses['weapon_lv100']/daily_income*100:.1f}% of daily)")
    print(f"  Guild Creation: {expenses['guild_creation']} gold ({expenses['guild_creation']/daily_income*100:.1f}% of daily)")
    
    # Balance assessment
    print("\n🎯 Balance Assessment:")
    issues = []
    
    # Check if weapon costs scale too aggressively
    weapon_lv50_ratio = expenses['weapon_lv50'] / daily_income
    weapon_lv100_ratio = expenses['weapon_lv100'] / daily_income
    
    if weapon_lv100_ratio > 10:  # More than 10 days of income
        issues.append(f"⚠️ Level 100 weapons cost {weapon_lv100_ratio:.1f} days of income (too expensive)")
    
    if expenses['guild_creation'] / daily_income > 30:  # More than 30 days
        issues.append(f"⚠️ Guild creation costs {expenses['guild_creation']/daily_income:.1f} days of income (too expensive)")
    
    # Check progression curve
    hunter_progression = expenses['hunter_lv100'] / expenses['hunter_lv10']
    weapon_progression = expenses['weapon_lv100'] / expenses['weapon_lv10']
    
    if weapon_progression > 50:  # More than 50x increase
        issues.append(f"⚠️ Weapon cost progression too steep ({weapon_progression}x from lv10 to lv100)")
    
    if not issues:
        print("✅ Economy appears balanced")
    else:
        print("🚨 Balance Issues Found:")
        for issue in issues:
            print(f"  {issue}")
    
    return len(issues) == 0

def suggest_fixes():
    """Suggest fixes for economic issues"""
    print("\n🔧 SUGGESTED FIXES")
    print("=" * 50)
    
    print("1. **Weapon Gold Cost Scaling**:")
    print("   Current: 2000 * (2 ** (level // 20))")
    print("   Problem: Exponential growth too aggressive")
    print("   Fix: 2000 * (1.5 ** (level // 20)) or linear scaling")
    
    print("\n2. **Guild Creation Cost**:")
    print("   Current: 200,000 gold")
    print("   Problem: Too expensive for new players")
    print("   Fix: Reduce to 50,000-100,000 gold")
    
    print("\n3. **Income Sources**:")
    print("   Current: Mainly daily login + AFK")
    print("   Suggestion: Add more active income sources")
    print("   - Gate completion bonuses")
    print("   - Dungeon clear rewards")
    print("   - PvP rewards")
    
    print("\n4. **Gear Acquisition**:")
    print("   Current: No clear source for gear items")
    print("   Suggestion: Add gear to shop or rewards")
    print("   - Daily shop with gear items")
    print("   - Gate/dungeon gear drops")
    print("   - Achievement gear rewards")

def main():
    """Main analysis function"""
    print("🏦 COMPREHENSIVE ECONOMY ANALYSIS")
    print("=" * 60)
    
    # Analyze all systems
    income = analyze_income_sources()
    expenses = analyze_expenses()
    balanced = analyze_balance()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    
    if balanced:
        print("✅ Overall economy is reasonably balanced")
        print("💡 Minor optimizations suggested for better progression")
    else:
        print("❌ Economy has significant balance issues")
        print("🔧 Major fixes needed for sustainable gameplay")
        suggest_fixes()
    
    print(f"\n🎯 Key Metrics:")
    print(f"  Max Daily Income: {income['daily_max'] + income['afk_24h_lv10']:,} gold")
    print(f"  Guild Creation: {expenses['guild_creation']:,} gold")
    print(f"  High-level Upgrades: {expenses['weapon_lv100']:,} gold")
    print(f"  Achievement Rewards: {income['achievement_total']:,} gold")

if __name__ == "__main__":
    main()
