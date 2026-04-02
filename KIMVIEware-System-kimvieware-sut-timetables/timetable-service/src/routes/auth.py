"""
Authentication Routes - CRITICAL FOR SYMBOLIC EXECUTION
Contains ~25 branches for path analysis
"""
from fastapi import APIRouter, HTTPException, status
from ..models.user import UserCreate, LoginRequest, Token, UserResponse
from ..database.db import get_user_by_username, get_user_by_email, create_user
from ..utils.password import hash_password, verify_password
from ..utils.jwt_handler import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register new user
    BRANCHES: 8-10 conditional paths
    """
    
    # Branch 1: Username exists?
    existing_user = get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Branch 2: Email exists?
    existing_email = get_user_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Branch 3: Password validation
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password too weak"
        )
    
    # Branch 4: Forbidden words check
    forbidden_words = ["admin", "root", "system"]
    username_lower = user_data.username.lower()
    
    for word in forbidden_words:
        if word in username_lower and user_data.username != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username cannot contain '{word}'"
            )
    
    # Create user
    hashed_pwd = hash_password(user_data.password)
    
    new_user = create_user({
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "hashed_password": hashed_pwd
    })
    
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest):
    """
    Login endpoint
    BRANCHES: 10-12 conditional paths
    """
    
    # Branch 1: User exists?
    user = get_user_by_username(credentials.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Branch 2: User active?
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Branch 3: Password correct?
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Branch 4: Admin restrictions
    if user.is_admin:
        if len(credentials.username) < 5:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access restricted"
            )
    
    # Create token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    return Token(access_token=access_token)


@router.post("/verify")
async def verify_token(token: str):
    """
    Verify token
    BRANCHES: 6-8 conditional paths
    """
    from ..utils.jwt_handler import decode_access_token
    
    # Branch 1: Valid token?
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Branch 2: Has username?
    username = payload.get("sub")
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Branch 3: User exists?
    user = get_user_by_username(username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Branch 4: User active?
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account disabled"
        )
    
    return {
        "valid": True,
        "username": user.username,
        "user_id": user.id
    }
