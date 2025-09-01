#!/usr/bin/env python3
"""
Tool to fix missing emojis for existing items.
This script helps add emojis to items that were created before custom emoji support.
"""

import asyncio
import json
import sys
sys.path.append('.')

from structure.items import ItemManager
from structure.emoji import getEmoji

async def find_items_without_emojis():
    """Find all items that don't have emojis in the emoji system"""
    print("🔍 Scanning for items without emojis...")
    
    items = await ItemManager.get_all()
    missing_emojis = []
    
    for item in items:
        emoji_result = getEmoji(item.id)
        custom_emoji = getattr(item, 'custom_emoji', '')
        
        # Item needs emoji if both custom_emoji is empty AND getEmoji returns ❔
        if not custom_emoji and emoji_result == "❔":
            missing_emojis.append(item)
    
    return missing_emojis

async def main():
    print("🎨 EMOJI FIXER TOOL")
    print("=" * 50)
    
    missing_items = await find_items_without_emojis()
    
    if not missing_items:
        print("✅ All items have emojis! No fixes needed.")
        return
    
    print(f"❌ Found {len(missing_items)} items without emojis:")
    print()
    
    for i, item in enumerate(missing_items[:20], 1):  # Show first 20
        print(f"{i:2d}. {item.name} (ID: {item.id})")
    
    if len(missing_items) > 20:
        print(f"    ... and {len(missing_items) - 20} more")
    
    print()
    print("🛠️  SOLUTIONS:")
    print("1. Use 'sl create item' to create new items with custom emojis")
    print("2. Upload emojis to Discord and add them to emojis.json manually")
    print("3. Use the admin emoji management system (coming soon)")
    print()
    print("📝 To add emojis manually to emojis.json:")
    print('   "item_id": "<:emoji_name:DISCORD_EMOJI_ID>"')
    print()
    
    # Show example for first few items
    print("📋 Example entries for emojis.json:")
    for item in missing_items[:5]:
        print(f'  "{item.id}": "<:{item.id}:YOUR_EMOJI_ID>",')

if __name__ == "__main__":
    asyncio.run(main())
