import json
import logging
import aiosqlite
from structure.player import Player

def get_database_path():
    try:
        with open("db.json", "r") as f:
            config = json.load(f)
            return config.get("player", "data/player.db")
    except Exception as e:
        logging.error(f"Error loading database configuration: {e}")
        return "data/player.db"

DATABASE_PATH = get_database_path()

class RankingLeaderboard:
    @staticmethod
    async def initialize_db():
        """Initialize the leaderboard database."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Create the leaderboard table
            await db.execute(''' 
                CREATE TABLE IF NOT EXISTS leaderboard (
                    id INTEGER PRIMARY KEY,
                    rank TEXT NOT NULL,
                    rank_ INTEGER NOT NULL,
                    power INTEGER NOT NULL
                )
            ''')
            # Create the S-Rank hunters table
            await db.execute(''' 
                CREATE TABLE IF NOT EXISTS srank_hunters (
                    id INTEGER PRIMARY KEY
                )
            ''')
            await db.commit()

    async def assign_rank(self, player_power):
        """Assign a rank to a player based on their power level."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Fetch all players' power levels from the database
            cursor = await db.execute('SELECT id, power FROM leaderboard')
            players = await cursor.fetchall()

        if not players:
            return 'S-Rank', 1  # If no players, assign S-Rank by default with rank 1

        # Sort players by power in descending order
        sorted_players = sorted(players, key=lambda x: x[1], reverse=True)

        # Find the player's position based on their power level
        player_position = 0
        for i, player in enumerate(sorted_players):
            if player_power >= player[1]:
                player_position = i
                break

        # Calculate the percentile
        total_players = len(sorted_players)
        percentile = ((player_position + 1) / total_players) * 100  # Positions are 1-based

        # Determine rank based on percentile
        if percentile <= 10:
            return 'S-Rank', player_position + 1
        elif percentile <= 25:
            return 'A-Rank', player_position + 1
        elif percentile <= 50:
            return 'B-Rank', player_position + 1
        elif percentile <= 75:
            return 'C-Rank', player_position + 1
        elif percentile <= 90:
            return 'D-Rank', player_position + 1
        else:
            return 'E-Rank', player_position + 1 

    async def add_player(self, player_id, power):
        """Add a new player to the leaderboard with a calculated rank."""
        rank, rank_ = await self.assign_rank(power)

        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Insert the player into the leaderboard
            await db.execute('''
                INSERT INTO leaderboard (id, rank, rank_, power)
                VALUES (?, ?, ?, ?)
            ''', (player_id, rank, rank_, power))
            await db.commit()

    async def get_all_players(self):
        """Retrieve all players in the leaderboard."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT * FROM leaderboard ORDER BY rank_')
            players = await cursor.fetchall()
            return players

    @staticmethod
    async def get(player_id):
        """Get a player by their ID."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT * FROM leaderboard WHERE id = ?', (player_id,))
            player = await cursor.fetchone()
            return player

    async def delete_player(self, player_id):
        """Delete a player from the leaderboard."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('DELETE FROM leaderboard WHERE id = ?', (player_id,))
            await db.commit()

    async def evaluate(self, player_id, new_power):
        """Evaluate a player's new power and update their rank."""
        rank, rank_ = await self.assign_rank(new_power)

        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Update the player's rank and power
            await db.execute('''
                UPDATE leaderboard
                SET rank = ?, rank_ = ?, power = ?
                WHERE id = ?
            ''', (rank, rank_, new_power, player_id))
            await db.commit()

        return rank, rank_


    async def update_srank(self):
        """Update the S-Rank players in the separate table."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Fetch all S-Rank players
            cursor = await db.execute('SELECT id FROM leaderboard WHERE rank = "S-Rank"')
            srank_players = await cursor.fetchall()

            if not srank_players:
                return "No S-Rank players to update."

            # Create or update the S-Rank players table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS srank_players (
                    id INTEGER PRIMARY KEY
                )
            ''')

            # Insert or update the S-Rank players into the table
            for player in srank_players:
                player_id = player[0]
                await db.execute('''
                    INSERT OR REPLACE INTO srank_players (id)
                    VALUES (?)
                ''', (player_id,))

            await db.commit()

        return "S-Rank players have been updated!"

    
    async def get_srank_players(self):
        """Fetch all S-Rank players from the srank_players table."""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT id FROM srank_players')
            srank_players = await cursor.fetchall()
            return srank_players
       