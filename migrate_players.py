import sqlite3
import json
import logging

# --- Configuration ---
OLD_DB_PATH = 'old/player.db'
NEW_DB_PATH = 'new_player.db'
# ---------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_table_columns(cursor, table_name):
    """Gets the column names of a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def migrate_data():
    """Merges player data from the old database into the new one."""
    try:
        # Connect to the old database
        old_conn = sqlite3.connect(OLD_DB_PATH)
        old_cursor = old_conn.cursor()
        logging.info(f"Successfully connected to old database: {OLD_DB_PATH}")

        # Connect to the new database
        new_conn = sqlite3.connect(NEW_DB_PATH)
        new_cursor = new_conn.cursor()
        logging.info(f"Successfully connected to new database: {NEW_DB_PATH}")

        # Get columns from both tables
        try:
            old_columns = get_table_columns(old_cursor, 'players')
            new_columns = get_table_columns(new_cursor, 'players')
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                logging.error(f"Critical error: The 'players' table does not exist in one of the databases. Please ensure both database files are correct and contain the table.")
                return
            raise e

        # Find common columns
        common_columns = [col for col in old_columns if col in new_columns]
        
        if not common_columns:
            logging.error("No common columns found between the two databases. Cannot migrate.")
            logging.error(f"Old columns: {old_columns}")
            logging.error(f"New columns: {new_columns}")
            return

        logging.info(f"Found {len(common_columns)} common columns to migrate.")

        # Fetch all data from the old players table
        old_cursor.execute(f"SELECT {', '.join(common_columns)} FROM players")
        players_to_migrate = old_cursor.fetchall()
        logging.info(f"Found {len(players_to_migrate)} players to migrate from the old database.")

        # Prepare the INSERT OR REPLACE statement
        columns_str = ', '.join(common_columns)
        placeholders_str = ', '.join(['?'] * len(common_columns))
        query = f"INSERT OR REPLACE INTO players ({columns_str}) VALUES ({placeholders_str})"

        # Insert or replace data into the new table
        count = 0
        for player_data in players_to_migrate:
            new_cursor.execute(query, player_data)
            count += 1

        new_conn.commit()
        logging.info(f"Successfully migrated {count} player records.")

    except sqlite3.Error as e:
        logging.error(f"A database error occurred: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        if 'old_conn' in locals():
            old_conn.close()
        if 'new_conn' in locals():
            new_conn.close()
        logging.info("Database connections closed.")

if __name__ == '__main__':
    print("--- Player Data Migration Script ---")
    print(f"This script will merge data from '{OLD_DB_PATH}' into '{NEW_DB_PATH}'.")
    print("The new database will be modified. Please make a backup before proceeding.")
    
    # Create the table in the new DB if it doesn't exist
    try:
        conn = sqlite3.connect(NEW_DB_PATH)
        cursor = conn.cursor()
        # This schema is based on the new player structure.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                level INTEGER, xp INTEGER, attack INTEGER, defense INTEGER, hp INTEGER, mp INTEGER,
                gold INTEGER, precision INTEGER, diamond INTEGER, stone INTEGER, ticket INTEGER,
                crystals INTEGER, premiumT INTEGER, premium BOOLEAN, quests TEXT, inventory TEXT,
                equipped TEXT, hunters TEXT, skillPoints INTEGER, afk TEXT, afk_level INTEGER,
                gacha INTEGER, skills TEXT, army_lv INTEGER, shadows TEXT, fcube INTEGER, icube INTEGER,
                wcube INTEGER, dcube INTEGER, lcube INTEGER, tos INTEGER, gear1 INTEGER, gear2 INTEGER,
                gear3 INTEGER, boss TEXT, train TEXT, daily TEXT, guild TEXT, trivia TEXT, raid TEXT,
                prem1 TEXT, prem2 TEXT, prem3 TEXT, inc BOOLEAN, fight TEXT, dungeon TEXT, trade BOOLEAN,
                key INTEGER, vote TEXT, mission TEXT, aStreak INTEGER, aC INTEGER, dS INTEGER, lD TEXT,
                vS INTEGER, lV TEXT, loot TEXT, market TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error preparing the new database: {e}")
        exit()

    user_input = input("Are you sure you want to continue? (yes/no): ")
    if user_input.lower() == 'yes':
        logging.info("Starting migration...")
        migrate_data()
    else:
        print("Migration cancelled.")
