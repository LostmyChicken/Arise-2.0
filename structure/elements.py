"""
Elemental System for Combat
Handles elemental weaknesses, strengths, and combat calculations
"""

import discord
from structure.emoji import getEmoji
from enum import Enum
from typing import Dict, List, Tuple

class Element(Enum):
    """Elemental types in the game"""
    FIRE = "fire"
    WATER = "water"
    WIND = "wind"
    EARTH = "earth"
    LIGHT = "light"
    DARK = "dark"
    NEUTRAL = "neutral"

class ElementalSystem:
    """Manages elemental interactions and combat calculations"""
    
    # Elemental weakness chart
    # Key defeats Value (Key is strong against Value)
    WEAKNESS_CHART = {
        Element.FIRE: [Element.WIND, Element.EARTH],
        Element.WATER: [Element.FIRE, Element.EARTH],
        Element.WIND: [Element.WATER, Element.EARTH],
        Element.EARTH: [Element.FIRE, Element.WATER],
        Element.LIGHT: [Element.DARK],
        Element.DARK: [Element.LIGHT],
        Element.NEUTRAL: []  # Neutral has no advantages
    }
    
    # Damage multipliers
    SUPER_EFFECTIVE = 1.5  # 50% more damage
    NORMAL_EFFECTIVE = 1.0  # Normal damage
    NOT_VERY_EFFECTIVE = 0.75  # 25% less damage
    
    @classmethod
    def get_element_emoji(cls, element: Element) -> str:
        """Get the custom emoji for an element"""
        emoji_map = {
            Element.FIRE: getEmoji("fire_element"),      # Fire element emoji
            Element.WATER: getEmoji("water_element"),    # Water element emoji
            Element.WIND: getEmoji("wind_element"),      # Wind element emoji
            Element.EARTH: getEmoji("earth_element"),    # Earth element emoji
            Element.LIGHT: getEmoji("light_element"),    # Light element emoji
            Element.DARK: getEmoji("dark_element"),      # Dark element emoji
            Element.NEUTRAL: "⚪"                        # Neutral
        }
        return emoji_map.get(element, "❓")

    @classmethod
    def get_cube_emoji(cls, element: Element) -> str:
        """Get the custom cube emoji for an element (for inventory/crafting)"""
        cube_map = {
            Element.FIRE: getEmoji("fcube"),      # Fire cube emoji
            Element.WATER: getEmoji("icube"),     # Water/Ice cube emoji
            Element.WIND: getEmoji("wcube"),      # Wind cube emoji
            Element.EARTH: getEmoji("ecube"),     # Earth cube emoji
            Element.LIGHT: getEmoji("lcube"),     # Light cube emoji
            Element.DARK: getEmoji("dcube"),      # Dark cube emoji
            Element.NEUTRAL: "⚪"                 # Neutral
        }
        return cube_map.get(element, "❓")

    @classmethod
    def get_element_name(cls, element: Element) -> str:
        """Get the display name for an element"""
        name_map = {
            Element.FIRE: "Fire",
            Element.WATER: "Water",
            Element.WIND: "Wind",
            Element.EARTH: "Earth",
            Element.LIGHT: "Light",
            Element.DARK: "Dark",
            Element.NEUTRAL: "Neutral"
        }
        return name_map.get(element, "Unknown")
    
    @classmethod
    def get_element_color(cls, element: Element) -> discord.Color:
        """Get the color associated with an element"""
        color_map = {
            Element.FIRE: discord.Color.red(),
            Element.WATER: discord.Color.blue(),
            Element.WIND: discord.Color.green(),
            Element.EARTH: discord.Color.from_rgb(139, 69, 19),  # Brown
            Element.LIGHT: discord.Color.gold(),
            Element.DARK: discord.Color.purple(),
            Element.NEUTRAL: discord.Color.light_grey()
        }
        return color_map.get(element, discord.Color.default())
    
    @classmethod
    def calculate_damage_multiplier(cls, attacker_element: Element, defender_element: Element) -> float:
        """Calculate damage multiplier based on elemental matchup"""
        if defender_element in cls.WEAKNESS_CHART.get(attacker_element, []):
            return cls.SUPER_EFFECTIVE
        elif attacker_element in cls.WEAKNESS_CHART.get(defender_element, []):
            return cls.NOT_VERY_EFFECTIVE
        else:
            return cls.NORMAL_EFFECTIVE
    
    @classmethod
    def get_effectiveness_text(cls, multiplier: float) -> str:
        """Get effectiveness text based on multiplier"""
        if multiplier > cls.NORMAL_EFFECTIVE:
            return "**SUPER EFFECTIVE!**"
        elif multiplier < cls.NORMAL_EFFECTIVE:
            return "*Not very effective...*"
        else:
            return ""
    
    @classmethod
    def get_effectiveness_emoji(cls, multiplier: float) -> str:
        """Get effectiveness emoji based on multiplier"""
        if multiplier > cls.NORMAL_EFFECTIVE:
            return "💥"
        elif multiplier < cls.NORMAL_EFFECTIVE:
            return "💨"
        else:
            return ""
    
    @classmethod
    def create_weakness_chart_embed(cls) -> discord.Embed:
        """Create an embed showing the elemental weakness chart"""
        embed = discord.Embed(
            title="⚔️ **ELEMENTAL WEAKNESS CHART** ⚔️",
            description="Learn the strengths and weaknesses of each element!",
            color=discord.Color.blue()
        )
        
        # Create weakness chart
        chart_text = []
        for attacker, weaknesses in cls.WEAKNESS_CHART.items():
            if weaknesses:  # Skip neutral
                attacker_emoji = cls.get_element_emoji(attacker)
                attacker_name = cls.get_element_name(attacker)
                
                weakness_list = []
                for weakness in weaknesses:
                    weakness_emoji = cls.get_element_emoji(weakness)
                    weakness_name = cls.get_element_name(weakness)
                    weakness_list.append(f"{weakness_emoji} {weakness_name}")
                
                chart_text.append(f"{attacker_emoji} **{attacker_name}** → {' & '.join(weakness_list)}")
        
        embed.add_field(
            name="💥 **SUPER EFFECTIVE MATCHUPS** 💥",
            value="\n".join(chart_text),
            inline=False
        )
        
        # Add damage multipliers
        embed.add_field(
            name="📊 **DAMAGE MULTIPLIERS** 📊",
            value=(
                f"💥 **Super Effective**: {cls.SUPER_EFFECTIVE}x damage (+50%)\n"
                f"⚪ **Normal**: {cls.NORMAL_EFFECTIVE}x damage (normal)\n"
                f"💨 **Not Very Effective**: {cls.NOT_VERY_EFFECTIVE}x damage (-25%)"
            ),
            inline=False
        )
        
        # Add element list
        element_list = []
        for element in Element:
            if element != Element.NEUTRAL:
                emoji = cls.get_element_emoji(element)
                name = cls.get_element_name(element)
                element_list.append(f"{emoji} {name}")
        
        embed.add_field(
            name="🌟 **ALL ELEMENTS** 🌟",
            value=" • ".join(element_list),
            inline=False
        )
        
        embed.add_field(
            name="💡 **STRATEGY TIPS** 💡",
            value=(
                "• Choose hunters with advantageous elements\n"
                "• Mix different elements in your team\n"
                "• Check enemy elements before battle\n"
                "• Use elemental cubes to enhance attacks"
            ),
            inline=False
        )
        
        embed.set_footer(text="Use 'sl elements' to view this chart anytime!")
        
        return embed
    
    @classmethod
    def get_random_element(cls) -> Element:
        """Get a random element (excluding neutral)"""
        import random
        elements = [e for e in Element if e != Element.NEUTRAL]
        return random.choice(elements)
    
    @classmethod
    def parse_element_from_string(cls, element_str: str) -> Element:
        """Parse element from string input"""
        element_str = element_str.lower().strip()
        
        element_map = {
            "fire": Element.FIRE,
            "f": Element.FIRE,
            "red": Element.FIRE,
            "water": Element.WATER,
            "w": Element.WATER,
            "ice": Element.WATER,
            "blue": Element.WATER,
            "wind": Element.WIND,
            "air": Element.WIND,
            "green": Element.WIND,
            "earth": Element.EARTH,
            "ground": Element.EARTH,
            "brown": Element.EARTH,
            "light": Element.LIGHT,
            "holy": Element.LIGHT,
            "yellow": Element.LIGHT,
            "gold": Element.LIGHT,
            "dark": Element.DARK,
            "shadow": Element.DARK,
            "purple": Element.DARK,
            "neutral": Element.NEUTRAL,
            "normal": Element.NEUTRAL,
            "none": Element.NEUTRAL
        }
        
        return element_map.get(element_str, Element.NEUTRAL)

class ElementalCombat:
    """Handles elemental combat calculations and effects"""
    
    @classmethod
    def calculate_elemental_damage(cls, base_damage: int, attacker_element: Element, 
                                 defender_element: Element) -> Tuple[int, float, str]:
        """
        Calculate final damage with elemental modifiers
        Returns: (final_damage, multiplier, effectiveness_text)
        """
        multiplier = ElementalSystem.calculate_damage_multiplier(attacker_element, defender_element)
        final_damage = int(base_damage * multiplier)
        effectiveness_text = ElementalSystem.get_effectiveness_text(multiplier)
        
        return final_damage, multiplier, effectiveness_text
    
    @classmethod
    def create_combat_result_text(cls, attacker_name: str, attacker_element: Element,
                                defender_name: str, defender_element: Element,
                                damage: int, multiplier: float) -> str:
        """Create formatted combat result text with elemental info"""
        attacker_emoji = ElementalSystem.get_element_emoji(attacker_element)
        defender_emoji = ElementalSystem.get_element_emoji(defender_element)
        effectiveness_emoji = ElementalSystem.get_effectiveness_emoji(multiplier)
        effectiveness_text = ElementalSystem.get_effectiveness_text(multiplier)
        
        result = f"{attacker_emoji} **{attacker_name}** attacks {defender_emoji} **{defender_name}**"
        result += f"\n💥 **{damage:,}** damage dealt!"
        
        if effectiveness_text:
            result += f"\n{effectiveness_emoji} {effectiveness_text}"
        
        return result
