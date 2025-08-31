import aiosqlite
import logging

DATABASE_PATH = "data/player.db"

async def run_migration():
    """
    Performs data migrations to fix database issues.
    This function will:
    1. Check if the migration is needed by looking for a 'migration_v1_complete' flag.
    2. If needed, it will swap the values in the 'ticket' and 'key' columns.
    3. Add missing columns like 'oshi_list' and 'locked_items'.
    4. It will then create the 'migration_v1_complete' table to prevent running again.
    """
    try:
        async with aiosqlite.connect(DATABASE_PATH) as conn:
            # Check if the migration has already been completed
            cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='migration_v1_complete'")
            if await cursor.fetchone():
                logging.info("Data migration for ticket/key swap already completed. Checking for missing columns.")
                # Still need to check for missing columns
                await add_missing_columns(conn)
                await conn.commit()
                return

            logging.info("Starting one-time data migration to swap 'ticket' and 'key' values.")

            # Start a transaction
            await conn.execute("BEGIN TRANSACTION;")

            try:
                # 1. Add a temporary column to hold original key values
                await conn.execute("ALTER TABLE players ADD COLUMN temp_key_storage INTEGER")
                logging.info("Added temporary column 'temp_key_storage'.")

                # 2. Copy original 'key' values to the temporary column
                await conn.execute("UPDATE players SET temp_key_storage = key")
                logging.info("Backed up 'key' values to temporary column.")

                # 3. Copy 'ticket' values to the 'key' column (where the corruption happened)
                await conn.execute("UPDATE players SET key = ticket")
                logging.info("Moved 'ticket' values to 'key' column.")

                # 4. Copy the original 'key' values from temp storage to the 'ticket' column
                await conn.execute("UPDATE players SET ticket = temp_key_storage")
                logging.info("Restored original 'key' values into 'ticket' column.")

                # 5. Remove the temporary column
                await conn.execute("ALTER TABLE players DROP COLUMN temp_key_storage")
                logging.info("Removed temporary column.")

                # 6. Add missing columns if they don't exist
                await add_missing_columns(conn)

                # Commit the transaction
                await conn.commit()
                logging.info("Transaction committed successfully.")

            except Exception as e:
                # If any step fails, roll back the entire transaction
                await conn.rollback()
                logging.error(f"An error occurred during migration. Rolled back changes. Error: {e}", exc_info=True)
                return

            # 6. Create a flag table to indicate completion
            await conn.execute("CREATE TABLE migration_v1_complete (completed_at TEXT)")
            await conn.execute("INSERT INTO migration_v1_complete (completed_at) VALUES (CURRENT_TIMESTAMP)")
            await conn.commit()
            
            logging.info("Successfully completed the ticket/key data migration and flagged it as complete.")

    except Exception as e:
        logging.error(f"Failed to run data migration: {e}", exc_info=True)


async def add_missing_columns(conn):
    """Add missing columns to the players table"""
    try:
        # Check and add oshi_list column
        cursor = await conn.execute("PRAGMA table_info(players)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'oshi_list' not in column_names:
            await conn.execute("ALTER TABLE players ADD COLUMN oshi_list TEXT DEFAULT '[]'")
            logging.info("Added 'oshi_list' column to players table.")

        if 'locked_items' not in column_names:
            await conn.execute("ALTER TABLE players ADD COLUMN locked_items TEXT DEFAULT '{}'")
            logging.info("Added 'locked_items' column to players table.")

    except Exception as e:
        logging.error(f"Failed to add missing columns: {e}")
        raise
