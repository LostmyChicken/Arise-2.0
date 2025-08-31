from datetime import datetime
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from structure.player import Player

LEADERBOARD_PATH = Path("leaderboard.json")

class Leaderboard:
    @staticmethod
    async def refresh():
        """Refresh the leaderboard data and store top 15 players for each category"""
        try:
            all_players = await Player.all()
            
            # Sort players by each metric
            gold_leaderboard = sorted(all_players, key=lambda p: p.gold, reverse=True)[:15]
            diamond_leaderboard = sorted(all_players, key=lambda p: p.diamonds, reverse=True)[:15]
            streak_leaderboard = sorted(all_players, key=lambda p: p.aStreak, reverse=True)[:15]
            
            # Convert to serializable data
            leaderboard_data = {
                "gold": [Leaderboard._player_to_dict(p) for p in gold_leaderboard],
                "diamonds": [Leaderboard._player_to_dict(p) for p in diamond_leaderboard],
                "streak": [Leaderboard._player_to_dict(p) for p in streak_leaderboard],
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            # Save to file
            with open(LEADERBOARD_PATH, "w") as f:
                json.dump(leaderboard_data, f, indent=2)
                
            return True
        except Exception as e:
            logging.error(f"Error refreshing leaderboard: {e}", exc_info=True)
            return False

    @staticmethod
    def _player_to_dict(player) -> Dict[str, Any]:
        """Convert player object to dictionary for JSON serialization"""
        return {
            "id": player.id,
            "name": player.name,
            "gold": player.gold,
            "diamonds": player.diamonds,
            "aStreak": player.aStreak
            # Add any other relevant fields you want to display
        }

    @staticmethod
    def load() -> Dict[str, Any]:
        """Load leaderboard data from file"""
        try:
            if not LEADERBOARD_PATH.exists():
                return {"gold": [], "diamonds": [], "streak": []}
                
            with open(LEADERBOARD_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading leaderboard: {e}", exc_info=True)
            return {"gold": [], "diamonds": [], "streak": []}

    @staticmethod
    async def display(category: str = "gold") -> str:
        """
        Generate a formatted leaderboard string for the given category
        Categories: "gold", "diamonds", or "streak"
        """
        valid_categories = ["gold", "diamonds", "streak"]
        if category not in valid_categories:
            return f"Invalid category. Available: {', '.join(valid_categories)}"
            
        data = Leaderboard.load()
        leaderboard = data.get(category, [])
        
        if not leaderboard:
            return "No leaderboard data available. Try refreshing first."
        
        # Determine emoji and title based on category
        category_info = {
            "gold": {"emoji": "💰", "title": "Gold"},
            "diamonds": {"emoji": "💎", "title": "Diamonds"},
            "streak": {"emoji": "🔥", "title": "Achievement Streak"}
        }
        
        emoji = category_info[category]["emoji"]
        title = category_info[category]["title"]
        
        # Generate the leaderboard message
        message = [f"{emoji} **{title} Leaderboard** {emoji}"]
        
        for idx, player in enumerate(leaderboard, 1):
            if category == "gold":
                value = f"{player['gold']:,}g"
            elif category == "diamonds":
                value = f"{player['diamonds']:,}💎"
            else:  # streak
                value = f"{player['aStreak']} days"
                
            message.append(f"{idx}. **{player['name']}** - {value}")
        
        message.append(f"\nLast updated: {data.get('last_updated', 'unknown')}")
        return "\n".join(message)