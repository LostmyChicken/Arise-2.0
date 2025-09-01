#!/usr/bin/env python3
"""
Quick tool to add emojis to emojis.json
Usage: python3 add_emoji_to_json.py item_id emoji_string
Example: python3 add_emoji_to_json.py chicken_gun "<:chicken_gun:1234567890>"
"""

import json
import sys

def add_emoji(item_id, emoji_string):
    """Add an emoji to emojis.json"""
    try:
        # Load current emojis
        with open('emojis.json', 'r') as f:
            emojis = json.load(f)
        
        # Add the new emoji
        emojis[item_id] = emoji_string
        
        # Save back to file
        with open('emojis.json', 'w') as f:
            json.dump(emojis, f, indent=2)
        
        print(f"✅ Added emoji for '{item_id}': {emoji_string}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 add_emoji_to_json.py <item_id> <emoji_string>")
        print("Example: python3 add_emoji_to_json.py chicken_gun \"<:chicken_gun:1234567890>\"")
        print()
        print("Missing emojis found:")
        print("- chicken_gun")
        print("- test") 
        print("- demon_king_daggers")
        print("- vulcan's_rage")
        print("- slime_sword")
        print("- mondragon_rifle")
        print("- shadow's_grasp")
        print("- stormbringer")
        print("- jingke")
        return
    
    item_id = sys.argv[1]
    emoji_string = sys.argv[2]
    
    if add_emoji(item_id, emoji_string):
        print("🎉 Emoji added successfully!")
        print("Now test with 'sl gallery weapons' to see the change!")
    else:
        print("💥 Failed to add emoji")

if __name__ == "__main__":
    main()
