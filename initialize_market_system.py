#!/usr/bin/env python3
"""
Initialize the market system and ensure counters table is properly set up
"""
import asyncio
import sqlite3
import aiosqlite
import json
import logging

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("database", "players.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "players.db"

DATABASE_PATH = get_database_path()

async def initialize_market_system():
    """Initialize the market system with proper counters table"""
    print("🏪 Initializing Market System...")
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Create counters table if it doesn't exist
            await db.execute("""
                CREATE TABLE IF NOT EXISTS counters (
                    name TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                )
            """)
            print("  ✅ Created/verified counters table")
            
            # Create market table if it doesn't exist
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
            print("  ✅ Created/verified market table")
            
            # Initialize market counter if it doesn't exist
            await db.execute("""
                INSERT OR IGNORE INTO counters (name, value)
                VALUES ('market', 0)
            """)
            print("  ✅ Initialized market counter")
            
            # Check current counter value
            async with db.execute("SELECT value FROM counters WHERE name = 'market'") as cursor:
                result = await cursor.fetchone()
                if result:
                    counter_value = result[0]
                    print(f"  📊 Current market counter value: {counter_value}")
                else:
                    print("  ❌ Market counter not found")
            
            await db.commit()
            print("  ✅ Market system initialization complete")
            
    except Exception as e:
        print(f"  ❌ Error initializing market system: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def verify_database_tables():
    """Verify that all required database tables exist"""
    print("\n🔍 Verifying Database Tables...")
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Get list of all tables
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
                tables = await cursor.fetchall()
                table_names = [table[0] for table in tables]
            
            print(f"  📋 Found {len(table_names)} tables in database")
            
            # Check for required tables
            required_tables = [
                'players', 'market', 'counters', 'leaderboard', 
                'player_ranks', 'hunter_rankings', 'glory'
            ]
            
            missing_tables = []
            for table in required_tables:
                if table in table_names:
                    print(f"    ✅ {table}")
                else:
                    print(f"    ❌ {table} - MISSING")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"  ⚠️ Missing tables: {missing_tables}")
                return False
            else:
                print("  ✅ All required tables are present")
                return True
                
    except Exception as e:
        print(f"  ❌ Error verifying database tables: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_counters_table():
    """Test that the counters table is working properly"""
    print("\n🧪 Testing Counters Table...")
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Test reading from counters table
            async with db.execute("SELECT name, value FROM counters") as cursor:
                counters = await cursor.fetchall()
            
            print(f"  📊 Found {len(counters)} counters:")
            for name, value in counters:
                print(f"    • {name}: {value}")
            
            # Test that market counter exists
            async with db.execute("SELECT value FROM counters WHERE name = 'market'") as cursor:
                result = await cursor.fetchone()
                if result:
                    print(f"  ✅ Market counter working: {result[0]}")
                    return True
                else:
                    print("  ❌ Market counter not found")
                    return False
                    
    except Exception as e:
        print(f"  ❌ Error testing counters table: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    print("🔧 MARKET SYSTEM INITIALIZATION")
    print("=" * 50)
    
    # Initialize market system
    market_init = await initialize_market_system()
    
    # Verify database tables
    tables_ok = await verify_database_tables()
    
    # Test counters table
    counters_ok = await test_counters_table()
    
    print("\n" + "=" * 50)
    print("📊 INITIALIZATION SUMMARY")
    print(f"✅ Market System: {'PASS' if market_init else 'FAIL'}")
    print(f"✅ Database Tables: {'PASS' if tables_ok else 'FAIL'}")
    print(f"✅ Counters Table: {'PASS' if counters_ok else 'FAIL'}")
    
    if market_init and tables_ok and counters_ok:
        print("\n🎉 MARKET SYSTEM READY!")
        print("🚀 The counters table error should be resolved!")
        print("\n📋 WHAT WAS FIXED:")
        print("  • Created missing counters table")
        print("  • Initialized market counter to 0")
        print("  • Verified all database tables exist")
        print("  • Tested counters table functionality")
        print("\n🎮 COMMANDS SHOULD NOW WORK:")
        print("  • Market commands (sl market)")
        print("  • List commands that use counters")
        print("  • Any other features using the counters table")
    else:
        print("\n⚠️ SOME ISSUES REMAIN")
        print("🔧 Please check the errors above")
    
    return market_init and tables_ok and counters_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
