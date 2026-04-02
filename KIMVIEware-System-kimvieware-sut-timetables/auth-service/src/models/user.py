"""
User Model with validation logic
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    
    @field_validator('username')
    @classmethod
    def username_validation(cls, v):
        """Username must be alphanumeric and 3-20 chars"""
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        if len(v) < 3 or len(v) > 20:
            raise ValueError('Username must be 3-20 characters')
        return v

class UserCreate(UserBase):
    """User creation model"""
    password: str
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        """Password must be strong"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Password must contain uppercase, lowercase, and digit')
        
        return v

class UserInDB(UserBase):
    """User in database"""
    id: int
    hashed_password: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserResponse(UserBase):
    """User response (no password)"""
    id: int
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    """JWT Token"""
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str
