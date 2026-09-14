from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base

# 5. Group Students (Junction Table for Many-to-Many)
group_students = Table(
    "group_students",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("lab_groups.group_id", ondelete="CASCADE"), primary_key=True),
    Column("student_id", Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("team_code", String(255), nullable=True),
)

# 1. Colleges
class College(Base):
    __tablename__ = "colleges"

    college_id = Column(Integer, primary_key=True, index=True)
    college_name = Column(String(255), nullable=False)

    # Relationships
    courses = relationship("Course", back_populates="college", cascade="all, delete-orphan")

# 2. Courses
class Course(Base):
    __tablename__ = "courses"

    course_id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey("colleges.college_id", ondelete="CASCADE"), nullable=False)
    course_name = Column(String(255), nullable=False)
    course_code = Column(String(255), nullable=False)
    lab_work_weight = Column(Integer, default=100)
    prep_report_weight = Column(Integer, default=0)
    summary_report_weight = Column(Integer, default=0)
    final_lab_weight = Column(Integer, default=0)
    quiz_weight = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Relationships
    college = relationship("College", back_populates="courses")
    lab_groups = relationship("LabGroup", back_populates="course", cascade="all, delete-orphan")
    lab_topics = relationship("LabTopic", back_populates="course", cascade="all, delete-orphan")
    final_grades = relationship("CourseFinalGrade", back_populates="course", cascade="all, delete-orphan")

# 3. Users
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    id_number = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    password = Column(String(255), nullable=True)
    role = Column(String(255), nullable=False)
    is_miluim = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    student_groups = relationship("LabGroup", secondary=group_students, back_populates="students")
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")
    final_grades = relationship("CourseFinalGrade", back_populates="student", cascade="all, delete-orphan")
    swap_requests = relationship("SwapRequest", foreign_keys="[SwapRequest.student_id]", back_populates="student", cascade="all, delete-orphan")

# 4. Lab Groups
class LabGroup(Base):
    __tablename__ = "lab_groups"

    group_id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    group_code = Column(String(255), nullable=False)
    day = Column(String(255), nullable=False)
    time = Column(String(255), nullable=False)
    instructor_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    lecturer_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)

    # Relationships
    course = relationship("Course", back_populates="lab_groups")
    instructor = relationship("User", foreign_keys=[instructor_id])
    lecturer = relationship("User", foreign_keys=[lecturer_id])
    students = relationship("User", secondary=group_students, back_populates="student_groups")
    schedules = relationship("LabSchedule", back_populates="group", cascade="all, delete-orphan")

# 6. Lab Topics
class LabTopic(Base):
    __tablename__ = "lab_topics"

    topic_id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    topic_name = Column(String(255), nullable=False)

    # Relationships
    course = relationship("Course", back_populates="lab_topics")
    schedules = relationship("LabSchedule", back_populates="topic", cascade="all, delete-orphan")

# 7. Lab Schedules
class LabSchedule(Base):
    __tablename__ = "lab_schedules"

    schedule_id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("lab_groups.group_id", ondelete="CASCADE"), nullable=False)
    topic_id = Column(Integer, ForeignKey("lab_topics.topic_id", ondelete="CASCADE"), nullable=False)
    lab_date = Column(DateTime, nullable=False)
    week_number = Column(Integer, nullable=False)
    session_type = Column(String(255), default="REGULAR")

    # Relationships
    group = relationship("LabGroup", back_populates="schedules")
    topic = relationship("LabTopic", back_populates="schedules")
    grades = relationship("Grade", back_populates="schedule", cascade="all, delete-orphan")
    current_swap_requests = relationship("SwapRequest", foreign_keys="[SwapRequest.current_schedule_id]", back_populates="current_schedule")
    target_swap_requests = relationship("SwapRequest", foreign_keys="[SwapRequest.target_schedule_id]", back_populates="target_schedule")

# 8. Grades
class Grade(Base):
    __tablename__ = "grades"

    grade_id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("lab_schedules.schedule_id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    attendance_status = Column(String(255), nullable=False)
    lab_work_grade = Column(Integer, nullable=True)
    prep_report_grade = Column(Integer, nullable=True)
    summary_report_grade = Column(Integer, nullable=True)
    final_calculated_grade = Column(Integer, nullable=True)
    internal_notes = Column(Text, nullable=False)
    student_feedback = Column(Text, nullable=True)

    # Relationships
    schedule = relationship("LabSchedule", back_populates="grades")
    student = relationship("User", back_populates="grades")

# 9. Course Final Grades
class CourseFinalGrade(Base):
    __tablename__ = "course_final_grades"

    enrollment_id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    final_score = Column(Integer, nullable=True)
    is_approved = Column(Boolean, default=False)
    updated_at = Column(DateTime, nullable=True)

    # Relationships
    course = relationship("Course", back_populates="final_grades")
    student = relationship("User", back_populates="final_grades")

# 10. Swap Requests
class SwapRequest(Base):
    __tablename__ = "swap_requests"

    request_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    current_schedule_id = Column(Integer, ForeignKey("lab_schedules.schedule_id", ondelete="CASCADE"), nullable=False)
    target_schedule_id = Column(Integer, ForeignKey("lab_schedules.schedule_id", ondelete="CASCADE"), nullable=False)
    is_team_swap = Column(Boolean, default=True)
    status = Column(String(255), default="PENDING")
    reason = Column(Text, nullable=False)
    reviewed_by = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)

    # Relationships
    student = relationship("User", foreign_keys=[student_id], back_populates="swap_requests")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    current_schedule = relationship("LabSchedule", foreign_keys=[current_schedule_id], back_populates="current_swap_requests")
    target_schedule = relationship("LabSchedule", foreign_keys=[target_schedule_id], back_populates="target_swap_requests")

# 11. CMS Content
class CmsContent(Base):
    __tablename__ = "cms_content"

    content_id = Column(Integer, primary_key=True, index=True)
    key_name = Column(String(255), unique=True, nullable=False)
    content_value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, nullable=True)