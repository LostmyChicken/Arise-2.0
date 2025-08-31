import json
import random
import discord
from discord import app_commands
import re
from datetime import datetime, timedelta
from typing import List

# Define your color palette
SUCCESS_COLOR = 0x2ECC71
ERROR_COLOR = 0xE74C3C
INFO_COLOR = 0x3498DB
WARNING_COLOR = 0xF1C40F

# Forward declare classes to resolve potential circular import issues
class Player: pass
class ItemManager: pass
class HeroManager: pass
class SkillManager: pass
class Shadow: pass

# Now import the actual classes
from structure.player import Player
from structure.items import ItemManager
from structure.heroes import HeroManager
from structure.skills import SkillManager
from structure.shadow import Shadow
from structure.emoji import getEmoji


async def getStatWeapon(weapon_id: str, level: int):
    """Calculates the stats of a weapon based on its level."""
    weapon = await ItemManager.get(weapon_id)
    if not weapon:
        return None

    scaled_attack = weapon.attack + (3 * (level - 1))
    scaled_defense = weapon.defense + (3 * (level - 1))
    scaled_hp = weapon.health + (4 * (level - 1))
    scaled_mp = weapon.mp + (2 * (level - 1))
    total_power = scaled_attack + scaled_defense + (scaled_hp // 2)

    return {
        "attack": round(scaled_attack),
        "defense": round(scaled_defense),
        "hp": round(scaled_hp),
        "mp": round(scaled_mp),
        "total_power": round(total_power)
    }

def extractId(name: str) -> str:
    """Converts a display name into a database-friendly ID."""
    return name.lower().replace(" ", "_")

def extractName(id_str: str) -> str:
    """Converts a database ID back into a display-friendly name."""
    if id_str is None:
        return "None"
    return id_str.replace("_", " ").title()

def get_emoji_url(emoji_str: str):
    """Extracts the URL from a custom Discord emoji string."""
    if not emoji_str: return None
    match = re.match(r"<a?:\w+:(\d+)>", emoji_str)
    if match:
        emoji_id = match.group(1)
        # Assumes emojis are not animated for static URLs, adjust if needed
        return f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
    return None

def get_emoji(name: str) -> str:
    """Retrieves a custom emoji string from the emojis.json file."""
    try:
        with open('emojis.json', 'r') as file:
            emojis = json.load(file)
        return emojis.get(name, "❔")
    except (FileNotFoundError, json.JSONDecodeError):
        return "❔"

def get_image(name: str) -> str:
    """Retrieves an image URL from the images.json file."""
    try:
        with open('images.json', 'r') as file:
            images = json.load(file)
        url = images.get(name, "https://files.catbox.moe/jvxvcr.png")
        return validate_url(url)
    except (FileNotFoundError, json.JSONDecodeError):
        return "https://files.catbox.moe/jvxvcr.png"

def validate_url(url: str) -> str:
    """Validates a URL and returns a safe fallback if invalid."""
    if not url or not isinstance(url, str):
        return "https://files.catbox.moe/jvxvcr.png"

    # Check if it's a valid HTTP/HTTPS URL
    if not url.startswith(('http://', 'https://')):
        return "https://files.catbox.moe/jvxvcr.png"

    # Check for placeholder URLs
    if 'example.com' in url.lower():
        return "https://files.catbox.moe/jvxvcr.png"

    return url

def getStat(stat_type: str, level: int, base_stat: float) -> float:
    """Generic stat scaling function."""
    scaling_factors = {"HP": 6.682, "Attack": 6.186, "Defense": 6.186, "Total Power": 10.458}
    total_scaling_factor = scaling_factors.get(stat_type, 1.0)
    upgraded_stat = base_stat * (1 + total_scaling_factor * (level - 1) / 100)
    return round(upgraded_stat)

class HunterStats:
    """Data class for storing calculated hunter stats."""
    def __init__(self, hp: float, mp: float, attack: float, defense: float, total_power: float):
        self.hp = round(hp)
        self.mp = round(mp)
        self.attack = round(attack)
        self.defense = round(defense)
        self.total_power = round(total_power)

async def getStatHunter(hunter_id: str, level: int):
    """Calculates the stats of a hunter based on their level."""
    scaling_factors = {"HP": 7.682, "MP": 5, "Attack": 6.186, "Defense": 6.186, "Total Power": 10.458}
    h = await HeroManager.get(hunter_id)
    if not h: return None
    
    hp, mp, atk, defe = h.health, h.mp + 100, h.attack, h.defense
    tp = (hp / 2) + atk + defe + mp
    
    upgraded_hp = hp * (1 + scaling_factors["HP"] * (level - 1) / 100)
    upgraded_mp = mp * (1 + scaling_factors["MP"] * (level - 1) / 100)
    upgraded_atk = atk * (1 + scaling_factors["Attack"] * (level - 1) / 100)
    upgraded_defe = defe * (1 + scaling_factors["Defense"] * (level - 1) / 100)
    upgraded_tp = tp * (1 + scaling_factors["Total Power"] * (level - 1) / 100)
    
    return HunterStats(upgraded_hp, upgraded_mp, upgraded_atk, upgraded_defe, upgraded_tp)

# --- AUTOCOMPLETE FUNCTIONS (CORRECTED) ---
async def player_hunter_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    try:
        # Check if interaction is already acknowledged
        if interaction.response.is_done():
            return []

        player = await Player.get(interaction.user.id)
        if not player: return []

        choices = []
        for item_id in player.get_hunters().keys():
            hunter = await HeroManager.get(item_id)
            if hunter and current.lower() in hunter.name.lower():
                choices.append(app_commands.Choice(name=hunter.name, value=hunter.name))
        return choices[:25]
    except Exception as e:
        print(f"Error in player_hunter_autocomplete: {e}")
        return []

async def hunter_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    try:
        all_items = await HeroManager.get_all()
        if not current.strip():
            return [app_commands.Choice(name=item.name, value=item.name) for item in all_items][:25]
        return [app_commands.Choice(name=item.name, value=item.name) for item in all_items if current.lower() in item.name.lower()][:25]
    except Exception as e:
        print(f"Error in hunter_autocomplete: {e}")
        return []

async def player_item_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    try:
        player = await Player.get(interaction.user.id)
        if not player: return []

        choices = []
        for item_id in player.get_inventory().keys():
            item = await ItemManager.get(item_id)
            if item and current.lower() in item.name.lower():
                choices.append(app_commands.Choice(name=item.name, value=item.name))
        return choices[:25]
    except Exception as e:
        print(f"Error in player_item_autocomplete: {e}")
        return []

async def item_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    await interaction.response.defer()
    all_items = await ItemManager.get_all()
    if not current.strip():
        return [app_commands.Choice(name=item.name, value=item.name) for item in all_items][:25]
    return [app_commands.Choice(name=item.name, value=item.name) for item in all_items if current.lower() in item.name.lower()][:25]

async def skill_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    try:
        all_skills = await SkillManager.get_all()
        jinwoo_skills = [s for s in all_skills if s.character_id == "sung_jinwoo"]
        if not current.strip():
            return [app_commands.Choice(name=s.name, value=s.name) for s in jinwoo_skills][:25]
        return [app_commands.Choice(name=s.name, value=s.name) for s in jinwoo_skills if current.lower() in s.name.lower()][:25]
    except Exception as e:
        print(f"Error in skill_autocomplete: {e}")
        return []

async def shadow_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    await interaction.response.defer()
    all_shadows = await Shadow.get_all()
    if not current.strip():
        return [app_commands.Choice(name=s.name, value=s.name) for s in all_shadows][:25]
    return [app_commands.Choice(name=s.name, value=s.name) for s in all_shadows if current.lower() in s.name.lower()][:25]

ELEMENT_WEAKNESSES = {
    "Dark": {"weak_to": ["Light"], "effective_against": ["Light"]},
    "Light": {"weak_to": ["Dark"], "effective_against": ["Dark"]},
    "Water": {"weak_to": ["Wind"], "effective_against": ["Fire"]},
    "Fire": {"weak_to": ["Water"], "effective_against": ["Wind"]},
    "Wind": {"weak_to": ["Fire"], "effective_against": ["Water"]},
}

def PremiumCheck(player: Player):
    """Checks for active premium subscriptions and returns the cooldown reduction multiplier."""
    subscription_packs = {
        "prem3": {"timestamp": player.prem3, "reduction": 0.25},
        "prem2": {"timestamp": player.prem2, "reduction": 0.10},
        "prem1": {"timestamp": player.prem1, "reduction": 0.05},
    }
    current_time = datetime.utcnow()
    one_month = timedelta(days=30)

    for _, details in subscription_packs.items():
        if details["timestamp"]:
            # Handle both string and numeric timestamps
            try:
                if isinstance(details["timestamp"], str):
                    timestamp = float(details["timestamp"])
                else:
                    timestamp = details["timestamp"]
                sub_time = datetime.utcfromtimestamp(timestamp)
                if (sub_time + one_month) > current_time:
                    return 1 - details["reduction"]  # Return the multiplier, e.g., 0.75 for 25% reduction
            except (ValueError, TypeError):
                continue  # Skip invalid timestamps
    return 1.0  # No active subscription, no reduction

# Load monster data
try:
    with open("small.json", "r") as file:
        small_json = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    small_json = {}

def randM(rank: str):
    """Gets a random monster of a specific rank from the loaded data."""
    rank_key = f"{rank}-Rank"
    if rank_key not in small_json: return None
    return random.choice(small_json[rank_key])

def create_embed(
    title: str,
    description: str = "",
    color: int = INFO_COLOR,
    author: discord.User = None,
    thumbnail_url: str = None
) -> discord.Embed:
    """Creates a standardized embed for the bot."""

    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )

    embed.set_footer(text="Solo Leveling: Arise") # Add your bot's icon_url here

    if author:
        embed.set_author(name=f"Requested by {author.display_name}", icon_url=author.display_avatar.url if author.display_avatar else None)

    # Set thumbnail with validation
    if thumbnail_url:
        validated_url = validate_url(thumbnail_url)
        if validated_url != "https://files.catbox.moe/jvxvcr.png":  # Only set if not fallback
            embed.set_thumbnail(url=validated_url)

    return embed

def safe_set_thumbnail(embed: discord.Embed, url: str) -> None:
    """Safely set thumbnail URL with validation."""
    if url:
        validated_url = validate_url(url)
        if validated_url and validated_url.startswith(('http://', 'https://')):
            embed.set_thumbnail(url=validated_url)

def create_progress_bar(current, total, length=10):
    if total == 0:
        return "`N/A`"
    progress = current / total
    filled_length = int(length * progress)
    bar = '█' * filled_length + '░' * (length - filled_length)
    return f"[{bar}] {current:,}/{total:,}"

async def get_emoji(item_id: str):
    """Retrieves the emoji associated with an item."""
    # Use the getEmoji function from structure.emoji with the item ID
    return getEmoji(item_id)