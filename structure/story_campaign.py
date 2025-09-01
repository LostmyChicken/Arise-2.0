import json
import aiosqlite
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from structure.player import Player
from structure.emoji import getEmoji
from utilis.database_setup import DATABASE_PATH

class StoryChapter(Enum):
    """Story chapters following Solo Leveling narrative"""
    PROLOGUE = "prologue"
    DOUBLE_DUNGEON = "double_dungeon"
    FIRST_REAWAKENING = "first_reawakening"
    CARTENON_TEMPLE = "cartenon_temple"
    DEMON_CASTLE = "demon_castle"
    RED_GATE = "red_gate"
    SHADOW_MONARCH = "shadow_monarch"
    JEJU_ISLAND = "jeju_island"
    MONARCHS_WAR = "monarchs_war"
    FINAL_BATTLE = "final_battle"

class StoryDifficulty(Enum):
    """Story mission difficulty levels"""
    NORMAL = "normal"
    HARD = "hard"
    NIGHTMARE = "nightmare"

@dataclass
class StoryReward:
    """Rewards for completing story missions"""
    gold: int = 0
    xp: int = 0
    diamonds: int = 0
    tickets: int = 0
    items: List[str] = None
    hunters: List[str] = None
    shadows: List[str] = None
    stat_points: int = 0
    skill_points: int = 0
    title: str = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
        if self.hunters is None:
            self.hunters = []
        if self.shadows is None:
            self.shadows = []

@dataclass
class StoryMission:
    """Individual story mission"""
    id: str
    name: str
    description: str
    chapter: StoryChapter
    difficulty: StoryDifficulty
    level_requirement: int
    prerequisites: List[str]  # List of mission IDs that must be completed first
    objectives: List[str]  # List of objectives to complete
    rewards: StoryReward
    enemies: List[Dict]  # Enemy data for battles
    dialogue: List[Dict]  # Story dialogue and cutscenes
    unlocks: List[str] = None  # What this mission unlocks (features, areas, etc.)
    
    def __post_init__(self):
        if self.unlocks is None:
            self.unlocks = []

class StoryCampaign:
    """Main story campaign system"""
    
    # Story missions data - following Solo Leveling narrative
    STORY_MISSIONS = {
        # PROLOGUE CHAPTER
        "prologue_001": StoryMission(
            id="prologue_001",
            name="The Weakest Hunter",
            description="Begin your journey as the world's weakest E-rank hunter.",
            chapter=StoryChapter.PROLOGUE,
            difficulty=StoryDifficulty.NORMAL,
            level_requirement=1,
            prerequisites=[],
            objectives=[
                "Complete your first dungeon",
                "Defeat 3 goblins",
                "Survive the encounter"
            ],
            rewards=StoryReward(
                gold=25,      # Level 1 * 25 = 25 gold (balanced)
                xp=15,        # Level 1 * 15 = 15 XP (balanced)
                stat_points=1, # Much more reasonable
                title="Novice Hunter"
            ),
            enemies=[
                {"name": "Goblin Scout", "level": 1, "hp": 50, "attack": 15, "defense": 5}
            ],
            dialogue=[
                {"speaker": "System", "text": "Welcome to the world of hunters. You are currently E-rank, the lowest possible rank."},
                {"speaker": "Narrator", "text": "In a world where monsters emerge from gates, hunters are humanity's last hope."},
                {"speaker": "System", "text": "Your first mission: survive your first dungeon raid."}
            ],
            unlocks=["daily_quests", "basic_training"]
        ),

        "prologue_002": StoryMission(
            id="prologue_002",
            name="Hunter's License",
            description="Obtain your official hunter's license and join the Hunter's Association.",
            chapter=StoryChapter.PROLOGUE,
            difficulty=StoryDifficulty.NORMAL,
            level_requirement=5,
            prerequisites=["prologue_001"],
            objectives=[
                "Visit the Hunter's Association",
                "Complete the registration process",
                "Receive your E-rank license"
            ],
            rewards=StoryReward(
                gold=163,     # Level 5 * 25 * 1.3 (milestone) = 163 gold
                xp=98,        # Level 5 * 15 * 1.3 (milestone) = 98 XP
                diamonds=1,   # Level 5 // 20 * 1.5 (milestone) = 1 diamond
                tickets=1,    # Level 5 // 20 = 1 ticket
                stat_points=1, # Much more reasonable
                title="Licensed Hunter"
            ),
            enemies=[],
            dialogue=[
                {"speaker": "Association Staff", "text": "Welcome to the Hunter's Association. Here's your E-rank license."},
                {"speaker": "Sung Jin-Woo", "text": "Finally... I'm officially a hunter. Time to prove myself."},
                {"speaker": "System", "text": "Hunter registration complete. Access to official raids granted."}
            ],
            unlocks=["hunter_association", "official_raids"]
        ),

        "prologue_003": StoryMission(
            id="prologue_003",
            name="First Steps",
            description="Learn the basics of being a hunter and complete your first real mission.",
            chapter=StoryChapter.PROLOGUE,
            difficulty=StoryDifficulty.NORMAL,
            level_requirement=8,
            prerequisites=["prologue_002"],
            objectives=[
                "Reach level 5",
                "Complete 3 daily quests",
                "Upgrade your first weapon"
            ],
            rewards=StoryReward(
                gold=200,     # Level 8 * 25 = 200 gold
                xp=120,       # Level 8 * 15 = 120 XP
                tickets=1,    # Level 8 // 20 = 1 ticket
                items=["the_huntsman"],  # Using real item from database
                stat_points=1  # Much more reasonable
            ),
            enemies=[
                {"name": "Goblin Warrior", "level": 3, "hp": 80, "attack": 20, "defense": 8}
            ],
            dialogue=[
                {"speaker": "Guild Master", "text": "You're showing promise, hunter. Keep training and you might survive longer than most E-ranks."},
                {"speaker": "System", "text": "Daily training is essential for growth. Complete your daily quests to become stronger."}
            ],
            unlocks=["weapon_upgrade", "skill_system"]
        ),
        
        # DOUBLE DUNGEON CHAPTER - The turning point
        "double_dungeon_001": StoryMission(
            id="double_dungeon_001",
            name="The Double Dungeon",
            description="Enter the mysterious double dungeon that will change your fate forever.",
            chapter=StoryChapter.DOUBLE_DUNGEON,
            difficulty=StoryDifficulty.HARD,
            level_requirement=10,
            prerequisites=["prologue_003"],
            objectives=[
                "Enter the double dungeon",
                "Survive the statue room",
                "Witness the massacre"
            ],
            rewards=StoryReward(
                gold=275,     # Level 10 * 25 * 1.1 (double dungeon) = 275 gold
                xp=165,       # Level 10 * 15 * 1.1 = 165 XP
                diamonds=1,   # Level 10 // 20 = 1 diamond
                title="Survivor"
            ),
            enemies=[
                {"name": "Stone Statue", "level": 15, "hp": 500, "attack": 50, "defense": 30}
            ],
            dialogue=[
                {"speaker": "Narrator", "text": "The double dungeon... a place where nightmares become reality."},
                {"speaker": "System", "text": "WARNING: Extreme danger detected. Survival probability: 2%"},
                {"speaker": "Sung Jin-Woo", "text": "I... I have to survive. I can't die here!"}
            ],
            unlocks=["system_awakening"]
        ),
        
        "double_dungeon_002": StoryMission(
            id="double_dungeon_002",
            name="System Awakening",
            description="Awaken to the mysterious System that will grant you unlimited growth.",
            chapter=StoryChapter.DOUBLE_DUNGEON,
            difficulty=StoryDifficulty.HARD,
            level_requirement=10,
            prerequisites=["double_dungeon_001"],
            objectives=[
                "Accept the System's offer",
                "Complete the first daily quest",
                "Unlock your true potential"
            ],
            rewards=StoryReward(
                gold=275,     # Level 10 * 25 * 1.1 = 275 gold
                xp=165,       # Level 10 * 15 * 1.1 = 165 XP
                diamonds=1,   # Level 10 // 20 = 1 diamond
                stat_points=1, # Much more reasonable
                skill_points=1, # Much more reasonable
                title="System User"
            ),
            enemies=[],  # No combat, story mission
            dialogue=[
                {"speaker": "System", "text": "CONGRATULATIONS! You have been selected as the Player."},
                {"speaker": "System", "text": "You now have access to unlimited growth potential."},
                {"speaker": "Sung Jin-Woo", "text": "This... this changes everything. I'm no longer the weakest!"}
            ],
            unlocks=["leveling_system", "stat_allocation", "skill_trees"]
        ),

        # INSTANT DUNGEON CHAPTER
        "instant_dungeon_001": StoryMission(
            id="instant_dungeon_001",
            name="Daily Quest Penalty",
            description="Face the consequences of ignoring the System's Daily Quest in the terrifying Penalty Zone.",
            chapter=StoryChapter.DOUBLE_DUNGEON,
            difficulty=StoryDifficulty.HARD,
            level_requirement=12,
            prerequisites=["double_dungeon_002"],
            objectives=[
                "Survive the Penalty Zone",
                "Defeat the Giant Centipedes",
                "Learn the importance of Daily Quests"
            ],
            rewards=StoryReward(
                gold=8000,
                xp=4000,
                diamonds=20,
                stat_points=10,
                title="Penalty Survivor"
            ),
            enemies=[
                {"name": "Giant Centipede", "level": 8, "hp": 300, "attack": 35, "defense": 15}
            ],
            dialogue=[
                {"speaker": "System", "text": "PENALTY QUEST: Survive for 4 hours in the Penalty Zone."},
                {"speaker": "Sung Jin-Woo", "text": "I can't ignore the System anymore... I have to get stronger!"},
                {"speaker": "System", "text": "Daily Quests are mandatory. Failure will result in penalties."}
            ],
            unlocks=["daily_quest_system", "penalty_awareness"]
        ),

        # JOB CHANGE CHAPTER
        "job_change_001": StoryMission(
            id="job_change_001",
            name="The Trial of Strength",
            description="Undergo the dangerous Job Change Quest to unlock your true potential and class.",
            chapter=StoryChapter.FIRST_REAWAKENING,
            difficulty=StoryDifficulty.NIGHTMARE,
            level_requirement=30,
            prerequisites=["instant_dungeon_001"],
            objectives=[
                "Accept the Job Change Quest",
                "Defeat the Trial Knight",
                "Unlock your hidden class"
            ],
            rewards=StoryReward(
                gold=25000,
                xp=15000,
                diamonds=100,
                stat_points=100,
                skill_points=50,
                title="Necromancer"
            ),
            enemies=[
                {"name": "Trial Knight", "level": 30, "hp": 3500, "attack": 100, "defense": 80}
            ],
            dialogue=[
                {"speaker": "System", "text": "JOB CHANGE QUEST AVAILABLE: Complete the trials to unlock your true potential."},
                {"speaker": "Knight of Trials", "text": "Show me your resolve, challenger. Prove that you are worthy of power!"},
                {"speaker": "System", "text": "CONGRATULATIONS! You have unlocked the hidden class: NECROMANCER."}
            ],
            unlocks=["necromancer_class", "shadow_extraction", "death_magic"]
        ),

        # FIRST REAWAKENING CHAPTER
        "reawakening_001": StoryMission(
            id="reawakening_001",
            name="The Reawakening Test",
            description="Take the reawakening test to officially change your hunter rank.",
            chapter=StoryChapter.FIRST_REAWAKENING,
            difficulty=StoryDifficulty.NORMAL,
            level_requirement=35,
            prerequisites=["job_change_001"],
            objectives=[
                "Reach level 25",
                "Defeat the test golem",
                "Prove your new strength"
            ],
            rewards=StoryReward(
                gold=15000,
                xp=7500,
                diamonds=50,
                hunters=["test_golem_shadow"],
                title="Reawakened Hunter"
            ),
            enemies=[
                {"name": "Test Golem", "level": 25, "hp": 1000, "attack": 75, "defense": 50}
            ],
            dialogue=[
                {"speaker": "Test Administrator", "text": "This is impossible... your mana reading is off the charts!"},
                {"speaker": "Sung Jin-Woo", "text": "I'm not the same person who entered that double dungeon."}
            ],
            unlocks=["shadow_extraction", "advanced_dungeons"]
        ),

        # CARTENON TEMPLE CHAPTER
        "cartenon_001": StoryMission(
            id="cartenon_001",
            name="The Cartenon Temple",
            description="Enter the mysterious Cartenon Temple and face the trials within.",
            chapter=StoryChapter.CARTENON_TEMPLE,
            difficulty=StoryDifficulty.HARD,
            level_requirement=40,
            prerequisites=["reawakening_001"],
            objectives=[
                "Enter the Cartenon Temple",
                "Defeat the temple guardians",
                "Reach the inner sanctum"
            ],
            rewards=StoryReward(
                gold=25000,
                xp=15000,
                diamonds=100,
                tickets=10,
                stat_points=25,
                skill_points=15,
                items=["moonshadow", "phoenix_soul"],  # Using real items from database
                title="Temple Conqueror"
            ),
            enemies=[
                {"name": "Temple Guardian", "level": 35, "hp": 2000, "attack": 120, "defense": 80},
                {"name": "Stone Sentinel", "level": 32, "hp": 1500, "attack": 100, "defense": 100}
            ],
            dialogue=[
                {"speaker": "System", "text": "WARNING: High-level magical energy detected. Proceed with caution."},
                {"speaker": "Sung Jin-Woo", "text": "This place... it's different from other dungeons. The mana here is ancient."},
                {"speaker": "Temple Voice", "text": "Only the worthy may pass. Prove your strength, young hunter."}
            ],
            unlocks=["advanced_magic", "temple_rewards"]
        ),

        "cartenon_002": StoryMission(
            id="cartenon_002",
            name="The Temple's Secret",
            description="Discover the ancient secrets hidden within the Cartenon Temple.",
            chapter=StoryChapter.CARTENON_TEMPLE,
            difficulty=StoryDifficulty.HARD,
            level_requirement=42,
            prerequisites=["cartenon_001"],
            objectives=[
                "Solve the temple puzzles",
                "Defeat the High Priest",
                "Claim the temple's treasure"
            ],
            rewards=StoryReward(
                gold=30000,
                xp=18000,
                diamonds=150,
                tickets=15,
                stat_points=30,
                skill_points=20,
                shadows=["high_priest_shadow"],
                title="Temple Master"
            ),
            enemies=[
                {"name": "High Priest", "level": 38, "hp": 3000, "attack": 150, "defense": 120}
            ],
            dialogue=[
                {"speaker": "High Priest", "text": "You dare defile this sacred place, mortal?"},
                {"speaker": "Sung Jin-Woo", "text": "I'm here for answers, not destruction."},
                {"speaker": "System", "text": "Shadow Extraction is now possible on this target."}
            ],
            unlocks=["priest_magic", "shadow_mastery"]
        ),

        # DEMON CASTLE CHAPTER
        "demon_castle_001": StoryMission(
            id="demon_castle_001",
            name="Demon Castle Entrance",
            description="Approach the foreboding Demon Castle and face its outer defenses.",
            chapter=StoryChapter.DEMON_CASTLE,
            difficulty=StoryDifficulty.HARD,
            level_requirement=45,
            prerequisites=["cartenon_002"],
            objectives=[
                "Approach the Demon Castle",
                "Defeat the outer guards",
                "Find the castle entrance"
            ],
            rewards=StoryReward(
                gold=35000,
                xp=20000,
                diamonds=200,
                tickets=20,
                stat_points=35,
                skill_points=25,
                shadows=["demon_guard_shadow"],
                title="Castle Challenger"
            ),
            enemies=[
                {"name": "Demon Guard", "level": 45, "hp": 3000, "attack": 150, "defense": 100},
                {"name": "Hell Hound", "level": 42, "hp": 2500, "attack": 140, "defense": 80}
            ],
            dialogue=[
                {"speaker": "System", "text": "DANGER: Demonic energy levels are extremely high. Retreat is advised."},
                {"speaker": "Sung Jin-Woo", "text": "I've come too far to turn back now. These demons... they're strong."},
                {"speaker": "Demon Guard", "text": "No mortal shall pass into our lord's domain!"}
            ],
            unlocks=["demon_extraction", "castle_access"]
        ),

        "demon_castle_002": StoryMission(
            id="demon_castle_002",
            name="The Demon King's Throne",
            description="Face the Demon King in his throne room and claim victory.",
            chapter=StoryChapter.DEMON_CASTLE,
            difficulty=StoryDifficulty.NIGHTMARE,
            level_requirement=47,
            prerequisites=["demon_castle_001"],
            objectives=[
                "Navigate the castle interior",
                "Defeat the Demon King",
                "Claim the throne room"
            ],
            rewards=StoryReward(
                gold=50000,
                xp=30000,
                diamonds=300,
                tickets=30,
                stat_points=50,
                skill_points=40,
                shadows=["demon_king_shadow"],
                title="Demon Slayer"
            ),
            enemies=[
                {"name": "Demon King", "level": 50, "hp": 5000, "attack": 200, "defense": 150}
            ],
            dialogue=[
                {"speaker": "Demon King", "text": "A human dares to challenge me in my own domain?"},
                {"speaker": "Sung Jin-Woo", "text": "I'm not just any human. I am the Shadow Monarch."},
                {"speaker": "System", "text": "Congratulations! You have defeated a Monarch-level enemy."}
            ],
            unlocks=["monarch_recognition", "demon_army"]
        ),

        # RED GATE CHAPTER
        "red_gate_001": StoryMission(
            id="red_gate_001",
            name="Red Gate Emergency",
            description="Respond to a Red Gate emergency and save trapped hunters.",
            chapter=StoryChapter.RED_GATE,
            difficulty=StoryDifficulty.NIGHTMARE,
            level_requirement=50,
            prerequisites=["demon_castle_002"],
            objectives=[
                "Enter the Red Gate",
                "Locate trapped hunters",
                "Defeat the Ice Bears",
                "Evacuate all survivors"
            ],
            rewards=StoryReward(
                gold=60000,
                xp=35000,
                diamonds=400,
                tickets=40,
                stat_points=60,
                skill_points=50,
                hunters=["ice_bear_hunter"],
                shadows=["ice_bear_shadow"],
                title="Red Gate Hero"
            ),
            enemies=[
                {"name": "Ice Bear", "level": 55, "hp": 6000, "attack": 220, "defense": 180},
                {"name": "Frost Elemental", "level": 52, "hp": 4500, "attack": 200, "defense": 150}
            ],
            dialogue=[
                {"speaker": "Trapped Hunter", "text": "Help! We've been trapped here for days! The cold is killing us!"},
                {"speaker": "Sung Jin-Woo", "text": "Don't worry. I'll get you all out of here safely."},
                {"speaker": "System", "text": "New skill unlocked: Shadow Exchange. Use it to save the hunters."}
            ],
            unlocks=["shadow_exchange", "red_gate_mastery"]
        ),

        # SHADOW MONARCH CHAPTER
        "shadow_monarch_001": StoryMission(
            id="shadow_monarch_001",
            name="Shadow Monarch Awakening",
            description="Embrace your true nature as the Shadow Monarch and command the army of the dead.",
            chapter=StoryChapter.SHADOW_MONARCH,
            difficulty=StoryDifficulty.NIGHTMARE,
            level_requirement=60,
            prerequisites=["red_gate_001"],
            objectives=[
                "Accept your role as Shadow Monarch",
                "Command your shadow army",
                "Defeat the rival monarch"
            ],
            rewards=StoryReward(
                gold=100000,
                xp=50000,
                diamonds=500,
                tickets=50,
                stat_points=100,
                skill_points=75,
                shadows=["beru_shadow", "igris_shadow", "tank_shadow"],
                title="Shadow Monarch"
            ),
            enemies=[
                {"name": "Rival Monarch", "level": 70, "hp": 10000, "attack": 300, "defense": 200}
            ],
            dialogue=[
                {"speaker": "System", "text": "You have awakened as the true Shadow Monarch. Your power is now limitless."},
                {"speaker": "Sung Jin-Woo", "text": "I understand now. This is my destiny. I am the Shadow Monarch."},
                {"speaker": "Beru", "text": "My liege! Your loyal servant Beru is at your command!"}
            ],
            unlocks=["monarch_powers", "shadow_army", "unlimited_growth"]
        ),

        # JEJU ISLAND CHAPTER
        "jeju_island_001": StoryMission(
            id="jeju_island_001",
            name="The Ant Queen's Domain",
            description="Lead the raid to reclaim Jeju Island from the giant ants.",
            chapter=StoryChapter.JEJU_ISLAND,
            difficulty=StoryDifficulty.NIGHTMARE,
            level_requirement=70,
            prerequisites=["shadow_monarch_001"],
            objectives=[
                "Infiltrate Jeju Island",
                "Locate the Ant Queen",
                "Defeat the Ant Army",
                "Claim the Queen's power"
            ],
            rewards=StoryReward(
                gold=150000,
                xp=75000,
                diamonds=750,
                tickets=75,
                stat_points=150,
                skill_points=100,
                shadows=["ant_queen_shadow", "soldier_ant_shadow"],
                title="Island Liberator"
            ),
            enemies=[
                {"name": "Ant Queen", "level": 80, "hp": 15000, "attack": 400, "defense": 300},
                {"name": "Soldier Ant", "level": 75, "hp": 8000, "attack": 350, "defense": 250}
            ],
            dialogue=[
                {"speaker": "Goto Ryuji", "text": "This island... it's completely overrun. How can we possibly win?"},
                {"speaker": "Sung Jin-Woo", "text": "Leave it to me. My shadows will handle this."},
                {"speaker": "Ant Queen", "text": "You... you are not human. What are you?"}
            ],
            unlocks=["ant_army", "island_mastery"]
        ),

        "jeju_island_002": StoryMission(
            id="jeju_island_002",
            name="Beru's Loyalty",
            description="Extract the Ant King Beru and gain his eternal loyalty.",
            chapter=StoryChapter.JEJU_ISLAND,
            difficulty=StoryDifficulty.NIGHTMARE,
            level_requirement=72,
            prerequisites=["jeju_island_001"],
            objectives=[
                "Face the Ant King Beru",
                "Defeat him in single combat",
                "Successfully extract his shadow"
            ],
            rewards=StoryReward(
                gold=200000,
                xp=100000,
                diamonds=1000,
                tickets=100,
                stat_points=200,
                skill_points=150,
                shadows=["beru_king_shadow"],
                title="Ant King Master"
            ),
            enemies=[
                {"name": "Beru (Ant King)", "level": 85, "hp": 20000, "attack": 500, "defense": 400}
            ],
            dialogue=[
                {"speaker": "Beru", "text": "You dare challenge the King of Ants?"},
                {"speaker": "Sung Jin-Woo", "text": "I don't want to destroy you. Join me, and serve as my shadow."},
                {"speaker": "Beru", "text": "My liege... I pledge my eternal loyalty to you."}
            ],
            unlocks=["beru_powers", "ant_mastery"]
        ),

        # MONARCHS WAR CHAPTER
        "monarchs_war_001": StoryMission(
            id="monarchs_war_001",
            name="The Beast Monarch",
            description="Face the Beast Monarch in an epic battle for supremacy.",
            chapter=StoryChapter.MONARCHS_WAR,
            difficulty=StoryDifficulty.NIGHTMARE,
            level_requirement=80,
            prerequisites=["jeju_island_002"],
            objectives=[
                "Locate the Beast Monarch",
                "Engage in single combat",
                "Prove your superiority"
            ],
            rewards=StoryReward(
                gold=250000,
                xp=125000,
                diamonds=1250,
                tickets=125,
                stat_points=250,
                skill_points=200,
                shadows=["beast_monarch_shadow"],
                title="Monarch Slayer"
            ),
            enemies=[
                {"name": "Beast Monarch", "level": 90, "hp": 25000, "attack": 600, "defense": 500}
            ],
            dialogue=[
                {"speaker": "Beast Monarch", "text": "So, the Shadow Monarch finally shows himself."},
                {"speaker": "Sung Jin-Woo", "text": "I won't let you destroy this world."},
                {"speaker": "System", "text": "WARNING: Monarch-level threat detected. All systems at maximum power."}
            ],
            unlocks=["monarch_battle", "beast_powers"]
        ),

        "monarchs_war_002": StoryMission(
            id="monarchs_war_002",
            name="The Ice Monarch",
            description="Battle the Ice Monarch in the frozen wastelands.",
            chapter=StoryChapter.MONARCHS_WAR,
            difficulty=StoryDifficulty.NIGHTMARE,
            level_requirement=82,
            prerequisites=["monarchs_war_001"],
            objectives=[
                "Travel to the frozen realm",
                "Survive the ice storms",
                "Defeat the Ice Monarch"
            ],
            rewards=StoryReward(
                gold=300000,
                xp=150000,
                diamonds=1500,
                tickets=150,
                stat_points=300,
                skill_points=250,
                shadows=["ice_monarch_shadow"],
                title="Frost Conqueror"
            ),
            enemies=[
                {"name": "Ice Monarch", "level": 92, "hp": 30000, "attack": 650, "defense": 550}
            ],
            dialogue=[
                {"speaker": "Ice Monarch", "text": "This world will freeze under my eternal winter."},
                {"speaker": "Sung Jin-Woo", "text": "Not while I still draw breath."},
                {"speaker": "Igris", "text": "My lord, we stand ready to fight alongside you."}
            ],
            unlocks=["ice_powers", "frozen_mastery"]
        ),

        "monarchs_war_003": StoryMission(
            id="monarchs_war_003",
            name="The Dragon Emperor",
            description="Face the most powerful of all Monarchs - the Dragon Emperor.",
            chapter=StoryChapter.MONARCHS_WAR,
            difficulty=StoryDifficulty.NIGHTMARE,
            level_requirement=85,
            prerequisites=["monarchs_war_002"],
            objectives=[
                "Enter the Dragon's domain",
                "Withstand the Dragon's fury",
                "Claim victory over the Emperor"
            ],
            rewards=StoryReward(
                gold=500000,
                xp=250000,
                diamonds=2500,
                tickets=250,
                stat_points=500,
                skill_points=400,
                shadows=["dragon_emperor_shadow"],
                title="Dragon Slayer"
            ),
            enemies=[
                {"name": "Dragon Emperor", "level": 95, "hp": 40000, "attack": 750, "defense": 650}
            ],
            dialogue=[
                {"speaker": "Dragon Emperor", "text": "I am the oldest and strongest of the Monarchs. You cannot defeat me."},
                {"speaker": "Sung Jin-Woo", "text": "We'll see about that. Arise, my shadows!"},
                {"speaker": "System", "text": "All shadow soldiers are responding to your call, my lord."}
            ],
            unlocks=["dragon_powers", "emperor_mastery"]
        ),

        # FINAL BATTLE CHAPTER
        "final_battle_001": StoryMission(
            id="final_battle_001",
            name="The Architect's Plan",
            description="Discover the truth behind the System and face its creator.",
            chapter=StoryChapter.FINAL_BATTLE,
            difficulty=StoryDifficulty.NIGHTMARE,
            level_requirement=90,
            prerequisites=["monarchs_war_003"],
            objectives=[
                "Confront the Architect",
                "Learn the truth about the System",
                "Make the ultimate choice"
            ],
            rewards=StoryReward(
                gold=750000,
                xp=375000,
                diamonds=3750,
                tickets=375,
                stat_points=750,
                skill_points=600,
                title="Truth Seeker"
            ),
            enemies=[],  # No combat, story revelation
            dialogue=[
                {"speaker": "Architect", "text": "You have exceeded all expectations, Shadow Monarch."},
                {"speaker": "Sung Jin-Woo", "text": "Why? Why did you create the System? Why me?"},
                {"speaker": "Architect", "text": "To save both worlds. The choice is now yours to make."}
            ],
            unlocks=["architect_knowledge", "final_choice"]
        ),

        "final_battle_002": StoryMission(
            id="final_battle_002",
            name="The Ultimate Sacrifice",
            description="Make the ultimate sacrifice to save both worlds and reset time itself.",
            chapter=StoryChapter.FINAL_BATTLE,
            difficulty=StoryDifficulty.NIGHTMARE,
            level_requirement=95,
            prerequisites=["final_battle_001"],
            objectives=[
                "Accept the burden of time",
                "Reset the timeline",
                "Save both worlds"
            ],
            rewards=StoryReward(
                gold=1000000,
                xp=500000,
                diamonds=5000,
                tickets=500,
                stat_points=1000,
                skill_points=1000,
                title="World Savior"
            ),
            enemies=[],  # No combat, ultimate choice
            dialogue=[
                {"speaker": "Sung Jin-Woo", "text": "If this is what it takes to save everyone... I'll do it."},
                {"speaker": "System", "text": "Time reversal initiated. All memories will be preserved."},
                {"speaker": "Sung Jin-Woo", "text": "This time, I'll protect everyone from the very beginning."}
            ],
            unlocks=["time_mastery", "world_savior", "new_game_plus"]
        ),

        "final_battle_003": StoryMission(
            id="final_battle_003",
            name="The New Beginning",
            description="Begin anew with all your power intact, ready to face any threat.",
            chapter=StoryChapter.FINAL_BATTLE,
            difficulty=StoryDifficulty.NORMAL,
            level_requirement=100,
            prerequisites=["final_battle_002"],
            objectives=[
                "Embrace your new reality",
                "Prepare for future threats",
                "Become the ultimate protector"
            ],
            rewards=StoryReward(
                gold=2000000,
                xp=1000000,
                diamonds=10000,
                tickets=1000,
                stat_points=2000,
                skill_points=2000,
                shadows=["ultimate_shadow_army"],
                title="Eternal Shadow Monarch"
            ),
            enemies=[],  # No combat, completion reward
            dialogue=[
                {"speaker": "Sung Jin-Woo", "text": "This world... it's peaceful now. But I'll always be ready."},
                {"speaker": "System", "text": "Congratulations. You have completed the ultimate journey."},
                {"speaker": "Narrator", "text": "And so, the Shadow Monarch watches over both worlds, eternal and vigilant."}
            ],
            unlocks=["eternal_power", "complete_mastery", "legend_status"]
        )
    }
    
    @classmethod
    async def get_player_story_progress(cls, player_id: str) -> Dict:
        """Get player's story campaign progress"""
        try:
            player = await Player.get(player_id)
            if not player:
                return {}

            # Get story progress from player data
            if hasattr(player, 'story_progress') and player.story_progress:
                if isinstance(player.story_progress, str):
                    try:
                        return json.loads(player.story_progress)
                    except json.JSONDecodeError:
                        return {}
                elif isinstance(player.story_progress, dict):
                    return player.story_progress
            return {}
        except Exception as e:
            logging.error(f"Error getting story progress for player {player_id}: {e}")
            return {}
    
    @classmethod
    async def update_story_progress(cls, player_id: str, mission_id: str, completed: bool = True):
        """Update player's story progress"""
        try:
            player = await Player.get(player_id)
            if not player:
                return False

            progress = await cls.get_player_story_progress(player_id)
            progress[mission_id] = {
                "completed": completed,
                "completed_at": int(__import__('time').time()) if completed else None
            }

            # Ensure player has story_progress attribute
            if not hasattr(player, 'story_progress'):
                player.story_progress = {}

            # Update player data
            player.story_progress = progress
            await player.save()
            return True
        except Exception as e:
            logging.error(f"Error updating story progress for player {player_id}: {e}")
            return False
    
    @classmethod
    async def is_mission_available(cls, player_id: str, mission_id: str) -> Tuple[bool, str]:
        """Check if a mission is available to the player"""
        if mission_id not in cls.STORY_MISSIONS:
            return False, "Mission not found"
        
        mission = cls.STORY_MISSIONS[mission_id]
        player = await Player.get(player_id)
        
        if not player:
            return False, "Player not found"
        
        # Check level requirement
        if player.level < mission.level_requirement:
            return False, f"Requires level {mission.level_requirement}"
        
        # Check prerequisites
        progress = await cls.get_player_story_progress(player_id)
        for prereq in mission.prerequisites:
            if prereq not in progress or not progress[prereq].get("completed", False):
                prereq_mission = cls.STORY_MISSIONS.get(prereq)
                prereq_name = prereq_mission.name if prereq_mission else prereq
                return False, f"Must complete '{prereq_name}' first"
        
        # Don't block already completed missions - allow them to be viewed/replayed
        # if mission_id in progress and progress[mission_id].get("completed", False):
        #     return False, "Already completed"

        return True, "Available"
    
    @classmethod
    async def get_available_missions(cls, player_id: str) -> List[StoryMission]:
        """Get all available missions for a player"""
        available = []
        for mission_id, mission in cls.STORY_MISSIONS.items():
            is_available, _ = await cls.is_mission_available(player_id, mission_id)
            if is_available:
                available.append(mission)
        return available
    
    @classmethod
    async def get_completed_missions(cls, player_id: str) -> List[StoryMission]:
        """Get all completed missions for a player"""
        progress = await cls.get_player_story_progress(player_id)
        completed = []
        for mission_id, mission in cls.STORY_MISSIONS.items():
            if mission_id in progress and progress[mission_id].get("completed", False):
                completed.append(mission)
        return completed
    
    @classmethod
    async def complete_mission(cls, player_id: str, mission_id: str) -> Tuple[bool, str, StoryReward]:
        """Complete a story mission and give rewards"""
        # Check if mission is already completed to prevent duplicate rewards
        progress = await cls.get_player_story_progress(player_id)
        if mission_id in progress and progress[mission_id].get("completed", False):
            return False, "Mission already completed", None

        is_available, reason = await cls.is_mission_available(player_id, mission_id)
        if not is_available:
            return False, reason, None

        mission = cls.STORY_MISSIONS[mission_id]
        player = await Player.get(player_id)

        # Use balanced rewards if available, otherwise use mission rewards
        try:
            from structure.balanced_story_rewards import BALANCED_MISSION_REWARDS
            rewards = BALANCED_MISSION_REWARDS.get(mission_id, mission.rewards)
        except ImportError:
            rewards = mission.rewards
        if rewards.gold > 0:
            player.gold += rewards.gold
        if rewards.xp > 0:
            # Add XP directly without level up notifications (since we don't have bot/channel context)
            old_level = player.level
            player.xp += rewards.xp

            # Handle level ups manually
            while True:
                xp_needed = player.level * 100
                if player.xp >= xp_needed:
                    player.level += 1
                    player.xp -= xp_needed
                    # Give stat and skill points for level up
                    player.statPoints += 10
                    player.skillPoints += 5
                else:
                    break
        if rewards.diamonds > 0:
            player.diamond += rewards.diamonds
        if rewards.tickets > 0:
            player.ticket += rewards.tickets
        if rewards.stat_points > 0:
            player.statPoints += rewards.stat_points
        if rewards.skill_points > 0:
            player.skillPoints += rewards.skill_points

        # Add title reward if present
        if hasattr(rewards, 'title') and rewards.title:
            # Ensure player has titles attribute
            if not hasattr(player, 'titles'):
                player.titles = {}

            # Convert title name to title ID (lowercase, replace spaces with underscores)
            title_id = rewards.title.lower().replace(' ', '_').replace('-', '_')

            # Add the title to player's collection
            player.titles[title_id] = True
            print(f"Awarded title '{rewards.title}' to player {player_id}")

        # Add items to inventory (validate items exist in database)
        from structure.items import ItemManager
        for item_id in rewards.items:
            # Validate that the item exists in the database
            item = await ItemManager.get(item_id)
            if item:
                # Item exists, add it (handles duplicates automatically)
                is_duplicate = player.add_item(item_id)
                if is_duplicate:
                    print(f"Player already owns {item.name}, added shard instead")
            else:
                print(f"Warning: Story reward item '{item_id}' not found in database, skipping")
        
        # Add hunters (validate hunters exist in database)
        from structure.heroes import HeroManager
        for hunter_id in rewards.hunters:
            # Validate that the hunter exists in the database
            hunter = await HeroManager.get(hunter_id)
            if hunter:
                # Hunter exists, add it (handles duplicates automatically)
                is_duplicate = player.add_hunter(hunter_id)
                if is_duplicate:
                    print(f"Player already owns {hunter.name}, added shard instead")
            else:
                print(f"Warning: Story reward hunter '{hunter_id}' not found in database, skipping")
        
        # Add shadows (validate shadows exist in database)
        from structure.shadow import Shadow
        for shadow_id in rewards.shadows:
            # Validate that the shadow exists in the database
            shadow = await Shadow.get(shadow_id)
            if shadow:
                if not hasattr(player, 'shadows') or not player.shadows:
                    player.shadows = {}
                if shadow_id in player.shadows:
                    print(f"Player already owns {shadow.name}, keeping existing shadow")
                else:
                    player.shadows[shadow_id] = {"level": 1, "tier": 0}
            else:
                print(f"Warning: Story reward shadow '{shadow_id}' not found in database, skipping")
        
        # Mark mission as completed
        await cls.update_story_progress(player_id, mission_id, True)
        await player.save()
        
        # Apply feature unlocks based on mission completion
        await cls.apply_feature_unlocks(player_id, mission_id)

        return True, f"Mission '{mission.name}' completed!", rewards

    @classmethod
    async def apply_feature_unlocks(cls, player_id: str, mission_id: str):
        """Apply feature unlocks when specific story missions are completed"""
        try:
            player = await Player.get(player_id)
            if not player:
                return

            # Initialize unlocked_features if it doesn't exist
            if not hasattr(player, 'unlocked_features'):
                player.unlocked_features = {}
            elif isinstance(player.unlocked_features, str):
                try:
                    player.unlocked_features = json.loads(player.unlocked_features)
                except:
                    player.unlocked_features = {}

            # Story mode is now OPTIONAL - no command locking
            # Players get rewards and titles for completing story, but all commands remain unlocked
            feature_unlocks = {
                # No feature unlocks - story is optional for rewards only
            }

            # Story mode is optional - no feature unlocking needed
            # Players get rewards and titles but all commands remain available
            await player.save()

        except Exception as e:
            print(f"Error applying feature unlocks: {e}")

    @classmethod
    async def check_feature_unlocked(cls, player_id: str, feature: str) -> bool:
        """Check if a player has unlocked a specific feature - DISABLED: Story mode is optional"""
        # Story mode is now optional - all features are always unlocked
        return True

    @classmethod
    async def get_unlocked_features(cls, player_id: str) -> Dict[str, Dict]:
        """Get all unlocked features for a player"""
        try:
            player = await Player.get(player_id)
            if not player:
                return {}

            if not hasattr(player, 'unlocked_features'):
                return {}

            unlocked_features = player.unlocked_features
            if isinstance(unlocked_features, str):
                try:
                    unlocked_features = json.loads(unlocked_features)
                except:
                    return {}

            return unlocked_features

        except Exception as e:
            print(f"Error getting unlocked features: {e}")
            return {}

    @classmethod
    async def require_story_completion(cls, player_id: str, required_mission: str, feature_name: str) -> tuple[bool, str]:
        """Check if player has completed required story mission for a feature - DISABLED: Story mode is optional"""
        # Story mode is now optional - all features are always available
        return True, ""

    @classmethod
    async def reset_player_story_progress(cls, player_id: str) -> tuple[bool, str, dict]:
        """Reset a player's story progress completely"""
        try:
            player = await Player.get(player_id)
            if not player:
                return False, "Player not found", {}

            # Store previous progress for confirmation
            previous_progress = player.story_progress.copy() if hasattr(player, 'story_progress') and player.story_progress else {}

            # Reset story progress
            player.story_progress = {}
            await player.save()

            # Get available missions after reset
            available_missions = await cls.get_available_missions(player_id)

            return True, f"Story progress reset successfully. {len(available_missions)} missions now available.", previous_progress

        except Exception as e:
            return False, f"Error resetting story progress: {str(e)}", {}

# Utility function for easy access - DISABLED: Story mode is optional
async def check_story_lock(player_id: str, required_mission: str, feature_name: str) -> tuple[bool, str]:
    """Utility function to check story locks from anywhere in the codebase - Story mode is optional"""
    # Story mode is now optional - all features are always available
    return True, ""

    @classmethod
    def apply_balanced_rewards_to_all_missions(cls):
        """Apply balanced rewards to all story missions to prevent economy breaking"""

        # Balanced reward calculation
        def calculate_balanced_reward(level_req: int, chapter: StoryChapter, difficulty: StoryDifficulty, is_milestone: bool = False) -> StoryReward:
            # Base rewards (much more reasonable)
            base_gold = level_req * 25
            base_xp = level_req * 15
            base_diamonds = max(1, level_req // 20)
            base_tickets = max(1, level_req // 20)
            base_stat_points = max(1, level_req // 20)
            base_skill_points = max(1, level_req // 30)

            # Difficulty multipliers
            difficulty_mult = {"normal": 1.0, "hard": 1.5, "nightmare": 2.0}[difficulty.value]

            # Chapter multipliers (balanced)
            chapter_mult = {
                StoryChapter.PROLOGUE: 1.0,
                StoryChapter.DOUBLE_DUNGEON: 1.1,
                StoryChapter.FIRST_REAWAKENING: 1.2,
                StoryChapter.CARTENON_TEMPLE: 1.3,
                StoryChapter.DEMON_CASTLE: 1.4,
                StoryChapter.RED_GATE: 1.5,
                StoryChapter.SHADOW_MONARCH: 1.6,
                StoryChapter.JEJU_ISLAND: 1.7,
                StoryChapter.MONARCHS_WAR: 1.8,
                StoryChapter.FINAL_BATTLE: 2.0
            }[chapter]

            # Calculate final rewards
            final_gold = int(base_gold * difficulty_mult * chapter_mult)
            final_xp = int(base_xp * difficulty_mult * chapter_mult)
            final_diamonds = int(base_diamonds * difficulty_mult * chapter_mult)
            final_tickets = int(base_tickets * difficulty_mult * chapter_mult)
            final_stat_points = int(base_stat_points * difficulty_mult)
            final_skill_points = int(base_skill_points * difficulty_mult)

            # Milestone bonus (reduced)
            if is_milestone:
                final_gold = int(final_gold * 1.3)
                final_xp = int(final_xp * 1.3)
                final_diamonds = int(final_diamonds * 1.5)
                final_stat_points = int(final_stat_points * 1.5)
                final_skill_points = int(final_skill_points * 1.5)

            # Strict caps to prevent economy breaking
            final_gold = min(final_gold, 5000)
            final_xp = min(final_xp, 2000)
            final_diamonds = min(final_diamonds, 25)
            final_tickets = min(final_tickets, 10)
            final_stat_points = min(final_stat_points, 5)
            final_skill_points = min(final_skill_points, 3)

            return StoryReward(
                gold=final_gold,
                xp=final_xp,
                diamonds=final_diamonds,
                tickets=final_tickets,
                stat_points=final_stat_points,
                skill_points=final_skill_points
            )

        # Apply balanced rewards to all missions
        for mission_id, mission in cls.STORY_MISSIONS.items():
            # Determine if it's a milestone mission
            is_milestone = mission_id in [
                "prologue_002",  # Hunter License
                "double_dungeon_002",  # System Awakening
                "job_change_001",  # Job Change
                "reawakening_001",  # Reawakening
                "cartenon_002",  # Temple Secrets
                "demon_castle_002",  # Demon King
                "red_gate_001",  # Red Gate
                "shadow_monarch_001",  # Shadow Monarch
                "jeju_island_002",  # Ant King
                "monarchs_war_003",  # Dragon Emperor
                "final_battle_003"  # New Beginning
            ]

            # Calculate balanced rewards
            balanced_reward = calculate_balanced_reward(
                mission.level_requirement,
                mission.chapter,
                mission.difficulty,
                is_milestone
            )

            # Keep original title and special rewards (items, shadows, hunters)
            original_reward = mission.rewards
            balanced_reward.title = original_reward.title
            balanced_reward.items = original_reward.items
            balanced_reward.shadows = original_reward.shadows
            balanced_reward.hunters = original_reward.hunters

            # Update the mission's rewards
            mission.rewards = balanced_reward

# Note: Balanced rewards are applied automatically when missions are created
# The balanced reward system is built into the mission creation process
