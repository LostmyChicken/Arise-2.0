import json
import logging
import aiosqlite
from typing import Dict, List, Optional, Set
from enum import Enum
from structure.skills import Skill, SkillType, Element, EffectType

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("skill_trees", "skill_trees.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "skill_trees.db"

DATABASE_PATH = get_database_path()

class SkillTreeType(Enum):
    """Different skill tree paths"""
    SHADOW_MONARCH = "Shadow Monarch"
    WARRIOR = "Warrior"
    MAGE = "Mage"
    ASSASSIN = "Assassin"
    TANK = "Tank"
    SUPPORT = "Support"

class SkillNode:
    """Individual skill node in a skill tree"""
    
    def __init__(self, skill_id: str, skill: Skill, prerequisites: List[str] = None, 
                 level_requirement: int = 1, skill_points_cost: int = 1, max_level: int = 5):
        self.skill_id = skill_id
        self.skill = skill
        self.prerequisites = prerequisites or []
        self.level_requirement = level_requirement
        self.skill_points_cost = skill_points_cost
        self.max_level = max_level

class SkillTree:
    """Complete skill tree for a specific path"""
    
    def __init__(self, tree_type: SkillTreeType, name: str, description: str):
        self.tree_type = tree_type
        self.name = name
        self.description = description
        self.nodes: Dict[str, SkillNode] = {}
    
    def add_node(self, node: SkillNode):
        """Add a skill node to the tree"""
        self.nodes[node.skill_id] = node
    
    def get_available_skills(self, player_level: int, unlocked_skills: Set[str]) -> List[SkillNode]:
        """Get skills that can be unlocked by the player"""
        available = []
        
        for node in self.nodes.values():
            # Check level requirement
            if player_level < node.level_requirement:
                continue
            
            # Check if already unlocked
            if node.skill_id in unlocked_skills:
                continue
            
            # Check prerequisites
            prerequisites_met = all(prereq in unlocked_skills for prereq in node.prerequisites)
            if not prerequisites_met:
                continue
            
            available.append(node)
        
        return available

class SkillTreeSystem:
    """
    Enhanced Solo Leveling style Skill Tree System
    """
    
    # Predefined skill trees
    SKILL_TREES: Dict[SkillTreeType, SkillTree] = {}
    
    @classmethod
    def initialize_skill_trees(cls):
        """Initialize all skill trees with their nodes"""
        
        # Shadow Monarch Tree
        shadow_tree = SkillTree(
            SkillTreeType.SHADOW_MONARCH,
            "Shadow Monarch",
            "The path of the Shadow Monarch - command the undead and darkness itself"
        )
        
        # Shadow Monarch Skills - Authentic Solo Leveling abilities
        shadow_tree.add_node(SkillNode(
            "shadow_extraction",
            Skill("shadow_extraction", SkillType.ULTIMATE, "Shadow Extraction",
                  [EffectType.DAMAGE], 150, 50, Element.DARK),
            [], 10, 5, 10
        ))

        shadow_tree.add_node(SkillNode(
            "dagger_rush",
            Skill("dagger_rush", SkillType.BASIC, "Dagger Rush",
                  [EffectType.DAMAGE, EffectType.CRIT_BOOST], 80, 25, Element.DARK),
            [], 5, 3, 8
        ))

        shadow_tree.add_node(SkillNode(
            "stealth",
            Skill("stealth", SkillType.QTE, "Stealth",
                  [EffectType.BUFF], 0, 30, Element.DARK),
            ["dagger_rush"], 8, 4, 6
        ))

        shadow_tree.add_node(SkillNode(
            "shadow_save",
            Skill("shadow_save", SkillType.QTE, "Shadow Save",
                  [EffectType.HEAL, EffectType.BUFF], 100, 40, Element.DARK),
            ["stealth"], 15, 6, 5
        ))

        shadow_tree.add_node(SkillNode(
            "shadow_army",
            Skill("shadow_army", SkillType.ULTIMATE, "Arise (Shadow Army)",
                  [EffectType.AREA_DAMAGE, EffectType.BUFF], 200, 80, Element.DARK),
            ["shadow_extraction", "shadow_save"], 25, 10, 5
        ))

        shadow_tree.add_node(SkillNode(
            "rulers_authority",
            Skill("rulers_authority", SkillType.ULTIMATE, "Ruler's Authority",
                  [EffectType.AREA_DAMAGE, EffectType.STUN], 250, 100, Element.DARK),
            ["shadow_army"], 35, 15, 4
        ))

        shadow_tree.add_node(SkillNode(
            "monarch_domain",
            Skill("monarch_domain", SkillType.ULTIMATE, "Domain of the Monarch",
                  [EffectType.AREA_DAMAGE, EffectType.DEBUFF, EffectType.INVINCIBILITY], 400, 150, Element.DARK),
            ["rulers_authority"], 50, 25, 3
        ))

        shadow_tree.add_node(SkillNode(
            "shadow_exchange",
            Skill("shadow_exchange", SkillType.QTE, "Shadow Exchange",
                  [EffectType.BUFF], 0, 60, Element.DARK),
            ["monarch_domain"], 60, 30, 1
        ))
        
        # Warrior Tree
        warrior_tree = SkillTree(
            SkillTreeType.WARRIOR,
            "Warrior",
            "The path of the warrior - master of weapons and physical combat"
        )
        
        # Warrior Skills - Physical combat mastery
        warrior_tree.add_node(SkillNode(
            "basic_swordsmanship",
            Skill("basic_swordsmanship", SkillType.BASIC, "Basic Swordsmanship",
                  [EffectType.DAMAGE], 60, 10, Element.FIRE),
            [], 3, 2, 10
        ))

        warrior_tree.add_node(SkillNode(
            "vital_strike",
            Skill("vital_strike", SkillType.BASIC, "Vital Strike",
                  [EffectType.DAMAGE, EffectType.CRIT_BOOST], 80, 15, Element.FIRE),
            ["basic_swordsmanship"], 8, 3, 8
        ))

        warrior_tree.add_node(SkillNode(
            "bloodlust",
            Skill("bloodlust", SkillType.QTE, "Bloodlust",
                  [EffectType.BUFF, EffectType.LIFE_STEAL], 0, 25, Element.FIRE),
            ["vital_strike"], 12, 4, 6
        ))

        warrior_tree.add_node(SkillNode(
            "sprint",
            Skill("sprint", SkillType.QTE, "Sprint",
                  [EffectType.BUFF], 0, 20, Element.WIND),
            ["bloodlust"], 15, 5, 5
        ))

        warrior_tree.add_node(SkillNode(
            "sword_mastery",
            Skill("sword_mastery", SkillType.QTE, "Advanced Swordsmanship",
                  [EffectType.BUFF, EffectType.CRIT_BOOST], 0, 35, Element.FIRE),
            ["sprint"], 20, 8, 4
        ))

        warrior_tree.add_node(SkillNode(
            "berserker_rage",
            Skill("berserker_rage", SkillType.ULTIMATE, "Berserker's Rage",
                  [EffectType.BUFF, EffectType.AREA_DAMAGE], 150, 50, Element.FIRE),
            ["sword_mastery"], 30, 12, 3
        ))

        warrior_tree.add_node(SkillNode(
            "devastating_blow",
            Skill("devastating_blow", SkillType.ULTIMATE, "Devastating Blow",
                  [EffectType.DAMAGE, EffectType.STUN], 300, 80, Element.FIRE),
            ["berserker_rage"], 40, 18, 2
        ))
        
        # Mage Tree
        mage_tree = SkillTree(
            SkillTreeType.MAGE,
            "Mage",
            "The path of magic - harness elemental forces and arcane power"
        )
        
        # Mage Skills - Elemental magic mastery
        mage_tree.add_node(SkillNode(
            "mana_recovery",
            Skill("mana_recovery", SkillType.QTE, "Mana Recovery",
                  [EffectType.HEAL], 50, 0, Element.LIGHT),
            [], 2, 1, 10
        ))

        mage_tree.add_node(SkillNode(
            "fireball",
            Skill("fireball", SkillType.BASIC, "Fireball",
                  [EffectType.DAMAGE], 70, 20, Element.FIRE),
            ["mana_recovery"], 5, 3, 10
        ))

        mage_tree.add_node(SkillNode(
            "ice_shard",
            Skill("ice_shard", SkillType.BASIC, "Ice Shard",
                  [EffectType.DAMAGE, EffectType.STUN], 60, 18, Element.WATER),
            ["mana_recovery"], 5, 3, 10
        ))

        mage_tree.add_node(SkillNode(
            "wind_blade",
            Skill("wind_blade", SkillType.BASIC, "Wind Blade",
                  [EffectType.DAMAGE, EffectType.CRIT_BOOST], 65, 16, Element.WIND),
            ["fireball", "ice_shard"], 10, 4, 8
        ))

        mage_tree.add_node(SkillNode(
            "lightning_bolt",
            Skill("lightning_bolt", SkillType.QTE, "Lightning Bolt",
                  [EffectType.DAMAGE, EffectType.AREA_DAMAGE], 120, 35, Element.WIND),
            ["wind_blade"], 18, 6, 6
        ))

        mage_tree.add_node(SkillNode(
            "flame_tornado",
            Skill("flame_tornado", SkillType.ULTIMATE, "Flame Tornado",
                  [EffectType.AREA_DAMAGE, EffectType.DAMAGE], 200, 60, Element.FIRE),
            ["lightning_bolt"], 25, 10, 4
        ))

        mage_tree.add_node(SkillNode(
            "blizzard",
            Skill("blizzard", SkillType.ULTIMATE, "Blizzard",
                  [EffectType.AREA_DAMAGE, EffectType.STUN], 180, 70, Element.WATER),
            ["lightning_bolt"], 25, 10, 4
        ))

        mage_tree.add_node(SkillNode(
            "meteor",
            Skill("meteor", SkillType.ULTIMATE, "Meteor",
                  [EffectType.AREA_DAMAGE, EffectType.DAMAGE], 350, 120, Element.FIRE),
            ["flame_tornado", "blizzard"], 45, 25, 2
        ))

        # Add Resurrection to Mage tree as ultimate healing skill
        mage_tree.add_node(SkillNode(
            "resurrection",
            Skill("resurrection", SkillType.ULTIMATE, "Resurrection",
                  [EffectType.HEAL, EffectType.BUFF], 200, 120, Element.LIGHT),
            ["meteor"], 60, 30, 1  # Single level, very expensive ultimate
        ))
        
        # Assassin Tree
        assassin_tree = SkillTree(
            SkillTreeType.ASSASSIN,
            "Assassin",
            "The path of shadows - strike from darkness with precision and speed"
        )
        
        assassin_tree.add_node(SkillNode(
            "stealth", 
            Skill("stealth", SkillType.QTE, "Stealth", 
                  [EffectType.BUFF], 0, 25, Element.DARK),
            [], 8, 3, 8
        ))
        
        assassin_tree.add_node(SkillNode(
            "backstab", 
            Skill("backstab", SkillType.BASIC, "Backstab", 
                  [EffectType.DAMAGE, EffectType.CRIT_BOOST], 100, 20, Element.DARK),
            ["stealth"], 12, 5, 10
        ))
        
        assassin_tree.add_node(SkillNode(
            "shadow_clone", 
            Skill("shadow_clone", SkillType.ULTIMATE, "Shadow Clone", 
                  [EffectType.DAMAGE, EffectType.AREA_DAMAGE], 180, 70, Element.DARK),
            ["backstab"], 35, 18, 5
        ))
        
        # Tank Tree
        tank_tree = SkillTree(
            SkillTreeType.TANK,
            "Tank",
            "The path of defense - protect allies and endure any assault"
        )
        
        tank_tree.add_node(SkillNode(
            "shield_wall", 
            Skill("shield_wall", SkillType.QTE, "Shield Wall", 
                  [EffectType.SHIELD, EffectType.BUFF], 0, 30, Element.LIGHT),
            [], 6, 3, 8
        ))
        
        tank_tree.add_node(SkillNode(
            "taunt",
            Skill("taunt", SkillType.BASIC, "Taunt",
                  [EffectType.DEBUFF], 0, 15, Element.LIGHT),
            ["shield_wall"], 10, 4, 10
        ))
        
        tank_tree.add_node(SkillNode(
            "fortress", 
            Skill("fortress", SkillType.ULTIMATE, "Fortress", 
                  [EffectType.SHIELD, EffectType.INVINCIBILITY], 0, 80, Element.LIGHT),
            ["taunt"], 45, 25, 3
        ))
        
        # Support Tree
        support_tree = SkillTree(
            SkillTreeType.SUPPORT,
            "Support",
            "The path of healing - aid allies and turn the tide of battle"
        )
        
        support_tree.add_node(SkillNode(
            "heal",
            Skill("heal", SkillType.BASIC, "Heal",
                  [EffectType.HEAL], 0, 25, Element.LIGHT),
            [], 4, 2, 10
        ))

        support_tree.add_node(SkillNode(
            "group_heal",
            Skill("group_heal", SkillType.QTE, "Group Heal",
                  [EffectType.HEAL], 0, 40, Element.LIGHT),
            ["heal"], 18, 8, 8
        ))

        support_tree.add_node(SkillNode(
            "resurrection",
            Skill("resurrection", SkillType.ULTIMATE, "Resurrection",
                  [EffectType.HEAL, EffectType.BUFF], 0, 120, Element.LIGHT),
            ["group_heal"], 60, 30, 1
        ))
        
        # Store all trees
        cls.SKILL_TREES[SkillTreeType.SHADOW_MONARCH] = shadow_tree
        cls.SKILL_TREES[SkillTreeType.WARRIOR] = warrior_tree
        cls.SKILL_TREES[SkillTreeType.MAGE] = mage_tree
        cls.SKILL_TREES[SkillTreeType.ASSASSIN] = assassin_tree
        cls.SKILL_TREES[SkillTreeType.TANK] = tank_tree
        cls.SKILL_TREES[SkillTreeType.SUPPORT] = support_tree
    
    @classmethod
    async def initialize(cls):
        """Initialize the skill tree database"""
        cls.initialize_skill_trees()
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS player_skill_trees (
                    player_id TEXT,
                    tree_type TEXT,
                    unlocked_skills TEXT DEFAULT '[]',
                    skill_levels TEXT DEFAULT '{}',
                    total_points_spent INTEGER DEFAULT 0,
                    PRIMARY KEY (player_id, tree_type)
                )
            """)
            await db.commit()
    
    @classmethod
    async def get_player_skill_tree(cls, player_id: str, tree_type: SkillTreeType) -> Dict:
        """Get player's progress in a specific skill tree"""
        # Ensure skill trees are initialized
        if not cls.SKILL_TREES:
            cls.initialize_skill_trees()

        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("""
                SELECT unlocked_skills, skill_levels, total_points_spent 
                FROM player_skill_trees 
                WHERE player_id = ? AND tree_type = ?
            """, (player_id, tree_type.value))
            
            result = await cursor.fetchone()
            await cursor.close()
            
            if result:
                unlocked_skills = json.loads(result[0])
                skill_levels = json.loads(result[1])
                total_points_spent = result[2]
            else:
                unlocked_skills = []
                skill_levels = {}
                total_points_spent = 0
            
            return {
                'unlocked_skills': set(unlocked_skills),
                'skill_levels': skill_levels,
                'total_points_spent': total_points_spent,
                'tree': cls.SKILL_TREES.get(tree_type)
            }
    
    @classmethod
    async def can_unlock_skill(cls, player_id: str, tree_type: SkillTreeType, skill_id: str,
                              player_level: int, available_points: int) -> Dict:
        """Check if a player can unlock a skill"""
        # Ensure skill trees are initialized
        if not cls.SKILL_TREES:
            cls.initialize_skill_trees()

        tree_data = await cls.get_player_skill_tree(player_id, tree_type)
        tree = tree_data['tree']

        if not tree or skill_id not in tree.nodes:
            return {'can_unlock': False, 'reason': 'Skill not found'}

        node = tree.nodes[skill_id]

        # Check level requirement
        if player_level < node.level_requirement:
            return {'can_unlock': False, 'reason': f'Requires level {node.level_requirement}'}

        # Check skill points requirement
        if available_points < node.skill_points_cost:
            return {'can_unlock': False, 'reason': f'Requires {node.skill_points_cost} skill points'}

        # Check prerequisites
        for prereq in node.prerequisites:
            if prereq not in tree_data['unlocked_skills']:
                return {'can_unlock': False, 'reason': f'Requires skill: {prereq}'}

        # Check if already unlocked
        if skill_id in tree_data['unlocked_skills']:
            return {'can_unlock': False, 'reason': 'Already unlocked'}

        return {'can_unlock': True, 'reason': 'Ready to unlock'}

    @classmethod
    async def unlock_skill(cls, player_id: str, tree_type: SkillTreeType, skill_id: str,
                          player_level: int, available_points: int) -> Dict:
        """Attempt to unlock a skill for a player"""
        tree_data = await cls.get_player_skill_tree(player_id, tree_type)
        tree = tree_data['tree']
        
        if not tree or skill_id not in tree.nodes:
            return {'success': False, 'message': 'Skill not found'}
        
        node = tree.nodes[skill_id]
        
        # Check if already unlocked
        if skill_id in tree_data['unlocked_skills']:
            return {'success': False, 'message': 'Skill already unlocked'}
        
        # Check level requirement
        if player_level < node.level_requirement:
            return {'success': False, 'message': f'Requires level {node.level_requirement}'}
        
        # Check skill points
        if available_points < node.skill_points_cost:
            return {'success': False, 'message': f'Requires {node.skill_points_cost} skill points'}
        
        # Check prerequisites
        for prereq in node.prerequisites:
            if prereq not in tree_data['unlocked_skills']:
                return {'success': False, 'message': f'Missing prerequisite: {prereq}'}
        
        # Unlock the skill
        tree_data['unlocked_skills'].add(skill_id)
        tree_data['skill_levels'][skill_id] = 1
        tree_data['total_points_spent'] += node.skill_points_cost
        
        # Save to database
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                INSERT OR REPLACE INTO player_skill_trees 
                (player_id, tree_type, unlocked_skills, skill_levels, total_points_spent)
                VALUES (?, ?, ?, ?, ?)
            """, (
                player_id, tree_type.value,
                json.dumps(list(tree_data['unlocked_skills'])),
                json.dumps(tree_data['skill_levels']),
                tree_data['total_points_spent']
            ))
            await db.commit()
        
        return {
            'success': True, 
            'message': f'Unlocked {node.skill.name}!',
            'skill': node.skill,
            'points_spent': node.skill_points_cost
        }
    
    @classmethod
    def get_tree_by_type(cls, tree_type: SkillTreeType) -> Optional[SkillTree]:
        """Get skill tree by type"""
        # Ensure skill trees are initialized
        if not cls.SKILL_TREES:
            cls.initialize_skill_trees()
        return cls.SKILL_TREES.get(tree_type)
    
    @classmethod
    def get_all_trees(cls) -> Dict[SkillTreeType, SkillTree]:
        """Get all skill trees"""
        # Ensure skill trees are initialized
        if not cls.SKILL_TREES:
            cls.initialize_skill_trees()
        return cls.SKILL_TREES.copy()

    @classmethod
    async def upgrade_skill(cls, player_id: str, tree_type: SkillTreeType, skill_id: str,
                           player_level: int, available_points: int) -> Dict:
        """Upgrade an existing skill to the next level"""
        # Ensure skill trees are initialized
        if not cls.SKILL_TREES:
            cls.initialize_skill_trees()

        tree_data = await cls.get_player_skill_tree(player_id, tree_type)
        tree = tree_data['tree']

        if not tree or skill_id not in tree.nodes:
            return {'success': False, 'message': 'Skill not found'}

        node = tree.nodes[skill_id]

        # Check if skill is unlocked
        if skill_id not in tree_data['unlocked_skills']:
            return {'success': False, 'message': 'Skill not unlocked yet'}

        # Get current skill level
        current_level = tree_data['skill_levels'].get(skill_id, 1)

        # Check if already at max level
        if current_level >= node.max_level:
            return {'success': False, 'message': f'Skill already at max level ({node.max_level})'}

        # Calculate upgrade cost (increases with level)
        upgrade_cost = node.skill_points_cost * current_level

        # Check skill points
        if available_points < upgrade_cost:
            return {'success': False, 'message': f'Requires {upgrade_cost} skill points to upgrade'}

        # Upgrade the skill
        tree_data['skill_levels'][skill_id] = current_level + 1
        tree_data['total_points_spent'] += upgrade_cost

        # Save to database
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                INSERT OR REPLACE INTO player_skill_trees
                (player_id, tree_type, unlocked_skills, skill_levels, total_points_spent)
                VALUES (?, ?, ?, ?, ?)
            """, (
                player_id, tree_type.value,
                json.dumps(list(tree_data['unlocked_skills'])),
                json.dumps(tree_data['skill_levels']),
                tree_data['total_points_spent']
            ))
            await db.commit()

        return {
            'success': True,
            'message': f'Successfully upgraded {node.skill.name} to level {current_level + 1}!',
            'new_level': current_level + 1,
            'cost': upgrade_cost
        }

    @classmethod
    async def reset_player_skill_tree(cls, player_id: str, tree_type: SkillTreeType):
        """Reset a player's skill tree completely"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                # Delete the player's skill tree data
                await db.execute("""
                    DELETE FROM player_skill_trees
                    WHERE player_id = ? AND tree_type = ?
                """, (player_id, tree_type.value))
                await db.commit()

                return True

        except Exception as e:
            logging.error(f"Error resetting skill tree for player {player_id}: {e}")
            return False

    @classmethod
    async def integrate_with_skill_manager(cls, player_id: str, skill_id: str):
        """Integrate skill tree unlock with existing SkillManager"""
        try:
            from structure.skills import SkillManager, Skill
            from structure.player import Player

            # Get the skill from the skill tree
            if not cls.SKILL_TREES:
                cls.initialize_skill_trees()

            # Find the skill in all trees
            skill_obj = None
            for tree in cls.SKILL_TREES.values():
                if skill_id in tree.nodes:
                    skill_obj = tree.nodes[skill_id].skill
                    break

            if skill_obj:
                # Save the skill to the database using SkillManager
                await SkillManager.save(skill_obj)

                # Add skill to player's skills collection
                player = await Player.get(int(player_id))
                if player:
                    # Add to player's skills dictionary
                    if not hasattr(player, 'skills') or player.skills is None:
                        player.skills = {}
                    player.skills[skill_id] = {
                        'level': 1,
                        'unlocked': True,
                        'tree_type': None  # Will be set by the calling method
                    }
                    await player.save()
                    return True
        except Exception as e:
            print(f"Error integrating with SkillManager: {e}")
            import traceback
            traceback.print_exc()
        return False

    @classmethod
    async def register_all_skills_with_manager(cls):
        """Register all skill tree skills with SkillManager for gallery display"""
        try:
            from structure.skills import SkillManager

            if not cls.SKILL_TREES:
                cls.initialize_skill_trees()

            registered_count = 0
            for tree_type, tree in cls.SKILL_TREES.items():
                for skill_id, node in tree.nodes.items():
                    # Save each skill to the database
                    await SkillManager.save(node.skill)
                    registered_count += 1

            logging.info(f"Registered {registered_count} skill tree skills with SkillManager")
            return True

        except Exception as e:
            logging.error(f"Error registering skill tree skills: {e}")
            return False
