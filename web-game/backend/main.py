from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import socketio
import uvicorn
import os
from dotenv import load_dotenv

from api.auth import auth_router
from api.player import player_router
from api.game import game_router
from api.battle import battle_router
from api.gacha import gacha_router
from api.guild import guild_router
from api.story import story_router
from services.auth_service import verify_token
from services.database_service import init_database

load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Arise - Solo Leveling Web Game",
    description="A comprehensive web-based RPG game inspired by Solo Leveling",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO server for real-time features
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(player_router, prefix="/api/player", tags=["Player"])
app.include_router(game_router, prefix="/api/game", tags=["Game"])
app.include_router(battle_router, prefix="/api/battle", tags=["Battle"])
app.include_router(gacha_router, prefix="/api/gacha", tags=["Gacha"])
app.include_router(guild_router, prefix="/api/guild", tags=["Guild"])
app.include_router(story_router, prefix="/api/story", tags=["Story"])

# Serve static files (frontend build)
if os.path.exists("../frontend/build"):
    app.mount("/static", StaticFiles(directory="../frontend/build/static"), name="static")
    app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="frontend")

@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    await init_database()
    print("🚀 Arise Web Game Backend Started!")
    print("📊 Database initialized")
    print("🔌 WebSocket server ready")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Arise Web Game API is running!"}

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"🔌 Client {sid} connected")
    await sio.emit('connected', {'message': 'Welcome to Arise!'}, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"🔌 Client {sid} disconnected")

@sio.event
async def join_room(sid, data):
    """Join a specific room (for battles, guilds, etc.)"""
    room = data.get('room')
    if room:
        await sio.enter_room(sid, room)
        await sio.emit('joined_room', {'room': room}, room=sid)
        print(f"🏠 Client {sid} joined room {room}")

@sio.event
async def leave_room(sid, data):
    """Leave a specific room"""
    room = data.get('room')
    if room:
        await sio.leave_room(sid, room)
        await sio.emit('left_room', {'room': room}, room=sid)
        print(f"🏠 Client {sid} left room {room}")

@sio.event
async def battle_action(sid, data):
    """Handle battle actions in real-time"""
    room = data.get('battle_id')
    action = data.get('action')
    
    if room and action:
        # Broadcast battle action to all players in the battle
        await sio.emit('battle_update', {
            'player_id': data.get('player_id'),
            'action': action,
            'data': data.get('data', {})
        }, room=room)

@sio.event
async def world_boss_action(sid, data):
    """Handle world boss battle actions"""
    boss_id = data.get('boss_id')
    action = data.get('action')
    
    if boss_id and action:
        # Broadcast to all players fighting this world boss
        await sio.emit('world_boss_update', {
            'boss_id': boss_id,
            'player_id': data.get('player_id'),
            'action': action,
            'data': data.get('data', {})
        }, room=f"world_boss_{boss_id}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 56092))
    uvicorn.run(
        "main:socket_app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )