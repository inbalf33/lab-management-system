from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models import User, Grade, CourseFinalGrade, LabGroup, LabSchedule, Course, group_students
from app.api.deps import get_current_user, require_roles

from typing import Optional, List, Dict, Any, Optional

router = APIRouter()

# ==========================================
# Pydantic Schemas for Grades
# ==========================================



class MessageResponse(BaseModel):
    message: str


class StudentGradeViewSchema(BaseModel):
    grade_id: int
    schedule_id: int
    attendance_status: str
    lab_work_grade: Optional[int] = None
    prep_report_grade: Optional[int] = None
    summary_report_grade: Optional[int] = None
    final_calculated_grade: Optional[float] = None
    student_feedback: Optional[str] = None 

    class Config:
        from_attributes = True

# קלט: הזנת ציון לסטודנט בודד (למשל בהתפצלות/השלמה)
class GradeIndividualSchema(BaseModel):
    schedule_id: int
    student_id: int
    attendance_status: str = Field(..., description="present / absent / miluim / justified")
    lab_work_grade: Optional[int] = Field(None, ge=0, le=100)
    prep_report_grade: Optional[int] = Field(None, ge=0, le=100)
    summary_report_grade: Optional[int] = Field(None, ge=0, le=100)
    internal_notes: str = Field(..., description="הערות פנימיות - שדה חובה")
    student_feedback: Optional[str] = None


class GradeUpdateSchema(BaseModel):
    attendance_status: Optional[str] = Field(None, description="present / absent / miluim / justified")
    lab_work_grade: Optional[int] = Field(None, ge=0, le=100)
    prep_report_grade: Optional[int] = Field(None, ge=0, le=100)
    summary_report_grade: Optional[int] = Field(None, ge=0, le=100)
    internal_notes: Optional[str] = Field(None, description="הערות פנימיות")
    student_feedback: Optional[str] = None


# קלט: הזנת ציון מרוכז לכל חברי הצוות יחד
class GradeTeamSchema(BaseModel):
    schedule_id: int
    team_code: str = Field(..., description="קוד הצוות, למשל A1")
    attendance_status: str = Field("present", description="present / absent / miluim / justified")
    lab_work_grade: Optional[int] = Field(None, ge=0, le=100)
    prep_report_grade: Optional[int] = Field(None, ge=0, le=100)
    summary_report_grade: Optional[int] = Field(None, ge=0, le=100)
    internal_notes: str = Field(..., description="הערות פנימיות לצוות")
    student_feedback: Optional[str] = None

# קלט: עדכון אצווה מרוכז לרשימת סטודנטים חופשית
class GradeBatchItem(BaseModel):
    student_id: int
    attendance_status: Optional[str] = None
    lab_work_grade: Optional[int] = Field(None, ge=0, le=100)
    prep_report_grade: Optional[int] = Field(None, ge=0, le=100)
    summary_report_grade: Optional[int] = Field(None, ge=0, le=100)
    internal_notes: Optional[str] = None
    student_feedback: Optional[str] = None


class GradeTeamBatchRequest(BaseModel):
    schedule_id: int
    team_code: str = Field(..., description="קוד הצוות, למשל A1, B1")
    attendance_status: str = Field("present", description="present / absent / miluim / justified")
    lab_work_grade: Optional[int] = Field(None, ge=0, le=100)
    prep_report_grade: Optional[int] = Field(None, ge=0, le=100)
    summary_report_grade: Optional[int] = Field(None, ge=0, le=100)
    internal_notes: Optional[str] = Field("הוזן בהזנה קבוצתית", description="הערות פנימיות")
    student_feedback: Optional[str] = None

class GradeTeamBatchRequest(BaseModel):
    schedule_id: int
    team_code: str = Field(..., description="קוד הצוות, למשל A1, B1")
    attendance_status: str = Field("present", description="present / absent / miluim / justified")
    lab_work_grade: Optional[int] = Field(None, ge=0, le=100)
    prep_report_grade: Optional[int] = Field(None, ge=0, le=100)
    summary_report_grade: Optional[int] = Field(None, ge=0, le=100)
    internal_notes: Optional[str] = Field("הוזן בהזנה קבוצתית", description="הערות פנימיות")
    student_feedback: Optional[str] = None
   
class GradeBatchRequest(BaseModel):
    schedule_id: int
    grades: List[GradeBatchItem]

# קלט: פתיחה או נעילה של ציוני סוף סמסטר (Publish)
class GradesPublishRequest(BaseModel):
    course_id: int
    is_published: bool = Field(..., description="True לפתיחה לצפיית סטודנטים, False לנעילה")


# ==========================================
# Helper Function: Calculate Weighted Grade & Update student course final grade
# ==========================================

def calculate_final_grade(grade_item: Dict[str, Any], course: Course) -> Optional[float]:
    """חישוב ציון משוקלל למפגש לפי משקלי הקורס"""
    lw = grade_item.get("lab_work_grade")
    pr = grade_item.get("prep_report_grade")
    sr = grade_item.get("summary_report_grade")
    
    if lw is None and pr is None and sr is None:
        return None
        
    lw_val = lw if lw is not None else 0
    pr_val = pr if pr is not None else 100 
    sr_val = sr if sr is not None else 100 
    
    total_weight = course.lab_work_weight + course.prep_report_weight + course.summary_report_weight
    if total_weight <= 0:
        return float(lw_val)
        
    weighted_sum = (
        (lw_val * course.lab_work_weight) +
        (pr_val * course.prep_report_weight) +
        (sr_val * course.summary_report_weight)
    )
    return round(weighted_sum / total_weight, 2)


def update_student_course_final_grade(db: Session, student_id: int, course_id: int):
    """חישוב דינאמי ועדכון הציון הסופי של סטודנט בקורס ספציפי על בסיס כל המפגשים שהוזנו עד כה"""
    groups = db.query(LabGroup).filter(LabGroup.course_id == course_id).all()
    group_ids = [g.group_id for g in groups]
    if not group_ids:
        return
        
    schedules = db.query(LabSchedule).filter(LabSchedule.group_id.in_(group_ids)).all()
    schedule_ids = [s.schedule_id for s in schedules]
    if not schedule_ids:
        return

    student_grades = db.query(Grade).filter(
        Grade.student_id == student_id,
        Grade.schedule_id.in_(schedule_ids),
        Grade.final_calculated_grade.isnot(None)
    ).all()

    if not student_grades:
        return

    total_score = sum(g.final_calculated_grade for g in student_grades)
    # המרה למספר שלם כי ה-Schema דורש int
    current_final_score = int(round(total_score / len(student_grades)))

    final_grade_record = db.query(CourseFinalGrade).filter(
        CourseFinalGrade.course_id == course_id,
        CourseFinalGrade.student_id == student_id
    ).first()

    if final_grade_record:
        final_grade_record.final_score = current_final_score
        final_grade_record.updated_at = datetime.now(timezone.utc)
    else:
        new_final_record = CourseFinalGrade(
            course_id=course_id,
            student_id=student_id,
            final_score=current_final_score,
            is_approved=False,
            updated_at=datetime.now(timezone.utc)
        )
        db.add(new_final_record)



# ==========================================
# Endpoints
# ==========================================



# Get all grades and feedback for the currently logged-in student (only if published)

@router.get("/my-grades", response_model=List[StudentGradeViewSchema], status_code=status.HTTP_200_OK)
def get_my_grades(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can view their personal grades here")

    # 1. שליפת מזהי הקורסים שבהם הציונים הסופיים של הסטודנט מאושרים לפרסום
    approved_course_ids = db.query(CourseFinalGrade.course_id).filter(
        CourseFinalGrade.student_id == current_user.user_id,
        CourseFinalGrade.is_approved == True
    ).subquery()

    # 2. שליפת קבוצות המעבדה ששייכות לאותם קורסים מאושרים
    approved_groups = db.query(LabGroup.group_id).filter(
        LabGroup.course_id.in_(approved_course_ids)
    ).subquery()

    # 3. שליפת המפגשים ששייכים לקבוצות האלה
    approved_schedules = db.query(LabSchedule.schedule_id).filter(
        LabSchedule.group_id.in_(approved_groups)
    ).subquery()

    # 4. שליפת הציונים של הסטודנט אך ורק עבור מפגשים אלו
    grades = db.query(Grade).filter(
        Grade.student_id == current_user.user_id,
        Grade.schedule_id.in_(approved_schedules)
    ).all()

    return grades

@router.get("/my-completed-schedule-ids", response_model=List[int], status_code=status.HTTP_200_OK)
def get_my_completed_schedule_ids(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access this")

  
    completed_schedules = db.query(Grade.schedule_id).filter(
        Grade.student_id == current_user.user_id
    ).all()

    return [s[0] for s in completed_schedules]

# Get final course grades for the currently logged-in student (only if approved/published)

@router.get("/final/my", status_code=status.HTTP_200_OK)
def get_my_final_grades(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can view their final grades here")

    # שליפת הציונים הסופיים של הסטודנט אך ורק אם הם מאושרים לפרסום
    final_grades = db.query(CourseFinalGrade).filter(
        CourseFinalGrade.student_id == current_user.user_id,
        CourseFinalGrade.is_approved == True
    ).all()
    
    return final_grades


# Get full grades table (staff/admin only)

@router.get("", status_code=status.HTTP_200_OK)
def get_grades_table(
    group_id: Optional[int] = Query(None, description="סינון לפי מזהה קבוצת מעבדה"),
    student_id: Optional[int] = Query(None, description="סינון לפי מזהה סטודנט"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    """
    שליפת טבלת ציונים דינאמית לסגל, עם אפשרות סינון אופציונלית לפי קבוצה ו/או סטודנט.
    """
    query = db.query(Grade)
    
    # סינון דינאמי לפי קבוצת מעבדה (דרך שיוך למפגשים של הקבוצה)
    if group_id is not None:
        schedule_ids = db.query(LabSchedule.schedule_id).filter(LabSchedule.group_id == group_id).subquery()
        query = query.filter(Grade.schedule_id.in_(schedule_ids))
        
    # סינון דינאמי לפי סטודנט ספציפי
    if student_id is not None:
        query = query.filter(Grade.student_id == student_id)
        
    grades = query.all()
    return grades

# Get dynamic final grades table for staff with optional filters (course, group, student)

@router.get("/final/", status_code=status.HTTP_200_OK)
def get_final_grades_table(
    course_id: Optional[int] = Query(None, description="סינון לפי מזהה קורס"),
    group_id: Optional[int] = Query(None, description="סינון לפי מזהה קבוצת מעבדה"),
    student_id: Optional[int] = Query(None, description="סינון לפי מזהה סטודנט"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    """
    שפת טבלת הציונים הסופיים לקורסים בצורה דינאמית לסגל, כולל חישוב אוטומטי של המצב הנוכחי.
    """
    # אם סונן קורס ספציפי (או קבוצה ששייכת לקורס), נדאג שכל הסטודנטים הרלוונטיים יחושבו ויעודכנו בטבלה קודם לכן
    target_course_ids = set()
    if course_id is not None:
        target_course_ids.add(course_id)
    elif group_id is not None:
        group = db.query(LabGroup).filter(LabGroup.group_id == group_id).first()
        if group:
            target_course_ids.add(group.course_id)

    for cid in target_course_ids:
        # איתור כל הסטודנטים שמשוייכים לקבוצות בקורס הזה
        groups = db.query(LabGroup).filter(LabGroup.course_id == cid).all()
        g_ids = [g.group_id for g in groups]
        if g_ids:
            schedules = db.query(LabSchedule.schedule_id).filter(LabSchedule.group_id.in_(g_ids)).subquery()
            active_student_ids = db.query(Grade.student_id).filter(Grade.schedule_id.in_(schedules)).distinct().all()
            
            for (s_id,) in active_student_ids:
                update_student_course_final_grade(db, s_id, cid)
    
    db.commit()

    query = db.query(CourseFinalGrade)
    
    if course_id is not None:
        query = query.filter(CourseFinalGrade.course_id == course_id)
        
    if student_id is not None:
        query = query.filter(CourseFinalGrade.student_id == student_id)
        
    if group_id is not None:
        schedules = db.query(LabSchedule.schedule_id).filter(LabSchedule.group_id == group_id).subquery()
        student_ids_in_group = db.query(Grade.student_id).filter(Grade.schedule_id.in_(schedules)).distinct().subquery()
        query = query.filter(CourseFinalGrade.student_id.in_(student_ids_in_group))

    final_grades = query.all()
    return final_grades


@router.post("", status_code=status.HTTP_201_CREATED)
def create_or_update_individual_grade(
    grade_data: GradeIndividualSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    # שליפת המפגש והקורס כדי לדעת את המשקלים
    schedule = db.query(LabSchedule).filter(LabSchedule.schedule_id == grade_data.schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule session not found")
    
    group = db.query(LabGroup).filter(LabGroup.group_id == schedule.group_id).first()
    course = db.query(Course).filter(Course.course_id == group.course_id).first() if group else None
    
    # חישוב הציון המשוקלל
    calculated = calculate_final_grade(grade_data.model_dump(), course) if course else None

    # בדיקה האם כבר קיים ציון לסטודנט במפגש הזה
    existing = db.query(Grade).filter(
        Grade.schedule_id == grade_data.schedule_id,
        Grade.student_id == grade_data.student_id
    ).first()

    if existing:
        # עדכון השורה הקיימת
        existing.attendance_status = grade_data.attendance_status
        existing.lab_work_grade = grade_data.lab_work_grade
        existing.prep_report_grade = grade_data.prep_report_grade
        existing.summary_report_grade = grade_data.summary_report_grade
        existing.final_calculated_grade = calculated
        existing.internal_notes = grade_data.internal_notes
        existing.student_feedback = grade_data.student_feedback
        
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # יצירת שורה חדשה אם לא הייתה קיימת
        new_grade = Grade(
            schedule_id=grade_data.schedule_id,
            student_id=grade_data.student_id,
            attendance_status=grade_data.attendance_status,
            lab_work_grade=grade_data.lab_work_grade,
            prep_report_grade=grade_data.prep_report_grade,
            summary_report_grade=grade_data.summary_report_grade,
            final_calculated_grade=calculated,
            internal_notes=grade_data.internal_notes,
            student_feedback=grade_data.student_feedback
        )
        db.add(new_grade)
        db.commit()
        db.refresh(new_grade)
        return new_grade


# Batch update or create grades for all students in a specific team for a given session
@router.post("/team", status_code=status.HTTP_201_CREATED)
def create_or_update_team_grades(
    team_data: GradeTeamBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    # 1. בדיקה שהמפגש קיים
    schedule = db.query(LabSchedule).filter(LabSchedule.schedule_id == team_data.schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule session not found")
    
    # 2. שליפת הקבוצה והקורס לצורך חישוב הציון הסופי
    group = db.query(LabGroup).filter(LabGroup.group_id == schedule.group_id).first()
    course = db.query(Course).filter(Course.course_id == group.course_id).first() if group else None

    # 3. איתור כל הסטודנטים השייכים לצוות הספציפי בתוך הקבוצה הזו
    team_students = db.query(group_students).filter(
        group_students.c.group_id == schedule.group_id,
        group_students.c.team_code == team_data.team_code
    ).all()

    if not team_students:
        raise HTTPException(status_code=404, detail=f"No students found for team {team_data.team_code} in this group")

    # הכנת מילון הציון לצורך חישוב משוקלל
    grade_input_dict = {
        "lab_work_grade": team_data.lab_work_grade,
        "prep_report_grade": team_data.prep_report_grade,
        "summary_report_grade": team_data.summary_report_grade
    }
    calculated = calculate_final_grade(grade_input_dict, course) if course else None

    processed_count = 0

    # 4. מעבר על כל סטודנט בצוות וביצוע Upsert (עדכון אם קיים, יצירה אם לא)
    for ts in team_students:
        existing = db.query(Grade).filter(
            Grade.schedule_id == team_data.schedule_id,
            Grade.student_id == ts.student_id
        ).first()

        if existing:
            existing.attendance_status = team_data.attendance_status
            existing.lab_work_grade = team_data.lab_work_grade
            existing.prep_report_grade = team_data.prep_report_grade
            existing.summary_report_grade = team_data.summary_report_grade
            existing.final_calculated_grade = calculated
            if team_data.internal_notes:
                existing.internal_notes = team_data.internal_notes
            if team_data.student_feedback:
                existing.student_feedback = team_data.student_feedback
            
            # עדכון הציון הסופי הכולל של הסטודנט בקורס
            if course:
                update_student_course_final_grade(db, ts.student_id, course.course_id)
        else:
            new_g = Grade(
                schedule_id=team_data.schedule_id,
                student_id=ts.student_id,
                attendance_status=team_data.attendance_status,
                lab_work_grade=team_data.lab_work_grade,
                prep_report_grade=team_data.prep_report_grade,
                summary_report_grade=team_data.summary_report_grade,
                final_calculated_grade=calculated,
                internal_notes=team_data.internal_notes,
                student_feedback=team_data.student_feedback
            )
            db.add(new_g)
            db.flush() # כדי שה-ID יהיה זמין אם צריך
            
            # עדכון הציון הסופי הכולל של הסטודנט בקורס
            if course:
                update_student_course_final_grade(db, ts.student_id, course.course_id)

        processed_count += 1

    db.commit()
    return {"message": f"Successfully processed grades for {processed_count} students in team {team_data.team_code}"}

# Update an existing grade record (staff/admin only)
@router.put("/{grade_id}")
def update_grade(
    grade_id: int,
    grade_data: GradeUpdateSchema, 
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    grade_record = db.query(Grade).filter(Grade.grade_id == grade_id).first()
    if not grade_record:
        raise HTTPException(status_code=404, detail="Grade record not found")

    schedule = db.query(LabSchedule).filter(LabSchedule.schedule_id == grade_record.schedule_id).first()
    group = db.query(LabGroup).filter(LabGroup.group_id == schedule.group_id).first() if schedule else None
    course = db.query(Course).filter(Course.course_id == group.course_id).first() if group else None

    update_data = grade_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(grade_record, key, value)

    # חישוב מחדש של הציון המשוקלל בעדכון
    grade_dict = {
        "lab_work_grade": grade_record.lab_work_grade,
        "prep_report_grade": grade_record.prep_report_grade,
        "summary_report_grade": grade_record.summary_report_grade
    }
    if course:
        grade_record.final_calculated_grade = calculate_final_grade(grade_dict, course)
        update_student_course_final_grade(db, grade_record.student_id, course.course_id)

    db.commit()
    db.refresh(grade_record)
    return grade_record


# Batch update grades for multiple students in a session (staff/admin only)
@router.post("/batch", status_code=status.HTTP_201_CREATED)
def create_or_update_batch_grades(
    batch_data: GradeBatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    schedule = db.query(LabSchedule).filter(LabSchedule.schedule_id == batch_data.schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule session not found")
    
    group = db.query(LabGroup).filter(LabGroup.group_id == schedule.group_id).first()
    course = db.query(Course).filter(Course.course_id == group.course_id).first() if group else None

    processed_count = 0
    for item in batch_data.grades:
        # בדיקה האם כבר קיים ציון לסטודנט במפגש הזה (לע עדכון או יצירה)
        existing = db.query(Grade).filter(
            Grade.schedule_id == batch_data.schedule_id,
            Grade.student_id == item.student_id
        ).first()

        calculated = calculate_final_grade(item.model_dump(), course) if course else None

        if existing:
            existing.attendance_status = item.attendance_status or existing.attendance_status
            existing.lab_work_grade = item.lab_work_grade
            existing.prep_report_grade = item.prep_report_grade
            existing.summary_report_grade = item.summary_report_grade
            existing.final_calculated_grade = calculated
            if item.internal_notes:
                existing.internal_notes = item.internal_notes
            if item.student_feedback:
                existing.student_feedback = item.student_feedback
        else:
            new_g = Grade(
                schedule_id=batch_data.schedule_id,
                student_id=item.student_id,
                attendance_status=item.attendance_status or "present",
                lab_work_grade=item.lab_work_grade,
                prep_report_grade=item.prep_report_grade,
                summary_report_grade=item.summary_report_grade,
                final_calculated_grade=calculated,
                internal_notes=item.internal_notes or "הוזן בעדכון מרוכז",
                student_feedback=item.student_feedback
            )
            db.add(new_g)
        processed_count += 1

    db.commit()
    return {"message": f"Successfully processed {processed_count} grades in batch"}


# Delete a specific grade record (staff/admin only)
@router.delete("/{grade_id}", status_code=status.HTTP_200_OK)
def delete_grade(
    grade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    grade_record = db.query(Grade).filter(Grade.grade_id == grade_id).first()
    if not grade_record:
        raise HTTPException(status_code=404, detail="Grade record not found")

    db.delete(grade_record)
    db.commit()
    return {"message": f"Grade record {grade_id} deleted successfully"}


# Publish or lock final course grades for students (lecturer/admin only)

@router.post("/publish", status_code=status.HTTP_200_OK)
def publish_grades(
    publish_data: GradesPublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    # ודא שכל הציונים הסופיים של הסטודנטים בקורס מחושבים ומעודכנים בטבלה לפני הפרסום
    groups = db.query(LabGroup).filter(LabGroup.course_id == publish_data.course_id).all()
    group_ids = [g.group_id for g in groups]
    if group_ids:
        schedules = db.query(LabSchedule.schedule_id).filter(LabSchedule.group_id.in_(group_ids)).subquery()
        active_student_ids = db.query(Grade.student_id).filter(Grade.schedule_id.in_(schedules)).distinct().all()
        for (s_id,) in active_student_ids:
            update_student_course_final_grade(db, s_id, publish_data.course_id)

    # 1. עדכון סטטוס הפרסום בטבלת הציונים הסופיים של הקורס
    final_grades = db.query(CourseFinalGrade).filter(CourseFinalGrade.course_id == publish_data.course_id).all()
    
    for fg in final_grades:
        fg.is_approved = publish_data.is_published
        fg.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    status_text = "published" if publish_data.is_published else "locked"
    return {"message": f"All final grades successfully {status_text} for course {publish_data.course_id}"}

