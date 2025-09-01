# 🏰 Admin Guild Deletion System

## 🔧 **NEW ADMIN COMMANDS ADDED**

### **🗑️ Delete Guild Command**
```
sl deleteguild <guild_name_or_id>
```

**Features:**
- ✅ **Admin Only** - Restricted to bot administrators
- ✅ **Smart Search** - Find guilds by name or ID
- ✅ **Both Guild Types** - Works with Enhanced and Regular guilds
- ✅ **Safety Confirmation** - Requires explicit confirmation before deletion
- ✅ **Member Cleanup** - Automatically removes guild from all members
- ✅ **Complete Removal** - Permanently deletes all guild data

### **📋 List Guilds Command**
```
sl listguilds [page]
```

**Features:**
- ✅ **Admin Only** - Restricted to bot administrators
- ✅ **Comprehensive List** - Shows all Enhanced and Regular guilds
- ✅ **Pagination** - 10 guilds per page for easy browsing
- ✅ **Detailed Info** - Shows ID, owner, members, level for each guild
- ✅ **Summary Stats** - Total counts and breakdown by type

## 🛡️ **Security Features**

### **Admin Authorization**
- **Restricted Access** - Only users in `BOT_ADMINS` list can use commands
- **ID Verification** - Commands check admin status before execution
- **Error Handling** - Unauthorized users get clear denial messages

### **Confirmation System**
- **Interactive UI** - Buttons for confirm/cancel actions
- **Timeout Protection** - Auto-cancels after 60 seconds
- **Admin Lock** - Only the admin who initiated can confirm
- **Clear Warnings** - Shows exactly what will be deleted

### **Data Safety**
- **Member Cleanup** - Removes guild from all player accounts
- **Database Integrity** - Properly removes from both guild tables
- **Error Recovery** - Handles failures gracefully
- **Audit Trail** - Logs all deletion actions

## 🎮 **How to Use**

### **Step 1: List Guilds**
```
sl listguilds
```
This shows all guilds in the system with their details:
- Guild name and type (Enhanced/Regular)
- Guild ID for precise targeting
- Owner information
- Member count and level

### **Step 2: Delete a Guild**
```
sl deleteguild Shadow Hunters
```
or
```
sl deleteguild shadow_hunters
```

**The system will:**
1. **Search** for the guild by name or ID
2. **Display** guild information for confirmation
3. **Show Warning** about permanent deletion
4. **Wait** for your confirmation via buttons
5. **Execute** deletion if confirmed

### **Step 3: Confirmation**
- Click **🗑️ Delete Guild** to confirm deletion
- Click **❌ Cancel** to abort the operation
- Wait 60 seconds for automatic timeout/cancellation

## 📊 **What Gets Deleted**

### **Guild Data Removed**
- ✅ Guild record from database
- ✅ All guild settings and configuration
- ✅ Guild bank and resources
- ✅ Guild applications and history
- ✅ Alliance relationships

### **Member Impact**
- ✅ Guild removed from all member accounts
- ✅ Players become guildless automatically
- ✅ No impact on player stats or items
- ✅ Players can join other guilds immediately

### **Database Cleanup**
- ✅ Enhanced guilds table cleaned
- ✅ Regular guilds table cleaned
- ✅ Player guild references updated
- ✅ No orphaned data left behind

## 🔍 **Guild Search System**

### **Search Methods**
1. **By Name** - `sl deleteguild Shadow Hunters`
2. **By ID** - `sl deleteguild shadow_hunters`
3. **Case Insensitive** - Works with any capitalization
4. **Partial Matching** - Finds closest matches

### **Guild Types Supported**
- **Enhanced Guilds** - Full-featured guilds with advanced options
- **Regular Guilds** - Basic guild system for compatibility
- **Auto-Detection** - System determines guild type automatically

## ⚠️ **Important Warnings**

### **Permanent Action**
- **No Undo** - Deleted guilds cannot be recovered
- **Complete Loss** - All guild data is permanently removed
- **Member Impact** - All members lose their guild membership

### **Use Cases**
- **Inactive Guilds** - Remove abandoned guilds
- **Rule Violations** - Delete guilds that break server rules
- **Database Cleanup** - Remove test or duplicate guilds
- **Moderation** - Handle problematic guild situations

### **Best Practices**
- **Verify First** - Always check guild details before deletion
- **Communicate** - Inform guild members if possible
- **Document** - Keep records of why guilds were deleted
- **Coordinate** - Work with other admins on major deletions

## 🎯 **Admin Commands Summary**

### **Guild Management**
```bash
sl listguilds [page]     # List all guilds (paginated)
sl deleteguild <name>    # Delete guild with confirmation
sl fixguild @user        # Remove player from their guild
```

### **Access Control**
- **Admin Only** - All commands restricted to bot administrators
- **Safe Execution** - Confirmation required for destructive actions
- **Error Handling** - Clear messages for all failure cases

## 🚀 **Ready for Use**

The admin guild deletion system is now fully operational:

- ✅ **Commands Added** - `sl deleteguild` and `sl listguilds`
- ✅ **Security Implemented** - Admin-only access with confirmations
- ✅ **Safety Features** - Member cleanup and data integrity
- ✅ **User Interface** - Interactive buttons and clear feedback
- ✅ **Error Handling** - Graceful failure recovery
- ✅ **Documentation** - Complete usage instructions

### **Example Usage**
```bash
# List all guilds to see what exists
sl listguilds

# Delete a specific guild
sl deleteguild Shadow Hunters

# Confirm deletion when prompted
[Click 🗑️ Delete Guild button]

# Result: Guild permanently deleted, all members removed
```

Your Discord bot now has comprehensive admin tools for guild management! 🏰🗑️⚔️
