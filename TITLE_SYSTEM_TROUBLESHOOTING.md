# 🔧 Title System Troubleshooting Guide

## 🚨 **CURRENT ISSUE: Commands Not Loading**

The title system has been fully implemented but the commands are not loading in the bot. Here's what needs to be checked and fixed:

### **✅ What's Already Done**

#### **📁 Files Created**
- ✅ `structure/title_system.py` - Complete title management system
- ✅ `commands/titles.py` - Interactive UI commands
- ✅ Database columns added (`titles`, `active_title`)
- ✅ Profile integration completed
- ✅ All 25 titles defined and categorized

#### **🏆 Title System Features**
- ✅ 25 unique titles (19 story, 3 achievement, 2 rank, 1 special)
- ✅ 6 rarity levels (Common → Mythic)
- ✅ 5 categories (Story, Achievement, Rank, Special, Event)
- ✅ Interactive UI with dropdowns and buttons
- ✅ Profile display integration
- ✅ Auto-unlock from story progress

### **🔍 Troubleshooting Steps**

#### **Step 1: Verify Extension Loading**
The titles extension needs to be loaded in `main.py`:

```python
# In main.py, secondary_extensions list should include:
"commands.titles"
```

**Status**: ✅ FIXED - Added to main.py

#### **Step 2: Check Database Columns**
The database needs `titles` and `active_title` columns:

```sql
ALTER TABLE players ADD COLUMN titles TEXT DEFAULT '{}';
ALTER TABLE players ADD COLUMN active_title TEXT DEFAULT NULL;
```

**Status**: ✅ FIXED - Columns added manually

#### **Step 3: Test Imports**
All imports should work without errors:

```python
from structure.title_system import TitleManager, TitleCategory, Title
from commands.titles import TitleCog
```

**Status**: ⚠️ NEEDS TESTING - Fixed circular import issue

#### **Step 4: Bot Extension Loading**
The bot should load the extension without errors:

```python
await bot.load_extension("commands.titles")
```

**Status**: ❓ UNKNOWN - Needs testing

### **🛠️ Quick Fix Commands**

#### **Run the Fix Script**
```bash
cd /path/to/AriseProject/Arise
python3 fix_title_system.py
```

This script will:
- ✅ Check and fix database columns
- ✅ Test all imports
- ✅ Verify main.py configuration
- ✅ Test title functionality
- ✅ Test bot extension loading

#### **Manual Database Fix**
If database issues persist:
```python
import sqlite3
conn = sqlite3.connect('new_player.db')
cursor = conn.cursor()
cursor.execute('ALTER TABLE players ADD COLUMN titles TEXT DEFAULT "{}"')
cursor.execute('ALTER TABLE players ADD COLUMN active_title TEXT DEFAULT NULL')
conn.commit()
conn.close()
```

#### **Manual Extension Test**
Test extension loading:
```python
import asyncio
import discord
from discord.ext import commands

async def test():
    bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
    await bot.load_extension("commands.titles")
    print("Extension loaded successfully!")

asyncio.run(test())
```

### **🎯 Expected Commands After Fix**

#### **Main Commands**
- `sl titles` - Interactive title management UI
- `sl title` - Show current title
- `sl title "Title Name"` - Equip specific title
- `sl title remove` - Remove current title

#### **UI Features**
- 📋 Category browsing (Story, Achievement, Rank, Special)
- 🎯 Dropdown title selection
- 🔄 Real-time unlock checking
- 📄 Pagination for large collections
- ✅ Equip/unequip functionality

### **🔍 Diagnostic Information**

#### **Files to Check**
1. `main.py` - Extension loading
2. `structure/title_system.py` - Core system
3. `commands/titles.py` - Commands and UI
4. `structure/player.py` - Player integration
5. `commands/profile.py` - Profile display

#### **Database Schema**
```sql
-- Required columns in players table:
titles TEXT DEFAULT '{}',           -- JSON of unlocked titles
active_title TEXT DEFAULT NULL     -- Currently equipped title ID
```

#### **Import Dependencies**
```
commands.titles
├── discord
├── discord.ext.commands
├── discord.ui
├── structure.player
├── structure.title_system
└── utilis.utilis

structure.title_system
├── json
├── logging
├── typing
├── enum
├── dataclasses
└── structure.player
```

### **🚀 Next Steps**

1. **Run Fix Script**: Execute `fix_title_system.py` to diagnose all issues
2. **Check Bot Logs**: Look for extension loading errors when starting the bot
3. **Test Commands**: Try `sl titles` and `sl title` commands
4. **Verify Database**: Ensure title columns exist and are accessible
5. **Check Imports**: Verify all imports work without circular dependencies

### **📞 If Issues Persist**

If the title system still doesn't work after running the fix script:

1. **Check Bot Startup Logs** - Look for extension loading errors
2. **Verify Python Path** - Ensure all modules are accessible
3. **Test Individual Components** - Run test scripts for each part
4. **Check Discord.py Version** - Ensure compatibility with UI components
5. **Restart Bot** - Sometimes a full restart is needed after adding extensions

## 🎉 **Expected Result After Fix**

Once fixed, players will be able to:
- ✅ Use `sl titles` for interactive title management
- ✅ Browse 25 unique titles across 5 categories
- ✅ Equip titles that display on their profile
- ✅ Auto-unlock story titles as they progress
- ✅ Enjoy a fully functional title collection system

The title system will be one of the most comprehensive features in your Solo Leveling Discord bot!
