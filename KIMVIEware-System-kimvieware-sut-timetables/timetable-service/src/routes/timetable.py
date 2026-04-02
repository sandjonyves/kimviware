"""
Timetable Service - EXTREME Branch Explosion
~500+ branches for symbolic execution stress test
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, time, timedelta

router = APIRouter(prefix="/timetable", tags=["Timetable"])

# Database
schedules_db = {}
conflicts_db = {}
next_schedule_id = 1

class TimeSlot(BaseModel):
    day: str  # Monday-Friday
    start_time: str  # HH:MM
    end_time: str  # HH:MM

class Schedule(BaseModel):
    course_id: int
    room_id: int
    instructor_id: str
    time_slots: List[TimeSlot]
    semester: str
    year: int

class ScheduleResponse(BaseModel):
    id: int
    course_id: int
    room_id: int
    instructor_id: str
    time_slots: List[TimeSlot]
    semester: str
    year: int
    conflicts: List[str]

@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(schedule: Schedule):
    """
    Create timetable entry with MASSIVE validation
    
    BRANCHES: 100+ decision points!
    
    Categories:
    - Day validation (7 branches)
    - Time validation (20+ branches)
    - Conflict detection (30+ branches)
    - Instructor validation (15 branches)
    - Room validation (15 branches)
    - Semester validation (10 branches)
    - Capacity checks (20 branches)
    """
    global next_schedule_id
    
    conflicts = []
    
    # ============================================================
    # BRANCH GROUP 1: Course ID Validation (10 branches)
    # ============================================================
    if schedule.course_id <= 0:
        raise HTTPException(400, "Invalid course ID")
    
    if schedule.course_id > 999999:
        raise HTTPException(400, "Course ID out of range")
    
    # Course level validation (based on ID)
    course_level = schedule.course_id // 1000
    
    if course_level == 0:
        raise HTTPException(400, "Course level cannot be 0")
    
    if course_level > 9:
        raise HTTPException(400, "Course level too high")
    
    if course_level < 1:
        raise HTTPException(400, "Undergraduate courses start at level 1")
    
    if course_level > 5 and course_level < 7:
        raise HTTPException(400, "Invalid graduate course level")
    
    if course_level >= 7:  # PhD courses
        if schedule.year < 2020:
            raise HTTPException(400, "PhD courses not offered before 2020")
    
    # Course number validation
    course_num = schedule.course_id % 1000
    
    if course_num == 0:
        raise HTTPException(400, "Course number cannot be 0")
    
    if course_num > 900 and course_level < 5:
        raise HTTPException(400, "900-level courses only for graduate")
    
    if course_num % 100 == 0:  # Special courses
        if schedule.semester != "Summer":
            raise HTTPException(400, "Special courses only in Summer")
    
    # ============================================================
    # BRANCH GROUP 2: Room ID Validation (15 branches)
    # ============================================================
    if schedule.room_id <= 0:
        raise HTTPException(400, "Invalid room ID")
    
    if schedule.room_id > 10000:
        raise HTTPException(400, "Room ID out of range")
    
    # Building extraction
    building = schedule.room_id // 1000
    room_num = schedule.room_id % 1000
    
    if building == 0:
        raise HTTPException(400, "Building cannot be 0")
    
    if building > 20:
        raise HTTPException(400, "Building number too high")
    
    if room_num == 0:
        raise HTTPException(400, "Room number cannot be 0")
    
    if room_num > 500:
        raise HTTPException(400, "Room number too high")
    
    # Special room types
    if room_num > 300:  # Labs
        if course_level == 1:
            raise HTTPException(400, "First-year courses cannot use labs")
        if "theory" in str(schedule.course_id):
            raise HTTPException(400, "Theory courses don't need labs")
    
    if room_num > 400:  # Auditoriums
        if course_level > 5:
            raise HTTPException(400, "Graduate courses too small for auditorium")
    
    if building > 10:  # Remote buildings
        if schedule.time_slots and schedule.time_slots[0].start_time < "09:00":
            raise HTTPException(400, "Remote buildings not accessible before 9 AM")
    
    # Building restrictions
    if building % 2 == 0:  # Even buildings
        if schedule.semester == "Winter":
            conflicts.append("Even buildings under renovation in Winter")
    
    if building == 13:
        raise HTTPException(400, "Building 13 permanently closed")
    
    # Room capacity checks
    estimated_capacity = room_num // 10
    
    if estimated_capacity < 10 and course_level == 1:
        raise HTTPException(400, "Introductory courses need larger rooms")
    
    if estimated_capacity > 100 and course_level > 6:
        raise HTTPException(400, "PhD courses need smaller rooms")
    
    # ============================================================
    # BRANCH GROUP 3: Instructor Validation (20 branches)
    # ============================================================
    if not schedule.instructor_id:
        raise HTTPException(400, "Instructor ID required")
    
    if len(schedule.instructor_id) < 3:
        raise HTTPException(400, "Instructor ID too short")
    
    if len(schedule.instructor_id) > 15:
        raise HTTPException(400, "Instructor ID too long")
    
    if not schedule.instructor_id[0].isalpha():
        raise HTTPException(400, "Instructor ID must start with letter")
    
    if not schedule.instructor_id[-1].isdigit():
        raise HTTPException(400, "Instructor ID must end with digit")
    
    # Instructor type detection
    if schedule.instructor_id.startswith("DR"):
        instructor_type = "professor"
    elif schedule.instructor_id.startswith("TA"):
        instructor_type = "assistant"
    elif schedule.instructor_id.startswith("ADJ"):
        instructor_type = "adjunct"
    else:
        instructor_type = "unknown"
    
    # Instructor-course matching
    if instructor_type == "assistant":
        if course_level > 3:
            raise HTTPException(400, "TAs cannot teach advanced courses")
        if room_num > 100:
            raise HTTPException(400, "TAs cannot teach in large rooms")
    
    if instructor_type == "adjunct":
        if course_level == 1:
            raise HTTPException(400, "Adjuncts cannot teach intro courses")
        if schedule.semester == "Summer":
            raise HTTPException(400, "No adjuncts in Summer")
    
    if instructor_type == "unknown":
        raise HTTPException(400, "Invalid instructor type")
    
    # Instructor workload check (simulated)
    instructor_courses = sum(
        1 for s in schedules_db.values()
        if s["instructor_id"] == schedule.instructor_id and s["semester"] == schedule.semester
    )
    
    if instructor_courses >= 3:
        if instructor_type == "assistant":
            raise HTTPException(400, "TAs cannot teach more than 3 courses")
    
    if instructor_courses >= 4:
        if instructor_type == "adjunct":
            raise HTTPException(400, "Adjuncts cannot teach more than 4 courses")
    
    if instructor_courses >= 5:
        raise HTTPException(400, "Instructors cannot teach more than 5 courses")
    
    # Seniority checks
    instructor_num = int(''.join(filter(str.isdigit, schedule.instructor_id)))
    
    if instructor_num < 100:  # Junior faculty
        if course_level > 6:
            raise HTTPException(400, "Junior faculty cannot teach PhD courses")
    
    if instructor_num > 900:  # Emeritus
        if schedule.semester != "Fall":
            raise HTTPException(400, "Emeritus only teach in Fall")
    
    # ============================================================
    # BRANCH GROUP 4: Time Slot Validation (50+ branches!)
    # ============================================================
    if not schedule.time_slots:
        raise HTTPException(400, "At least one time slot required")
    
    if len(schedule.time_slots) > 5:
        raise HTTPException(400, "Maximum 5 time slots per course")
    
    if len(schedule.time_slots) == 1:
        if course_level < 5:
            raise HTTPException(400, "Undergraduate courses need multiple sessions")
    
    if len(schedule.time_slots) > 3:
        if course_level > 5:
            raise HTTPException(400, "Graduate courses meet max 3 times/week")
    
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    for i, slot in enumerate(schedule.time_slots):
        # Day validation
        if slot.day not in valid_days:
            raise HTTPException(400, f"Invalid day: {slot.day}")
        
        if slot.day == "Friday":
            if course_level == 1:
                raise HTTPException(400, "No intro courses on Friday")
        
        # Time format validation
        try:
            start_h, start_m = map(int, slot.start_time.split(":"))
            end_h, end_m = map(int, slot.end_time.split(":"))
        except:
            raise HTTPException(400, f"Invalid time format in slot {i}")
        
        # Time range validation
        if start_h < 7:
            raise HTTPException(400, f"Classes cannot start before 7 AM")
        
        if start_h >= 22:
            raise HTTPException(400, f"Classes cannot start after 10 PM")
        
        if end_h > 23:
            raise HTTPException(400, f"Classes must end by 11 PM")
        
        if start_h > end_h:
            raise HTTPException(400, f"Start time after end time in slot {i}")
        
        if start_h == end_h and start_m >= end_m:
            raise HTTPException(400, f"Invalid time range in slot {i}")
        
        # Duration checks
        duration_minutes = (end_h * 60 + end_m) - (start_h * 60 + start_m)
        
        if duration_minutes < 30:
            raise HTTPException(400, f"Class too short (min 30 min)")
        
        if duration_minutes > 180:
            raise HTTPException(400, f"Class too long (max 3 hours)")
        
        if duration_minutes == 30:
            if course_level > 1:
                raise HTTPException(400, "Only intro courses can be 30 min")
        
        if duration_minutes > 120:
            if course_level < 5:
                raise HTTPException(400, "Only graduate courses can exceed 2 hours")
        
        # Time of day checks
        if start_h < 8:  # Early morning
            if building > 10:
                raise HTTPException(400, f"Remote buildings not ready before 8 AM")
        
        if start_h >= 18:  # Evening
            if course_level == 1:
                raise HTTPException(400, "No evening classes for first-years")
            if instructor_type == "assistant":
                raise HTTPException(400, "TAs don't teach evening classes")
        
        if start_h >= 20:  # Night
            if room_num < 100:
                raise HTTPException(400, "Small rooms closed at night")
        
        # Standard time slots check
        if start_m not in [0, 30]:
            conflicts.append(f"Non-standard start time: {slot.start_time}")
        
        if end_m not in [0, 30]:
            conflicts.append(f"Non-standard end time: {slot.end_time}")
        
        # Lunch break check
        if start_h == 12 and duration_minutes > 60:
            conflicts.append("Class conflicts with lunch break")
        
        # Peak time check
        if 10 <= start_h <= 14:  # Peak hours
            if room_num > 200:
                conflicts.append("Large room during peak hours - high demand")
        
        # Check against existing schedules (MANY branches)
        for existing in schedules_db.values():
            if existing["semester"] != schedule.semester:
                continue
            if existing["year"] != schedule.year:
                continue
            
            for ex_slot in existing["time_slots"]:
                if ex_slot["day"] != slot.day:
                    continue
                
                # Time overlap detection (complex!)
                ex_start_h, ex_start_m = map(int, ex_slot["start_time"].split(":"))
                ex_end_h, ex_end_m = map(int, ex_slot["end_time"].split(":"))
                
                start_total = start_h * 60 + start_m
                end_total = end_h * 60 + end_m
                ex_start_total = ex_start_h * 60 + ex_start_m
                ex_end_total = ex_end_h * 60 + ex_end_m
                
                # Multiple overlap conditions
                if start_total < ex_end_total and end_total > ex_start_total:
                    # Room conflict
                    if existing["room_id"] == schedule.room_id:
                        raise HTTPException(400, f"Room conflict on {slot.day} at {slot.start_time}")
                    
                    # Instructor conflict
                    if existing["instructor_id"] == schedule.instructor_id:
                        raise HTTPException(400, f"Instructor conflict on {slot.day} at {slot.start_time}")
                    
                    # Same building, adjacent rooms (noise)
                    if abs(existing["room_id"] - schedule.room_id) <= 2:
                        if existing["course_id"] // 1000 != course_level:
                            conflicts.append(f"Potential noise from adjacent room on {slot.day}")
    
    # ============================================================
    # BRANCH GROUP 5: Semester Validation (15 branches)
    # ============================================================
    valid_semesters = ["Fall", "Spring", "Summer", "Winter"]
    
    if schedule.semester not in valid_semesters:
        raise HTTPException(400, "Invalid semester")
    
    if schedule.semester == "Winter":
        if course_level == 1:
            raise HTTPException(400, "No intro courses in Winter")
        if len(schedule.time_slots) > 3:
            raise HTTPException(400, "Winter courses max 3 sessions/week")
    
    if schedule.semester == "Summer":
        if course_level > 5:
            raise HTTPException(400, "No graduate courses in Summer")
        if len(schedule.time_slots) < 3:
            raise HTTPException(400, "Summer courses need intensive schedule")
    
    # Year validation
    if schedule.year < 2020:
        raise HTTPException(400, "Cannot schedule courses before 2020")
    
    if schedule.year > 2030:
        raise HTTPException(400, "Cannot schedule more than 6 years ahead")
    
    current_year = 2026  # Hardcoded for testing
    
    if schedule.year < current_year:
        if schedule.semester != "Fall":
            raise HTTPException(400, "Can only modify past Fall schedules")
    
    if schedule.year > current_year + 2:
        if course_level < 5:
            raise HTTPException(400, "Undergraduate courses scheduled max 2 years ahead")
    
    # Semester-year combinations
    if schedule.year == 2026:
        if schedule.semester == "Spring":
            if schedule.time_slots[0].day == "Monday":
                conflicts.append("Spring 2026 starts on Tuesday (MLK Day)")
    
    # Academic calendar checks
    if schedule.semester == "Fall" and schedule.year % 4 == 0:
        conflicts.append("Presidential election year - consider schedule adjustments")
    
    if schedule.semester == "Spring":
        if len(schedule.time_slots) == 1:
            conflicts.append("Spring courses should meet multiple times due to breaks")
    
    # ============================================================
    # BRANCH GROUP 6: Cross-validation (20+ branches)
    # ============================================================
    
    # Course-room-time coherence
    if course_level >= 5:  # Graduate
        if schedule.time_slots[0].start_time < "14:00":
            conflicts.append("Graduate courses typically scheduled after 2 PM")
    
    if course_level == 1:  # Intro
        if schedule.time_slots[0].start_time > "17:00":
            conflicts.append("Intro courses should be during regular hours")
    
    # Workload distribution
    total_minutes = sum(
        (int(slot.end_time.split(":")[0]) * 60 + int(slot.end_time.split(":")[1])) -
        (int(slot.start_time.split(":")[0]) * 60 + int(slot.start_time.split(":")[1]))
        for slot in schedule.time_slots
    )
    
    if total_minutes < 120:
        if course_level >= 3:
            raise HTTPException(400, "Upper-level courses need at least 2 hours/week")
    
    if total_minutes > 240:
        if course_level < 5:
            raise HTTPException(400, "Undergraduate courses max 4 hours/week")
    
    # Resource optimization
    if building > 5 and len(schedule.time_slots) == 1:
        conflicts.append("Single session in remote building - consider consolidating")
    
    # Create schedule
    schedule_id = next_schedule_id
    schedules_db[schedule_id] = {
        "id": schedule_id,
        "course_id": schedule.course_id,
        "room_id": schedule.room_id,
        "instructor_id": schedule.instructor_id,
        "time_slots": [slot.dict() for slot in schedule.time_slots],
        "semester": schedule.semester,
        "year": schedule.year,
        "created_at": datetime.utcnow()
    }
    next_schedule_id += 1
    
    return ScheduleResponse(
        **schedules_db[schedule_id],
        conflicts=conflicts
    )

@router.get("/{schedule_id}")
async def get_schedule(schedule_id: int):
    """Get schedule with more validation branches"""
    
    if schedule_id <= 0:
        raise HTTPException(400, "Invalid schedule ID")
    
    if schedule_id not in schedules_db:
        raise HTTPException(404, "Schedule not found")
    
    schedule = schedules_db[schedule_id]
    
    # Additional status checks (more branches!)
    current_year = 2026
    is_past = schedule["year"] < current_year
    is_current = schedule["year"] == current_year
    is_future = schedule["year"] > current_year
    
    status = "unknown"
    if is_past:
        status = "archived"
    elif is_current:
        # Check semester
        if schedule["semester"] == "Fall":
            status = "active"
        elif schedule["semester"] == "Spring":
            status = "completed"
        else:
            status = "active"
    else:
        status = "planned"
    
    return {
        **schedule,
        "status": status,
        "conflicts": []
    }

# Initialize with sample
def init_timetable():
    global next_schedule_id
    schedules_db[1] = {
        "id": 1,
        "course_id": 1101,
        "room_id": 1201,
        "instructor_id": "DR001",
        "time_slots": [
            {"day": "Monday", "start_time": "10:00", "end_time": "11:30"},
            {"day": "Wednesday", "start_time": "10:00", "end_time": "11:30"}
        ],
        "semester": "Fall",
        "year": 2026,
        "created_at": datetime.utcnow()
    }
    next_schedule_id = 2

init_timetable()
