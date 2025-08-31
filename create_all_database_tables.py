#!/usr/bin/env python3
"""
Create all necessary database tables for the bot
"""
import asyncio
import aiosqlite
import json
import logging

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("player", "new_player.db")  # Use 'player' key from db.json
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "new_player.db"

DATABASE_PATH = get_database_path()

async def create_all_tables():
    """Create all necessary database tables"""
    print("🗄️ Creating All Database Tables...")
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Create players table (most important)
            await db.execute("""
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
                    lcube INTEGER DEFAULT 0,
                    dcube INTEGER DEFAULT 0,
                    ccube INTEGER DEFAULT 0,
                    rank TEXT DEFAULT 'E',
                    rank_progress INTEGER DEFAULT 0,
                    last_daily TEXT,
                    daily_streak INTEGER DEFAULT 0,
                    story_progress TEXT DEFAULT '{}',
                    achievements TEXT DEFAULT '{}',
                    settings TEXT DEFAULT '{}'
                )
            """)
            print("  ✅ Created players table")
            
            # Create counters table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS counters (
                    name TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                )
            """)
            print("  ✅ Created counters table")
            
            # Create market table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS market (
                    id INTEGER PRIMARY KEY,
                    sid INTEGER NOT NULL,
                    i_id TEXT NOT NULL,
                    i_t TEXT NOT NULL,
                    q INTEGER NOT NULL,
                    p INTEGER NOT NULL,
                    i_n TEXT NOT NULL,
                    FOREIGN KEY (sid) REFERENCES players(id)
                )
            """)
            print("  ✅ Created market table")
            
            # Create leaderboard table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS leaderboard (
                    id INTEGER PRIMARY KEY,
                    rank TEXT NOT NULL,
                    rank_ INTEGER NOT NULL,
                    power INTEGER NOT NULL
                )
            """)
            print("  ✅ Created leaderboard table")
            
            # Create player_ranks table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS player_ranks (
                    player_id TEXT PRIMARY KEY,
                    current_rank TEXT NOT NULL DEFAULT 'E',
                    progress INTEGER DEFAULT 0,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("  ✅ Created player_ranks table")
            
            # Create hunter_rankings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS hunter_rankings (
                    player_id TEXT PRIMARY KEY,
                    current_rank TEXT NOT NULL DEFAULT 'E',
                    rank_points INTEGER DEFAULT 0,
                    last_evaluation TEXT,
                    rank_history TEXT DEFAULT '[]',
                    total_evaluations INTEGER DEFAULT 0
                )
            """)
            print("  ✅ Created hunter_rankings table")
            
            # Create glory table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS glory (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    points INTEGER DEFAULT 0,
                    rank INTEGER DEFAULT 0,
                    hs INTEGER DEFAULT 0,
                    current_streak INTEGER DEFAULT 0,
                    logs TEXT,
                    FOREIGN KEY(user_id) REFERENCES players(id)
                )
            """)
            print("  ✅ Created glory table")
            
            # Create server_tracking table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS server_tracking (
                    guild_id TEXT PRIMARY KEY,
                    guild_name TEXT NOT NULL,
                    owner_name TEXT,
                    member_count INTEGER DEFAULT 0,
                    joined_at TEXT NOT NULL,
                    left_at TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    invite_source TEXT
                )
            """)
            print("  ✅ Created server_tracking table")
            
            # Create srank_hunters table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS srank_hunters (
                    id INTEGER PRIMARY KEY
                )
            """)
            print("  ✅ Created srank_hunters table")
            
            # Initialize counters
            await db.execute("""
                INSERT OR IGNORE INTO counters (name, value)
                VALUES ('market', 0)
            """)
            print("  ✅ Initialized market counter")
            
            await db.commit()
            print("  ✅ All tables created successfully!")
            
    except Exception as e:
        print(f"  ❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def verify_all_tables():
    """Verify that all tables were created successfully"""
    print("\n🔍 Verifying All Tables...")
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Get list of all tables
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
                tables = await cursor.fetchall()
                table_names = [table[0] for table in tables]
            
            print(f"  📋 Found {len(table_names)} tables in database:")
            for table in sorted(table_names):
                print(f"    ✅ {table}")
            
            # Check for required tables
            required_tables = [
                'players', 'counters', 'market', 'leaderboard', 
                'player_ranks', 'hunter_rankings', 'glory', 
                'server_tracking', 'srank_hunters'
            ]
            
            missing_tables = []
            for table in required_tables:
                if table not in table_names:
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"  ❌ Missing tables: {missing_tables}")
                return False
            else:
                print("  ✅ All required tables are present")
                return True
                
    except Exception as e:
        print(f"  ❌ Error verifying tables: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_functionality():
    """Test basic database functionality"""
    print("\n🧪 Testing Database Functionality...")
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Test counters table
            async with db.execute("SELECT name, value FROM counters WHERE name = 'market'") as cursor:
                result = await cursor.fetchone()
                if result:
                    print(f"  ✅ Market counter: {result[1]}")
                else:
                    print("  ❌ Market counter not found")
                    return False
            
            # Test players table structure
            async with db.execute("PRAGMA table_info(players)") as cursor:
                columns = await cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                required_columns = ['id', 'level', 'xp', 'gold', 'inventory', 'hunters']
                missing_columns = [col for col in required_columns if col not in column_names]
                
                if missing_columns:
                    print(f"  ❌ Players table missing columns: {missing_columns}")
                    return False
                else:
                    print(f"  ✅ Players table has {len(column_names)} columns")
            
            print("  ✅ Database functionality test passed")
            return True
            
    except Exception as e:
        print(f"  ❌ Error testing database: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    print("🔧 COMPLETE DATABASE INITIALIZATION")
    print("=" * 60)
    
    # Create all tables
    tables_created = await create_all_tables()
    
    # Verify all tables
    tables_verified = await verify_all_tables()
    
    # Test functionality
    functionality_ok = await test_database_functionality()
    
    print("\n" + "=" * 60)
    print("📊 DATABASE INITIALIZATION SUMMARY")
    print(f"✅ Tables Created: {'PASS' if tables_created else 'FAIL'}")
    print(f"✅ Tables Verified: {'PASS' if tables_verified else 'FAIL'}")
    print(f"✅ Functionality Test: {'PASS' if functionality_ok else 'FAIL'}")
    
    if tables_created and tables_verified and functionality_ok:
        print("\n🎉 DATABASE INITIALIZATION COMPLETE!")
        print("🚀 All database tables are ready!")
        print("\n📋 TABLES CREATED:")
        print("  • players - Main player data")
        print("  • counters - System counters (market, etc.)")
        print("  • market - Player marketplace")
        print("  • leaderboard - Player rankings")
        print("  • player_ranks - Rank progression")
        print("  • hunter_rankings - Hunter evaluations")
        print("  • glory - Glory point system")
        print("  • server_tracking - Server statistics")
        print("  • srank_hunters - S-rank hunter list")
        print("\n🎮 THE 'COUNTERS' ERROR SHOULD BE FIXED!")
        print("  • Market commands should work")
        print("  • List commands should work")
        print("  • All database-dependent features should work")
    else:
        print("\n⚠️ DATABASE INITIALIZATION FAILED")
        print("🔧 Please check the errors above")
    
    return tables_created and tables_verified and functionality_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
