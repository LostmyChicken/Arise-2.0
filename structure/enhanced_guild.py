"""
Enhanced Guild System with Vice Guild Masters and Advanced Features
"""
import json
import sqlite3
import aiosqlite
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from enum import Enum

DATABASE_PATH = "database.db"

class GuildRole(Enum):
    MEMBER = "member"
    OFFICER = "officer"
    VICE_MASTER = "vice_master"
    GUILD_MASTER = "guild_master"

class GuildPermission(Enum):
    INVITE_MEMBERS = "invite_members"
    KICK_MEMBERS = "kick_members"
    PROMOTE_MEMBERS = "promote_members"
    DEMOTE_MEMBERS = "demote_members"
    MANAGE_APPLICATIONS = "manage_applications"
    EDIT_GUILD_INFO = "edit_guild_info"
    MANAGE_ALLIANCES = "manage_alliances"
    DELETE_GUILD = "delete_guild"
    MANAGE_GUILD_BANK = "manage_guild_bank"
    START_GUILD_EVENTS = "start_guild_events"

class EnhancedGuild:
    def __init__(self, id: str, name: str, owner: int, members: List[Dict], level: int, 
                 points: int, image: str, description: str, gates: int, 
                 allow_alliances: bool = False, guild_bank: Dict = None, 
                 applications: List[Dict] = None, settings: Dict = None,
                 created_at: str = None, last_active: str = None):
        self.id = id
        self.name = name
        self.owner = owner  # Guild Master ID
        self.members = members or []  # [{"id": int, "role": str, "joined_at": str, "contribution": int, "last_active": str}]
        self.level = level
        self.points = points
        self.image = image
        self.description = description
        self.gates = gates
        self.allow_alliances = allow_alliances
        self.guild_bank = guild_bank or {"gold": 0, "diamond": 0, "crystals": 0}
        self.applications = applications or []  # [{"user_id": int, "message": str, "applied_at": str}]
        self.settings = settings or {
            "auto_accept_applications": False,
            "min_level_requirement": 1,
            "application_required": True,
            "max_members": 50,
            "public_visibility": True
        }
        self.created_at = created_at or datetime.now().isoformat()
        self.last_active = last_active or datetime.now().isoformat()

    @staticmethod
    def get_role_permissions(role: GuildRole) -> List[GuildPermission]:
        """Get permissions for a specific guild role"""
        permissions = {
            GuildRole.MEMBER: [],
            GuildRole.OFFICER: [
                GuildPermission.INVITE_MEMBERS,
                GuildPermission.MANAGE_APPLICATIONS
            ],
            GuildRole.VICE_MASTER: [
                GuildPermission.INVITE_MEMBERS,
                GuildPermission.KICK_MEMBERS,
                GuildPermission.PROMOTE_MEMBERS,
                GuildPermission.DEMOTE_MEMBERS,
                GuildPermission.MANAGE_APPLICATIONS,
                GuildPermission.EDIT_GUILD_INFO,
                GuildPermission.MANAGE_GUILD_BANK,
                GuildPermission.START_GUILD_EVENTS
            ],
            GuildRole.GUILD_MASTER: [perm for perm in GuildPermission]  # All permissions
        }
        return permissions.get(role, [])

    def get_member_role(self, user_id: int) -> Optional[GuildRole]:
        """Get the role of a specific member"""
        if user_id == self.owner:
            return GuildRole.GUILD_MASTER
        
        for member in self.members:
            if member["id"] == user_id:
                return GuildRole(member.get("role", "member"))
        return None

    def has_permission(self, user_id: int, permission: GuildPermission) -> bool:
        """Check if a user has a specific permission"""
        role = self.get_member_role(user_id)
        if not role:
            return False
        
        permissions = self.get_role_permissions(role)
        return permission in permissions

    async def add_member(self, user_id: int, role: GuildRole = GuildRole.MEMBER) -> bool:
        """Add a new member to the guild"""
        if len(self.members) >= self.settings["max_members"]:
            return False
        
        # Check if already a member
        if any(member["id"] == user_id for member in self.members):
            return False
        
        member_data = {
            "id": user_id,
            "role": role.value,
            "joined_at": datetime.now().isoformat(),
            "contribution": 0,
            "last_active": datetime.now().isoformat()
        }
        
        self.members.append(member_data)
        await self.save()
        return True

    async def remove_member(self, user_id: int) -> bool:
        """Remove a member from the guild"""
        original_count = len(self.members)
        self.members = [member for member in self.members if member["id"] != user_id]
        
        if len(self.members) < original_count:
            await self.save()
            return True
        return False

    async def promote_member(self, user_id: int, new_role: GuildRole) -> bool:
        """Promote a member to a higher role"""
        for member in self.members:
            if member["id"] == user_id:
                member["role"] = new_role.value
                await self.save()
                return True
        return False

    async def add_application(self, user_id: int, message: str = "") -> bool:
        """Add a guild application"""
        # Check if already applied
        if any(app["user_id"] == user_id for app in self.applications):
            return False
        
        application = {
            "user_id": user_id,
            "message": message,
            "applied_at": datetime.now().isoformat()
        }
        
        self.applications.append(application)
        await self.save()
        return True

    async def process_application(self, user_id: int, accepted: bool) -> bool:
        """Process a guild application (accept or reject)"""
        application = None
        for app in self.applications:
            if app["user_id"] == user_id:
                application = app
                break
        
        if not application:
            return False
        
        # Remove application
        self.applications = [app for app in self.applications if app["user_id"] != user_id]
        
        if accepted:
            await self.add_member(user_id)
        
        await self.save()
        return True

    async def contribute_to_bank(self, currency: str, amount: int) -> bool:
        """Add currency to guild bank"""
        if currency in self.guild_bank:
            self.guild_bank[currency] += amount
            await self.save()
            return True
        return False

    async def withdraw_from_bank(self, currency: str, amount: int) -> bool:
        """Withdraw currency from guild bank"""
        if currency in self.guild_bank and self.guild_bank[currency] >= amount:
            self.guild_bank[currency] -= amount
            await self.save()
            return True
        return False

    def get_member_count_by_role(self) -> Dict[str, int]:
        """Get count of members by role"""
        counts = {"member": 0, "officer": 0, "vice_master": 0, "guild_master": 1}
        
        for member in self.members:
            role = member.get("role", "member")
            if role in counts:
                counts[role] += 1
        
        return counts

    def get_top_contributors(self, limit: int = 10) -> List[Dict]:
        """Get top contributing members"""
        sorted_members = sorted(self.members, key=lambda x: x.get("contribution", 0), reverse=True)
        return sorted_members[:limit]

    async def update_member_activity(self, user_id: int):
        """Update member's last active timestamp"""
        for member in self.members:
            if member["id"] == user_id:
                member["last_active"] = datetime.now().isoformat()
                break
        
        self.last_active = datetime.now().isoformat()
        await self.save()

    async def save(self):
        """Save guild to database"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Check if guild exists
            async with db.execute("SELECT 1 FROM enhanced_guilds WHERE id = ?", (self.id,)) as cursor:
                exists = await cursor.fetchone()
            
            if exists:
                await db.execute("""
                    UPDATE enhanced_guilds SET
                    name = ?, owner = ?, members = ?, level = ?, points = ?, 
                    image = ?, description = ?, gates = ?, allow_alliances = ?,
                    guild_bank = ?, applications = ?, settings = ?, last_active = ?
                    WHERE id = ?
                """, (
                    self.name, self.owner, json.dumps(self.members), self.level, self.points,
                    self.image, self.description, self.gates, int(self.allow_alliances),
                    json.dumps(self.guild_bank), json.dumps(self.applications), 
                    json.dumps(self.settings), self.last_active, self.id
                ))
            else:
                await db.execute("""
                    INSERT INTO enhanced_guilds 
                    (id, name, owner, members, level, points, image, description, gates, 
                     allow_alliances, guild_bank, applications, settings, created_at, last_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.id, self.name, self.owner, json.dumps(self.members), self.level, self.points,
                    self.image, self.description, self.gates, int(self.allow_alliances),
                    json.dumps(self.guild_bank), json.dumps(self.applications), 
                    json.dumps(self.settings), self.created_at, self.last_active
                ))
            
            await db.commit()

    @staticmethod
    async def get(guild_id: str) -> Optional['EnhancedGuild']:
        """Get guild by ID"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT * FROM enhanced_guilds WHERE id = ?", (guild_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return EnhancedGuild(
                        id=row[0], name=row[1], owner=row[2], 
                        members=json.loads(row[3]) if row[3] else [],
                        level=row[4], points=row[5], image=row[6], description=row[7],
                        gates=row[8], allow_alliances=bool(row[9]),
                        guild_bank=json.loads(row[10]) if row[10] else {"gold": 0, "diamond": 0, "crystals": 0},
                        applications=json.loads(row[11]) if row[11] else [],
                        settings=json.loads(row[12]) if row[12] else {},
                        created_at=row[13], last_active=row[14]
                    )
        return None

    @staticmethod
    async def get_all() -> List['EnhancedGuild']:
        """Get all guilds"""
        guilds = []
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT * FROM enhanced_guilds ORDER BY points DESC") as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    guild = EnhancedGuild(
                        id=row[0], name=row[1], owner=row[2], 
                        members=json.loads(row[3]) if row[3] else [],
                        level=row[4], points=row[5], image=row[6], description=row[7],
                        gates=row[8], allow_alliances=bool(row[9]),
                        guild_bank=json.loads(row[10]) if row[10] else {"gold": 0, "diamond": 0, "crystals": 0},
                        applications=json.loads(row[11]) if row[11] else [],
                        settings=json.loads(row[12]) if row[12] else {},
                        created_at=row[13], last_active=row[14]
                    )
                    guilds.append(guild)
        return guilds

    @staticmethod
    def initialize():
        """Initialize enhanced guild database table"""
        with sqlite3.connect(DATABASE_PATH) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS enhanced_guilds (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    owner INTEGER NOT NULL,
                    members TEXT DEFAULT '[]',
                    level INTEGER DEFAULT 1,
                    points INTEGER DEFAULT 0,
                    image TEXT,
                    description TEXT,
                    gates INTEGER DEFAULT 0,
                    allow_alliances INTEGER DEFAULT 0,
                    guild_bank TEXT DEFAULT '{"gold": 0, "diamond": 0, "crystals": 0}',
                    applications TEXT DEFAULT '[]',
                    settings TEXT DEFAULT '{}',
                    created_at TEXT,
                    last_active TEXT
                )
            """)
            db.commit()

    async def delete(self):
        """Delete the guild"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("DELETE FROM enhanced_guilds WHERE id = ?", (self.id,))
            await db.commit()

    def get_guild_tier(self) -> tuple:
        """Get guild tier based on points"""
        tiers = {
            "Legendary": (2000000, 0xFFD700),  # Gold
            "S-Tier": (1000000, 0xFF6B6B),    # Red
            "A-Tier": (500000, 0x4ECDC4),     # Teal
            "B-Tier": (250000, 0x45B7D1),     # Blue
            "C-Tier": (100000, 0x96CEB4),     # Green
            "D-Tier": (50000, 0xFECA57),      # Yellow
            "E-Tier": (0, 0x95A5A6)           # Gray
        }

        for tier, (min_points, color) in tiers.items():
            if self.points >= min_points:
                return tier, color

        return "E-Tier", 0x95A5A6

    def get_level_progress(self) -> tuple:
        """Get guild level progress"""
        points_for_next_level = self.level * 10000  # 10k points per level
        current_level_points = self.points % points_for_next_level
        progress_percentage = (current_level_points / points_for_next_level) * 100

        return current_level_points, points_for_next_level, progress_percentage

    def is_member(self, user_id: int) -> bool:
        """Check if user is a member of the guild"""
        if user_id == self.owner:
            return True
        return any(member["id"] == user_id for member in self.members)

    def get_member_info(self, user_id: int) -> Optional[Dict]:
        """Get detailed member information"""
        if user_id == self.owner:
            return {
                "id": user_id,
                "role": "guild_master",
                "joined_at": self.created_at,
                "contribution": 0,
                "last_active": self.last_active
            }

        for member in self.members:
            if member["id"] == user_id:
                return member
        return None

    async def add_contribution(self, user_id: int, points: int):
        """Add contribution points to a member"""
        for member in self.members:
            if member["id"] == user_id:
                member["contribution"] = member.get("contribution", 0) + points
                break

        self.points += points

        # Check for level up
        new_level = (self.points // 10000) + 1
        if new_level > self.level:
            self.level = new_level

        await self.save()

    def get_inactive_members(self, days: int = 7) -> List[Dict]:
        """Get members inactive for specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        inactive_members = []

        for member in self.members:
            last_active = datetime.fromisoformat(member.get("last_active", self.created_at))
            if last_active < cutoff_date:
                inactive_members.append(member)

        return inactive_members

    def get_role_display_name(self, role: str) -> str:
        """Get display name for role"""
        role_names = {
            "member": "👤 Member",
            "officer": "⭐ Officer",
            "vice_master": "👑 Vice Master",
            "guild_master": "🏆 Guild Master"
        }
        return role_names.get(role, "👤 Member")

    def can_promote_to_role(self, promoter_role: GuildRole, target_role: GuildRole) -> bool:
        """Check if a role can promote to another role"""
        role_hierarchy = {
            GuildRole.MEMBER: 0,
            GuildRole.OFFICER: 1,
            GuildRole.VICE_MASTER: 2,
            GuildRole.GUILD_MASTER: 3
        }

        promoter_level = role_hierarchy.get(promoter_role, 0)
        target_level = role_hierarchy.get(target_role, 0)

        # Can only promote to roles below your own level
        return promoter_level > target_level and promoter_level >= 2  # Vice Master or Guild Master
