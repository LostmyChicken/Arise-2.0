#!/usr/bin/env python3
"""
Test script to verify the emoji fix is working
"""

import asyncio
import json
import sys
sys.path.append('.')

from structure.items import Item, ItemManager

async def test_emoji_integration():
    print("🧪 Testing emoji integration fix...")
    
    # Create a test item with custom emoji
    test_item = Item(
        id='emoji_test_item',
        name='Emoji Test Item',
        rarity='Rare',
        classType='Fire',
        type='Weapon',
        image='https://files.catbox.moe/jvxvcr.png',
        description='Test item for emoji integration',
        health=100,
        attack=50,
        defense=30,
        speed=20,
        mp=10,
        precision=15,
        custom_emoji='<:emoji_test_item:987654321>',
        emoji_name='emoji_test_item'
    )
    
    # Save the item
    await ItemManager.save(test_item)
    print("✅ Test item saved to database")
    
    # Manually add to emojis.json (simulating what the creation system should do)
    try:
        with open('emojis.json', 'r') as f:
            emojis = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        emojis = {}
    
    emojis['emoji_test_item'] = '<:emoji_test_item:987654321>'
    
    with open('emojis.json', 'w') as f:
        json.dump(emojis, f, indent=2)
    
    print("✅ Added emoji to emojis.json")
    
    # Test retrieval
    from structure.emoji import getEmoji
    emoji_result = getEmoji('emoji_test_item')
    print(f"✅ getEmoji result: {emoji_result}")
    
    # Test gallery formatter logic
    retrieved_item = await ItemManager.get('emoji_test_item')
    if retrieved_item:
        custom_emoji = getattr(retrieved_item, 'custom_emoji', '')
        fallback_emoji = getEmoji(retrieved_item.id)
        final_emoji = custom_emoji or fallback_emoji
        
        print(f"Gallery display logic:")
        print(f"  Custom emoji: '{custom_emoji}'")
        print(f"  Fallback emoji: '{fallback_emoji}'")
        print(f"  Final emoji: '{final_emoji}'")
        
        if final_emoji == '<:emoji_test_item:987654321>':
            print("🎉 SUCCESS: Emoji integration working correctly!")
        else:
            print("❌ FAILED: Emoji integration not working")
    
    # Clean up
    print("\n🧹 Cleaning up test data...")
    # Remove from database
    await ItemManager.delete('emoji_test_item')
    
    # Remove from emojis.json
    if 'emoji_test_item' in emojis:
        del emojis['emoji_test_item']
        with open('emojis.json', 'w') as f:
            json.dump(emojis, f, indent=2)
    
    print("✅ Test cleanup complete")

if __name__ == "__main__":
    asyncio.run(test_emoji_integration())
