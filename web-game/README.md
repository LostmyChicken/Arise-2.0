# 🗡️ Arise - Solo Leveling Web Game

A comprehensive web-based RPG game inspired by the Solo Leveling universe, converted from the original Discord bot into a fully playable browser game.

## ✨ Features

### 🎮 Core Game Systems
- **Character Creation & Progression**: Level up your hunter with stats and skills
- **Gacha System**: Pull hunters and weapons with proper rarity rates
- **Story Campaign**: Interactive Solo Leveling story with battles and choices
- **World Boss System**: Real-time multiplayer boss battles
- **Gate System**: Dungeon exploration with stamina mechanics
- **Trading System**: Player-to-player item and hunter trading
- **Guild System**: Create and manage guilds with alliance features

### ⚔️ Combat & Progression
- **Real-time Battle System**: Turn-based combat with skills and elements
- **Character Stats**: Attack, Defense, Health, MP with upgrade systems
- **Skill Trees**: Unlock and upgrade various combat abilities
- **Shadow System**: Collect and use shadows from defeated enemies
- **Equipment**: Weapons and items with enhancement mechanics
- **Achievements**: Unlock titles and rewards for various accomplishments

### 🌐 Web Features
- **Responsive Design**: Play on desktop, tablet, or mobile
- **Real-time Updates**: WebSocket connections for live battles and events
- **User Authentication**: Secure account system with progress saving
- **Cross-platform**: No downloads required, play directly in browser

## 🚀 Quick Start

### For Players
1. Visit the game URL
2. Create an account or login
3. Start your Solo Leveling journey!

### For Developers
1. Clone the repository
2. Install dependencies: `npm install` (frontend) and `pip install -r requirements.txt` (backend)
3. Start the development servers
4. Open http://localhost:54156 to play

## 🛠️ Technology Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Socket.IO
- **Backend**: FastAPI, Python 3.8+, SQLite, WebSockets
- **Real-time**: Socket.IO for live updates and multiplayer features
- **Database**: SQLite (compatible with original Discord bot data)

## 📁 Project Structure

```
web-game/
├── frontend/           # React frontend application
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   ├── pages/      # Game screens and pages
│   │   ├── hooks/      # Custom React hooks
│   │   ├── services/   # API and WebSocket services
│   │   └── types/      # TypeScript type definitions
├── backend/            # FastAPI backend application
│   ├── api/           # API route handlers
│   ├── models/        # Database models
│   ├── services/      # Business logic services
│   └── utils/         # Utility functions
└── shared/            # Shared types and utilities
```

## 🎮 Game Features

### Character System
- Create and customize your hunter
- Level up and allocate stat points
- Unlock and upgrade skills
- Equip weapons and armor

### Battle System
- Turn-based combat with strategic depth
- Use skills and abilities in battle
- Element weaknesses and strengths
- Real-time multiplayer battles

### Gacha & Collection
- Pull for rare hunters and weapons
- Set favorite characters for increased rates
- Upgrade and enhance your collection
- Trade with other players

### Story Mode
- Experience Sung Jin-Woo's complete journey
- Interactive story with choices and consequences
- Battle iconic bosses from the series
- Unlock new features as you progress

### Guild System
- Create or join guilds with friends
- Participate in guild battles and events
- Share resources and strategies
- Climb guild leaderboards

## 🔧 Development

### Prerequisites
- Node.js 16+ (for frontend)
- Python 3.8+ (for backend)
- Modern web browser

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd web-game

# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt

# Start development servers
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm start
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Original Discord bot by LostmyChicken
- Inspired by Solo Leveling manhwa/anime
- Built with modern web technologies
- Thanks to the Solo Leveling community

---

**Note**: This is a fan project and is not officially affiliated with Solo Leveling or its creators.