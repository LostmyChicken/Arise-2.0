#!/usr/bin/env python3
"""
Script to clean up broken emojis and keep only working ones.
"""

import json

# Keep only the emojis that are known to work
working_emojis = {
    "rare": "<:rare:1398824040352710666>",
    "SSR": "<:SSR:1398825441783185480>",
    "SR": "<:SR:1398825403551977543>"
}

# Write the cleaned emoji list
with open('emojis.json', 'w') as f:
    json.dump(working_emojis, f, indent=2)

print("✅ Cleaned emojis.json - removed all broken emoji entries")
print("✅ Kept only working emojis: rare, SSR, SR")
print("\nNow restart your bot and test 'sl hunters' - it should show:")
print("❔ Character Name • Type • ★☆☆☆☆ • LV 1")
print("\nTo add working emojis:")
print("1. Upload emoji to your Discord server")
print("2. Get the emoji ID (right-click emoji → Copy Link)")
print("3. Add to emojis.json: \"emoji_name\": \"<:emoji_name:EMOJI_ID>\"")
