from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal
from datetime import datetime

# ==============================
# 1. USER SCHEMAS
# ==============================
class UserBase(BaseModel):
    id_number: str = Field(..., description="תעודת זהות")
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    role: str = Field(default="student", description="admin / lecturer / instructor / student")
    is_miluim: bool = False
    is_active: bool = True

class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=6, description="סיסמה (לפחות 6 תווים)")

class UserResponse(UserBase):
    user_id: int

    class Config:
        from_attributes = True

class UserRoleUpdate(BaseModel):
    role: Literal["admin", "lecturer", "instructor", "student"] = Field(
        ..., description="תפקיד חדש: admin, lecturer, instructor, student"
    )


# ==============================
# 2. COLLEGE SCHEMAS
# ==============================
class CollegeBase(BaseModel):
    college_name: str

class CollegeCreate(CollegeBase):
    pass

class CollegeResponse(CollegeBase):
    college_id: int

    class Config:
        from_attributes = True


# ==============================
# 3. COURSE SCHEMAS
# ==============================
class CourseBase(BaseModel):
    college_id: int
    course_name: str
    course_code: str
    lab_work_weight: int = Field(default=100, ge=0, le=100)
    prep_report_weight: int = Field(default=0, ge=0, le=100)
    summary_report_weight: int = Field(default=0, ge=0, le=100)
    final_lab_weight: int = Field(default=0, ge=0, le=100)
    quiz_weight: int = Field(default=0, ge=0, le=100)
    is_active: bool = True

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    course_id: int

    class Config:
        from_attributes = True


# ==============================
# 4. LAB TOPIC SCHEMAS
# ==============================
class LabTopicBase(BaseModel):
    course_id: int
    topic_name: str

class LabTopicCreate(LabTopicBase):
    pass

class LabTopicResponse(LabTopicBase):
    topic_id: int

    class Config:
        from_attributes = True


# ==============================
# 5. LAB GROUP SCHEMAS
# ==============================
class LabGroupBase(BaseModel):
    course_id: int
    group_code: str
    day: str
    time: str
    instructor_id: Optional[int] = None
    lecturer_id: Optional[int] = None

class LabGroupCreate(LabGroupBase):
    pass

class LabGroupResponse(LabGroupBase):
    group_id: int

    class Config:
        from_attributes = True


# ==============================
# 6. GROUP STUDENTS SCHEMAS
# ==============================
class GroupStudentBase(BaseModel):
    group_id: int
    student_id: int
    team_code: Optional[str] = None

class GroupStudentCreate(GroupStudentBase):
    pass

class GroupStudentResponse(GroupStudentBase):
    group_id: int
    student_id: int
    team_code: Optional[str] = None

    class Config:
        from_attributes = True


# ==============================
# 7. LAB SCHEDULE SCHEMAS
# ==============================
class LabScheduleBase(BaseModel):
    group_id: int
    topic_id: int
    lab_date: datetime
    week_number: int
    session_type: str = Field(default="REGULAR", description="INTRO / REGULAR / FINAL_LAB / COMPLETION")

class LabScheduleCreate(LabScheduleBase):
    pass

class LabScheduleResponse(LabScheduleBase):
    schedule_id: int

    class Config:
        from_attributes = True


# ==============================
# 8. GRADE SCHEMAS
# ==============================
class GradeBase(BaseModel):
    schedule_id: int
    student_id: int
    attendance_status: str = Field(..., description="present / absent / miluim / justified")
    lab_work_grade: Optional[int] = Field(None, ge=0, le=100)
    prep_report_grade: Optional[int] = Field(None, ge=0, le=100)
    summary_report_grade: Optional[int] = Field(None, ge=0, le=100)
    final_calculated_grade: Optional[int] = Field(None, ge=0, le=100)
    internal_notes: str = Field(..., description="הערות פנימיות - שדה חובה לפי הסכימה")
    student_feedback: Optional[str] = None

class GradeCreate(GradeBase):
    pass

class GradeUpdate(BaseModel):
    attendance_status: Optional[str] = None
    lab_work_grade: Optional[int] = Field(None, ge=0, le=100)
    prep_report_grade: Optional[int] = Field(None, ge=0, le=100)
    summary_report_grade: Optional[int] = Field(None, ge=0, le=100)
    final_calculated_grade: Optional[int] = Field(None, ge=0, le=100)
    internal_notes: Optional[str] = None
    student_feedback: Optional[str] = None

class GradeResponse(GradeBase):
    grade_id: int

    class Config:
        from_attributes = True


# ==============================
# 9. COURSE FINAL GRADE SCHEMAS
# ==============================
class CourseFinalGradeBase(BaseModel):
    course_id: int
    student_id: int
    final_score: Optional[int] = Field(None, ge=0, le=100)
    is_approved: bool = False

class CourseFinalGradeCreate(CourseFinalGradeBase):
    pass

class CourseFinalGradeUpdate(BaseModel):
    final_score: Optional[int] = Field(None, ge=0, le=100)
    is_approved: Optional[bool] = None

class CourseFinalGradeResponse(CourseFinalGradeBase):
    enrollment_id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==============================
# 10. SWAP REQUEST SCHEMAS
# ==============================
class SwapRequestBase(BaseModel):
    current_schedule_id: int
    target_schedule_id: int
    is_team_swap: bool = True
    reason: str

class SwapRequestCreate(SwapRequestBase):
    pass

class SwapRequestReview(BaseModel):
    status: str = Field(..., description="APPROVED / REJECTED")
    reviewer_notes: Optional[str] = None

class SwapRequestResponse(SwapRequestBase):
    request_id: int
    student_id: int
    is_team_swap: bool
    status: str
    reviewed_by: Optional[int] = None
    reviewer_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================
# 11. CMS CONTENT SCHEMAS
# ==============================
class CmsContentBase(BaseModel):
    key_name: str
    content_value: str
    description: Optional[str] = None
    is_active: bool = True

class CmsContentCreate(CmsContentBase):
    pass

class CmsContentUpdate(BaseModel):
    content_value: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CmsContentResponse(CmsContentBase):
    content_id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==============================
# 12. AUTHENTICATION SCHEMAS
# ==============================
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None