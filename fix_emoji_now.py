#!/usr/bin/env python3
"""
Quick fix to add emoji to emojis.json for existing items
"""

import json

def add_emoji_to_json(item_id, emoji_string):
    """Add emoji to emojis.json"""
    try:
        # Load current emojis
        with open('emojis.json', 'r') as f:
            emojis = json.load(f)
        
        # Add the emoji
        emojis[item_id] = emoji_string
        
        # Save back
        with open('emojis.json', 'w') as f:
            json.dump(emojis, f, indent=2)
        
        print(f"✅ Added emoji for '{item_id}': {emoji_string}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🎨 QUICK EMOJI FIX")
    print("=" * 30)
    
    # Add emoji for the 'fuck' item (replace with actual emoji)
    # You need to replace this with the actual Discord emoji format
    emoji_string = input("Enter the Discord emoji for 'fuck' item (e.g., <:fuck:123456789>): ").strip()
    
    if emoji_string:
        if add_emoji_to_json('fuck', emoji_string):
            print("🎉 Emoji added! The item should now show the custom emoji in galleries.")
            print("Note: The bot doesn't need to restart for emojis.json changes.")
        else:
            print("💥 Failed to add emoji")
    else:
        print("❌ No emoji provided")

if __name__ == "__main__":
    main()
