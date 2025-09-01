# 🗡️ Arise - Solo Leveling Discord Bot

A comprehensive Discord bot inspired by the Solo Leveling universe, featuring an immersive RPG experience with gacha mechanics, story campaigns, world bosses, and much more!

## ✨ Features

### 🎮 Core Systems
- **Gacha System**: Pull hunters and weapons with proper rarity rates and pity system
- **Story Campaign**: Interactive Solo Leveling story with battles and choices
- **World Boss System**: Multi-server boss battles with scaling difficulty
- **Gate System**: Dungeon exploration with stamina mechanics
- **Trading System**: Player-to-player item and hunter trading
- **Guild System**: Create and manage guilds with alliance features

### ⚔️ Combat & Progression
- **Battle System**: Turn-based combat with skills and elements
- **Character Stats**: Attack, Defense, Health, MP with upgrade systems
- **Skill Trees**: Unlock and upgrade various combat abilities
- **Shadow System**: Collect and use shadows from defeated enemies
- **Equipment**: Weapons and items with enhancement mechanics
- **Achievements**: Unlock titles and rewards for various accomplishments

### 🎯 Additional Features
- **Market System**: Buy and sell items with other players
- **Daily Rewards**: Login bonuses and daily missions
- **Leaderboards**: Compete with other players across servers
- **Admin Tools**: Comprehensive content creation and management
- **Economy**: Gold, diamonds, crystals, and various currencies

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Discord Bot Token
- Discord Application with Bot permissions

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/LostmyChicken/Arise.git
   cd Arise
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_bot_token_here
   CLIENT_ID=your_client_id_here
   ```

4. **Database Setup**
   ```bash
   python database_setup.py
   ```

5. **Run the bot**
   ```bash
   python main.py
   ```

## 🎮 Commands

### Player Commands
- `/profile` - View your character profile
- `/stats` - Check your character statistics
- `/gacha` - Pull hunters and weapons
- `/story` - Access story campaign
- `/gate` - Enter dungeon gates
- `/inventory` - View your items
- `/trade` - Trade with other players
- `/guild` - Guild management

### Admin Commands
- `/create` - Create new content (items, hunters, etc.)
- `/give` - Give items to players
- `/admin` - Administrative tools
- `/reset` - Reset player data

## 📁 Project Structure

```
Arise/
├── commands/           # Bot commands organized by category
├── structure/          # Core game systems and data models
├── utilis/            # Utility functions and helpers
├── data/              # Database files
├── images/            # Character and item images
├── events/            # Discord event handlers
├── main.py            # Bot entry point
└── requirements.txt   # Python dependencies
```

## 🛠️ Configuration

### Bot Permissions
The bot requires the following Discord permissions:
- Send Messages
- Use Slash Commands
- Embed Links
- Attach Files
- Read Message History
- Add Reactions
- Use External Emojis

### Database
The bot uses SQLite databases for data storage:
- `players.db` - Player data and progress
- `items.db` - Items and equipment
- `heroes.db` - Hunter characters
- `guilds.db` - Guild information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by Solo Leveling manhwa/anime
- Built with discord.py
- Thanks to the Solo Leveling community

## 📞 Support

For support, join our Discord server or open an issue on GitHub.

---

**Note**: This bot is a fan project and is not officially affiliated with Solo Leveling or its creators.
