# 🔐 Solo Leveling Story - REALISTIC Locks & Unlocks

## ⚠️ **IMPORTANT: Based on ACTUAL Bot Features**

This guide shows what **actually gets locked and unlocked** based on the real commands and features that exist in your bot.

---

## 🔒 **WHAT'S LOCKED (Prerequisites)**

### **Mission Prerequisites**
- All 22 missions must be completed **in order**
- Each mission requires **previous mission completion**
- Each mission has **level requirements** (1-100)
- Players cannot skip ahead in Jin-Woo's story

---

## 🔓 **WHAT GETS UNLOCKED (Real Commands)**

### **📚 Prologue Chapter (Levels 1-8)**
**prologue_001** unlocks:
- `sl daily` - Daily rewards command
- `sl inventory` - View items and equipment

**prologue_002** unlocks:
- `sl upgrade` - Weapon and item upgrading
- `sl equip` - Equipment management

**prologue_003** unlocks:
- `sl party` - Party formation system
- `sl dungeonui` - Dungeon interface

### **⚡ Double Dungeon Chapter (Level 10)**
**double_dungeon_001** unlocks:
- `sl stats` - Character statistics
- `sl profile` - Player profile system

**double_dungeon_002** unlocks:
- `sl skills` - Skill management
- `sl train` - Training system

### **💪 Growth Chapters (Levels 12-35)**
**instant_dungeon_001** unlocks:
- `sl missions` - Mission system
- `sl cooldowns` - Cooldown tracking

**job_change_001** unlocks:
- `sl sacrifice` - Item sacrifice system
- `sl boost` - Boost management

**reawakening_001** unlocks:
- `sl arena` - Arena battles
- `sl leaderboard` - Ranking system

### **🏛️ Cartenon Temple Chapter (Levels 40-42)**
**cartenon_001** unlocks:
- `sl gacha` - Gacha system
- `sl pull` - Item pulling

**cartenon_002** unlocks:
- `sl shadows` - Shadow management
- `sl arise` - Shadow summoning

### **🏰 Demon Castle Chapter (Levels 45-47)**
**demon_castle_001** unlocks:
- `sl gates` - Gate exploration
- `sl fight` - Combat system

**demon_castle_002** unlocks:
- `sl raids` - Raid battles
- `sl system` - System commands

### **🔴 Red Gate Chapter (Level 50)**
**red_gate_001** unlocks:
- `sl guild` - Guild system
- `sl lb` - Leaderboard (short form)

### **👑 Shadow Monarch Chapter (Level 60)**
**shadow_monarch_001** unlocks:
- `sl view` - Advanced viewing
- `sl elements` - Element system

### **🏝️ Jeju Island Chapter (Levels 70-72)**
**jeju_island_001** unlocks:
- `sl market` - Market system
- `sl trade` - Trading system

**jeju_island_002** unlocks:
- `sl trivia` - Trivia games
- `sl vote` - Voting system

### **⚔️ Monarchs War Chapter (Levels 80-85)**
**monarchs_war_001** unlocks:
- `sl shop` - Shop system
- `sl oshi` - Oshi system

**monarchs_war_002** unlocks:
- `sl afk` - AFK system
- `sl badges` - Badge system

**monarchs_war_003** unlocks:
- `sl redeem` - Redemption system
- `sl titles` - Title system

### **💀 Final Battle Chapter (Levels 90-100)**
**final_battle_001** unlocks:
- `sl changelog` - Bot updates
- `sl tutorial` - Tutorial system

**final_battle_002** unlocks:
- `sl codex` - Information codex
- `sl gallery` - Gallery system

**final_battle_003** unlocks:
- `sl admin` - Admin commands (if admin)
- `sl patreon` - Patreon features

---

## 🎁 **ACTUAL REWARDS (What Players Get)**

### **💰 Currency & Resources**
- **Gold:** 25 → 500,000+ (scales with level)
- **XP:** 15 → 250,000+ (scales with level)
- **Diamonds:** 1 → 2,500+ (premium currency)
- **Tickets:** 1 → 250+ (dungeon access)
- **Stat Points:** 1 → 500+ (character enhancement)
- **Skill Points:** 0 → 400+ (ability upgrades)

### **🏆 Titles (8 Unique Titles)**
- "Novice Hunter" (prologue_001)
- "Licensed Hunter" (prologue_002)
- "Reawakened Hunter" (reawakening_001)
- "Temple Conqueror" (cartenon_001)
- "Demon Slayer" (demon_castle_002)
- "Red Gate Hero" (red_gate_001)
- "Shadow Monarch" (shadow_monarch_001)
- "World Savior" (final_battle_003)

### **⚔️ Items & Equipment**
- **Real items from your database** (like "the_huntsman", "moonshadow", "phoenix_soul")
- **Shadow soldiers** (demon_guard_shadow, demon_king_shadow, etc.)
- **Hunter allies** (test_golem_shadow, ice_bear_hunter, etc.)

---

## 🔧 **How It Works**

### **Lock Checking**
```python
# Check if player has unlocked a command
is_unlocked = await StoryCampaign.check_feature_unlocked(player_id, "shadows")
if not is_unlocked:
    return "🔒 Complete 'The Temple's Secret' to unlock shadow commands!"
```

### **Unlock Application**
- Features unlock **automatically** after mission completion
- **Permanent unlocks** - once unlocked, always available
- **Account-wide** per player

### **Lock Enforcement**
Commands can check story requirements:
```python
# Example in a command
unlocked, message = await StoryCampaign.require_story_completion(
    player_id, "cartenon_002", "Shadow Commands"
)
if not unlocked:
    await ctx.reply(message)
    return
```

---

## 🎮 **Player Experience**

### **Early Game (Levels 1-10)**
Players start with basic commands and gradually unlock core features like daily rewards, inventory, stats, and skills.

### **Mid Game (Levels 10-50)**
Advanced features unlock including arena, gacha, shadows, gates, and combat systems.

### **Late Game (Levels 50-100)**
End-game features like guilds, markets, trading, and admin tools become available.

---

## 🚫 **What Happens When Locked**

Players trying to use locked commands get messages like:

**🔒 Shadow Commands Locked**
*Complete the story mission **'The Temple's Secret'** to unlock shadow commands.*
*Use `sl story` to continue your journey!*

---

## ✅ **Benefits**

- **Guided Progression** - Players learn commands gradually
- **Story Integration** - Commands unlock as Jin-Woo gains power
- **Balanced Experience** - No overwhelming complexity early on
- **Clear Goals** - Always know what to unlock next
- **Authentic Journey** - Follows Solo Leveling story progression

**This creates a realistic progression system using your bot's actual features!** 🎮✨
