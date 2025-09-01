import random
import json
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from models.game_models import Hunter, Monster, Battle, Item, Shadow
from datetime import datetime

class BattleService:
    def __init__(self, db: Session):
        self.db = db
    
    def start_battle(self, hunter_id: int, monster_id: int) -> Dict:
        """Start a new battle between hunter and monster"""
        hunter = self.db.query(Hunter).filter(Hunter.id == hunter_id).first()
        monster = self.db.query(Monster).filter(Monster.id == monster_id).first()
        
        if not hunter or not monster:
            raise ValueError("Hunter or Monster not found")
        
        if hunter.energy < 10:
            raise ValueError("Not enough energy to battle")
        
        # Create battle record
        battle = Battle(
            hunter_id=hunter_id,
            monster_id=monster_id,
            hunter_health=hunter.max_health,
            monster_health=monster.max_health,
            battle_log=[]
        )
        
        self.db.add(battle)
        self.db.commit()
        self.db.refresh(battle)
        
        # Deduct energy
        hunter.energy -= 10
        self.db.commit()
        
        return {
            "battle_id": battle.id,
            "hunter": self._get_battle_hunter_data(hunter),
            "monster": self._get_battle_monster_data(monster),
            "status": "active",
            "turn": 1,
            "message": f"Battle started! {hunter.name} vs {monster.name}"
        }
    
    def perform_action(self, battle_id: int, action: str, target: str = None) -> Dict:
        """Perform a battle action (attack, skill, item, flee)"""
        battle = self.db.query(Battle).filter(Battle.id == battle_id).first()
        if not battle or battle.status != "active":
            raise ValueError("Battle not found or not active")
        
        hunter = battle.hunter
        monster = battle.monster
        
        # Parse battle log
        battle_log = battle.battle_log if battle.battle_log else []
        
        # Hunter's turn
        hunter_action = self._execute_hunter_action(hunter, monster, action, battle)
        battle_log.append(hunter_action)
        
        # Check if monster is defeated
        if battle.monster_health <= 0:
            return self._end_battle(battle, "won", battle_log)
        
        # Monster's turn
        monster_action = self._execute_monster_action(monster, hunter, battle)
        battle_log.append(monster_action)
        
        # Check if hunter is defeated
        if battle.hunter_health <= 0:
            return self._end_battle(battle, "lost", battle_log)
        
        # Update battle
        battle.turn += 1
        battle.battle_log = battle_log
        self.db.commit()
        
        return {
            "battle_id": battle.id,
            "hunter_health": battle.hunter_health,
            "monster_health": battle.monster_health,
            "turn": battle.turn,
            "status": "active",
            "last_actions": [hunter_action, monster_action],
            "battle_log": battle_log[-4:]  # Last 4 actions for UI
        }
    
    def _execute_hunter_action(self, hunter: Hunter, monster: Monster, action: str, battle: Battle) -> Dict:
        """Execute hunter's battle action"""
        if action == "attack":
            return self._basic_attack(hunter, monster, battle, is_hunter=True)
        elif action == "skill":
            return self._use_skill(hunter, monster, battle)
        elif action == "item":
            return self._use_item(hunter, battle)
        elif action == "flee":
            battle.status = "fled"
            return {"actor": "hunter", "action": "flee", "message": f"{hunter.name} fled from battle!"}
        else:
            return self._basic_attack(hunter, monster, battle, is_hunter=True)
    
    def _execute_monster_action(self, monster: Monster, hunter: Hunter, battle: Battle) -> Dict:
        """Execute monster's battle action"""
        # Simple AI: 70% attack, 30% skill if available
        if random.random() < 0.7 or not monster.abilities:
            return self._basic_attack(monster, hunter, battle, is_hunter=False)
        else:
            return self._monster_skill(monster, hunter, battle)
    
    def _basic_attack(self, attacker, defender, battle: Battle, is_hunter: bool) -> Dict:
        """Execute basic attack"""
        # Calculate damage
        base_damage = attacker.attack
        defense = defender.defense
        
        # Add some randomness (80-120% of base damage)
        damage_multiplier = random.uniform(0.8, 1.2)
        raw_damage = int(base_damage * damage_multiplier)
        
        # Apply defense (minimum 1 damage)
        final_damage = max(1, raw_damage - defense)
        
        # Apply damage
        if is_hunter:
            battle.monster_health = max(0, battle.monster_health - final_damage)
            target_name = battle.monster.name
        else:
            battle.hunter_health = max(0, battle.hunter_health - final_damage)
            target_name = battle.hunter.name
        
        return {
            "actor": "hunter" if is_hunter else "monster",
            "action": "attack",
            "damage": final_damage,
            "message": f"{attacker.name} attacks {target_name} for {final_damage} damage!"
        }
    
    def _use_skill(self, hunter: Hunter, monster: Monster, battle: Battle) -> Dict:
        """Use hunter skill"""
        if hunter.mana < 20:
            return {
                "actor": "hunter",
                "action": "skill_failed",
                "message": f"{hunter.name} doesn't have enough mana!"
            }
        
        # Deduct mana
        hunter.mana -= 20
        
        # Shadow Strike skill - 150% damage
        base_damage = int(hunter.attack * 1.5)
        defense = monster.defense
        final_damage = max(1, base_damage - defense)
        
        battle.monster_health = max(0, battle.monster_health - final_damage)
        
        return {
            "actor": "hunter",
            "action": "skill",
            "damage": final_damage,
            "mana_cost": 20,
            "message": f"{hunter.name} uses Shadow Strike for {final_damage} damage!"
        }
    
    def _use_item(self, hunter: Hunter, battle: Battle) -> Dict:
        """Use healing item"""
        if hunter.gold < 50:
            return {
                "actor": "hunter",
                "action": "item_failed",
                "message": f"{hunter.name} doesn't have enough gold for a potion!"
            }
        
        # Deduct gold and heal
        hunter.gold -= 50
        heal_amount = min(50, hunter.max_health - battle.hunter_health)
        battle.hunter_health += heal_amount
        
        return {
            "actor": "hunter",
            "action": "item",
            "heal": heal_amount,
            "cost": 50,
            "message": f"{hunter.name} uses a Health Potion and recovers {heal_amount} HP!"
        }
    
    def _monster_skill(self, monster: Monster, hunter: Hunter, battle: Battle) -> Dict:
        """Monster uses special skill"""
        abilities = monster.abilities if monster.abilities else []
        if not abilities:
            return self._basic_attack(monster, hunter, battle, is_hunter=False)
        
        # Use random ability
        ability = random.choice(abilities)
        
        if ability == "power_strike":
            # 130% damage attack
            base_damage = int(monster.attack * 1.3)
            defense = hunter.defense
            final_damage = max(1, base_damage - defense)
            battle.hunter_health = max(0, battle.hunter_health - final_damage)
            
            return {
                "actor": "monster",
                "action": "skill",
                "damage": final_damage,
                "message": f"{monster.name} uses Power Strike for {final_damage} damage!"
            }
        
        elif ability == "heal":
            # Heal 25% of max health
            heal_amount = min(int(monster.max_health * 0.25), monster.max_health - battle.monster_health)
            battle.monster_health += heal_amount
            
            return {
                "actor": "monster",
                "action": "heal",
                "heal": heal_amount,
                "message": f"{monster.name} heals for {heal_amount} HP!"
            }
        
        else:
            return self._basic_attack(monster, hunter, battle, is_hunter=False)
    
    def _end_battle(self, battle: Battle, result: str, battle_log: List) -> Dict:
        """End the battle and calculate rewards"""
        battle.status = result
        battle.ended_at = datetime.utcnow()
        battle.battle_log = battle_log
        
        hunter = battle.hunter
        monster = battle.monster
        
        if result == "won":
            # Calculate rewards
            exp_gained = monster.experience_reward
            gold_gained = monster.gold_reward
            
            # Apply rewards
            hunter.experience += exp_gained
            hunter.gold += gold_gained
            
            # Check for level up
            level_up = self._check_level_up(hunter)
            
            # Random item drop
            items_gained = self._calculate_item_drops(monster)
            
            battle.experience_gained = exp_gained
            battle.gold_gained = gold_gained
            battle.items_gained = items_gained
            
            # Restore some health and mana
            hunter.health = min(hunter.max_health, hunter.health + 20)
            hunter.mana = min(hunter.max_mana, hunter.mana + 10)
            
            message = f"Victory! Gained {exp_gained} EXP and {gold_gained} gold!"
            if level_up:
                message += f" Level up! Now level {hunter.level}!"
            
        else:
            exp_gained = gold_gained = 0
            items_gained = []
            level_up = False
            message = "Defeat! Better luck next time."
        
        self.db.commit()
        
        return {
            "battle_id": battle.id,
            "status": result,
            "message": message,
            "rewards": {
                "experience": exp_gained,
                "gold": gold_gained,
                "items": items_gained,
                "level_up": level_up
            },
            "battle_log": battle_log
        }
    
    def _check_level_up(self, hunter: Hunter) -> bool:
        """Check if hunter levels up and apply level up"""
        exp_needed = hunter.level * 100  # Simple formula
        
        if hunter.experience >= exp_needed:
            hunter.level += 1
            hunter.experience -= exp_needed
            
            # Increase stats on level up
            hunter.max_health += 10
            hunter.max_mana += 5
            hunter.attack += 2
            hunter.defense += 1
            hunter.health = hunter.max_health  # Full heal on level up
            hunter.mana = hunter.max_mana
            
            return True
        return False
    
    def _calculate_item_drops(self, monster: Monster) -> List[Dict]:
        """Calculate random item drops"""
        if not monster.drop_items:
            return []
        
        drops = []
        for item_data in monster.drop_items:
            if random.random() < item_data.get("drop_rate", 0.1):
                drops.append({
                    "item_id": item_data["item_id"],
                    "name": item_data["name"],
                    "rarity": item_data.get("rarity", "common")
                })
        
        return drops
    
    def _get_battle_hunter_data(self, hunter: Hunter) -> Dict:
        """Get hunter data for battle"""
        return {
            "id": hunter.id,
            "name": hunter.name,
            "level": hunter.level,
            "health": hunter.max_health,
            "max_health": hunter.max_health,
            "mana": hunter.mana,
            "max_mana": hunter.max_mana,
            "attack": hunter.attack,
            "defense": hunter.defense
        }
    
    def _get_battle_monster_data(self, monster: Monster) -> Dict:
        """Get monster data for battle"""
        return {
            "id": monster.id,
            "name": monster.name,
            "level": monster.level,
            "health": monster.max_health,
            "max_health": monster.max_health,
            "attack": monster.attack,
            "defense": monster.defense,
            "rank": monster.rank
        }
    
    def get_battle_status(self, battle_id: int) -> Dict:
        """Get current battle status"""
        battle = self.db.query(Battle).filter(Battle.id == battle_id).first()
        if not battle:
            raise ValueError("Battle not found")
        
        return {
            "battle_id": battle.id,
            "status": battle.status,
            "turn": battle.turn,
            "hunter_health": battle.hunter_health,
            "monster_health": battle.monster_health,
            "hunter": self._get_battle_hunter_data(battle.hunter),
            "monster": self._get_battle_monster_data(battle.monster),
            "battle_log": battle.battle_log[-10:] if battle.battle_log else []
        }