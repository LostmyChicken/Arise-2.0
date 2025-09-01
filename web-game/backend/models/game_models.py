from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class Hunter(Base):
    __tablename__ = "hunters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    rank = Column(String, default="E")  # E, D, C, B, A, S
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # Stats
    health = Column(Integer, default=100)
    max_health = Column(Integer, default=100)
    mana = Column(Integer, default=50)
    max_mana = Column(Integer, default=50)
    attack = Column(Integer, default=10)
    defense = Column(Integer, default=5)
    agility = Column(Integer, default=5)
    intelligence = Column(Integer, default=5)
    
    # Resources
    gold = Column(Integer, default=1000)
    gems = Column(Integer, default=100)
    energy = Column(Integer, default=100)
    tickets = Column(Integer, default=5)
    
    # Equipment
    weapon_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    armor_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="hunter")
    weapon = relationship("Item", foreign_keys=[weapon_id])
    armor = relationship("Item", foreign_keys=[armor_id])
    shadows = relationship("Shadow", back_populates="hunter")
    battles = relationship("Battle", back_populates="hunter")

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)  # weapon, armor, consumable
    rarity = Column(String)  # common, rare, epic, legendary
    
    # Stats bonuses
    attack_bonus = Column(Integer, default=0)
    defense_bonus = Column(Integer, default=0)
    health_bonus = Column(Integer, default=0)
    mana_bonus = Column(Integer, default=0)
    
    # Item properties
    description = Column(Text)
    image_url = Column(String)
    price = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Shadow(Base):
    __tablename__ = "shadows"
    
    id = Column(Integer, primary_key=True, index=True)
    hunter_id = Column(Integer, ForeignKey("hunters.id"))
    name = Column(String)
    type = Column(String)  # soldier, knight, mage, archer
    rank = Column(String)  # normal, elite, boss
    level = Column(Integer, default=1)
    
    # Stats
    attack = Column(Integer)
    defense = Column(Integer)
    health = Column(Integer)
    
    # Special abilities
    abilities = Column(JSON)  # Store as JSON array
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    hunter = relationship("Hunter", back_populates="shadows")

class Monster(Base):
    __tablename__ = "monsters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)  # beast, undead, demon, etc.
    rank = Column(String)  # E, D, C, B, A, S
    level = Column(Integer)
    
    # Stats
    health = Column(Integer)
    max_health = Column(Integer)
    attack = Column(Integer)
    defense = Column(Integer)
    agility = Column(Integer)
    
    # Rewards
    experience_reward = Column(Integer)
    gold_reward = Column(Integer)
    drop_items = Column(JSON)  # Possible item drops
    
    # Monster properties
    description = Column(Text)
    image_url = Column(String)
    abilities = Column(JSON)  # Special abilities
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Battle(Base):
    __tablename__ = "battles"
    
    id = Column(Integer, primary_key=True, index=True)
    hunter_id = Column(Integer, ForeignKey("hunters.id"))
    monster_id = Column(Integer, ForeignKey("monsters.id"))
    
    # Battle state
    status = Column(String, default="active")  # active, won, lost, fled
    turn = Column(Integer, default=1)
    hunter_health = Column(Integer)
    monster_health = Column(Integer)
    
    # Battle log
    battle_log = Column(JSON)  # Store battle actions as JSON
    
    # Results
    experience_gained = Column(Integer, default=0)
    gold_gained = Column(Integer, default=0)
    items_gained = Column(JSON)  # Items received
    
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # Relationships
    hunter = relationship("Hunter", back_populates="battles")
    monster = relationship("Monster")

class GachaPull(Base):
    __tablename__ = "gacha_pulls"
    
    id = Column(Integer, primary_key=True, index=True)
    hunter_id = Column(Integer, ForeignKey("hunters.id"))
    pull_type = Column(String)  # single, ten_pull
    cost = Column(Integer)
    currency = Column(String)  # gems, tickets
    
    # Results
    items_received = Column(JSON)  # Items from the pull
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Guild(Base):
    __tablename__ = "guilds"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    leader_id = Column(Integer, ForeignKey("hunters.id"))
    
    # Guild stats
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    member_count = Column(Integer, default=1)
    max_members = Column(Integer, default=20)
    
    # Guild resources
    guild_gold = Column(Integer, default=0)
    guild_points = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    leader = relationship("Hunter")
    members = relationship("GuildMember", back_populates="guild")

class GuildMember(Base):
    __tablename__ = "guild_members"
    
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"))
    hunter_id = Column(Integer, ForeignKey("hunters.id"))
    role = Column(String, default="member")  # leader, officer, member
    contribution = Column(Integer, default=0)
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    guild = relationship("Guild", back_populates="members")
    hunter = relationship("Hunter")

class StoryChapter(Base):
    __tablename__ = "story_chapters"
    
    id = Column(Integer, primary_key=True, index=True)
    chapter_number = Column(Integer, unique=True)
    title = Column(String)
    description = Column(Text)
    
    # Requirements
    required_level = Column(Integer, default=1)
    required_rank = Column(String, default="E")
    
    # Rewards
    experience_reward = Column(Integer)
    gold_reward = Column(Integer)
    item_rewards = Column(JSON)
    
    # Story content
    story_text = Column(Text)
    choices = Column(JSON)  # Story choices and consequences
    
    created_at = Column(DateTime, default=datetime.utcnow)

class HunterProgress(Base):
    __tablename__ = "hunter_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    hunter_id = Column(Integer, ForeignKey("hunters.id"))
    chapter_id = Column(Integer, ForeignKey("story_chapters.id"))
    completed = Column(Boolean, default=False)
    choices_made = Column(JSON)  # Track player choices
    
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    hunter = relationship("Hunter")
    chapter = relationship("StoryChapter")