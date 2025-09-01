import random
import json
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from models.game_models import Hunter, Item, GachaPull, Shadow
from datetime import datetime

class GachaService:
    def __init__(self, db: Session):
        self.db = db
        
        # Gacha rates
        self.rates = {
            "legendary": 0.01,  # 1%
            "epic": 0.05,       # 5%
            "rare": 0.20,       # 20%
            "common": 0.74      # 74%
        }
        
        # Pity system
        self.pity_legendary = 100  # Guaranteed legendary after 100 pulls
        self.pity_epic = 20        # Guaranteed epic after 20 pulls
    
    def single_pull(self, hunter_id: int, currency: str = "gems") -> Dict:
        """Perform a single gacha pull"""
        hunter = self.db.query(Hunter).filter(Hunter.id == hunter_id).first()
        if not hunter:
            raise ValueError("Hunter not found")
        
        cost = 100 if currency == "gems" else 1  # 100 gems or 1 ticket
        
        # Check if hunter has enough currency
        if currency == "gems" and hunter.gems < cost:
            raise ValueError("Not enough gems")
        elif currency == "tickets" and hunter.tickets < cost:
            raise ValueError("Not enough tickets")
        
        # Deduct currency
        if currency == "gems":
            hunter.gems -= cost
        else:
            hunter.tickets -= cost
        
        # Perform pull
        result = self._perform_pull(hunter_id)
        
        # Record pull
        pull_record = GachaPull(
            hunter_id=hunter_id,
            pull_type="single",
            cost=cost,
            currency=currency,
            items_received=[result]
        )
        
        self.db.add(pull_record)
        self.db.commit()
        
        return {
            "type": "single_pull",
            "cost": cost,
            "currency": currency,
            "result": result,
            "remaining_currency": hunter.gems if currency == "gems" else hunter.tickets
        }
    
    def ten_pull(self, hunter_id: int, currency: str = "gems") -> Dict:
        """Perform a 10x gacha pull with guaranteed rare+"""
        hunter = self.db.query(Hunter).filter(Hunter.id == hunter_id).first()
        if not hunter:
            raise ValueError("Hunter not found")
        
        cost = 900 if currency == "gems" else 9  # 10% discount for 10-pull
        
        # Check if hunter has enough currency
        if currency == "gems" and hunter.gems < cost:
            raise ValueError("Not enough gems")
        elif currency == "tickets" and hunter.tickets < cost:
            raise ValueError("Not enough tickets")
        
        # Deduct currency
        if currency == "gems":
            hunter.gems -= cost
        else:
            hunter.tickets -= cost
        
        # Perform 10 pulls
        results = []
        for i in range(10):
            # Guarantee at least one rare+ in 10-pull
            if i == 9 and not any(r["rarity"] in ["rare", "epic", "legendary"] for r in results):
                result = self._perform_pull(hunter_id, guaranteed_rare=True)
            else:
                result = self._perform_pull(hunter_id)
            results.append(result)
        
        # Record pull
        pull_record = GachaPull(
            hunter_id=hunter_id,
            pull_type="ten_pull",
            cost=cost,
            currency=currency,
            items_received=results
        )
        
        self.db.add(pull_record)
        self.db.commit()
        
        return {
            "type": "ten_pull",
            "cost": cost,
            "currency": currency,
            "results": results,
            "remaining_currency": hunter.gems if currency == "gems" else hunter.tickets,
            "summary": self._summarize_pulls(results)
        }
    
    def _perform_pull(self, hunter_id: int, guaranteed_rare: bool = False) -> Dict:
        """Perform a single pull and determine rarity"""
        # Check pity system
        pity_count = self._get_pity_count(hunter_id)
        
        # Determine rarity
        if pity_count["legendary"] >= self.pity_legendary:
            rarity = "legendary"
            self._reset_pity(hunter_id, "legendary")
        elif pity_count["epic"] >= self.pity_epic or guaranteed_rare:
            if guaranteed_rare and random.random() < 0.8:  # 80% chance for rare, 20% for epic+
                rarity = "rare"
            else:
                rarity = self._determine_rarity_with_pity(pity_count)
        else:
            rarity = self._determine_rarity()
        
        # Get random item of determined rarity
        item = self._get_random_item(rarity)
        
        # Create item for hunter if it's a shadow/hunter
        if item["type"] == "shadow":
            shadow = self._create_shadow_for_hunter(hunter_id, item)
            return {
                "id": shadow.id,
                "type": "shadow",
                "name": item["name"],
                "rarity": rarity,
                "stats": {
                    "attack": shadow.attack,
                    "defense": shadow.defense,
                    "health": shadow.health
                },
                "abilities": shadow.abilities,
                "is_new": True
            }
        else:
            # Add item to hunter's inventory (simplified)
            return {
                "id": item["id"],
                "type": item["type"],
                "name": item["name"],
                "rarity": rarity,
                "stats": item.get("stats", {}),
                "description": item.get("description", ""),
                "is_new": True
            }
    
    def _determine_rarity(self) -> str:
        """Determine rarity based on rates"""
        rand = random.random()
        
        if rand < self.rates["legendary"]:
            return "legendary"
        elif rand < self.rates["legendary"] + self.rates["epic"]:
            return "epic"
        elif rand < self.rates["legendary"] + self.rates["epic"] + self.rates["rare"]:
            return "rare"
        else:
            return "common"
    
    def _determine_rarity_with_pity(self, pity_count: Dict) -> str:
        """Determine rarity with pity system consideration"""
        # Increase rates based on pity
        legendary_rate = self.rates["legendary"] * (1 + pity_count["legendary"] * 0.01)
        epic_rate = self.rates["epic"] * (1 + pity_count["epic"] * 0.02)
        
        rand = random.random()
        
        if rand < legendary_rate:
            self._reset_pity(pity_count["hunter_id"], "legendary")
            return "legendary"
        elif rand < legendary_rate + epic_rate:
            self._reset_pity(pity_count["hunter_id"], "epic")
            return "epic"
        elif rand < legendary_rate + epic_rate + self.rates["rare"]:
            return "rare"
        else:
            return "common"
    
    def _get_random_item(self, rarity: str) -> Dict:
        """Get a random item of specified rarity"""
        # This would normally query a database of available items
        # For now, we'll use predefined items
        
        items_by_rarity = {
            "legendary": [
                {
                    "id": "shadow_monarch",
                    "name": "Shadow Monarch",
                    "type": "shadow",
                    "description": "The ultimate shadow soldier",
                    "base_stats": {"attack": 100, "defense": 80, "health": 200}
                },
                {
                    "id": "demon_sword",
                    "name": "Demon King's Sword",
                    "type": "weapon",
                    "description": "A legendary weapon of immense power",
                    "stats": {"attack_bonus": 50, "health_bonus": 20}
                }
            ],
            "epic": [
                {
                    "id": "shadow_knight",
                    "name": "Shadow Knight",
                    "type": "shadow",
                    "description": "An elite shadow warrior",
                    "base_stats": {"attack": 60, "defense": 50, "health": 120}
                },
                {
                    "id": "dragon_armor",
                    "name": "Dragon Scale Armor",
                    "type": "armor",
                    "description": "Armor forged from dragon scales",
                    "stats": {"defense_bonus": 30, "health_bonus": 40}
                }
            ],
            "rare": [
                {
                    "id": "shadow_soldier",
                    "name": "Shadow Soldier",
                    "type": "shadow",
                    "description": "A reliable shadow warrior",
                    "base_stats": {"attack": 35, "defense": 25, "health": 80}
                },
                {
                    "id": "steel_sword",
                    "name": "Steel Sword",
                    "type": "weapon",
                    "description": "A well-crafted steel weapon",
                    "stats": {"attack_bonus": 20}
                }
            ],
            "common": [
                {
                    "id": "shadow_minion",
                    "name": "Shadow Minion",
                    "type": "shadow",
                    "description": "A basic shadow creature",
                    "base_stats": {"attack": 20, "defense": 15, "health": 50}
                },
                {
                    "id": "iron_sword",
                    "name": "Iron Sword",
                    "type": "weapon",
                    "description": "A basic iron weapon",
                    "stats": {"attack_bonus": 10}
                }
            ]
        }
        
        available_items = items_by_rarity.get(rarity, items_by_rarity["common"])
        return random.choice(available_items)
    
    def _create_shadow_for_hunter(self, hunter_id: int, item_data: Dict) -> Shadow:
        """Create a shadow for the hunter"""
        base_stats = item_data.get("base_stats", {"attack": 20, "defense": 15, "health": 50})
        
        shadow = Shadow(
            hunter_id=hunter_id,
            name=item_data["name"],
            type="soldier",  # Could be determined by item
            rank="normal",
            level=1,
            attack=base_stats["attack"],
            defense=base_stats["defense"],
            health=base_stats["health"],
            abilities=["basic_attack"]  # Default ability
        )
        
        self.db.add(shadow)
        self.db.commit()
        self.db.refresh(shadow)
        
        return shadow
    
    def _get_pity_count(self, hunter_id: int) -> Dict:
        """Get current pity count for hunter"""
        # This would normally be stored in database
        # For now, return mock data
        return {
            "hunter_id": hunter_id,
            "legendary": 0,
            "epic": 0
        }
    
    def _reset_pity(self, hunter_id: int, rarity: str):
        """Reset pity counter for specific rarity"""
        # This would normally update database
        pass
    
    def _summarize_pulls(self, results: List[Dict]) -> Dict:
        """Summarize the results of multiple pulls"""
        summary = {
            "legendary": 0,
            "epic": 0,
            "rare": 0,
            "common": 0,
            "new_shadows": 0,
            "new_items": 0
        }
        
        for result in results:
            summary[result["rarity"]] += 1
            if result["type"] == "shadow":
                summary["new_shadows"] += 1
            else:
                summary["new_items"] += 1
        
        return summary
    
    def get_gacha_rates(self) -> Dict:
        """Get current gacha rates"""
        return {
            "rates": self.rates,
            "pity_system": {
                "legendary_pity": self.pity_legendary,
                "epic_pity": self.pity_epic
            },
            "costs": {
                "single_pull_gems": 100,
                "ten_pull_gems": 900,
                "single_pull_tickets": 1,
                "ten_pull_tickets": 9
            }
        }
    
    def get_hunter_collection(self, hunter_id: int) -> Dict:
        """Get hunter's collection of shadows and items"""
        hunter = self.db.query(Hunter).filter(Hunter.id == hunter_id).first()
        if not hunter:
            raise ValueError("Hunter not found")
        
        shadows = self.db.query(Shadow).filter(Shadow.hunter_id == hunter_id).all()
        
        return {
            "shadows": [
                {
                    "id": shadow.id,
                    "name": shadow.name,
                    "type": shadow.type,
                    "rank": shadow.rank,
                    "level": shadow.level,
                    "stats": {
                        "attack": shadow.attack,
                        "defense": shadow.defense,
                        "health": shadow.health
                    },
                    "abilities": shadow.abilities
                }
                for shadow in shadows
            ],
            "total_shadows": len(shadows),
            "rarity_counts": self._count_by_rarity(shadows)
        }
    
    def _count_by_rarity(self, shadows: List[Shadow]) -> Dict:
        """Count shadows by rarity (simplified)"""
        # This would normally check actual rarity from database
        return {
            "legendary": len([s for s in shadows if "monarch" in s.name.lower()]),
            "epic": len([s for s in shadows if "knight" in s.name.lower()]),
            "rare": len([s for s in shadows if "soldier" in s.name.lower()]),
            "common": len([s for s in shadows if "minion" in s.name.lower()])
        }