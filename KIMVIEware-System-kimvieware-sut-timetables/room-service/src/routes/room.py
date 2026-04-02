"""
Room Management Routes
Booking and availability logic
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, time

router = APIRouter(prefix="/rooms", tags=["Rooms"])

# In-memory database
rooms_db = {}
bookings_db = {}
next_room_id = 1
next_booking_id = 1

class Room(BaseModel):
    number: str
    building: str
    capacity: int
    has_projector: bool
    has_whiteboard: bool

class RoomResponse(BaseModel):
    id: int
    number: str
    building: str
    capacity: int
    has_projector: bool
    has_whiteboard: bool
    is_available: bool

class Booking(BaseModel):
    room_id: int
    user_id: str
    start_time: str  # "HH:MM"
    end_time: str    # "HH:MM"
    purpose: str

@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(room: Room):
    """
    Create new room
    
    BRANCHES:
    1. Duplicate room number in building
    2. Capacity validation (5-200)
    3. Building name validation
    4. Room number format
    """
    global next_room_id
    
    # Branch 1: Check duplicate
    for r in rooms_db.values():
        if r["number"] == room.number and r["building"] == room.building:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Room {room.number} already exists in {room.building}"
            )
    
    # Branch 2: Validate capacity
    if room.capacity < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Capacity must be at least 5"
        )
    
    if room.capacity > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Capacity cannot exceed 200"
        )
    
    # Branch 3: Building validation
    valid_buildings = ["A", "B", "C", "D", "Main"]
    if room.building not in valid_buildings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid building. Must be one of: {', '.join(valid_buildings)}"
        )
    
    # Branch 4: Room number format (must start with digit)
    if not room.number[0].isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room number must start with a digit"
        )
    
    # Create room
    room_id = next_room_id
    rooms_db[room_id] = {
        "id": room_id,
        "number": room.number,
        "building": room.building,
        "capacity": room.capacity,
        "has_projector": room.has_projector,
        "has_whiteboard": room.has_whiteboard
    }
    next_room_id += 1
    
    return RoomResponse(is_available=True, **rooms_db[room_id])

@router.post("/bookings", status_code=status.HTTP_201_CREATED)
async def book_room(booking: Booking):
    """
    Book a room
    
    BRANCHES:
    1. Room exists?
    2. Time conflict?
    3. Room capacity sufficient?
    4. Valid time range?
    5. Booking duration limits
    6. Equipment requirements met?
    """
    
    # Branch 1: Room exists
    if booking.room_id not in rooms_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    room = rooms_db[booking.room_id]
    
    # Branch 2: Check time conflicts
    for b in bookings_db.values():
        if b["room_id"] == booking.room_id:
            # Simple time overlap check
            if (booking.start_time < b["end_time"] and booking.end_time > b["start_time"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Room already booked for this time slot"
                )
    
    # Branch 3: Validate time format and range
    try:
        start_h, start_m = map(int, booking.start_time.split(":"))
        end_h, end_m = map(int, booking.end_time.split(":"))
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid time format. Use HH:MM"
        )
    
    # Branch 4: Valid working hours (8:00-18:00)
    if start_h < 8 or end_h > 18:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bookings only allowed between 8:00 and 18:00"
        )
    
    # Branch 5: Duration limits (30 min - 4 hours)
    duration_minutes = (end_h * 60 + end_m) - (start_h * 60 + start_m)
    
    if duration_minutes < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum booking duration is 30 minutes"
        )
    
    if duration_minutes > 240:  # 4 hours
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum booking duration is 4 hours"
        )
    
    # Branch 6: Purpose validation
    if len(booking.purpose) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purpose must be at least 5 characters"
        )
    
    # Branch 7: Check if projector needed
    if "presentation" in booking.purpose.lower() or "projector" in booking.purpose.lower():
        if not room["has_projector"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Room does not have a projector"
            )
    
    # Create booking
    global next_booking_id
    bookings_db[next_booking_id] = {
        "id": next_booking_id,
        "room_id": booking.room_id,
        "user_id": booking.user_id,
        "start_time": booking.start_time,
        "end_time": booking.end_time,
        "purpose": booking.purpose,
        "booked_at": datetime.utcnow()
    }
    next_booking_id += 1
    
    return {"message": "Room booked successfully", "booking_id": next_booking_id - 1}

@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(room_id: int):
    """
    Get room details
    
    BRANCHES:
    1. Room exists?
    2. Currently available?
    """
    
    if room_id not in rooms_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    room = rooms_db[room_id]
    
    # Check current availability (simplified)
    is_available = True
    for b in bookings_db.values():
        if b["room_id"] == room_id:
            is_available = False
            break
    
    return RoomResponse(is_available=is_available, **room)

# Initialize with sample data
def init_rooms():
    global next_room_id
    rooms_db[1] = {
        "id": 1,
        "number": "101",
        "building": "A",
        "capacity": 30,
        "has_projector": True,
        "has_whiteboard": True
    }
    next_room_id = 2

init_rooms()
