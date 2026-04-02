"""
In-memory database (for symbolic execution testing)
"""
from datetime import datetime
from typing import Optional, Dict
from ..models.user import UserInDB
from ..utils.password import hash_password

# Simulate database as dict
users_db: Dict[int, UserInDB] = {}
users_by_username: Dict[str, int] = {}
users_by_email: Dict[str, int] = {}
next_user_id = 1

def init_db():
    """Initialize with test users"""
    global next_user_id
    
    # Admin user
    admin = UserInDB(
        id=next_user_id,
        email="admin@kimvieware.com",
        username="admin",
        full_name="System Admin",
        hashed_password=hash_password("Admin123!"),
        is_active=True,
        is_admin=True,
        created_at=datetime.utcnow()
    )
    
    users_db[next_user_id] = admin
    users_by_username["admin"] = next_user_id
    users_by_email["admin@kimvieware.com"] = next_user_id
    next_user_id += 1

def get_user_by_username(username: str) -> Optional[UserInDB]:
    """Get user by username"""
    user_id = users_by_username.get(username)
    if user_id:
        return users_db.get(user_id)
    return None

def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user by email"""
    user_id = users_by_email.get(email)
    if user_id:
        return users_db.get(user_id)
    return None

def create_user(user_data: dict) -> UserInDB:
    """Create new user"""
    global next_user_id
    
    user = UserInDB(
        id=next_user_id,
        email=user_data["email"],
        username=user_data["username"],
        full_name=user_data.get("full_name"),
        hashed_password=user_data["hashed_password"],
        is_active=True,
        is_admin=False,
        created_at=datetime.utcnow()
    )
    
    users_db[next_user_id] = user
    users_by_username[user.username] = next_user_id
    users_by_email[user.email] = next_user_id
    next_user_id += 1
    
    return user

# Initialize on import (best-effort). Don't raise on hashing failures
try:
    init_db()
except Exception:
    # If password hashing/backend fails during import, skip DB init
    pass
