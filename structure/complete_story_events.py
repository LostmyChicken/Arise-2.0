"""
Complete Solo Leveling Interactive Story Events
This file contains the full, immersive Solo Leveling story experience
"""

import discord
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from utilis.utilis import *

@dataclass
class StoryEvent:
    """Represents a single story event with choices and consequences"""
    id: str
    event_type: str  # NARRATIVE, DIALOGUE, BATTLE, EXPLORATION, EMOTIONAL
    title: str
    description: str
    speaker: str
    dialogue: str
    choices: List['StoryChoice'] = None
    battle_enemies: List[Dict] = None
    consequences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.choices is None:
            self.choices = []
        if self.battle_enemies is None:
            self.battle_enemies = []
        if self.consequences is None:
            self.consequences = {}

@dataclass
class StoryChoice:
    """Represents a choice the player can make in the story"""
    id: str
    text: str
    description: str
    choice_type: str  # HEROIC, CAUTIOUS, EMOTIONAL, PRACTICAL, etc.
    consequences: Dict[str, int]
    emoji: str
    requirements: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = {}

# COMPLETE SOLO LEVELING STORY EVENTS
COMPLETE_STORY_EVENTS = {
    # PROLOGUE - THE WEAKEST HUNTER (COMPLETE INTERACTIVE EXPERIENCE)
    "prologue_001": [
        StoryEvent(
            id="morning_routine",
            event_type="NARRATIVE",
            title="Another Morning, Another Risk",
            description="6:30 AM. Your alarm pierces the silence of your cramped apartment. You sleep on the floor beside Jin-Ah's bed, having given her the only mattress. Medical bills from your mother's hospital stay cover the table like fallen leaves - each one a reminder of why you must risk your life in dungeons today, despite being Korea's weakest hunter.",
            speaker="Jin-Woo (Internal)",
            dialogue="Another day, another dungeon. Everyone knows I'm the weakest... but Mom's bills won't pay themselves. I have to keep going, no matter how dangerous it gets. For her. For Jin-Ah.",
            choices=[
                StoryChoice(
                    id="check_bills",
                    text="Look at the medical bills",
                    description="Face the harsh reality of your financial burden",
                    choice_type="PRACTICAL",
                    consequences={"determination": 2, "stress": 1, "realism": 1},
                    emoji="💸"
                ),
                StoryChoice(
                    id="check_sister",
                    text="Check on Jin-Ah",
                    description="Make sure your sister is sleeping peacefully",
                    choice_type="CARING",
                    consequences={"family_bond": 2, "protectiveness": 1},
                    emoji="👧"
                ),
                StoryChoice(
                    id="prepare_quietly",
                    text="Prepare for the dungeon quietly",
                    description="Get ready without disturbing anyone",
                    choice_type="CONSIDERATE",
                    consequences={"responsibility": 1, "focus": 1, "discipline": 1},
                    emoji="🤫"
                ),
                StoryChoice(
                    id="morning_exercise",
                    text="Do some light exercise",
                    description="Try to build up your weak body",
                    choice_type="PRACTICAL",
                    consequences={"physical_training": 1, "self_improvement": 2, "hope": 1},
                    emoji="💪"
                ),
                StoryChoice(
                    id="study_hunter_news",
                    text="Read hunter news online",
                    description="Research dungeon strategies and hunter techniques",
                    choice_type="STRATEGIC",
                    consequences={"knowledge": 2, "preparation": 1, "tactical_thinking": 1},
                    emoji="📱"
                ),
                StoryChoice(
                    id="pray_quietly",
                    text="Say a quiet prayer",
                    description="Hope for safety and success in today's dungeon",
                    choice_type="SPIRITUAL",
                    consequences={"faith": 2, "inner_peace": 1, "hope": 2},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="write_note",
                    text="Write a note for Jin-Ah",
                    description="Leave encouraging words for your sister",
                    choice_type="CARING",
                    consequences={"family_bond": 3, "thoughtfulness": 2},
                    emoji="✍️"
                ),
                StoryChoice(
                    id="check_equipment",
                    text="Inspect your basic equipment",
                    description="Make sure your cheap gear is in working order",
                    choice_type="PRACTICAL",
                    consequences={"preparation": 2, "caution": 1, "professionalism": 1},
                    emoji="🛡️"
                )
            ]
        ),
        
        StoryEvent(
            id="hospital_visit",
            event_type="EMOTIONAL",
            title="The Eternal Sleep",
            description="Seoul National University Hospital, Room 1204. Your mother lies motionless, connected to machines that beep in steady rhythm. The 'Eternal Sleep Disease' - a mysterious condition that appeared after the gates opened - has kept her unconscious for years. The doctors say she's stable, but the treatments are expensive, and there's no guarantee she'll ever wake up.",
            speaker="Jin-Woo",
            dialogue="Mom... I'm going into another dungeon today. I know you'd tell me to be careful if you could hear me. Jin-Ah is doing so well in school - she's brilliant, just like you always said. I promise I'll find a way to wake you up. Somehow.",
            choices=[
                StoryChoice(
                    id="hold_hand",
                    text="Hold your mother's hand",
                    description="Spend a quiet moment with her",
                    choice_type="EMOTIONAL",
                    consequences={"love": 3, "determination": 2, "peace": 1},
                    emoji="🤝"
                ),
                StoryChoice(
                    id="promise_cure",
                    text="Promise to find a cure",
                    description="Vow to find a way to wake her up",
                    choice_type="HEROIC",
                    consequences={"determination": 3, "hope": 2, "resolve": 1},
                    emoji="💪"
                ),
                StoryChoice(
                    id="ask_doctor",
                    text="Speak with the doctor",
                    description="Get updates on her condition and bills",
                    choice_type="PRACTICAL",
                    consequences={"knowledge": 2, "worry": 1, "preparation": 1},
                    emoji="👨‍⚕️"
                ),
                StoryChoice(
                    id="tell_stories",
                    text="Tell her about Jin-Ah's achievements",
                    description="Share your sister's recent accomplishments",
                    choice_type="CARING",
                    consequences={"family_bond": 2, "pride": 2, "hope": 1},
                    emoji="📚"
                ),
                StoryChoice(
                    id="sing_lullaby",
                    text="Hum her favorite lullaby",
                    description="The song she used to sing to you and Jin-Ah",
                    choice_type="EMOTIONAL",
                    consequences={"nostalgia": 3, "love": 2, "peace": 2},
                    emoji="🎵"
                ),
                StoryChoice(
                    id="check_machines",
                    text="Study the medical equipment",
                    description="Try to understand her condition better",
                    choice_type="ANALYTICAL",
                    consequences={"knowledge": 2, "scientific_thinking": 1, "concern": 1},
                    emoji="🔬"
                ),
                StoryChoice(
                    id="pray_for_healing",
                    text="Pray for her recovery",
                    description="Ask for divine intervention",
                    choice_type="SPIRITUAL",
                    consequences={"faith": 3, "hope": 2, "inner_strength": 1},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="promise_return",
                    text="Promise to visit again soon",
                    description="Assure her you'll be back safely",
                    choice_type="CARING",
                    consequences={"commitment": 2, "love": 2, "responsibility": 1},
                    emoji="💝"
                ),
                StoryChoice(
                    id="leave_flower",
                    text="Leave a fresh flower by her bed",
                    description="Brighten her room with something beautiful",
                    choice_type="THOUGHTFUL",
                    consequences={"thoughtfulness": 3, "beauty": 1, "care": 2},
                    emoji="🌸"
                )
            ]
        ),
        
        StoryEvent(
            id="hunter_association",
            event_type="WORLD_BUILDING",
            title="The Korean Hunter Association",
            description="The imposing glass tower of the Korean Hunter Association looms above you. Inside, hunters of all ranks gather to form parties and accept missions. As an E-rank hunter, you're at the absolute bottom. Most parties reject you on sight, seeing you as dead weight. Today, however, you've found a group desperate enough to take you - probably out of pity.",
            speaker="Association Staff",
            dialogue="Sung Jin-Woo, E-rank hunter. Your survival rate is... concerning. Are you absolutely certain you want to continue with dungeon raids? There are safer jobs available for someone with your... limitations.",
            choices=[
                StoryChoice(
                    id="insist_continue",
                    text="I need to keep hunting",
                    description="Firmly state your commitment to dungeon raids",
                    choice_type="DETERMINED",
                    consequences={"determination": 2, "stubbornness": 1, "respect": -1},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="explain_situation",
                    text="My mother needs expensive treatment",
                    description="Explain your desperate financial situation",
                    choice_type="HONEST",
                    consequences={"sympathy": 2, "vulnerability": 1, "honesty": 1},
                    emoji="💔"
                ),
                StoryChoice(
                    id="stay_professional",
                    text="Just assign me to a party",
                    description="Keep your personal struggles private",
                    choice_type="PROFESSIONAL",
                    consequences={"privacy": 2, "distance": 1, "pride": 1},
                    emoji="📋"
                ),
                StoryChoice(
                    id="ask_for_advice",
                    text="What would you recommend?",
                    description="Seek guidance from experienced staff",
                    choice_type="HUMBLE",
                    consequences={"wisdom_seeking": 2, "humility": 2, "learning": 1},
                    emoji="🤔"
                ),
                StoryChoice(
                    id="mention_improvement",
                    text="I'm working to get stronger",
                    description="Show your commitment to self-improvement",
                    choice_type="OPTIMISTIC",
                    consequences={"hope": 2, "self_improvement": 2, "determination": 1},
                    emoji="📈"
                ),
                StoryChoice(
                    id="ask_about_training",
                    text="Are there training programs available?",
                    description="Inquire about ways to improve your abilities",
                    choice_type="PROACTIVE",
                    consequences={"initiative": 2, "learning_desire": 2, "planning": 1},
                    emoji="🎯"
                ),
                StoryChoice(
                    id="show_determination",
                    text="I won't give up, no matter what",
                    description="Display unwavering resolve despite the odds",
                    choice_type="HEROIC",
                    consequences={"determination": 3, "courage": 2, "inspiration": 1},
                    emoji="🔥"
                ),
                StoryChoice(
                    id="acknowledge_weakness",
                    text="I know I'm weak, but I have to try",
                    description="Admit your limitations while showing resolve",
                    choice_type="HONEST",
                    consequences={"self_awareness": 2, "honesty": 2, "humility": 1},
                    emoji="😔"
                ),
                StoryChoice(
                    id="ask_about_insurance",
                    text="What's the insurance coverage like?",
                    description="Show practical concern for safety",
                    choice_type="PRACTICAL",
                    consequences={"caution": 2, "practical_thinking": 2, "safety_awareness": 1},
                    emoji="🛡️"
                )
            ]
        ),
        
        StoryEvent(
            id="party_introduction",
            event_type="DIALOGUE",
            title="Meeting the Party",
            description="You approach a group of C and D-rank hunters gathered near the mission board. They're discussing a D-rank dungeon - far above your level, but the pay is decent. As you approach, their conversation stops, and they look at you with a mixture of pity and annoyance.",
            speaker="Party Leader (C-rank)",
            dialogue="So you're the E-rank we're babysitting today? Listen kid, stay in the back, don't touch anything, and try not to get yourself killed. We're only bringing you because we need one more body to meet the minimum party requirement.",
            choices=[
                StoryChoice(
                    id="thank_them",
                    text="Thank you for the opportunity",
                    description="Show gratitude despite their condescension",
                    choice_type="HUMBLE",
                    consequences={"humility": 2, "gratitude": 1, "respect": 1},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="promise_help",
                    text="I'll do whatever I can to help",
                    description="Offer to contribute however possible",
                    choice_type="SUPPORTIVE",
                    consequences={"teamwork": 2, "eagerness": 1, "determination": 1},
                    emoji="🤝"
                ),
                StoryChoice(
                    id="stay_quiet",
                    text="*Nod silently*",
                    description="Accept their terms without comment",
                    choice_type="SUBMISSIVE",
                    consequences={"acceptance": 1, "caution": 2, "self_control": 1},
                    emoji="😶"
                )
            ]
        ),

        StoryEvent(
            id="dungeon_entrance",
            event_type="EXPLORATION",
            title="Into the Unknown",
            description="You stand before the swirling portal of a D-rank dungeon. The air shimmers with magical energy, and you can feel the oppressive mana pressing against your skin. Your party members check their equipment one final time - expensive weapons and armor that you could never afford. Your own gear consists of a rusty dagger and leather armor held together with tape.",
            speaker="System",
            dialogue="WARNING: You are about to enter a D-rank dungeon. As an E-rank hunter, the recommended party size is 8-10 members. Current party size: 6. Survival probability: 23%. Do you wish to proceed?",
            choices=[
                StoryChoice(
                    id="enter_confidently",
                    text="Step forward first",
                    description="Show courage by entering the dungeon first",
                    choice_type="BRAVE",
                    consequences={"courage": 3, "leadership": 1, "recklessness": 1},
                    emoji="🚪"
                ),
                StoryChoice(
                    id="follow_group",
                    text="Stay with the group",
                    description="Enter safely with the other hunters",
                    choice_type="CAUTIOUS",
                    consequences={"safety": 2, "teamwork": 1, "caution": 1},
                    emoji="👥"
                ),
                StoryChoice(
                    id="hesitate_moment",
                    text="Take a deep breath first",
                    description="Steel yourself before entering",
                    choice_type="THOUGHTFUL",
                    consequences={"preparation": 2, "focus": 2, "anxiety": 1},
                    emoji="😤"
                )
            ]
        ),

        StoryEvent(
            id="first_monsters",
            event_type="BATTLE",
            title="Goblin Encounter",
            description="The dungeon's first chamber is dimly lit by glowing crystals. Suddenly, three goblins emerge from the shadows, their yellow eyes gleaming with malice. Your party members immediately spring into action, but one goblin breaks away from the group and charges directly at you - the weakest link.",
            speaker="Party Leader",
            dialogue="Jin-Woo! There's one coming your way! Try not to die on us - we don't want to deal with the paperwork!",
            battle_enemies=[
                {"name": "Goblin Scout", "level": 5, "hp": 150, "attack": 25, "defense": 10}
            ],
            choices=[
                StoryChoice(
                    id="fight_defensively",
                    text="Fight defensively",
                    description="Focus on survival over offense",
                    choice_type="DEFENSIVE",
                    consequences={"survival": 2, "defense_bonus": 10},
                    emoji="🛡️"
                ),
                StoryChoice(
                    id="attack_aggressively",
                    text="Attack with everything you have",
                    description="Go all-out despite the risk",
                    choice_type="AGGRESSIVE",
                    consequences={"damage_bonus": 15, "recklessness": 1},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="call_for_help",
                    text="Call for help from the party",
                    description="Ask the stronger hunters for assistance",
                    choice_type="SMART",
                    consequences={"teamwork": 1, "humility": 1, "safety": 1},
                    emoji="📢"
                )
            ]
        ),

        StoryEvent(
            id="post_battle_reflection",
            event_type="NARRATIVE",
            title="Barely Surviving",
            description="You manage to defeat the goblin, but barely. Your rusty dagger is chipped, your armor is torn, and you're breathing heavily. The other hunters have already finished their opponents and are looking at you with a mixture of pity and impatience. You realize just how vast the gap is between you and even D-rank hunters.",
            speaker="Jin-Woo (Internal)",
            dialogue="I'm so weak... Even a single goblin nearly killed me. How am I supposed to protect anyone like this? How am I supposed to save Mom? But I can't give up. I won't give up.",
            choices=[
                StoryChoice(
                    id="feel_determined",
                    text="This just makes me more determined",
                    description="Use your weakness as motivation",
                    choice_type="DETERMINED",
                    consequences={"determination": 3, "resolve": 2, "growth_mindset": 1},
                    emoji="💪"
                ),
                StoryChoice(
                    id="feel_discouraged",
                    text="Maybe I really am too weak...",
                    description="Doubt your abilities as a hunter",
                    choice_type="DOUBTFUL",
                    consequences={"self_doubt": 2, "realism": 1, "vulnerability": 1},
                    emoji="😔"
                ),
                StoryChoice(
                    id="analyze_mistakes",
                    text="Think about what went wrong",
                    description="Analyze your performance to improve",
                    choice_type="ANALYTICAL",
                    consequences={"wisdom": 2, "learning": 2, "strategy": 1},
                    emoji="🤔"
                )
            ]
        )
    ],

    # PROLOGUE MISSION 2 - HUNTER'S LICENSE
    "prologue_002": [
        StoryEvent(
            id="association_office",
            event_type="WORLD_BUILDING",
            title="Official Hunter Registration",
            description="After surviving your first dungeon (barely), you return to the Hunter Association to complete your official registration. The building buzzes with activity as hunters of all ranks come and go. You notice how the higher-ranked hunters are treated with respect and admiration, while you're largely ignored.",
            speaker="Registration Officer",
            dialogue="Sung Jin-Woo, congratulations on surviving your first official dungeon raid. Here's your E-rank Hunter License. Please note that this rank reflects your current abilities and may be subject to re-evaluation.",
            choices=[
                StoryChoice(
                    id="accept_gracefully",
                    text="Thank you for the opportunity",
                    description="Accept your rank with grace",
                    choice_type="GRACIOUS",
                    consequences={"humility": 2, "acceptance": 1, "maturity": 1},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="ask_about_advancement",
                    text="How can I improve my rank?",
                    description="Inquire about rank advancement",
                    choice_type="AMBITIOUS",
                    consequences={"ambition": 2, "curiosity": 1, "hope": 1},
                    emoji="📈"
                ),
                StoryChoice(
                    id="study_license",
                    text="Examine the license carefully",
                    description="Look at your new hunter license",
                    choice_type="OBSERVANT",
                    consequences={"attention_to_detail": 1, "pride": 1, "focus": 1},
                    emoji="🔍"
                )
            ]
        )
    ],

    # DOUBLE DUNGEON - THE LIFE-CHANGING EVENT
    "double_dungeon_001": [
        StoryEvent(
            id="mysterious_invitation",
            event_type="NARRATIVE",
            title="An Unusual Opportunity",
            description="Three weeks after getting your hunter license, you receive an unexpected call. A C-rank party needs one more member for a D-rank dungeon raid - they're desperate enough to take an E-rank hunter. The pay is better than usual, which makes you suspicious, but your mother's medical bills are mounting.",
            speaker="Party Leader (Phone)",
            dialogue="Listen, we know you're E-rank, but we need six people minimum for this dungeon. It's supposed to be a simple D-rank cave system. Easy money. You in or not?",
            choices=[
                StoryChoice(
                    id="accept_immediately",
                    text="I'll take it",
                    description="Accept the offer without hesitation",
                    choice_type="DESPERATE",
                    consequences={"desperation": 2, "quick_decision": 1},
                    emoji="💰"
                ),
                StoryChoice(
                    id="ask_details",
                    text="What kind of dungeon is it?",
                    description="Ask for more information about the raid",
                    choice_type="CAUTIOUS",
                    consequences={"caution": 2, "wisdom": 1},
                    emoji="❓"
                ),
                StoryChoice(
                    id="negotiate_pay",
                    text="What's the payment?",
                    description="Focus on the financial aspect",
                    choice_type="PRACTICAL",
                    consequences={"business_sense": 1, "necessity": 2},
                    emoji="💸"
                )
            ]
        ),

        StoryEvent(
            id="dungeon_entrance_ominous",
            event_type="WORLD_BUILDING",
            title="The Double Dungeon",
            description="You arrive at the dungeon site with five other hunters. The gate shimmers with an unusual purple hue instead of the typical blue. The mana emanating from it feels different - heavier, more oppressive. Your instincts scream danger, but the other hunters seem eager to get started.",
            speaker="Song Chi-Yul (C-rank Hunter)",
            dialogue="Strange... I've never seen a gate with this color before. The mana reading is definitely D-rank though. Probably just a visual anomaly. Let's get this over with quickly.",
            choices=[
                StoryChoice(
                    id="voice_concern",
                    text="Something feels wrong about this gate",
                    description="Express your unease about the dungeon",
                    choice_type="INTUITIVE",
                    consequences={"intuition": 3, "caution": 2, "respect": -1},
                    emoji="⚠️"
                ),
                StoryChoice(
                    id="trust_others",
                    text="If you say it's safe...",
                    description="Trust the more experienced hunters",
                    choice_type="TRUSTING",
                    consequences={"trust": 2, "naivety": 1},
                    emoji="🤝"
                ),
                StoryChoice(
                    id="stay_alert",
                    text="*Stay quiet but remain vigilant*",
                    description="Keep your concerns to yourself but stay alert",
                    choice_type="OBSERVANT",
                    consequences={"alertness": 3, "wisdom": 1},
                    emoji="👁️"
                )
            ]
        ),

        StoryEvent(
            id="temple_discovery",
            event_type="EXPLORATION",
            title="The Hidden Temple",
            description="After clearing the initial cave monsters, your party discovers something impossible - a massive stone door hidden behind the dungeon's final chamber. Ancient runes glow with an eerie light, and the air thrums with power far beyond a D-rank dungeon. This is a Double Dungeon - a dungeon within a dungeon.",
            speaker="Kim Sang-Shik (D-rank Hunter)",
            dialogue="What the hell is this? This wasn't in the briefing! That door... it's giving off S-rank level mana! We should report this and leave immediately!",
            choices=[
                StoryChoice(
                    id="agree_to_leave",
                    text="We should definitely leave",
                    description="Support the idea of retreating",
                    choice_type="WISE",
                    consequences={"wisdom": 3, "survival_instinct": 2},
                    emoji="🏃"
                ),
                StoryChoice(
                    id="curious_about_door",
                    text="What do those runes mean?",
                    description="Show curiosity about the mysterious door",
                    choice_type="CURIOUS",
                    consequences={"curiosity": 2, "knowledge_seeking": 1, "danger": 1},
                    emoji="🔍"
                ),
                StoryChoice(
                    id="suggest_caution",
                    text="Maybe we should be very careful",
                    description="Advocate for extreme caution",
                    choice_type="CAUTIOUS",
                    consequences={"caution": 3, "leadership": 1},
                    emoji="⚠️"
                )
            ]
        ),

        StoryEvent(
            id="greed_takes_over",
            event_type="DIALOGUE",
            title="Fatal Greed",
            description="Despite the obvious danger, the party leader's eyes gleam with greed. He's thinking about the potential rewards from an undiscovered high-rank dungeon. The other hunters are torn between fear and the promise of wealth. You realize that your opinion as the weakest member carries little weight.",
            speaker="Party Leader",
            dialogue="Think about it - we're the first ones to find this place! The treasures inside could set us up for life! We just need to be careful and stick together. What's the worst that could happen?",
            choices=[
                StoryChoice(
                    id="strongly_object",
                    text="This is suicide! We need to leave now!",
                    description="Strongly oppose entering the temple",
                    choice_type="DESPERATE_WARNING",
                    consequences={"desperation": 2, "wisdom": 3, "isolation": 1},
                    emoji="🚨"
                ),
                StoryChoice(
                    id="reluctant_agreement",
                    text="If everyone else agrees...",
                    description="Reluctantly go along with the group",
                    choice_type="PEER_PRESSURE",
                    consequences={"conformity": 2, "regret": 1, "fear": 2},
                    emoji="😰"
                ),
                StoryChoice(
                    id="silent_dread",
                    text="*Say nothing, filled with dread*",
                    description="Stay silent while feeling overwhelming dread",
                    choice_type="FATALISTIC",
                    consequences={"dread": 3, "helplessness": 2, "premonition": 1},
                    emoji="😨"
                )
            ]
        )
    ],

    # DOUBLE DUNGEON PART 2 - THE TEMPLE OF TRIALS
    "double_dungeon_002": [
        StoryEvent(
            id="temple_entrance",
            event_type="HORROR",
            title="Entering the Temple of Death",
            description="The massive stone doors grind open with an ominous rumble. Inside, you see a vast temple chamber lit by torches that burn with blue flames. Six enormous stone statues line the walls - warriors, mages, and creatures of immense power. At the far end sits a colossal statue on a throne, its eyes closed as if sleeping. The air is thick with ancient magic and the scent of death.",
            speaker="System (First Activation)",
            dialogue="WARNING: You have entered an S-rank dungeon. Survival probability for current party: 0.3%. Recommended action: IMMEDIATE EVACUATION.",
            choices=[
                StoryChoice(
                    id="try_to_run",
                    text="We need to get out of here NOW!",
                    description="Try to convince everyone to flee immediately",
                    choice_type="SURVIVAL_INSTINCT",
                    consequences={"survival_instinct": 3, "desperation": 2},
                    emoji="🏃‍♂️"
                ),
                StoryChoice(
                    id="examine_statues",
                    text="Look at the statues carefully",
                    description="Study the threatening stone guardians",
                    choice_type="ANALYTICAL",
                    consequences={"observation": 3, "knowledge": 2, "fear": 1},
                    emoji="👁️"
                ),
                StoryChoice(
                    id="feel_overwhelmed",
                    text="*Feel completely overwhelmed*",
                    description="Be paralyzed by the magnitude of danger",
                    choice_type="OVERWHELMED",
                    consequences={"fear": 3, "helplessness": 2, "realization": 1},
                    emoji="😱"
                )
            ]
        ),

        StoryEvent(
            id="commandments_revealed",
            event_type="WORLD_BUILDING",
            title="The Three Commandments",
            description="As your party ventures deeper into the temple, ancient text appears on the walls, glowing with divine light. Three commandments are written in multiple languages, including Korean. The other hunters dismiss them as flavor text, but something deep in your soul tells you these rules are deadly serious.",
            speaker="Ancient Text",
            dialogue="COMMANDMENT I: Worship the God. COMMANDMENT II: Praise the God. COMMANDMENT III: Prove your faith to the God. Those who do not follow the commandments shall face divine punishment.",
            choices=[
                StoryChoice(
                    id="warn_about_rules",
                    text="These rules might be important!",
                    description="Try to warn the party about the commandments",
                    choice_type="WARNING",
                    consequences={"wisdom": 3, "concern": 2, "ignored": 1},
                    emoji="⚠️"
                ),
                StoryChoice(
                    id="memorize_rules",
                    text="*Memorize the commandments carefully*",
                    description="Commit the rules to memory",
                    choice_type="PREPARATION",
                    consequences={"preparation": 3, "memory": 2, "caution": 1},
                    emoji="🧠"
                ),
                StoryChoice(
                    id="feel_dread",
                    text="*Feel an ominous chill*",
                    description="Sense the supernatural danger in these words",
                    choice_type="INTUITIVE",
                    consequences={"intuition": 3, "dread": 2, "sensitivity": 1},
                    emoji="🥶"
                )
            ]
        ),

        StoryEvent(
            id="statues_awaken",
            event_type="BATTLE",
            title="Divine Punishment",
            description="One of the hunters laughs at the commandments and makes a mocking gesture toward the central statue. Suddenly, the temple shakes violently. The six guardian statues begin to glow with malevolent energy, their stone eyes opening to reveal burning light. They step down from their pedestals with earth-shaking footsteps. The massacre begins.",
            speaker="Stone Guardian",
            dialogue="THOSE WHO DO NOT FOLLOW THE COMMANDMENTS... SHALL PERISH!",
            battle_enemies=[
                {"name": "Stone Guardian", "level": 50, "hp": 10000, "attack": 300, "defense": 200}
            ],
            choices=[
                StoryChoice(
                    id="follow_commandments",
                    text="Immediately worship the central statue",
                    description="Drop to your knees and worship desperately",
                    choice_type="SURVIVAL_WORSHIP",
                    consequences={"survival": 5, "humility": 3, "desperation": 2},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="try_to_fight",
                    text="Try to help fight the guardians",
                    description="Attempt to battle the stone monsters",
                    choice_type="HEROIC_FUTILE",
                    consequences={"courage": 2, "futility": 3, "injury": 2},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="hide_and_worship",
                    text="Hide while following the commandments",
                    description="Find cover while worshipping the god",
                    choice_type="SMART_SURVIVAL",
                    consequences={"survival": 4, "wisdom": 2, "cowardice": 1},
                    emoji="🫣"
                )
            ]
        ),

        StoryEvent(
            id="party_massacre",
            event_type="HORROR",
            title="Watching Your Friends Die",
            description="The stone guardians move with impossible speed and strength. One by one, your party members are brutally killed. Song Chi-Yul is crushed by a massive stone fist. Kim Sang-Shik is impaled by a stone spear. The others scream in terror and agony as they're systematically slaughtered. You can only watch in horror while desperately following the commandments, praying it will keep you alive.",
            speaker="Jin-Woo (Internal)",
            dialogue="They're all dying... everyone is dying and there's nothing I can do. I'm too weak to help them. I can only watch and pray that following these rules will keep me alive. I'm a coward... but I want to live. I have to live. For Mom. For Jin-Ah.",
            choices=[
                StoryChoice(
                    id="feel_guilt",
                    text="Feel overwhelming guilt for surviving",
                    description="Be consumed by survivor's guilt",
                    choice_type="GUILT",
                    consequences={"guilt": 4, "trauma": 3, "self_blame": 2},
                    emoji="😭"
                ),
                StoryChoice(
                    id="focus_survival",
                    text="Focus only on staying alive",
                    description="Suppress emotions and focus on survival",
                    choice_type="SURVIVAL_MODE",
                    consequences={"survival_instinct": 4, "emotional_suppression": 2, "determination": 1},
                    emoji="😤"
                ),
                StoryChoice(
                    id="pray_desperately",
                    text="Pray more desperately to the god",
                    description="Increase your worship intensity",
                    choice_type="DESPERATE_FAITH",
                    consequences={"desperation": 3, "faith": 2, "survival": 3},
                    emoji="🙏"
                )
            ]
        ),

        StoryEvent(
            id="system_awakening",
            event_type="TRANSFORMATION",
            title="The System Awakens",
            description="As you kneel in terror, the only survivor among the corpses of your party, something impossible happens. A translucent blue screen appears before your eyes - visible only to you. Text scrolls across it in perfect Korean, and a mechanical voice speaks directly into your mind. The 'System' has chosen you as its Player.",
            speaker="System",
            dialogue="CONGRATULATIONS! You have been selected as the Player. You have been granted the unique ability to grow stronger without limits. Welcome to the System, Sung Jin-Woo.",
            choices=[
                StoryChoice(
                    id="question_system",
                    text="What... what is this?",
                    description="Question the mysterious system",
                    choice_type="CONFUSED",
                    consequences={"confusion": 2, "curiosity": 3, "wonder": 1},
                    emoji="❓"
                ),
                StoryChoice(
                    id="think_hallucination",
                    text="Am I hallucinating from trauma?",
                    description="Wonder if you're losing your mind",
                    choice_type="RATIONAL_DOUBT",
                    consequences={"rationality": 2, "doubt": 2, "trauma": 1},
                    emoji="🤔"
                ),
                StoryChoice(
                    id="accept_gratefully",
                    text="Thank you for choosing me",
                    description="Accept the system with gratitude",
                    choice_type="GRATEFUL",
                    consequences={"gratitude": 3, "acceptance": 2, "hope": 2},
                    emoji="🙏"
                )
            ]
        )
    ],

    # PROLOGUE MISSION 3 - FIRST STEPS
    "prologue_003": [
        StoryEvent(
            id="first_real_mission",
            event_type="NARRATIVE",
            title="First Real Mission",
            description="You've received your hunter's license and now face your first official mission. The other hunters still look at you with doubt, but you're determined to prove yourself.",
            speaker="Jin-Woo (Internal)",
            dialogue="This is it. My first real mission as a licensed hunter. I can't mess this up - I need to show everyone that I'm not just dead weight.",
            choices=[
                StoryChoice(
                    id="study_mission",
                    text="Carefully study the mission details",
                    description="Review all available information about the dungeon",
                    choice_type="PREPARATION",
                    consequences={"preparation": 2, "knowledge": 1, "confidence": 1},
                    emoji="📋"
                ),
                StoryChoice(
                    id="talk_to_team",
                    text="Introduce yourself to the team",
                    description="Try to build rapport with your fellow hunters",
                    choice_type="SOCIAL",
                    consequences={"teamwork": 2, "social": 1, "courage": 1},
                    emoji="🤝"
                ),
                StoryChoice(
                    id="stay_quiet",
                    text="Stay quiet and observe",
                    description="Keep a low profile and learn from watching",
                    choice_type="CAUTIOUS",
                    consequences={"observation": 2, "caution": 1, "wisdom": 1},
                    emoji="👁️"
                )
            ]
        ),

        StoryEvent(
            id="first_mission_battle",
            event_type="BATTLE",
            title="Proving Your Worth",
            description="The dungeon contains low-level monsters, but for you, every battle is a life-or-death struggle. You must prove that you can contribute to the team.",
            speaker="Team Leader",
            dialogue="Jin-Woo, stay back and let us handle the dangerous ones. You can take care of any stragglers.",
            battle_enemies=[
                {
                    "name": "Goblin Warrior",
                    "level": 3,
                    "hp": 80,
                    "attack": 20,
                    "defense": 8,
                    "skills": ["Slash", "Block"]
                }
            ],
            choices=[
                StoryChoice(
                    id="fight_carefully",
                    text="Fight with extreme caution",
                    description="Use defensive tactics to minimize risk",
                    choice_type="DEFENSIVE",
                    consequences={"survival": 2, "caution": 1, "experience": 1},
                    emoji="🛡️"
                ),
                StoryChoice(
                    id="try_to_impress",
                    text="Try to show your skills",
                    description="Take calculated risks to prove your worth",
                    choice_type="AMBITIOUS",
                    consequences={"courage": 2, "risk": 1, "determination": 1},
                    emoji="⚔️"
                )
            ]
        )
    ],

    # INSTANT DUNGEON - DAILY QUEST PENALTY
    "instant_dungeon_001": [
        StoryEvent(
            id="penalty_zone_entry",
            event_type="HORROR",
            title="The Penalty Zone",
            description="You ignored the System's Daily Quest, and now you're trapped in a nightmarish dimension filled with giant centipedes. The air is thick with the stench of death, and you can hear the clicking of massive mandibles in the darkness.",
            speaker="System",
            dialogue="PENALTY QUEST INITIATED. Survive for 4 hours or eliminate all threats. Failure will result in DEATH.",
            choices=[
                StoryChoice(
                    id="find_hiding_spot",
                    text="Look for a place to hide",
                    description="Try to find somewhere safe to wait out the penalty",
                    choice_type="SURVIVAL",
                    consequences={"survival": 2, "fear": 1, "caution": 2},
                    emoji="🫣"
                ),
                StoryChoice(
                    id="fight_immediately",
                    text="Face the centipedes head-on",
                    description="Attack the monsters before they can surround you",
                    choice_type="AGGRESSIVE",
                    consequences={"courage": 3, "recklessness": 1, "determination": 2},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="analyze_situation",
                    text="Study the environment first",
                    description="Carefully observe the centipedes' behavior patterns",
                    choice_type="TACTICAL",
                    consequences={"intelligence": 2, "observation": 2, "strategy": 1},
                    emoji="🧠"
                )
            ]
        ),

        StoryEvent(
            id="centipede_battle",
            event_type="BATTLE",
            title="Giant Centipede Swarm",
            description="The massive centipedes emerge from the shadows, their chitinous bodies gleaming with a sickly sheen. You realize that this is a fight for your very survival.",
            speaker="Jin-Woo (Internal)",
            dialogue="I can't die here! I have to survive this nightmare and get back to Jin-Ah and Mom!",
            battle_enemies=[
                {
                    "name": "Giant Centipede",
                    "level": 8,
                    "hp": 300,
                    "attack": 35,
                    "defense": 15,
                    "skills": ["Poison Bite", "Tunnel Strike"]
                }
            ]
        )
    ],

    # JOB CHANGE QUEST
    "job_change_001": [
        StoryEvent(
            id="job_change_preparation",
            event_type="SYSTEM_MESSAGE",
            title="The Job Change Quest",
            description="The System has offered you a Job Change Quest - a dangerous trial that could unlock your true potential or kill you in the process.",
            speaker="System",
            dialogue="JOB CHANGE QUEST AVAILABLE. WARNING: This quest has a high mortality rate. Do you wish to proceed?",
            choices=[
                StoryChoice(
                    id="accept_immediately",
                    text="Accept the quest without hesitation",
                    description="Embrace the risk for the chance at power",
                    choice_type="BOLD",
                    consequences={"courage": 3, "determination": 2, "recklessness": 1},
                    emoji="💪"
                ),
                StoryChoice(
                    id="ask_questions",
                    text="Ask the System for more details",
                    description="Try to understand what you're getting into",
                    choice_type="CAUTIOUS",
                    consequences={"wisdom": 2, "preparation": 2, "intelligence": 1},
                    emoji="❓"
                ),
                StoryChoice(
                    id="consider_carefully",
                    text="Take time to consider the risks",
                    description="Weigh the potential benefits against the dangers",
                    choice_type="ANALYTICAL",
                    consequences={"analysis": 2, "caution": 1, "responsibility": 1},
                    emoji="🤔"
                )
            ]
        )
    ],

    # REAWAKENING TEST
    "reawakening_001": [
        StoryEvent(
            id="reawakening_center",
            event_type="NARRATIVE",
            title="The Reawakening Center",
            description="You stand before the Korean Hunter Association's Reawakening Center. After your mysterious growth in power, you've come to officially test your new rank. The other hunters whisper about the 'miracle' E-rank who survived impossible odds.",
            speaker="Association Staff",
            dialogue="Sung Jin-Woo? You're here for a reawakening test? That's... unusual for someone so young. Are you sure about this?",
            choices=[
                StoryChoice(
                    id="confident_response",
                    text="I'm ready to show my true strength",
                    description="Display confidence in your newfound abilities",
                    choice_type="CONFIDENT",
                    consequences={"confidence": 3, "determination": 2, "presence": 1},
                    emoji="💪"
                ),
                StoryChoice(
                    id="humble_response",
                    text="I just want to know where I stand",
                    description="Remain humble about your growth",
                    choice_type="HUMBLE",
                    consequences={"humility": 2, "wisdom": 1, "respect": 2},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="mysterious_response",
                    text="Let the test speak for itself",
                    description="Keep your abilities mysterious",
                    choice_type="MYSTERIOUS",
                    consequences={"mystery": 2, "intrigue": 2, "caution": 1},
                    emoji="🎭"
                )
            ]
        ),

        StoryEvent(
            id="golem_battle",
            event_type="BATTLE",
            title="The Magic Beast Test",
            description="You face the testing golem - a massive stone construct designed to measure a hunter's true capabilities. This is your chance to prove that you're no longer the weakest hunter.",
            speaker="Jin-Woo (Internal)",
            dialogue="This is it. Time to show everyone - including myself - just how much I've changed.",
            battle_enemies=[
                {
                    "name": "Testing Golem",
                    "level": 15,
                    "hp": 800,
                    "attack": 60,
                    "defense": 40,
                    "skills": ["Stone Fist", "Rock Throw", "Defensive Stance"]
                }
            ]
        )
    ],

    # CARTENON TEMPLE MISSION 1
    "cartenon_001": [
        StoryEvent(
            id="temple_approach",
            event_type="EXPLORATION",
            title="Approaching the Cartenon Temple",
            description="The ancient Cartenon Temple looms before you, its weathered stones covered in mysterious runes. The air around it feels heavy with magical energy, and you can sense powerful guardians within.",
            speaker="Guild Master",
            dialogue="This temple has claimed many lives, Jin-Woo. The magic here is ancient and dangerous. Are you certain you're ready for this?",
            choices=[
                StoryChoice(
                    id="study_runes",
                    text="Examine the ancient runes",
                    description="Try to understand the temple's magical protections",
                    choice_type="SCHOLARLY",
                    consequences={"knowledge": 2, "magic_understanding": 2, "preparation": 1},
                    emoji="📜"
                ),
                StoryChoice(
                    id="enter_boldly",
                    text="Enter the temple immediately",
                    description="Show no fear and proceed with confidence",
                    choice_type="BOLD",
                    consequences={"courage": 3, "leadership": 1, "recklessness": 1},
                    emoji="🚪"
                ),
                StoryChoice(
                    id="scout_perimeter",
                    text="Scout around the temple first",
                    description="Look for alternative entrances or hidden dangers",
                    choice_type="TACTICAL",
                    consequences={"strategy": 2, "observation": 2, "caution": 1},
                    emoji="🔍"
                )
            ]
        ),

        StoryEvent(
            id="temple_guardian_battle",
            event_type="BATTLE",
            title="The Temple Guardian",
            description="A massive stone guardian awakens as you enter the temple's inner sanctum. Its eyes glow with ancient magic, and you realize this is a test of your worthiness.",
            speaker="Temple Guardian",
            dialogue="WHO DARES DISTURB THE SACRED HALLS? PROVE YOUR WORTH OR FACE DESTRUCTION!",
            battle_enemies=[
                {
                    "name": "Temple Guardian",
                    "level": 35,
                    "hp": 2000,
                    "attack": 120,
                    "defense": 80,
                    "skills": ["Sacred Strike", "Stone Prison", "Ancient Magic"]
                }
            ]
        )
    ],

    # CARTENON TEMPLE MISSION 2
    "cartenon_002": [
        StoryEvent(
            id="temple_secret_discovery",
            event_type="MYSTERY",
            title="The Temple's Hidden Secret",
            description="Deep within the Cartenon Temple, you discover a hidden chamber containing ancient artifacts and mysterious inscriptions. The air hums with power, and you sense that this place holds secrets about the true nature of hunters and magic.",
            speaker="Ancient Inscription",
            dialogue="Those who seek power must first understand sacrifice. The path of the hunter is paved with both triumph and loss.",
            choices=[
                StoryChoice(
                    id="touch_artifact",
                    text="Touch the central artifact",
                    description="Risk direct contact with the mysterious power source",
                    choice_type="RISKY",
                    consequences={"power": 3, "knowledge": 2, "danger": 2},
                    emoji="✋"
                ),
                StoryChoice(
                    id="study_inscriptions",
                    text="Study the ancient inscriptions",
                    description="Try to understand the temple's history and purpose",
                    choice_type="SCHOLARLY",
                    consequences={"wisdom": 3, "ancient_knowledge": 2, "understanding": 1},
                    emoji="📚"
                ),
                StoryChoice(
                    id="proceed_carefully",
                    text="Proceed with extreme caution",
                    description="Explore the chamber while minimizing risks",
                    choice_type="CAUTIOUS",
                    consequences={"safety": 2, "observation": 2, "patience": 1},
                    emoji="🚶"
                )
            ]
        )
    ],

    # DEMON CASTLE MISSION 1 - ENTRANCE
    "demon_castle_001": [
        StoryEvent(
            id="castle_approach",
            event_type="OMINOUS",
            title="The Demon Castle Looms",
            description="The massive Demon Castle rises before you like a monument to darkness. Its black spires pierce the crimson sky, and the very air around it seems to writhe with malevolent energy. You can feel the presence of countless demons within its walls.",
            speaker="Jin-Woo (Internal)",
            dialogue="This place... it's like nothing I've ever felt before. The demonic energy here is overwhelming. But I've come too far to turn back now.",
            choices=[
                StoryChoice(
                    id="frontal_assault",
                    text="Attack the main gate directly",
                    description="Face the demon guards head-on with overwhelming force",
                    choice_type="AGGRESSIVE",
                    consequences={"courage": 3, "directness": 2, "recklessness": 1},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="stealth_approach",
                    text="Look for a hidden entrance",
                    description="Use stealth to avoid unnecessary confrontation",
                    choice_type="TACTICAL",
                    consequences={"stealth": 3, "strategy": 2, "patience": 1},
                    emoji="🥷"
                ),
                StoryChoice(
                    id="study_defenses",
                    text="Observe the castle's defenses",
                    description="Analyze the demon guards' patterns and weaknesses",
                    choice_type="ANALYTICAL",
                    consequences={"intelligence": 2, "preparation": 2, "observation": 2},
                    emoji="👁️"
                )
            ]
        ),

        StoryEvent(
            id="demon_guard_battle",
            event_type="BATTLE",
            title="The Demon Guards",
            description="Massive demon guards block your path, their eyes burning with hellfire. These are no ordinary monsters - they are elite defenders of the demon realm, each one capable of destroying entire hunter teams.",
            speaker="Demon Guard Captain",
            dialogue="A human dares to approach our lord's castle? You will make fine sport for our blades!",
            battle_enemies=[
                {
                    "name": "Demon Guard",
                    "level": 45,
                    "hp": 3000,
                    "attack": 150,
                    "defense": 100,
                    "skills": ["Hellfire Slash", "Demon Roar", "Dark Shield"]
                },
                {
                    "name": "Hell Hound",
                    "level": 42,
                    "hp": 2500,
                    "attack": 140,
                    "defense": 80,
                    "skills": ["Fire Breath", "Savage Bite", "Pack Hunt"]
                }
            ]
        )
    ],

    # DEMON CASTLE MISSION 2 - THE DEMON KING'S THRONE (The one that was auto-completing!)
    "demon_castle_002": [
        StoryEvent(
            id="throne_room_approach",
            event_type="CLIMACTIC",
            title="The Demon King's Throne Room",
            description="You stand before the massive doors to the Demon King's throne room. The air is thick with demonic power, and you can feel the presence of an ancient evil beyond. This is the moment you've been preparing for - the confrontation that will determine your fate.",
            speaker="Jin-Woo (Internal)",
            dialogue="Behind these doors waits the Demon King himself. Everything I've learned, every battle I've fought, has led to this moment. I won't back down now.",
            choices=[
                StoryChoice(
                    id="dramatic_entrance",
                    text="Burst through the doors dramatically",
                    description="Make a bold entrance to intimidate the Demon King",
                    choice_type="DRAMATIC",
                    consequences={"presence": 3, "intimidation": 2, "boldness": 2},
                    emoji="💥"
                ),
                StoryChoice(
                    id="respectful_entry",
                    text="Enter with respectful caution",
                    description="Show respect for a powerful opponent",
                    choice_type="HONORABLE",
                    consequences={"honor": 2, "respect": 2, "wisdom": 1},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="silent_entry",
                    text="Enter silently and observe",
                    description="Study the Demon King before revealing yourself",
                    choice_type="TACTICAL",
                    consequences={"stealth": 2, "observation": 3, "strategy": 1},
                    emoji="👤"
                ),
                StoryChoice(
                    id="confident_stride",
                    text="Walk in with unwavering confidence",
                    description="Show no fear as you approach the throne",
                    choice_type="CONFIDENT",
                    consequences={"confidence": 3, "presence": 2, "fearlessness": 2},
                    emoji="🚶‍♂️"
                ),
                StoryChoice(
                    id="weapon_ready",
                    text="Enter with weapon drawn",
                    description="Be ready for immediate combat",
                    choice_type="AGGRESSIVE",
                    consequences={"combat_readiness": 3, "aggression": 2, "intimidation": 1},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="analyze_room",
                    text="Carefully examine the throne room",
                    description="Look for traps, exits, and tactical advantages",
                    choice_type="ANALYTICAL",
                    consequences={"tactical_awareness": 3, "preparation": 2, "caution": 1},
                    emoji="🔍"
                ),
                StoryChoice(
                    id="shadow_power",
                    text="Let your shadow power emanate",
                    description="Display your newfound abilities as a warning",
                    choice_type="POWER_DISPLAY",
                    consequences={"shadow_mastery": 3, "intimidation": 2, "power_control": 1},
                    emoji="👥"
                ),
                StoryChoice(
                    id="humble_approach",
                    text="Approach with humble determination",
                    description="Show respect while maintaining resolve",
                    choice_type="HUMBLE",
                    consequences={"humility": 2, "respect": 2, "inner_strength": 2},
                    emoji="🙇‍♂️"
                ),
                StoryChoice(
                    id="challenge_immediately",
                    text="Issue an immediate challenge",
                    description="Waste no time with pleasantries",
                    choice_type="DIRECT",
                    consequences={"directness": 3, "impatience": 1, "boldness": 2},
                    emoji="⚡"
                )
            ]
        ),

        StoryEvent(
            id="demon_king_dialogue",
            event_type="DIALOGUE",
            title="Face to Face with the Demon King",
            description="The Demon King sits upon his obsidian throne, his presence radiating power that makes the air itself tremble. His eyes, burning with the fires of hell, fix upon you with a mixture of amusement and respect.",
            speaker="Demon King",
            dialogue="So, a human has finally reached my throne room. Impressive. It has been centuries since anyone dared to challenge me in my own domain. Tell me, mortal, what drives you to seek death so eagerly?",
            choices=[
                StoryChoice(
                    id="declare_purpose",
                    text="I'm here to claim your power",
                    description="Boldly state your intention to defeat him",
                    choice_type="BOLD",
                    consequences={"confidence": 3, "determination": 2, "arrogance": 1},
                    emoji="👑"
                ),
                StoryChoice(
                    id="show_respect",
                    text="I seek to test my strength against yours",
                    description="Frame it as a test of worthiness",
                    choice_type="RESPECTFUL",
                    consequences={"honor": 2, "respect": 2, "humility": 1},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="mysterious_answer",
                    text="That's for me to know",
                    description="Keep your motivations mysterious",
                    choice_type="ENIGMATIC",
                    consequences={"mystery": 2, "intrigue": 2, "coolness": 1},
                    emoji="🎭"
                ),
                StoryChoice(
                    id="family_motivation",
                    text="I fight for those I must protect",
                    description="Reveal your drive to protect your family",
                    choice_type="NOBLE",
                    consequences={"nobility": 3, "family_bond": 2, "righteousness": 2},
                    emoji="👨‍👩‍👧"
                ),
                StoryChoice(
                    id="evolution_speech",
                    text="I seek to evolve beyond human limits",
                    description="Express your desire for transcendence",
                    choice_type="PHILOSOPHICAL",
                    consequences={"ambition": 3, "evolution_desire": 2, "transcendence": 1},
                    emoji="🦋"
                ),
                StoryChoice(
                    id="challenge_authority",
                    text="Your reign of terror ends today",
                    description="Position yourself as a hero stopping evil",
                    choice_type="HEROIC",
                    consequences={"heroism": 3, "justice": 2, "righteousness": 2},
                    emoji="🛡️"
                ),
                StoryChoice(
                    id="acknowledge_power",
                    text="I've come to learn from the strongest",
                    description="Show respect for his power while asserting your own growth",
                    choice_type="RESPECTFUL",
                    consequences={"wisdom_seeking": 2, "respect": 2, "learning_desire": 2},
                    emoji="📚"
                ),
                StoryChoice(
                    id="shadow_kinship",
                    text="We are both masters of shadows",
                    description="Acknowledge your shared connection to shadow power",
                    choice_type="UNDERSTANDING",
                    consequences={"shadow_mastery": 2, "kinship": 2, "understanding": 2},
                    emoji="🌑"
                ),
                StoryChoice(
                    id="destiny_claim",
                    text="This is my destiny",
                    description="Assert that fate has brought you here",
                    choice_type="FATALISTIC",
                    consequences={"destiny_belief": 3, "confidence": 2, "fate_acceptance": 1},
                    emoji="⭐"
                ),
                StoryChoice(
                    id="simple_truth",
                    text="I need to become stronger",
                    description="Give an honest, straightforward answer",
                    choice_type="HONEST",
                    consequences={"honesty": 2, "simplicity": 2, "determination": 2},
                    emoji="💪"
                )
            ]
        ),

        StoryEvent(
            id="demon_king_battle",
            event_type="BATTLE",
            title="The Ultimate Confrontation",
            description="The Demon King rises from his throne, his massive form radiating power that shakes the very foundations of the castle. This is the battle that will determine whether you're truly worthy of the title 'Shadow Monarch'.",
            speaker="Demon King",
            dialogue="Very well, human. Show me the strength that brought you to my throne. Let us see if you are worthy of the power you seek!",
            battle_enemies=[
                {
                    "name": "Demon King",
                    "level": 50,
                    "hp": 5000,
                    "attack": 200,
                    "defense": 150,
                    "skills": ["Demon Lord's Wrath", "Hellfire Storm", "Dark Regeneration", "Throne of Shadows"]
                }
            ]
        ),

        StoryEvent(
            id="victory_aftermath",
            event_type="TRIUMPHANT",
            title="The Demon King Falls",
            description="The Demon King lies defeated at your feet, his once-mighty form now still. As his power flows into you, you feel a fundamental change taking place. You are no longer just a hunter - you are becoming something far greater.",
            speaker="Demon King (Dying)",
            dialogue="Impossible... to think a human could possess such power... You are no ordinary mortal. Perhaps... perhaps you truly are worthy of the shadows...",
            choices=[
                StoryChoice(
                    id="show_mercy",
                    text="Grant him a warrior's death",
                    description="Show respect for a fallen opponent",
                    choice_type="HONORABLE",
                    consequences={"honor": 3, "respect": 2, "nobility": 2},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="claim_power",
                    text="Absorb his demonic power",
                    description="Take his strength to fuel your own growth",
                    choice_type="PRAGMATIC",
                    consequences={"power": 3, "darkness": 1, "strength": 2},
                    emoji="⚡"
                ),
                StoryChoice(
                    id="ask_questions",
                    text="Demand answers about the shadows",
                    description="Learn more about your true nature",
                    choice_type="INQUISITIVE",
                    consequences={"knowledge": 3, "understanding": 2, "wisdom": 1},
                    emoji="❓"
                )
            ]
        )
    ],

    # RED GATE EMERGENCY
    "red_gate_001": [
        StoryEvent(
            id="red_gate_emergency",
            event_type="URGENT",
            title="Red Gate Crisis",
            description="A Red Gate has appeared - a dungeon break that traps everyone inside until cleared. Several hunters are trapped within, and time is running out. The Association has called for emergency assistance.",
            speaker="Association Official",
            dialogue="Jin-Woo! We have a Red Gate situation. Multiple hunters are trapped inside, including some civilians. We need someone strong enough to clear it quickly. Will you help?",
            choices=[
                StoryChoice(
                    id="immediate_response",
                    text="I'll go in immediately",
                    description="Rush to save the trapped hunters without delay",
                    choice_type="HEROIC",
                    consequences={"heroism": 3, "urgency": 2, "leadership": 1},
                    emoji="🚨"
                ),
                StoryChoice(
                    id="gather_information",
                    text="Tell me about the situation first",
                    description="Get details about the Red Gate before entering",
                    choice_type="TACTICAL",
                    consequences={"preparation": 2, "intelligence": 2, "strategy": 1},
                    emoji="📋"
                ),
                StoryChoice(
                    id="assess_risks",
                    text="What are the risks involved?",
                    description="Understand the dangers before committing",
                    choice_type="CAUTIOUS",
                    consequences={"caution": 2, "analysis": 2, "responsibility": 1},
                    emoji="⚠️"
                )
            ]
        ),

        StoryEvent(
            id="red_gate_interior",
            event_type="RESCUE",
            title="Inside the Red Gate",
            description="The Red Gate's interior is a twisted landscape of ice and fire. You can sense the trapped hunters' fear and desperation. Time is running out, and the gate's instability is growing worse by the minute.",
            speaker="Trapped Hunter",
            dialogue="Thank god! Someone's here to help! The monsters in here are unlike anything we've faced before. Please, get us out of here!",
            battle_enemies=[
                {
                    "name": "Red Gate Guardian",
                    "level": 48,
                    "hp": 3500,
                    "attack": 160,
                    "defense": 120,
                    "skills": ["Dimensional Rift", "Chaos Strike", "Reality Tear"]
                }
            ]
        )
    ],

    # SHADOW MONARCH AWAKENING
    "shadow_monarch_001": [
        StoryEvent(
            id="monarch_awakening",
            event_type="TRANSFORMATION",
            title="The Shadow Monarch Awakens",
            description="Deep within your consciousness, something ancient stirs. The power you've been accumulating, the shadows that have been following you - it all leads to this moment. You are not just a hunter. You are the Shadow Monarch, ruler of the undead.",
            speaker="Shadow Monarch (Inner Voice)",
            dialogue="The time has come to embrace your true nature. You are not human - you are the sovereign of shadows, the commander of the dead. Will you accept your destiny?",
            choices=[
                StoryChoice(
                    id="embrace_destiny",
                    text="I accept my role as Shadow Monarch",
                    description="Fully embrace your true nature and power",
                    choice_type="ACCEPTANCE",
                    consequences={"power": 5, "darkness": 2, "authority": 3},
                    emoji="👑"
                ),
                StoryChoice(
                    id="resist_change",
                    text="I'm still human at heart",
                    description="Try to maintain your humanity despite the power",
                    choice_type="RESISTANCE",
                    consequences={"humanity": 3, "struggle": 2, "inner_conflict": 2},
                    emoji="❤️"
                ),
                StoryChoice(
                    id="seek_balance",
                    text="I'll use this power to protect others",
                    description="Channel your monarch power for good",
                    choice_type="BALANCED",
                    consequences={"protection": 3, "balance": 2, "nobility": 2},
                    emoji="⚖️"
                )
            ]
        ),

        StoryEvent(
            id="shadow_army_command",
            event_type="POWER",
            title="Command of the Shadow Army",
            description="Your shadow soldiers rise from the darkness - Igris, Tank, Iron, and countless others. They kneel before you, awaiting your commands. You feel the weight of absolute authority over the army of the dead.",
            speaker="Igris",
            dialogue="My lord, your shadow army awaits your command. We are yours to command in life, death, and beyond.",
            choices=[
                StoryChoice(
                    id="test_army",
                    text="Test the army's capabilities",
                    description="Put your shadow soldiers through their paces",
                    choice_type="TACTICAL",
                    consequences={"command": 2, "understanding": 2, "preparation": 1},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="show_respect",
                    text="Thank them for their loyalty",
                    description="Acknowledge your soldiers' dedication",
                    choice_type="RESPECTFUL",
                    consequences={"respect": 3, "loyalty": 2, "leadership": 1},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="plan_strategy",
                    text="Plan for future battles",
                    description="Discuss strategy with your shadow generals",
                    choice_type="STRATEGIC",
                    consequences={"strategy": 3, "planning": 2, "wisdom": 1},
                    emoji="🗺️"
                )
            ]
        )
    ],

    # JEJU ISLAND MISSION 1 - ANT QUEEN'S DOMAIN
    "jeju_island_001": [
        StoryEvent(
            id="jeju_island_arrival",
            event_type="EPIC",
            title="The Ant-Infested Island",
            description="Jeju Island stretches before you, but it's no longer the peaceful tourist destination it once was. Giant ant hills dot the landscape, and the air buzzes with the sound of massive insect wings. This is the domain of the Ant Queen - one of the most dangerous S-rank dungeons in the world.",
            speaker="Raid Leader",
            dialogue="Jin-Woo, this is it. The Ant Queen's domain. We've lost so many hunters to this place. Are you ready to face the most dangerous raid of your life?",
            choices=[
                StoryChoice(
                    id="lead_charge",
                    text="I'll lead the assault",
                    description="Take command of the raid and lead from the front",
                    choice_type="LEADERSHIP",
                    consequences={"leadership": 3, "courage": 2, "responsibility": 2},
                    emoji="👑"
                ),
                StoryChoice(
                    id="scout_ahead",
                    text="Let me scout the ant colonies first",
                    description="Use stealth to gather intelligence on the enemy",
                    choice_type="TACTICAL",
                    consequences={"intelligence": 3, "stealth": 2, "strategy": 1},
                    emoji="🔍"
                ),
                StoryChoice(
                    id="coordinate_team",
                    text="Coordinate with the other hunters",
                    description="Work together to plan the best approach",
                    choice_type="COLLABORATIVE",
                    consequences={"teamwork": 3, "coordination": 2, "unity": 1},
                    emoji="🤝"
                )
            ]
        ),

        StoryEvent(
            id="ant_queen_battle",
            event_type="BATTLE",
            title="The Ant Queen's Wrath",
            description="The massive Ant Queen emerges from her underground lair, her chitinous body gleaming with deadly beauty. She is accompanied by her elite guard - soldier ants the size of trucks, each one capable of destroying entire hunter teams.",
            speaker="Ant Queen",
            dialogue="*SCREECHES* Intruders in my domain! You dare challenge the mother of all ants? My children will feast on your bones!",
            battle_enemies=[
                {
                    "name": "Ant Queen",
                    "level": 65,
                    "hp": 8000,
                    "attack": 250,
                    "defense": 200,
                    "skills": ["Queen's Command", "Acid Spray", "Swarm Call", "Royal Guard"]
                },
                {
                    "name": "Elite Soldier Ant",
                    "level": 60,
                    "hp": 4000,
                    "attack": 180,
                    "defense": 140,
                    "skills": ["Mandible Crush", "Armor Pierce", "Hive Mind"]
                }
            ]
        )
    ],

    # JEJU ISLAND MISSION 2 - BERU'S LOYALTY
    "jeju_island_002": [
        StoryEvent(
            id="beru_encounter",
            event_type="DRAMATIC",
            title="The Ant King Beru",
            description="Before you stands Beru, the Ant King - a magnificent and terrifying creature with intelligence that rivals humans. Unlike the mindless drones, Beru possesses wisdom, pride, and an unshakeable loyalty to his queen. But now, with the queen defeated, he faces you with a mixture of respect and defiance.",
            speaker="Beru",
            dialogue="You... you are the one who defeated my queen. I sense great power within you, Shadow Monarch. But I am Beru, King of the Ants. I will not submit easily.",
            choices=[
                StoryChoice(
                    id="show_respect",
                    text="I respect your loyalty to your queen",
                    description="Acknowledge his devotion and honor",
                    choice_type="RESPECTFUL",
                    consequences={"respect": 3, "honor": 2, "understanding": 2},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="demonstrate_power",
                    text="Submit to my authority",
                    description="Display your overwhelming power to compel obedience",
                    choice_type="DOMINANT",
                    consequences={"dominance": 3, "authority": 2, "intimidation": 1},
                    emoji="👑"
                ),
                StoryChoice(
                    id="offer_partnership",
                    text="Join me as an equal",
                    description="Offer him a place as your trusted general",
                    choice_type="DIPLOMATIC",
                    consequences={"diplomacy": 3, "alliance": 2, "wisdom": 1},
                    emoji="🤝"
                )
            ]
        ),

        StoryEvent(
            id="beru_extraction",
            event_type="TRANSFORMATION",
            title="The Shadow Extraction",
            description="You extend your hand toward the fallen Ant King, calling upon your power as the Shadow Monarch. The extraction process begins - Beru's essence being drawn into the shadow realm, where he will be reborn as your eternal servant.",
            speaker="System",
            dialogue="SHADOW EXTRACTION IN PROGRESS... Target: Ant King Beru. Extraction Success Rate: 98%. Proceed with extraction?",
            choices=[
                StoryChoice(
                    id="complete_extraction",
                    text="Complete the shadow extraction",
                    description="Transform Beru into your shadow soldier",
                    choice_type="DECISIVE",
                    consequences={"power": 3, "shadow_army": 3, "authority": 2},
                    emoji="👤"
                ),
                StoryChoice(
                    id="offer_choice",
                    text="Give Beru a choice in the matter",
                    description="Allow him to decide his own fate",
                    choice_type="MERCIFUL",
                    consequences={"mercy": 3, "respect": 2, "honor": 2},
                    emoji="⚖️"
                )
            ]
        )
    ],

    # MONARCHS WAR MISSION 1 - BEAST MONARCH
    "monarchs_war_001": [
        StoryEvent(
            id="beast_monarch_confrontation",
            event_type="EPIC",
            title="The Beast Monarch's Challenge",
            description="The Beast Monarch stands before you - a primal force of nature given form. His massive frame radiates raw, untamed power, and his eyes burn with the fury of all wild things. This is not just a battle between individuals, but a clash between two fundamental forces of the universe.",
            speaker="Beast Monarch",
            dialogue="Shadow Monarch... so you are the one who has been disrupting the balance. I am the Beast Monarch, ruler of all wild creatures. Face me, and let us see which of us is truly worthy of the title 'Monarch'!",
            choices=[
                StoryChoice(
                    id="accept_challenge",
                    text="I accept your challenge",
                    description="Meet his challenge with equal pride and determination",
                    choice_type="HONORABLE",
                    consequences={"honor": 3, "courage": 2, "respect": 2},
                    emoji="⚔️"
                ),
                StoryChoice(
                    id="question_motives",
                    text="Why do you oppose me?",
                    description="Try to understand his motivations",
                    choice_type="DIPLOMATIC",
                    consequences={"understanding": 2, "wisdom": 2, "diplomacy": 1},
                    emoji="❓"
                ),
                StoryChoice(
                    id="display_power",
                    text="Show him your shadow army",
                    description="Demonstrate your authority over the shadows",
                    choice_type="INTIMIDATING",
                    consequences={"intimidation": 3, "authority": 2, "power": 1},
                    emoji="👤"
                )
            ]
        ),

        StoryEvent(
            id="beast_monarch_battle",
            event_type="BATTLE",
            title="Clash of the Monarchs",
            description="The battle between you and the Beast Monarch shakes the very earth. His primal fury meets your calculated precision, raw power against refined technique. This is a fight that will determine the hierarchy of the Monarchs.",
            speaker="Beast Monarch",
            dialogue="Show me your true power, Shadow Monarch! Let us see if you are worthy to stand among the rulers of this world!",
            battle_enemies=[
                {
                    "name": "Beast Monarch",
                    "level": 90,
                    "hp": 25000,
                    "attack": 600,
                    "defense": 500,
                    "skills": ["Primal Roar", "Beast King's Fury", "Wild Hunt", "Monarch's Authority"]
                }
            ]
        )
    ],

    # MONARCHS WAR MISSION 2 - ICE MONARCH
    "monarchs_war_002": [
        StoryEvent(
            id="ice_monarch_domain",
            event_type="CHILLING",
            title="The Frozen Wasteland",
            description="You enter the Ice Monarch's domain - a realm of eternal winter where the very air freezes in your lungs. Ice sculptures of fallen warriors line the path, and the aurora borealis dances overhead in unnatural patterns. The Ice Monarch awaits you at the heart of this frozen hell.",
            speaker="Ice Monarch",
            dialogue="Welcome to my domain, Shadow Monarch. Here, in the eternal cold, I have waited for a worthy opponent. Your shadows may be deep, but can they withstand the absolute zero of my realm?",
            choices=[
                StoryChoice(
                    id="adapt_to_cold",
                    text="Adapt your shadows to the cold",
                    description="Use your power to resist the freezing environment",
                    choice_type="ADAPTIVE",
                    consequences={"adaptation": 3, "resilience": 2, "power": 1},
                    emoji="❄️"
                ),
                StoryChoice(
                    id="direct_confrontation",
                    text="Face him immediately",
                    description="Don't give him time to use his domain advantage",
                    choice_type="AGGRESSIVE",
                    consequences={"aggression": 3, "speed": 2, "boldness": 1},
                    emoji="⚡"
                ),
                StoryChoice(
                    id="study_environment",
                    text="Analyze his frozen domain",
                    description="Look for weaknesses in his icy realm",
                    choice_type="ANALYTICAL",
                    consequences={"analysis": 3, "intelligence": 2, "strategy": 1},
                    emoji="🔍"
                )
            ]
        ),

        StoryEvent(
            id="ice_monarch_battle",
            event_type="BATTLE",
            title="Fire and Ice",
            description="The Ice Monarch's power is absolute zero - the complete absence of heat and motion. But your shadows burn with the fire of determination. This battle is between the stillness of death and the movement of life itself.",
            speaker="Ice Monarch",
            dialogue="Behold the power of absolute zero! In my domain, even time itself freezes!",
            battle_enemies=[
                {
                    "name": "Ice Monarch",
                    "level": 92,
                    "hp": 28000,
                    "attack": 650,
                    "defense": 550,
                    "skills": ["Absolute Zero", "Frozen Time", "Ice Age", "Glacial Prison"]
                }
            ]
        )
    ],

    # MONARCHS WAR MISSION 3 - DRAGON EMPEROR
    "monarchs_war_003": [
        StoryEvent(
            id="dragon_emperor_arrival",
            event_type="LEGENDARY",
            title="The Dragon Emperor's Domain",
            description="You stand before the most ancient and powerful of all Monarchs - the Dragon Emperor. His massive form coils through the air, scales gleaming like molten gold, eyes burning with the wisdom of eons. This is the ultimate test of your power as the Shadow Monarch.",
            speaker="Dragon Emperor",
            dialogue="So, the Shadow Monarch finally comes before me. I have ruled since before your kind learned to make fire. I have seen empires rise and fall like waves upon the shore. What makes you think you can challenge one such as I?",
            choices=[
                StoryChoice(
                    id="show_humility",
                    text="I seek to learn from your wisdom",
                    description="Approach with respect for his ancient knowledge",
                    choice_type="HUMBLE",
                    consequences={"wisdom": 3, "respect": 3, "learning": 2},
                    emoji="🙏"
                ),
                StoryChoice(
                    id="declare_equality",
                    text="We are both Monarchs",
                    description="Assert your right to stand as his equal",
                    choice_type="CONFIDENT",
                    consequences={"confidence": 3, "authority": 2, "pride": 1},
                    emoji="👑"
                ),
                StoryChoice(
                    id="challenge_directly",
                    text="Your age means nothing to me",
                    description="Boldly challenge his authority",
                    choice_type="DEFIANT",
                    consequences={"defiance": 3, "courage": 2, "recklessness": 1},
                    emoji="⚔️"
                )
            ]
        ),

        StoryEvent(
            id="dragon_emperor_battle",
            event_type="BATTLE",
            title="The Ultimate Monarch Battle",
            description="The Dragon Emperor unleashes his full power - the accumulated might of countless millennia. His roar shakes the foundations of reality itself, and his flames burn with the heat of dying stars. This is the battle that will determine the true ruler of all Monarchs.",
            speaker="Dragon Emperor",
            dialogue="Very well, young Shadow Monarch. Let me show you the power that has ruled this world since time immemorial!",
            battle_enemies=[
                {
                    "name": "Dragon Emperor",
                    "level": 95,
                    "hp": 40000,
                    "attack": 750,
                    "defense": 650,
                    "skills": ["Dragon Emperor's Wrath", "Stellar Flame", "Time Distortion", "Imperial Command", "Ancient Wisdom"]
                }
            ]
        )
    ],

    # FINAL BATTLE MISSION 1 - THE ARCHITECT'S PLAN
    "final_battle_001": [
        StoryEvent(
            id="architect_revelation",
            event_type="REVELATION",
            title="The Truth Behind the System",
            description="You stand before the Architect - the mysterious entity behind the System that has guided your growth. The truth is more shocking than you could have imagined: the System, the gates, the monsters - all of it was designed to prepare humanity for a war between worlds.",
            speaker="The Architect",
            dialogue="Welcome, Shadow Monarch. You have exceeded all expectations. The System I created was designed to forge the ultimate weapon against the Rulers - and that weapon is you. But now, you must choose: will you fulfill your purpose, or will you forge your own path?",
            choices=[
                StoryChoice(
                    id="question_purpose",
                    text="What is my true purpose?",
                    description="Demand to know the full truth about your role",
                    choice_type="INQUISITIVE",
                    consequences={"knowledge": 3, "understanding": 2, "truth": 2},
                    emoji="❓"
                ),
                StoryChoice(
                    id="reject_manipulation",
                    text="I refuse to be your weapon",
                    description="Reject the Architect's plans for you",
                    choice_type="DEFIANT",
                    consequences={"independence": 3, "defiance": 2, "free_will": 2},
                    emoji="✊"
                ),
                StoryChoice(
                    id="accept_responsibility",
                    text="I'll protect both worlds",
                    description="Accept the burden of protecting humanity and the shadow realm",
                    choice_type="HEROIC",
                    consequences={"heroism": 3, "responsibility": 2, "sacrifice": 1},
                    emoji="🛡️"
                )
            ]
        ),

        StoryEvent(
            id="architect_battle",
            event_type="BATTLE",
            title="Creator vs Creation",
            description="The Architect reveals his true form - a being of pure energy and calculation, the embodiment of systematic perfection. This battle is not just physical, but a clash between predetermined fate and free will itself.",
            speaker="The Architect",
            dialogue="If you will not serve your purpose willingly, then I will remake you into the weapon I need!",
            battle_enemies=[
                {
                    "name": "The Architect",
                    "level": 100,
                    "hp": 50000,
                    "attack": 800,
                    "defense": 700,
                    "skills": ["System Override", "Reality Rewrite", "Fate Manipulation", "Perfect Calculation"]
                }
            ]
        )
    ],

    # FINAL BATTLE MISSION 2 - THE ULTIMATE SACRIFICE
    "final_battle_002": [
        StoryEvent(
            id="ultimate_choice",
            event_type="CLIMACTIC",
            title="The Ultimate Sacrifice",
            description="The war between worlds has reached its climax. The Rulers have launched their final assault, and only you have the power to stop them. But victory will require the ultimate sacrifice - using your power to reset time itself, erasing your growth and starting over.",
            speaker="Jin-Woo (Internal)",
            dialogue="This is it. The final choice. I can save everyone - Mom, Jin-Ah, all the hunters who died, everyone who suffered because of the gates. But I'll lose everything I've gained. Is it worth it?",
            choices=[
                StoryChoice(
                    id="make_sacrifice",
                    text="Reset time to save everyone",
                    description="Sacrifice your power to give everyone a second chance",
                    choice_type="SACRIFICIAL",
                    consequences={"sacrifice": 5, "love": 3, "heroism": 3},
                    emoji="⏰"
                ),
                StoryChoice(
                    id="find_another_way",
                    text="Look for an alternative solution",
                    description="Try to find a way to save everyone without losing your power",
                    choice_type="DETERMINED",
                    consequences={"determination": 3, "creativity": 2, "hope": 2},
                    emoji="💡"
                ),
                StoryChoice(
                    id="accept_losses",
                    text="Some sacrifices are necessary",
                    description="Accept that some losses are unavoidable",
                    choice_type="PRAGMATIC",
                    consequences={"pragmatism": 2, "realism": 2, "burden": 3},
                    emoji="⚖️"
                )
            ]
        )
    ],

    # FINAL BATTLE MISSION 3 - THE NEW BEGINNING
    "final_battle_003": [
        StoryEvent(
            id="new_timeline",
            event_type="HOPEFUL",
            title="A New Beginning",
            description="Time has been reset, but you retain your memories and power. The gates never opened, the monsters never came, and the people you love are safe. You stand at the beginning of a new timeline, with the wisdom of your experiences and the power to protect this peaceful world.",
            speaker="Jin-Woo (Internal)",
            dialogue="It worked. Everyone is safe. Mom is healthy, Jin-Ah is happy, and the world is at peace. I remember everything, but to them, the nightmare never happened. This is the world I fought to protect.",
            choices=[
                StoryChoice(
                    id="live_quietly",
                    text="Live a normal life with your family",
                    description="Enjoy the peaceful world you created",
                    choice_type="PEACEFUL",
                    consequences={"peace": 3, "family": 3, "contentment": 2},
                    emoji="🏠"
                ),
                StoryChoice(
                    id="stay_vigilant",
                    text="Remain ready for any threats",
                    description="Keep your power hidden but stay prepared",
                    choice_type="VIGILANT",
                    consequences={"vigilance": 3, "preparedness": 2, "responsibility": 2},
                    emoji="👁️"
                ),
                StoryChoice(
                    id="help_others",
                    text="Use your power to help people secretly",
                    description="Become a hidden guardian of this peaceful world",
                    choice_type="GUARDIAN",
                    consequences={"protection": 3, "altruism": 2, "purpose": 2},
                    emoji="🛡️"
                ),
                StoryChoice(
                    id="cherish_memories",
                    text="Treasure the memories of your journey",
                    description="Hold onto the experiences that made you who you are",
                    choice_type="REFLECTIVE",
                    consequences={"wisdom": 3, "nostalgia": 2, "growth_appreciation": 2},
                    emoji="💭"
                ),
                StoryChoice(
                    id="teach_others",
                    text="Subtly guide others to be their best",
                    description="Help people grow without revealing your true nature",
                    choice_type="MENTOR",
                    consequences={"mentorship": 3, "guidance": 2, "wisdom_sharing": 2},
                    emoji="🎓"
                ),
                StoryChoice(
                    id="explore_world",
                    text="Explore this peaceful world",
                    description="Discover the beauty of a world without monsters",
                    choice_type="CURIOUS",
                    consequences={"exploration": 2, "wonder": 3, "appreciation": 2},
                    emoji="🌍"
                ),
                StoryChoice(
                    id="strengthen_bonds",
                    text="Focus on deepening family relationships",
                    description="Make up for lost time with those you love",
                    choice_type="FAMILY_FOCUSED",
                    consequences={"family_bond": 4, "love": 3, "healing": 2},
                    emoji="❤️"
                ),
                StoryChoice(
                    id="document_journey",
                    text="Record your experiences for posterity",
                    description="Ensure the lessons learned are never forgotten",
                    choice_type="HISTORIAN",
                    consequences={"legacy": 3, "wisdom_preservation": 2, "responsibility": 2},
                    emoji="📖"
                ),
                StoryChoice(
                    id="prepare_contingency",
                    text="Create safeguards for future threats",
                    description="Establish systems to protect this timeline",
                    choice_type="STRATEGIC",
                    consequences={"strategic_thinking": 3, "preparedness": 3, "foresight": 2},
                    emoji="🛡️"
                ),
                StoryChoice(
                    id="find_inner_peace",
                    text="Seek inner peace after your long journey",
                    description="Finally allow yourself to rest and heal",
                    choice_type="HEALING",
                    consequences={"inner_peace": 4, "healing": 3, "self_care": 2},
                    emoji="🧘‍♂️"
                )
            ]
        ),

        StoryEvent(
            id="eternal_guardian",
            event_type="EPILOGUE",
            title="The Eternal Guardian",
            description="You have become the eternal guardian of this peaceful world. Your shadow army remains hidden in the darkness, ready to defend against any threat that might emerge. You are no longer just the Shadow Monarch - you are the protector of all that is good and peaceful in this world.",
            speaker="Narrator",
            dialogue="And so, Sung Jin-Woo's journey comes full circle. From the weakest hunter to the strongest being in existence, from a desperate young man to the eternal guardian of peace. His story is one of growth, sacrifice, and ultimately, love for those he holds dear.",
            choices=[
                StoryChoice(
                    id="embrace_role",
                    text="Accept your role as eternal guardian",
                    description="Embrace your destiny as protector of the peaceful world",
                    choice_type="ACCEPTANCE",
                    consequences={"purpose": 5, "fulfillment": 3, "eternal_duty": 2},
                    emoji="👑"
                )
            ]
        )
    ]
}
