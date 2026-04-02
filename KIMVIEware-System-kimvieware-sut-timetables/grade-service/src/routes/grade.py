"""
Grade Management Service
Complex grading logic with MANY branches for explosion demonstration
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/grades", tags=["Grades"])

# Database
grades_db = {}
students_db = {}
courses_db = {}
next_grade_id = 1

class Grade(BaseModel):
    student_id: str
    course_id: int
    assignment_name: str
    score: float
    max_score: float
    weight: float  # 0.0-1.0

class GradeResponse(BaseModel):
    id: int
    student_id: str
    course_id: int
    assignment_name: str
    score: float
    max_score: float
    percentage: float
    letter_grade: str
    weight: float

@router.post("/", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
async def submit_grade(grade: Grade):
    """
    Submit a grade with EXTENSIVE validation
    
    BRANCHES (30+):
    - Student ID validation (5 branches)
    - Course ID validation (3 branches)
    - Score validation (10 branches)
    - Weight validation (5 branches)
    - Assignment name validation (4 branches)
    - Letter grade calculation (7 branches)
    - Duplicate check (2 branches)
    """
    global next_grade_id
    
    # BRANCH GROUP 1: Student ID validation (5 branches)
    if not grade.student_id:
        raise HTTPException(400, "Student ID required")
    
    if len(grade.student_id) < 3:
        raise HTTPException(400, "Student ID too short")
    
    if len(grade.student_id) > 20:
        raise HTTPException(400, "Student ID too long")
    
    if not grade.student_id[0].isalpha():
        raise HTTPException(400, "Student ID must start with letter")
    
    if not grade.student_id[-1].isdigit():
        raise HTTPException(400, "Student ID must end with digit")
    
    # BRANCH GROUP 2: Course ID validation (3 branches)
    if grade.course_id <= 0:
        raise HTTPException(400, "Invalid course ID")
    
    if grade.course_id > 10000:
        raise HTTPException(400, "Course ID out of range")
    
    if grade.course_id % 100 == 0:  # Special course IDs
        raise HTTPException(400, "Reserved course ID")
    
    # BRANCH GROUP 3: Score validation (10 branches)
    if grade.score < 0:
        raise HTTPException(400, "Score cannot be negative")
    
    if grade.score > grade.max_score:
        raise HTTPException(400, "Score exceeds maximum")
    
    if grade.max_score <= 0:
        raise HTTPException(400, "Invalid max score")
    
    if grade.max_score > 1000:
        raise HTTPException(400, "Max score too high")
    
    if grade.max_score < 10:
        raise HTTPException(400, "Max score too low")
    
    percentage = (grade.score / grade.max_score) * 100
    
    if percentage > 100:
        raise HTTPException(400, "Percentage exceeds 100%")
    
    if grade.score == 0 and grade.max_score > 0:
        # Special case: zero score
        if len(grade.assignment_name) < 5:
            raise HTTPException(400, "Zero score requires detailed assignment name")
    
    if grade.score == grade.max_score:
        # Perfect score
        if grade.weight < 0.1:
            raise HTTPException(400, "Perfect score on low-weight assignment suspicious")
    
    if percentage < 40 and grade.weight > 0.3:
        # Failing grade on major assignment
        if "makeup" not in grade.assignment_name.lower():
            raise HTTPException(400, "Low score on major assignment - use makeup designation")
    
    if percentage >= 98 and grade.weight > 0.4:
        # Exceptional performance
        if "honors" not in grade.assignment_name.lower() and "advanced" not in grade.assignment_name.lower():
            raise HTTPException(400, "Exceptional score requires honors/advanced designation")
    
    # BRANCH GROUP 4: Weight validation (5 branches)
    if grade.weight < 0:
        raise HTTPException(400, "Weight cannot be negative")
    
    if grade.weight > 1.0:
        raise HTTPException(400, "Weight cannot exceed 1.0")
    
    if grade.weight == 0:
        raise HTTPException(400, "Weight cannot be zero")
    
    if grade.weight > 0.5 and "quiz" in grade.assignment_name.lower():
        raise HTTPException(400, "Quiz weight too high")
    
    if grade.weight < 0.2 and "exam" in grade.assignment_name.lower():
        raise HTTPException(400, "Exam weight too low")
    
    # BRANCH GROUP 5: Assignment name validation (4 branches)
    if len(grade.assignment_name) < 3:
        raise HTTPException(400, "Assignment name too short")
    
    if len(grade.assignment_name) > 100:
        raise HTTPException(400, "Assignment name too long")
    
    if grade.assignment_name.isdigit():
        raise HTTPException(400, "Assignment name cannot be only numbers")
    
    forbidden_words = ["test", "null", "undefined", "none"]
    if any(word in grade.assignment_name.lower() for word in forbidden_words):
        raise HTTPException(400, "Assignment name contains forbidden word")
    
    # BRANCH GROUP 6: Duplicate check (2 branches)
    for g in grades_db.values():
        if (g["student_id"] == grade.student_id and 
            g["course_id"] == grade.course_id and 
            g["assignment_name"] == grade.assignment_name):
            raise HTTPException(400, "Grade already exists for this assignment")
    
    # BRANCH GROUP 7: Letter grade calculation (7 branches)
    if percentage >= 90:
        letter = "A"
    elif percentage >= 80:
        letter = "B"
    elif percentage >= 70:
        letter = "C"
    elif percentage >= 60:
        letter = "D"
    else:
        letter = "F"
    
    # Plus/minus modifiers (additional branches)
    if letter in ["A", "B", "C", "D"]:
        decimal = percentage % 10
        if decimal >= 7 and letter != "A":
            letter += "+"
        elif decimal < 3 and letter != "F":
            letter += "-"
    
    # Create grade
    grade_id = next_grade_id
    grades_db[grade_id] = {
        "id": grade_id,
        "student_id": grade.student_id,
        "course_id": grade.course_id,
        "assignment_name": grade.assignment_name,
        "score": grade.score,
        "max_score": grade.max_score,
        "weight": grade.weight,
        "percentage": percentage,
        "letter_grade": letter,
        "submitted_at": datetime.utcnow()
    }
    next_grade_id += 1
    
    return GradeResponse(**grades_db[grade_id])

@router.get("/student/{student_id}/gpa")
async def calculate_gpa(student_id: str):
    """
    Calculate GPA with complex logic
    
    BRANCHES (20+):
    - Different GPA scales (4.0, 5.0, 100)
    - Weighted vs unweighted
    - Honors courses bonus
    - Failed courses handling
    - Incomplete grades
    """
    
    student_grades = [g for g in grades_db.values() if g["student_id"] == student_id]
    
    if not student_grades:
        raise HTTPException(404, "No grades found for student")
    
    # BRANCH: GPA calculation method
    total_points = 0
    total_credits = 0
    
    for grade in student_grades:
        letter = grade["letter_grade"]
        weight = grade["weight"]
        
        # BRANCH: Letter to points conversion (multiple branches)
        if letter.startswith("A"):
            points = 4.0
            if "+" in letter:
                points = 4.0  # A+ = 4.0
            elif "-" in letter:
                points = 3.7
        elif letter.startswith("B"):
            points = 3.0
            if "+" in letter:
                points = 3.3
            elif "-" in letter:
                points = 2.7
        elif letter.startswith("C"):
            points = 2.0
            if "+" in letter:
                points = 2.3
            elif "-" in letter:
                points = 1.7
        elif letter.startswith("D"):
            points = 1.0
            if "+" in letter:
                points = 1.3
            elif "-" in letter:
                points = 0.7
        else:  # F
            points = 0.0
        
        # BRANCH: Honors bonus
        if "honors" in grade["assignment_name"].lower():
            points += 0.5
        
        if "advanced" in grade["assignment_name"].lower():
            points += 1.0
        
        # BRANCH: Weight consideration
        if weight > 0.3:  # Major assignment
            total_points += points * weight * 2
            total_credits += weight * 2
        else:
            total_points += points * weight
            total_credits += weight
    
    if total_credits == 0:
        raise HTTPException(400, "Cannot calculate GPA with zero credits")
    
    gpa = total_points / total_credits
    
    # BRANCH: GPA quality assessment
    if gpa >= 3.8:
        standing = "Summa Cum Laude"
    elif gpa >= 3.5:
        standing = "Magna Cum Laude"
    elif gpa >= 3.2:
        standing = "Cum Laude"
    elif gpa >= 2.0:
        standing = "Good Standing"
    else:
        standing = "Academic Probation"
    
    return {
        "student_id": student_id,
        "gpa": round(gpa, 2),
        "standing": standing,
        "total_credits": round(total_credits, 2),
        "grades_count": len(student_grades)
    }

@router.get("/course/{course_id}/statistics")
async def course_statistics(course_id: int):
    """
    Calculate course statistics with many branches
    
    BRANCHES (15+):
    - Average calculation
    - Median calculation
    - Standard deviation
    - Pass/fail rates
    - Grade distribution
    """
    
    course_grades = [g for g in grades_db.values() if g["course_id"] == course_id]
    
    if not course_grades:
        raise HTTPException(404, "No grades for this course")
    
    percentages = [g["percentage"] for g in course_grades]
    
    # BRANCH: Calculate average
    avg = sum(percentages) / len(percentages)
    
    # BRANCH: Calculate median
    sorted_percs = sorted(percentages)
    n = len(sorted_percs)
    if n % 2 == 0:
        median = (sorted_percs[n//2 - 1] + sorted_percs[n//2]) / 2
    else:
        median = sorted_percs[n//2]
    
    # BRANCH: Pass/fail counts
    passing = sum(1 for p in percentages if p >= 60)
    failing = len(percentages) - passing
    
    # BRANCH: Grade distribution
    distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for g in course_grades:
        letter = g["letter_grade"][0]
        if letter in distribution:
            distribution[letter] += 1
    
    # BRANCH: Course difficulty assessment
    if avg >= 85:
        difficulty = "Easy"
    elif avg >= 75:
        difficulty = "Moderate"
    elif avg >= 65:
        difficulty = "Challenging"
    else:
        difficulty = "Difficult"
    
    return {
        "course_id": course_id,
        "total_students": len(course_grades),
        "average": round(avg, 2),
        "median": round(median, 2),
        "passing": passing,
        "failing": failing,
        "pass_rate": round(passing / len(course_grades) * 100, 2),
        "distribution": distribution,
        "difficulty": difficulty
    }

# Initialize with sample data
def init_grades():
    global next_grade_id
    grades_db[1] = {
        "id": 1,
        "student_id": "STU001",
        "course_id": 101,
        "assignment_name": "Midterm Exam",
        "score": 85,
        "max_score": 100,
        "weight": 0.3,
        "percentage": 85.0,
        "letter_grade": "B",
        "submitted_at": datetime.utcnow()
    }
    next_grade_id = 2

init_grades()
