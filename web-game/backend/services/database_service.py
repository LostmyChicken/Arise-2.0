import aiosqlite
import json
import os
import shutil
from pathlib import Path

# Database paths
DATABASE_DIR = Path("../data")
ORIGINAL_DB_DIR = Path("../../")  # Original Discord bot databases

class DatabaseService:
    def __init__(self):
        self.db_paths = {
            'players': DATABASE_DIR / 'players.db',
            'items': DATABASE_DIR / 'items.db', 
            'heroes': DATABASE_DIR / 'heroes.db',
            'guilds': DATABASE_DIR / 'guilds.db',
            'battles': DATABASE_DIR / 'battles.db',
            'world_bosses': DATABASE_DIR / 'world_bosses.db'
        }
    
    async def get_connection(self, db_name: str):
        """Get database connection"""
        if db_name not in self.db_paths:
            raise ValueError(f"Unknown database: {db_name}")
        
        db_path = self.db_paths[db_name]
        return aiosqlite.connect(db_path)
    
    async def execute_query(self, db_name: str, query: str, params=None):
        """Execute a query and return results"""
        async with await self.get_connection(db_name) as db:
            if params:
                cursor = await db.execute(query, params)
            else:
                cursor = await db.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                return await cursor.fetchall()
            else:
                await db.commit()
                return cursor.rowcount

    async def execute_many(self, db_name: str, query: str, params_list):
        """Execute many queries with different parameters"""
        async with await self.get_connection(db_name) as db:
            await db.executemany(query, params_list)
            await db.commit()

# Global database service instance
db_service = DatabaseService()

async def init_database():
    """Initialize all databases with required tables"""
    
    # Create data directory
    DATABASE_DIR.mkdir(exist_ok=True)
    
    # Copy existing databases from Discord bot if they exist
    original_dbs = {
        'players': 'player.db',
        'items': 'items.db', 
        'heroes': 'heroes.db',
        'guilds': 'guilds.db'
    }
    
    for db_name, original_file in original_dbs.items():
        original_path = ORIGINAL_DB_DIR / original_file
        target_path = DATABASE_DIR / f"{db_name}.db"
        
        if original_path.exists() and not target_path.exists():
            shutil.copy2(original_path, target_path)
            print(f"📋 Copied {original_file} to web game database")
    
    # Initialize players database
    await init_players_db()
    
    # Initialize battles database
    await init_battles_db()
    
    # Initialize world bosses database
    await init_world_bosses_db()
    
    # Initialize web-specific tables
    await init_web_tables()

async def init_players_db():
    """Initialize players database with web-specific additions"""

    # Check if we need to add web-specific columns
    async with await db_service.get_connection('players') as db:
        # Create main players table first
        await db.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                attack INTEGER DEFAULT 10,
                defense INTEGER DEFAULT 10,
                hp INTEGER DEFAULT 100,
                mp INTEGER DEFAULT 10,
                gold INTEGER DEFAULT 10000,
                precision INTEGER DEFAULT 10,
                diamond INTEGER DEFAULT 10000,
                stone INTEGER DEFAULT 500,
                ticket INTEGER DEFAULT 50,
                crystals INTEGER DEFAULT 100,
                premiumT INTEGER DEFAULT 0,
                premium BOOLEAN DEFAULT FALSE,
                quests TEXT DEFAULT '{}',
                inventory TEXT DEFAULT '{}',
                equipped TEXT DEFAULT '{}',
                hunters TEXT DEFAULT '{}',
                skillPoints INTEGER DEFAULT 0,
                afk TEXT,
                afk_level INTEGER DEFAULT 1,
                gacha INTEGER DEFAULT 0,
                skills TEXT DEFAULT '{}',
                army_lv INTEGER DEFAULT 1,
                shadows TEXT DEFAULT '{}',
                fcube INTEGER DEFAULT 0,
                icube INTEGER DEFAULT 0,
                wcube INTEGER DEFAULT 0,
                dcube INTEGER DEFAULT 0,
                lcube INTEGER DEFAULT 0,
                tos INTEGER DEFAULT 0,
                gear1 INTEGER DEFAULT 0,
                gear2 INTEGER DEFAULT 0,
                gear3 INTEGER DEFAULT 0,
                gear4 INTEGER DEFAULT 0,
                gear5 INTEGER DEFAULT 0,
                gear6 INTEGER DEFAULT 0,
                gear7 INTEGER DEFAULT 0,
                gear8 INTEGER DEFAULT 0,
                gear9 INTEGER DEFAULT 0,
                gear10 INTEGER DEFAULT 0,
                gear11 INTEGER DEFAULT 0,
                gear12 INTEGER DEFAULT 0,
                gear13 INTEGER DEFAULT 0,
                gear14 INTEGER DEFAULT 0,
                gear15 INTEGER DEFAULT 0,
                gear16 INTEGER DEFAULT 0,
                gear17 INTEGER DEFAULT 0,
                gear18 INTEGER DEFAULT 0,
                gear19 INTEGER DEFAULT 0,
                gear20 INTEGER DEFAULT 0,
                story_progress TEXT DEFAULT '{}',
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create users table for web authentication
        await db.execute('''
            CREATE TABLE IF NOT EXISTS web_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                player_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')

        # Create sessions table for authentication
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES web_users (id)
            )
        ''')

        await db.commit()

async def init_battles_db():
    """Initialize battles database for real-time battles"""
    
    async with await db_service.get_connection('battles') as db:
        # Active battles table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS active_battles (
                id TEXT PRIMARY KEY,
                battle_type TEXT NOT NULL,
                players TEXT NOT NULL,  -- JSON array of player IDs
                battle_data TEXT NOT NULL,  -- JSON battle state
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Battle history table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS battle_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                battle_id TEXT NOT NULL,
                winner_id TEXT,
                loser_id TEXT,
                battle_type TEXT NOT NULL,
                duration INTEGER,  -- Battle duration in seconds
                rewards TEXT,  -- JSON rewards data
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()

async def init_world_bosses_db():
    """Initialize world bosses database"""
    
    async with await db_service.get_connection('world_bosses') as db:
        # Active world bosses
        await db.execute('''
            CREATE TABLE IF NOT EXISTS active_world_bosses (
                id TEXT PRIMARY KEY,
                boss_name TEXT NOT NULL,
                boss_level INTEGER NOT NULL,
                max_hp INTEGER NOT NULL,
                current_hp INTEGER NOT NULL,
                participants TEXT NOT NULL,  -- JSON array of participant data
                rewards TEXT NOT NULL,  -- JSON rewards data
                spawn_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # World boss participation
        await db.execute('''
            CREATE TABLE IF NOT EXISTS world_boss_participation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boss_id TEXT NOT NULL,
                player_id TEXT NOT NULL,
                damage_dealt INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (boss_id) REFERENCES active_world_bosses (id)
            )
        ''')
        
        await db.commit()

async def init_web_tables():
    """Initialize web-specific tables"""
    
    async with await db_service.get_connection('players') as db:
        # Player online status
        await db.execute('''
            CREATE TABLE IF NOT EXISTS player_status (
                player_id TEXT PRIMARY KEY,
                is_online BOOLEAN DEFAULT FALSE,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_activity TEXT,  -- What the player is currently doing
                socket_id TEXT  -- For real-time updates
            )
        ''')
        
        # Friend system
        await db.execute('''
            CREATE TABLE IF NOT EXISTS friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_id TEXT NOT NULL,
                addressee_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',  -- pending, accepted, blocked
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Chat messages (for guild chat, etc.)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_type TEXT NOT NULL,  -- guild, private, global
                channel_id TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                message TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await db.commit()

# Utility functions for common database operations
async def get_player_by_id(player_id: str):
    """Get player data by ID"""
    query = "SELECT * FROM players WHERE id = ?"
    result = await db_service.execute_query('players', query, (player_id,))
    return result[0] if result else None

async def get_user_by_username(username: str):
    """Get web user by username"""
    query = "SELECT * FROM web_users WHERE username = ?"
    result = await db_service.execute_query('players', query, (username,))
    return result[0] if result else None

async def create_web_user(username: str, email: str, password_hash: str, player_id: str):
    """Create a new web user"""
    query = '''
        INSERT INTO web_users (username, email, password_hash, player_id)
        VALUES (?, ?, ?, ?)
    '''
    return await db_service.execute_query('players', query, (username, email, password_hash, player_id))

async def update_player_status(player_id: str, is_online: bool, activity: str = None, socket_id: str = None):
    """Update player online status"""
    query = '''
        INSERT OR REPLACE INTO player_status (player_id, is_online, last_seen, current_activity, socket_id)
        VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
    '''
    return await db_service.execute_query('players', query, (player_id, is_online, activity, socket_id))

async def get_db_connection():
    """Get database connection for players database"""
    return await db_service.get_connection('players')