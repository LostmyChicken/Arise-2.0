# 🔧 Channel-Specific Command Management System

## Overview
This system allows server administrators to enable or disable specific bot commands in specific channels. This is perfect for creating specialized channels (like combat-only channels, economy-only channels, etc.) or preventing spam in certain areas.

## 🎯 Key Features
- ✅ **Channel-specific control**: Enable/disable commands per channel
- ✅ **Interactive UI**: Easy-to-use buttons and dropdowns
- ✅ **Quick commands**: Fast enable/disable with simple commands
- ✅ **Complete command list**: View all available commands organized by category
- ✅ **Persistent settings**: Settings are saved and persist across bot restarts
- ✅ **Permission-based**: Only users with "Manage Channels" permission can modify settings

## 📋 Complete Command List

### 👤 Player & Profile Commands
- `start` - Create your hunter profile
- `profile` - View your hunter profile
- `stats` - View and manage your stats
- `inventory` - View your inventory
- `team` - Manage your hunter team
- `equip` - Equip items and weapons
- `afk` - Set AFK status and rewards

### ⚔️ Combat & Battle Commands
- `fight` - Fight other players
- `arena` - Enter the arena
- `dungeonui` - Access dungeon system
- `gates` - Enter Solo Leveling gates
- `skills` - View and manage skills
- `system` - System awakening features

### 🎲 Gacha & Item Commands
- `pull` - Pull for new hunters/weapons
- `gacha` - Access gacha system
- `upgrade` - Upgrade your items
- `sacrifice` - Sacrifice items for rewards
- `oshi` - Oshi system features
- `redeem` - Redeem codes and rewards

### 🏰 Guild & Social Commands
- `guild` - Guild management
- `leaderboard` - View leaderboards
- `lb` - Leaderboard shortcut
- `vote` - Vote for the bot

### 💰 Economy & Trading Commands
- `daily` - Claim daily rewards
- `shop` - Access the shop
- `trade` - Trade with other players
- `market` - Access the market
- `boost` - Use boost items

### 🎮 Activities & Quest Commands
- `trivia` - Play trivia games
- `train` - Training activities
- `missions` - View and complete missions
- `tutorial` - Access tutorials
- `cooldowns` - View command cooldowns

### 🔧 Utility & Help Commands
- `help` - Get help and command info
- `fixuser` - Fix user data issues
- `unstuck` - Fix stuck states
- `ping` - Check bot latency
- `changelog` - View recent changes
- `view` - View detailed item/character info

### 👑 Admin Commands
- `adminhelp` - Admin command help
- `give` - Give items to players
- `create` - Create new content
- `fix` - Fix various issues
- `raid` - Raid management

## 🚀 How to Use

### Main Management Command
```
sl channelcommands
```
**Permission Required**: Manage Channels

Opens an interactive interface where you can:
- 🚫 **Disable Commands**: Select commands to disable in the current channel
- ✅ **Enable Commands**: Re-enable previously disabled commands
- 📋 **View All Commands**: See all commands with their current status

### Quick Commands

#### Disable a Single Command
```
sl disablecommand <command_name>
```
**Example**: `sl disablecommand gates`
**Result**: Disables the `gates` command in the current channel

#### Enable a Single Command
```
sl enablecommand <command_name>
```
**Example**: `sl enablecommand gates`
**Result**: Re-enables the `gates` command in the current channel

#### List All Commands
```
sl listcommands
```
Shows all available commands organized by category

## 💡 Usage Examples

### Example 1: Combat-Only Channel
To create a channel where only combat commands work:
1. Run `sl channelcommands`
2. Click "🚫 Disable Commands"
3. Select all non-combat commands (everything except fight, arena, dungeonui, gates, skills, system)
4. Result: Channel only allows combat-related commands

### Example 2: Economy-Only Channel
To create a channel for trading and economy:
1. Run `sl channelcommands`
2. Disable all commands except: daily, shop, trade, market, boost, inventory, profile
3. Result: Channel focused on economic activities

### Example 3: Disable Spam Commands
To reduce spam in a general chat:
1. Run `sl disablecommand pull`
2. Run `sl disablecommand gacha`
3. Run `sl disablecommand fight`
4. Result: Prevents spammy commands in general chat

## 🔒 Security Features

### Protected Commands
These commands **cannot** be disabled to ensure system functionality:
- `channelcommands` - Channel management interface
- `disablecommand` - Quick disable command
- `enablecommand` - Quick enable command  
- `listcommands` - Command listing

### Permission Requirements
- **Manage Channels** permission required to modify command settings
- Only the command initiator can use the interactive buttons
- Settings are per-channel and don't affect other channels

## 📊 Technical Details

### Database Storage
- Settings stored in `data/channel_commands.db`
- Persistent across bot restarts
- Efficient caching for fast lookups

### Performance
- Cached command states for minimal database queries
- Non-blocking command checks
- Minimal impact on command execution speed

## 🆘 Troubleshooting

### Command Still Works After Disabling
- Wait a few seconds for cache to update
- Try running the command again
- Check if you have the correct permissions

### Can't Access Management Commands
- Ensure you have "Manage Channels" permission
- Management commands themselves cannot be disabled

### Want to Reset All Settings
Contact a bot administrator to clear channel settings if needed.

## 🎯 Best Practices

1. **Plan Your Channels**: Think about what each channel should allow before configuring
2. **Test Settings**: Try commands after configuring to ensure they work as expected
3. **Communicate Changes**: Let your server members know about channel-specific restrictions
4. **Use Categories**: Disable entire categories of commands for cleaner channel purposes
5. **Keep Help Available**: Always keep `help` and `listcommands` enabled for user guidance

---

**Need Help?** Use `sl help` or contact your server administrators!
