import aiosqlite
import logging

DATABASE_PATH = "data/player.db"

async def setup_database():
    """
    Sets up the database, creating the players table with the correct schema
    if it doesn't exist.
    """
    try:
        async with aiosqlite.connect(DATABASE_PATH) as conn:
            await conn.execute("PRAGMA journal_mode=WAL;")
            await conn.execute("PRAGMA busy_timeout = 5000;")
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY,
                    level INTEGER DEFAULT 1,
                    xp INTEGER DEFAULT 0,
                    attack INTEGER DEFAULT 10,
                    defense INTEGER DEFAULT 10,
                    hp INTEGER DEFAULT 100,
                    mp INTEGER DEFAULT 10,
                    gold INTEGER DEFAULT 0,
                    precision INTEGER DEFAULT 10,
                    diamond INTEGER DEFAULT 0,
                    stone INTEGER DEFAULT 0,
                    ticket INTEGER DEFAULT 0,
                    crystals INTEGER DEFAULT 0,
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
                    ecube INTEGER DEFAULT 0,
                    dcube INTEGER DEFAULT 0,
                    lcube INTEGER DEFAULT 0,
                    tos INTEGER DEFAULT 0,
                    gear1 INTEGER DEFAULT 0,
                    gear2 INTEGER DEFAULT 0,
                    gear3 INTEGER DEFAULT 0,
                    boss TEXT,
                    train TEXT,
                    daily TEXT,
                    guild TEXT,
                    trivia TEXT,
                    raid TEXT,
                    prem1 TEXT,
                    prem2 TEXT,
                    prem3 TEXT,
                    inc BOOLEAN DEFAULT FALSE,
                    fight TEXT,
                    dungeon TEXT,
                    trade BOOLEAN DEFAULT FALSE,
                    key INTEGER DEFAULT 0,
                    vote TEXT,
                    mission TEXT DEFAULT '{"cmd": "", "times": 0}',
                    aStreak INTEGER DEFAULT 0,
                    aC INTEGER DEFAULT 0,
                    dS INTEGER DEFAULT 0,
                    lD TEXT,
                    vS INTEGER DEFAULT 0,
                    lV TEXT,
                    loot TEXT DEFAULT '{"won": 0, "lose": 0}',
                    market TEXT DEFAULT '{}',
                    defeated_bosses TEXT DEFAULT '{}',
                    oshi_list TEXT DEFAULT '[]',
                    story_progress TEXT DEFAULT '{}',
            unlocked_features TEXT DEFAULT '{}'
                )
            """)

            # Add oshi_list column if it doesn't exist (for existing databases)
            try:
                await conn.execute("ALTER TABLE players ADD COLUMN oshi_list TEXT DEFAULT '[]'")
                logging.info("Added oshi_list column to existing players table.")
            except Exception:
                # Column already exists, which is fine
                pass

            # Add ecube column if it doesn't exist (for Earth element cubes)
            try:
                await conn.execute("ALTER TABLE players ADD COLUMN ecube INTEGER DEFAULT 0")
                logging.info("Added ecube column to existing players table.")
            except Exception:
                # Column already exists, which is fine
                pass

            # Add story_progress column if it doesn't exist (for Story Campaign System)
            try:
                await conn.execute("ALTER TABLE players ADD COLUMN story_progress TEXT DEFAULT '{}'")
                logging.info("Added story_progress column to existing players table.")
            except Exception:
                # Column already exists, which is fine
                pass

            # Add titles column if it doesn't exist (for Title System)
            try:
                await conn.execute("ALTER TABLE players ADD COLUMN titles TEXT DEFAULT '{}'")
                logging.info("Added titles column to existing players table.")
            except Exception:
                # Column already exists, which is fine
                pass

            # Add active_title column if it doesn't exist (for Title System)
            try:
                await conn.execute("ALTER TABLE players ADD COLUMN active_title TEXT DEFAULT NULL")
                logging.info("Added active_title column to existing players table.")
            except Exception:
                # Column already exists, which is fine
                pass

            # Create enhanced_guilds table if it doesn't exist (for Enhanced Guild System)
            await conn.execute("""
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
            logging.info("Created/verified enhanced_guilds table.")

            # Create regular guilds table if it doesn't exist (for backward compatibility)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS guilds (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    owner INTEGER,
                    members TEXT,
                    level INTEGER,
                    points INTEGER,
                    image TEXT,
                    description TEXT,
                    gates INTEGER DEFAULT 0,
                    allow_alliances INTEGER DEFAULT 0
                )
            """)
            logging.info("Created/verified guilds table.")

            # Create notifications table for Custom Notifications System
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    notification_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    scheduled_time REAL NOT NULL,
                    created_time REAL NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_recurring INTEGER DEFAULT 0,
                    recurring_interval INTEGER DEFAULT 0,
                    notification_data TEXT DEFAULT '{}',
                    delivery_method TEXT DEFAULT 'dm',
                    FOREIGN KEY (user_id) REFERENCES players (id)
                )
            """)
            logging.info("Created/verified notifications table.")

            # Create notification_settings table for user preferences
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS notification_settings (
                    user_id INTEGER PRIMARY KEY,
                    cooldown_alerts INTEGER DEFAULT 1,
                    world_boss_alerts INTEGER DEFAULT 1,
                    daily_reminders INTEGER DEFAULT 0,
                    custom_alerts INTEGER DEFAULT 1,
                    dm_notifications INTEGER DEFAULT 1,
                    channel_notifications INTEGER DEFAULT 0,
                    preferred_channel INTEGER DEFAULT NULL,
                    notification_sound INTEGER DEFAULT 1,
                    quiet_hours_start INTEGER DEFAULT NULL,
                    quiet_hours_end INTEGER DEFAULT NULL,
                    timezone_offset INTEGER DEFAULT 0,
                    world_boss_servers TEXT DEFAULT '[]',
                    world_boss_rarities TEXT DEFAULT '["common","rare","epic","legendary"]',
                    world_boss_hours_start INTEGER DEFAULT NULL,
                    world_boss_hours_end INTEGER DEFAULT NULL,
                    settings_data TEXT DEFAULT '{}',
                    FOREIGN KEY (user_id) REFERENCES players (id)
                )
            """)
            logging.info("Created/verified notification_settings table.")

            logging.info("Database setup complete. All tables are ready.")
            await conn.commit()
    except Exception as e:
        logging.error(f"Failed to set up database: {e}", exc_info=True)

