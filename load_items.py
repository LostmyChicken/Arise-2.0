import json
import asyncio
import aiosqlite

DATABASE_PATH = "items.db"
JSON_PATH = "items.json"

async def populate_items_from_json():
    """
    Populates the items table from a JSON file.
    """
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            items_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {JSON_PATH} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode {JSON_PATH}.")
        return

    async with aiosqlite.connect(DATABASE_PATH) as conn:
        # Create table if it doesn't exist
        await conn.execute(
            ''' 
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                rarity TEXT NOT NULL,
                classType TEXT NOT NULL,
                type TEXT NOT NULL,
                image TEXT NOT NULL,
                description TEXT,
                health INTEGER DEFAULT 0,
                attack INTEGER DEFAULT 0,
                defense INTEGER DEFAULT 0,
                speed INTEGER DEFAULT 0,
                mp INTEGER DEFAULT 0,
                precision INTEGER DEFAULT 0
            )
            '''
        )
        
        for item in items_data:
            try:
                await conn.execute(
                    ''' 
                    INSERT INTO items (id, name, rarity, classType, type, image, description, health, attack, defense, speed, mp, precision)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name=excluded.name,
                        rarity=excluded.rarity,
                        classType=excluded.classType,
                        type=excluded.type,
                        image=excluded.image,
                        description=excluded.description,
                        health=excluded.health,
                        attack=excluded.attack,
                        defense=excluded.defense,
                        speed=excluded.speed,
                        mp=excluded.mp,
                        precision=excluded.precision
                    ''',
                    (
                        item.get("id"),
                        item.get("name"),
                        item.get("rarity"),
                        item.get("classType"),
                        item.get("type"),
                        item.get("image"),
                        item.get("description", ""),
                        item.get("health", 0),
                        item.get("attack", 0),
                        item.get("defense", 0),
                        item.get("speed", 0),
                        item.get("mp", 0),
                        item.get("precision", 0),
                    ),
                )
            except Exception as e:
                print(f"Error inserting item {item.get('id')}: {e}")

        await conn.commit()
        print(f"Successfully loaded {len(items_data)} items into the database.")

if __name__ == "__main__":
    asyncio.run(populate_items_from_json())
