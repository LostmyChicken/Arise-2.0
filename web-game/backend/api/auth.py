from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from services.auth_service import auth_service
from services.database_service import update_player_status

router = APIRouter()
security = HTTPBearer()

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    player_id: str
    username: str

@router.post("/register", response_model=dict)
async def register(user_data: UserRegister):
    """Register a new user"""
    try:
        # Validate input
        if len(user_data.username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be at least 3 characters long"
            )
        
        if len(user_data.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        
        # Register user
        user = await auth_service.register_user(
            user_data.username,
            user_data.email,
            user_data.password
        )
        
        return {
            "message": "User registered successfully",
            "username": user["username"],
            "player_id": user["player_id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login user and return access token"""
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(user_data.username, user_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user["player_id"], "username": user["username"]},
            expires_delta=access_token_expires
        )
        
        # Update player online status
        await update_player_status(user["player_id"], True, "logged_in")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "player_id": user["player_id"],
            "username": user["username"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/logout")
async def logout(current_user: str = Depends(lambda: "placeholder")):
    """Logout user"""
    try:
        # Update player offline status
        # Note: In a real implementation, you'd get the current user from the token
        # await update_player_status(current_user, False, "logged_out")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.get("/me")
async def get_current_user_info(current_user: str = Depends(lambda: "placeholder")):
    """Get current user information"""
    try:
        # In a real implementation, you'd decode the JWT token to get user info
        return {
            "player_id": "placeholder",
            "username": "placeholder",
            "message": "This endpoint needs proper JWT implementation"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}"
        )

# Export router
auth_router = router