from enum import Enum
import json
import re

def getEmoji(name: str, as_url: bool = False):
    """Retrieves a custom emoji string or its URL from the emojis.json file."""
    try:
        with open('emojis.json', 'r') as file:
            emojis = json.load(file)
        emoji_str = emojis.get(name, "❔")

        if as_url:
            match = re.match(r"<a?:\w+:(\d+)>", emoji_str)
            if match:
                emoji_id = match.group(1)
                return f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
            return None # Return None if it's not a custom emoji or no match
        
        return emoji_str
    except (FileNotFoundError, json.JSONDecodeError):
        return "❔" if not as_url else None

def get_image(name: str) -> str:
    """Retrieves the image URL of an item or character based on its name."""
    # Try to get from images.json first, fallback to default image
    try:
        with open('images.json', 'r') as file:
            images = json.load(file)
        return images.get(name, "https://files.catbox.moe/jvxvcr.png")  # Default fallback image
    except (FileNotFoundError, json.JSONDecodeError):
        return "https://files.catbox.moe/jvxvcr.png"  # Default fallback image

class Rarity(Enum):
    UR = "UR"
    SSR = "SSR"
    SUPER_RARE = "Super Rare"
    CUSTOM = "Custom"

class ItemClass(Enum):
    DARK = "dark"
    EARTH = "earth"
    FIRE = "fire"
    LIGHT = "light"
    WATER = "water"
    WIND = "wind"

class SkillType(Enum):
    BASIC = "Basic"
    QTE = "QTE"             
    ULTIMATE = "Ultimate"

def getSkillTypeEmoji(SkillType):
    rarity_emoji_dict = {
        "basic": "<:Hunter_Basic_Skill:1325820007849918516>",
        "qte": "<:qte:1325923175997112371>",
        "ultimate": "<:ult:1325924065730367518>"
    }

    # Normalize the rarity input
    rarity = SkillType.strip().lower()

    if rarity in rarity_emoji_dict:
        return rarity_emoji_dict[rarity]
    else:
        return f"Emoji not found for skill '{rarity}'"

def getRarityEmoji(rarity):
    rarity_emoji_dict = {
        "ur": "💎",  # Diamond emoji for UR rarity
        "ssr": "<:SSR:1398825441783185480>",
        "super rare": "<:SR:1398825403551977543>",
        "rare": "<:rare:1398824040352710666>",  # Keep for badge display
        "custom":"<:custom:1355912227089154262>"
    }

    # Handle malformed rarity data (extract actual rarity from description)
    if rarity and isinstance(rarity, str):
        rarity = rarity.strip()

        # Check if rarity contains known rarity keywords
        rarity_lower = rarity.lower()
        if "ur" in rarity_lower and "super" not in rarity_lower:
            rarity = "ur"
        elif "ssr" in rarity_lower:
            rarity = "ssr"
        elif "super rare" in rarity_lower or "sr" in rarity_lower:
            rarity = "super rare"
        elif "rare" in rarity_lower:
            rarity = "rare"
        elif "custom" in rarity_lower:
            rarity = "custom"
        else:
            # Try to extract just the rarity part if it's at the end
            rarity = rarity.lower()
    else:
        rarity = str(rarity).lower() if rarity else "rare"

    if rarity in rarity_emoji_dict:
        return rarity_emoji_dict[rarity]
    else:
        # Default to rare emoji if rarity not found
        return rarity_emoji_dict.get("rare", "❔")


def getClassEmoji(item_class):
    """Get elemental emoji using the centralized emoji system."""
    item_class = item_class.strip().lower()

    # Map class names to emoji keys
    class_to_emoji = {
        "dark": "dark_element",
        "earth": "earth_element",
        "fire": "fire_element",
        "light": "light_element",
        "water": "water_element",
        "wind": "wind_element"
    }

    emoji_key = class_to_emoji.get(item_class)
    if emoji_key:
        return getEmoji(emoji_key)
    else:
        return f"❔"  # Return question mark for unknown classes