from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import secrets
import string

from services.database_service import db_service, get_user_by_username, create_web_user

# Security configuration
SECRET_KEY = "your-secret-key-change-this-in-production"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self):
        self.pwd_context = pwd_context
        self.ACCESS_TOKEN_EXPIRE_MINUTES = ACCESS_TOKEN_EXPIRE_MINUTES
        self.ACCESS_TOKEN_EXPIRE_MINUTES = ACCESS_TOKEN_EXPIRE_MINUTES
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def generate_player_id(self) -> str:
        """Generate a unique player ID"""
        # Generate a random player ID similar to Discord user IDs
        return ''.join(secrets.choice(string.digits) for _ in range(18))
    
    async def authenticate_user(self, username: str, password: str):
        """Authenticate a user with username and password"""
        user = await get_user_by_username(username)
        if not user:
            return False
        
        # user is a tuple from database query
        user_dict = {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'password_hash': user[3],
            'player_id': user[4],
            'created_at': user[5],
            'last_login': user[6],
            'is_active': user[7]
        }
        
        if not self.verify_password(password, user_dict['password_hash']):
            return False
        
        if not user_dict['is_active']:
            return False
        
        return user_dict
    
    async def register_user(self, username: str, email: str, password: str):
        """Register a new user"""
        # Check if username already exists
        existing_user = await get_user_by_username(username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        query = "SELECT * FROM web_users WHERE email = ?"
        existing_email = await db_service.execute_query('players', query, (email,))
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Generate player ID and hash password
        player_id = self.generate_player_id()
        password_hash = self.get_password_hash(password)
        
        # Create user in database
        await create_web_user(username, email, password_hash, player_id)
        
        # Create initial player data
        await self.create_initial_player(player_id, username)
        
        return {
            'username': username,
            'email': email,
            'player_id': player_id
        }
    
    async def create_initial_player(self, player_id: str, username: str):
        """Create initial player data for new user"""
        # Import here to avoid circular imports
        from services.player_service import PlayerService
        
        player_service = PlayerService()
        await player_service.create_new_player(player_id, username)

# Global auth service instance
auth_service = AuthService()

def verify_token(token: str):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )