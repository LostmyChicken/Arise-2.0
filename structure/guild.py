import json
import logging
import sqlite3
import aiosqlite

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("player", "data/player.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "data/player.db"

DATABASE_PATH = get_database_path()

import json

class Guild:
    def __init__(self, id, name, owner, members, level, points, image, description, gates, allow_alliances=False):
        self.id = id
        self.name = name
        self.owner = owner
        self.members = members  # List of dictionaries: [{"id": member_id, "gc": gates_cleared}, ...]
        self.level = level
        self.points = points
        self.image = image
        self.description = description
        self.gates = gates  # Total guild gates cleared
        self.allow_alliances = allow_alliances  # New: Allow other guilds to join gates
        
    async def delete(self):
        """Deletes the guild from the database."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("DELETE FROM guilds WHERE id = ?", (self.id,))
            await db.commit()

    @staticmethod
    async def get(guild_id: str):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT * FROM guilds WHERE id = ?", (guild_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    row = list(row)
                    # Parse members as JSON
                    row[3] = json.loads(row[3]) if row[3] else []
                    # Handle missing allow_alliances column for backward compatibility
                    if len(row) < 10:
                        row.append(False)  # Default to False for allow_alliances
                    else:
                        row[9] = bool(row[9])  # Convert to boolean
                    return Guild(*row)
                return None

    @staticmethod
    async def get_all():
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT * FROM guilds") as cursor:
                rows = await cursor.fetchall()
                if rows:
                    guilds = []
                    for row in rows:
                        row = list(row)
                        # Parse members as JSON
                        row[3] = json.loads(row[3]) if row[3] else []
                        guilds.append(Guild(*row))
                    return guilds
                return []

    async def save(self):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT 1 FROM guilds WHERE id = ?", (self.id,)) as cursor:
                if await cursor.fetchone():
                    await db.execute("""
                        UPDATE guilds
                        SET name = ?, owner = ?, members = ?, level = ?, points = ?, image = ?, description = ?, gates = ?, allow_alliances = ?
                        WHERE id = ?
                    """, (self.name, self.owner, json.dumps(self.members), self.level, self.points, self.image, self.description, self.gates, int(self.allow_alliances), self.id))
                else:
                    await db.execute("""
                        INSERT INTO guilds (id, name, owner, members, level, points, image, description, gates, allow_alliances)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (self.id, self.name, self.owner, json.dumps(self.members), self.level, self.points, self.image, self.description, self.gates, int(self.allow_alliances)))
                await db.commit()

    async def get_members(self):
        """
        Fetch all members of the guild with their gates cleared (gc) count.
        Returns a list of dictionaries containing member ID and gates cleared.
        """
        return self.members

    async def add_member(self, member_id: str, gates_cleared: int = 0):
        """
        Add a member to the guild with their gates cleared count.
        """
        self.members.append({"id": member_id, "gc": gates_cleared})
        await self.save()

    def update_member_gc(self, member_id: str):
        """
        Update the gates cleared count for a member.
        """
        for member in self.members:
            if member["id"] == member_id:
                member["gc"] += 1
                break

    async def remove_member(self, member_id: str):
        """
        Remove a member from the guild.
        """
        self.members = [member for member in self.members if member["id"] != member_id]
        await self.save()
        
    async def add_points(self, points: int):
        self.points += points
        await self.save()
        
    @staticmethod
    def initialize():
        with sqlite3.connect(DATABASE_PATH) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS guilds (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    owner INTEGER,
                    members TEXT,  -- Store members as JSON
                    level INTEGER,
                    points INTEGER,
                    image TEXT,
                    description TEXT,
                    gates INTEGER DEFAULT 0,
                    allow_alliances INTEGER DEFAULT 0  -- New: Allow other guilds to join gates
                )
            """)
            # Add the new column if it doesn't exist (for existing databases)
            try:
                db.execute("ALTER TABLE guilds ADD COLUMN allow_alliances INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Column already exists
            db.commit()
    @staticmethod
    async def clear():      
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("DROP TABLE IF EXISTS guilds")
            await db.commit()