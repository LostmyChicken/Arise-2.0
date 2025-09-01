import asyncio
import json
import os
import re
import aiohttp
from PIL import Image, ImageOps
from io import BytesIO
import discord
from discord.ext import commands
from structure.heroes import HeroManager
from utilis.utilis import extractId
from datetime import datetime
import logging
from typing import Dict, Optional

# Configuration
CONFIG = {
    "OUTPUT_JSON": "emojis.json",
    "IMAGES_JSON": "images.json",
    "IMAGES_FOLDER": "images",
    "LOG_FILE": "emoji_uploader.log",
    "GUILD_ID": 1366127975627755540,
    "MAX_EMOJI_SLOTS": 50,  # Discord server emoji limit
    "IMAGE_SIZE": (128, 128),  # Size for emoji images
    "MAX_RETRIES": 3,  # Max retries for uploads
    "RETRY_DELAY": 5,  # Seconds between retries
}

# Image Host Configuration
IMAGE_HOSTS = {
    "catbox": {
        "enabled": True,
        "url": "https://catbox.moe/user/api.php",
        "requires_key": False
    },
    "imgur": {
        "enabled": False,
        "url": "https://api.imgur.com/3/image",
        "requires_key": True,
        "client_id": "YOUR_IMGUR_CLIENT_ID"  # Only needed if using Imgur
    }
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["LOG_FILE"]),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

os.makedirs(CONFIG["IMAGES_FOLDER"], exist_ok=True)

class EmojiUploader(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.session = None
        self.emoji_data = {}
        self.image_data = {}
        self.load_existing_data()
        self.upload_stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }

    def load_existing_data(self):
        """Load existing emoji and image data from JSON files"""
        try:
            if os.path.exists(CONFIG["OUTPUT_JSON"]):
                with open(CONFIG["OUTPUT_JSON"], 'r') as f:
                    self.emoji_data = json.load(f)
            
            if os.path.exists(CONFIG["IMAGES_JSON"]):
                with open(CONFIG["IMAGES_JSON"], 'r') as f:
                    self.image_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading existing data: {e}")

    async def save_data(self):
        """Save current emoji and image data to JSON files"""
        try:
            with open(CONFIG["OUTPUT_JSON"], 'w') as f:
                json.dump(self.emoji_data, f, indent=2)
            
            with open(CONFIG["IMAGES_JSON"], 'w') as f:
                json.dump(self.image_data, f, indent=2)
            
            logger.info("Data saved successfully")
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    async def upload_image(self, image_path: str, retry_count: int = 0) -> Optional[str]:
        """
        Upload image to the configured image host
        Returns URL if successful, None otherwise
        """
        if IMAGE_HOSTS["catbox"]["enabled"]:
            return await self.upload_to_catbox(image_path, retry_count)
        elif IMAGE_HOSTS["imgur"]["enabled"]:
            return await self.upload_to_imgur(image_path, retry_count)
        else:
            logger.warning("No image host enabled in configuration")
            return None

    async def upload_to_catbox(self, image_path: str, retry_count: int) -> Optional[str]:
        """Upload image to Catbox.moe"""
        url = IMAGE_HOSTS["catbox"]["url"]
        
        try:
            with open(image_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('reqtype', 'fileupload')
                data.add_field('userhash', '')
                data.add_field('fileToUpload', f, filename=os.path.basename(image_path))
                
                async with self.session.post(
                    url,
                    data=data,
                    headers={'User-Agent': 'Mozilla/5.0'},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        return (await response.text()).strip()
                    else:
                        error_msg = f"Catbox upload failed: {response.status} - {await response.text()}"
                        if retry_count < CONFIG["MAX_RETRIES"]:
                            logger.warning(f"{error_msg}. Retrying...")
                            await asyncio.sleep(CONFIG["RETRY_DELAY"])
                            return await self.upload_to_catbox(image_path, retry_count + 1)
                        else:
                            logger.error(error_msg)
                            return None
        except Exception as e:
            error_msg = f"Error uploading to Catbox: {str(e)}"
            if retry_count < CONFIG["MAX_RETRIES"]:
                logger.warning(f"{error_msg}. Retrying...")
                await asyncio.sleep(CONFIG["RETRY_DELAY"])
                return await self.upload_to_catbox(image_path, retry_count + 1)
            else:
                logger.error(error_msg)
                return None

    async def upload_to_imgur(self, image_path: str, retry_count: int) -> Optional[str]:
        """Upload image to Imgur"""
        if not IMAGE_HOSTS["imgur"]["client_id"]:
            logger.error("Imgur client ID not configured")
            return None
            
        url = IMAGE_HOSTS["imgur"]["url"]
        headers = {"Authorization": f"Client-ID {IMAGE_HOSTS['imgur']['client_id']}"}
        
        try:
            with open(image_path, 'rb') as f:
                async with self.session.post(
                    url,
                    headers=headers,
                    data={'image': f},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data['data']['link']
                    else:
                        error_msg = f"Imgur upload failed: {response.status} - {await response.text()}"
                        if retry_count < CONFIG["MAX_RETRIES"]:
                            logger.warning(f"{error_msg}. Retrying...")
                            await asyncio.sleep(CONFIG["RETRY_DELAY"])
                            return await self.upload_to_imgur(image_path, retry_count + 1)
                        else:
                            logger.error(error_msg)
                            return None
        except Exception as e:
            error_msg = f"Error uploading to Imgur: {str(e)}"
            if retry_count < CONFIG["MAX_RETRIES"]:
                logger.warning(f"{error_msg}. Retrying...")
                await asyncio.sleep(CONFIG["RETRY_DELAY"])
                return await self.upload_to_imgur(image_path, retry_count + 1)
            else:
                logger.error(error_msg)
                return None

    async def process_hero_image(self, hero, session: aiohttp.ClientSession) -> bool:
        """Process a single hero's image and create emoji"""
        try:
            hero_id = extractId(hero.name)  # Access name as attribute
            if not hero_id:
                logger.error(f"Invalid hero ID for {hero.name}")
                return False

            image_filename = f"{hero_id}.png"
            image_path = os.path.join(CONFIG["IMAGES_FOLDER"], image_filename)
            self.upload_stats["total"] += 1

            # Skip if already processed
            if hero_id in self.emoji_data and hero_id in self.image_data:
                logger.info(f"Skipping {hero.name} (already processed)")
                self.upload_stats["skipped"] += 1
                return True

            # Download and process image
            if not os.path.exists(image_path):
                logger.info(f"Downloading image for {hero.name}...")
                async with session.get(hero.image, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download image for {hero.name}")
                        self.upload_stats["failed"] += 1
                        return False
                    
                    image_data = await response.read()
                    image = Image.open(BytesIO(image_data)).convert("RGBA")
                    
                    # Create square image with transparent background
                    size = max(image.size)
                    square_image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                    offset = ((size - image.width) // 2, (size - image.height) // 2)
                    square_image.paste(image, offset)
                    
                    # Resize and save
                    square_image = square_image.resize(CONFIG["IMAGE_SIZE"], Image.Resampling.LANCZOS)
                    square_image.save(image_path, format="PNG", optimize=True)
                    logger.info(f"Processed image for {hero.name}")

            # Upload image if needed
            if hero_id not in self.image_data:
                logger.info(f"Uploading image for {hero.name}...")
                image_url = await self.upload_image(image_path)
                if image_url:
                    self.image_data[hero_id] = image_url
                    logger.info(f"Uploaded image: {image_url}")
                else:
                    logger.error(f"Failed to upload image for {hero.name}")
                    self.upload_stats["failed"] += 1
                    return False

            # Create emoji if needed
            if hero_id not in self.emoji_data:
                guild = self.get_guild(CONFIG["GUILD_ID"])
                if not guild:
                    logger.error("Guild not found")
                    self.upload_stats["failed"] += 1
                    return False

                # Check emoji slots
                if len(guild.emojis) >= CONFIG["MAX_EMOJI_SLOTS"]:
                    logger.error(f"Cannot create emoji for {hero.name} - server emoji slots full")
                    self.upload_stats["failed"] += 1
                    return False

                with open(image_path, 'rb') as f:
                    emoji_name = re.sub(r"[^a-zA-Z0-9_]", "", hero_id)
                    if not emoji_name:
                        logger.error(f"Invalid emoji name for {hero.name}")
                        self.upload_stats["failed"] += 1
                        return False

                    try:
                        emoji = await guild.create_custom_emoji(
                            name=emoji_name,
                            image=f.read(),
                            reason=f"Auto-upload for hero {hero.name}"
                        )
                        self.emoji_data[hero_id] = f"<:{emoji.name}:{emoji.id}>"
                        logger.info(f"Created emoji for {hero.name}")
                        self.upload_stats["success"] += 1
                    except discord.HTTPException as e:
                        logger.error(f"Failed to create emoji for {hero.name}: {e}")
                        self.upload_stats["failed"] += 1
                        return False

            return True

        except Exception as e:
            logger.error(f"Error processing {hero['name']}: {e}")
            self.upload_stats["failed"] += 1
            return False

    async def on_ready(self):
        """Main processing when bot is ready"""
        logger.info(f"Logged in as {self.user} ({self.user.id})")
        
        self.session = aiohttp.ClientSession()
        start_time = datetime.now()
        
        try:
            heroes = await HeroManager.get_all()
            if not heroes:
                logger.error("No heroes found")
                await self.close()
                return

            logger.info(f"Processing {len(heroes)} heroes...")
            
            # Process heroes in batches to avoid rate limits
            batch_size = 5
            for i in range(0, len(heroes), batch_size):
                batch = heroes[i:i + batch_size]
                await asyncio.gather(*[self.process_hero_image(hero, self.session) for hero in batch])
                await asyncio.sleep(1)  # Brief pause between batches
            
            # Save final data
            await self.save_data()
            
            # Print summary
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"\n=== Upload Summary ===\n"
                f"Total processed: {self.upload_stats['total']}\n"
                f"Successful: {self.upload_stats['success']}\n"
                f"Failed: {self.upload_stats['failed']}\n"
                f"Skipped: {self.upload_stats['skipped']}\n"
                f"Time taken: {duration:.2f} seconds"
            )

        except Exception as e:
            logger.error(f"Error in main processing: {e}")
        finally:
            if self.session:
                await self.session.close()
            await self.close()

    async def close(self):
        """Cleanup before closing"""
        if hasattr(self, 'session') and self.session:
            await self.session.close()
        await super().close()

if __name__ == "__main__":
    # Remove old token from your code - never commit tokens!
    bot = EmojiUploader()
    # bot.run("YOUR_BOT_TOKEN_HERE")  # Replace with your actual bot token from environment variables