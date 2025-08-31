import aiosqlite
import discord
from datetime import datetime
import logging
import json
from typing import Optional, List, Dict

DATABASE_PATH = "database.db"

class ServerTracker:
    """Track server invitations and maintain permanent records"""
    
    @staticmethod
    async def initialize_database():
        """Initialize the server tracking database"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                # Create server tracking table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS server_tracking (
                        guild_id INTEGER PRIMARY KEY,
                        guild_name TEXT NOT NULL,
                        owner_id INTEGER,
                        owner_name TEXT,
                        member_count INTEGER,
                        joined_at TEXT NOT NULL,
                        left_at TEXT,
                        is_active INTEGER DEFAULT 1,
                        invite_source TEXT,
                        features TEXT,
                        region TEXT,
                        verification_level INTEGER,
                        created_at TEXT,
                        last_updated TEXT NOT NULL
                    )
                """)
                
                # Create server events table for detailed tracking
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS server_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (guild_id) REFERENCES server_tracking (guild_id)
                    )
                """)
                
                await conn.commit()
                logging.info("Server tracking database initialized")
        except Exception as e:
            logging.error(f"Error initializing server tracking database: {e}")
    
    @staticmethod
    async def track_server_join(guild: discord.Guild, invite_source: str = None):
        """Track when bot joins a server"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                now = datetime.utcnow().isoformat()
                
                # Get guild features
                features = json.dumps(guild.features) if guild.features else "[]"
                
                # Insert or update server record
                await conn.execute("""
                    INSERT OR REPLACE INTO server_tracking (
                        guild_id, guild_name, owner_id, owner_name, member_count,
                        joined_at, is_active, invite_source, features, region,
                        verification_level, created_at, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?)
                """, (
                    guild.id,
                    guild.name,
                    guild.owner_id,
                    guild.owner.display_name if guild.owner else "Unknown",
                    guild.member_count,
                    now,
                    invite_source,
                    features,
                    str(guild.region) if hasattr(guild, 'region') else "Unknown",
                    guild.verification_level.value if guild.verification_level else 0,
                    guild.created_at.isoformat(),
                    now
                ))
                
                # Log the join event
                await conn.execute("""
                    INSERT INTO server_events (guild_id, event_type, event_data, timestamp)
                    VALUES (?, 'JOIN', ?, ?)
                """, (
                    guild.id,
                    json.dumps({
                        "guild_name": guild.name,
                        "member_count": guild.member_count,
                        "owner": guild.owner.display_name if guild.owner else "Unknown",
                        "invite_source": invite_source
                    }),
                    now
                ))
                
                await conn.commit()
                logging.info(f"Tracked server join: {guild.name} ({guild.id})")
                
        except Exception as e:
            logging.error(f"Error tracking server join for {guild.id}: {e}")
    
    @staticmethod
    async def track_server_leave(guild: discord.Guild):
        """Track when bot leaves a server (but keep the record)"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                now = datetime.utcnow().isoformat()
                
                # Update server record to mark as inactive
                await conn.execute("""
                    UPDATE server_tracking 
                    SET is_active = 0, left_at = ?, last_updated = ?
                    WHERE guild_id = ?
                """, (now, now, guild.id))
                
                # Log the leave event
                await conn.execute("""
                    INSERT INTO server_events (guild_id, event_type, event_data, timestamp)
                    VALUES (?, 'LEAVE', ?, ?)
                """, (
                    guild.id,
                    json.dumps({
                        "guild_name": guild.name,
                        "member_count": guild.member_count,
                        "reason": "Bot removed or kicked"
                    }),
                    now
                ))
                
                await conn.commit()
                logging.info(f"Tracked server leave: {guild.name} ({guild.id})")
                
        except Exception as e:
            logging.error(f"Error tracking server leave for {guild.id}: {e}")
    
    @staticmethod
    async def update_server_info(guild: discord.Guild):
        """Update server information periodically"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                now = datetime.utcnow().isoformat()
                features = json.dumps(guild.features) if guild.features else "[]"
                
                await conn.execute("""
                    UPDATE server_tracking 
                    SET guild_name = ?, owner_id = ?, owner_name = ?, 
                        member_count = ?, features = ?, last_updated = ?
                    WHERE guild_id = ? AND is_active = 1
                """, (
                    guild.name,
                    guild.owner_id,
                    guild.owner.display_name if guild.owner else "Unknown",
                    guild.member_count,
                    features,
                    now,
                    guild.id
                ))
                
                await conn.commit()
                
        except Exception as e:
            logging.error(f"Error updating server info for {guild.id}: {e}")
    
    @staticmethod
    async def get_server_stats() -> Dict:
        """Get comprehensive server statistics"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                # Get basic stats
                cursor = await conn.execute("""
                    SELECT 
                        COUNT(*) as total_servers,
                        COUNT(CASE WHEN is_active = 1 THEN 1 END) as active_servers,
                        COUNT(CASE WHEN is_active = 0 THEN 1 END) as left_servers,
                        SUM(CASE WHEN is_active = 1 THEN member_count ELSE 0 END) as total_members
                    FROM server_tracking
                """)
                stats = await cursor.fetchone()
                
                # Get recent joins (last 30 days)
                cursor = await conn.execute("""
                    SELECT COUNT(*) FROM server_tracking 
                    WHERE joined_at > datetime('now', '-30 days')
                """)
                recent_joins = await cursor.fetchone()
                
                # Get top servers by member count
                cursor = await conn.execute("""
                    SELECT guild_name, member_count, joined_at 
                    FROM server_tracking 
                    WHERE is_active = 1 
                    ORDER BY member_count DESC 
                    LIMIT 5
                """)
                top_servers = await cursor.fetchall()
                
                return {
                    "total_servers": stats[0] or 0,
                    "active_servers": stats[1] or 0,
                    "left_servers": stats[2] or 0,
                    "total_members": stats[3] or 0,
                    "recent_joins": recent_joins[0] or 0,
                    "top_servers": top_servers
                }
                
        except Exception as e:
            logging.error(f"Error getting server stats: {e}")
            return {
                "total_servers": 0,
                "active_servers": 0,
                "left_servers": 0,
                "total_members": 0,
                "recent_joins": 0,
                "top_servers": []
            }
    
    @staticmethod
    async def get_server_history(guild_id: int) -> List[Dict]:
        """Get complete history for a specific server"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                cursor = await conn.execute("""
                    SELECT event_type, event_data, timestamp 
                    FROM server_events 
                    WHERE guild_id = ? 
                    ORDER BY timestamp DESC
                """, (guild_id,))
                
                events = []
                async for row in cursor:
                    events.append({
                        "event_type": row[0],
                        "event_data": json.loads(row[1]) if row[1] else {},
                        "timestamp": row[2]
                    })
                
                return events
                
        except Exception as e:
            logging.error(f"Error getting server history for {guild_id}: {e}")
            return []
    
    @staticmethod
    async def get_all_servers() -> List[Dict]:
        """Get all tracked servers (active and inactive)"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as conn:
                cursor = await conn.execute("""
                    SELECT guild_id, guild_name, owner_name, member_count, 
                           joined_at, left_at, is_active, invite_source
                    FROM server_tracking 
                    ORDER BY joined_at DESC
                """)
                
                servers = []
                async for row in cursor:
                    servers.append({
                        "guild_id": row[0],
                        "guild_name": row[1],
                        "owner_name": row[2],
                        "member_count": row[3],
                        "joined_at": row[4],
                        "left_at": row[5],
                        "is_active": bool(row[6]),
                        "invite_source": row[7]
                    })
                
                return servers
                
        except Exception as e:
            logging.error(f"Error getting all servers: {e}")
            return []
