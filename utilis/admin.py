"""
Centralized admin system for the bot.
Only users with IDs in this list can use admin commands.
"""

# Bot Admin IDs - ONLY these users can use admin commands
BOT_ADMINS = [
    1325220545439993888,  # Admin 1
    903926304301269013,   # Admin 2
    1173222152284147732,  # Admin 3
    389564516436017162,   # Admin 4
    1322159704117350400   # Admin 5 
]

def is_bot_admin(user_id: int) -> bool:
    """
    Check if a user ID is in the bot admin list.
    
    Args:
        user_id (int): Discord user ID to check
        
    Returns:
        bool: True if user is a bot admin, False otherwise
    """
    return user_id in BOT_ADMINS

def get_admin_list() -> list:
    """
    Get the list of bot admin IDs.
    
    Returns:
        list: List of admin user IDs
    """
    return BOT_ADMINS.copy()

def add_admin(user_id: int) -> bool:
    """
    Add a user to the admin list (for runtime additions).
    Note: This doesn't persist across restarts.
    
    Args:
        user_id (int): Discord user ID to add
        
    Returns:
        bool: True if added, False if already admin
    """
    if user_id not in BOT_ADMINS:
        BOT_ADMINS.append(user_id)
        return True
    return False

def remove_admin(user_id: int) -> bool:
    """
    Remove a user from the admin list (for runtime removals).
    Note: This doesn't persist across restarts.
    
    Args:
        user_id (int): Discord user ID to remove
        
    Returns:
        bool: True if removed, False if not admin
    """
    if user_id in BOT_ADMINS:
        BOT_ADMINS.remove(user_id)
        return True
    return False
