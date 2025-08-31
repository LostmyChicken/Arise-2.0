
import sqlite3
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_database_path():
    """Reads the database path from db.json."""
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            # Assuming the player database is the one that needs the market table
            return config.get("player", "data/player.db")
    except FileNotFoundError:
        logging.error("db.json not found. Using default database path 'data/player.db'.")
        return "data/player.db"
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "data.player.db"

def setup_database():
    """Connects to the database and creates the market table if it doesn't exist."""
    db_path = get_database_path()
    logging.info(f"Connecting to database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # SQL statement to create the market table
        create_market_table_sql = """
        CREATE TABLE IF NOT EXISTS market (
            id TEXT PRIMARY KEY,
            item_id TEXT NOT NULL,
            seller_id INTEGER NOT NULL,
            price INTEGER NOT NULL,
            currency TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            listed_at REAL NOT NULL
        );
        """
        
        cursor.execute(create_market_table_sql)
        logging.info("Successfully executed CREATE TABLE IF NOT EXISTS for 'market'.")

        # Verify that the table was created by listing all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='market';")
        if cursor.fetchone():
            logging.info("Verification successful: 'market' table exists.")
        else:
            logging.error("Verification failed: 'market' table was not created.")

        conn.commit()
        conn.close()
        logging.info("Database setup complete and connection closed.")

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    setup_database()
