import io
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
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
# Pydantic Schemas for Labs
# ==========================================

class MessageResponse(BaseModel):
    message: str


# תצוגה: פרטי קבוצת מעבדה מלאים
class LabGroupResponseSchema(BaseModel):
    group_id: int
    course_id: int
    group_code: str
    day: str
    time: str
    instructor_id: Optional[int] = None
    lecturer_id: Optional[int] = None

    class Config:
        from_attributes = True


# קלט: יצירת קבוצת מעבדה חדשה
class LabGroupCreateSchema(BaseModel):
    course_id: int
    group_code: str = Field(..., description="קוד הקבוצה, למשל ערב-1")
    day: str = Field(..., description="יום הפעילות, למשל ראשון")
    time: str = Field(..., description="שעת הפעילות, למשל 16:00")
    instructor_id: Optional[int] = Field(None, description="מזהה המדריך")
    lecturer_id: Optional[int] = Field(None, description="מזהה המרצה")


# קלט: עדכון פרטי קבוצת מעבדה קיימת
class LabGroupUpdateSchema(BaseModel):
    course_id: Optional[int] = None
    group_code: Optional[str] = None
    day: Optional[str] = None
    time: Optional[str] = None
    instructor_id: Optional[int] = None
    lecturer_id: Optional[int] = None


# תצוגה: פרטי סטודנט בתוך קבוצת מעבדה (כולל קוד צוות)
class LabStudentViewSchema(BaseModel):
    user_id: int
    id_number: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    is_miluim: bool
    team_code: Optional[str] = None

    class Config:
        from_attributes = True


# קלט: שיוך סטודנט בודד למעבדה (לפי ת"ז או מזהה)
class AddStudentToLabSchema(BaseModel):
    id_number: str = Field(..., description="תעודת הזהות של הסטודנט")
    team_code: Optional[str] = Field(None, description="קוד צוות אופציונלי בעת השיוך")


# קלט: עדכון קוד צוות לסטודנט בודד
class UpdateStudentTeamSchema(BaseModel):
    team_code: Optional[str] = Field(None, description="קוד הצוות החדש לסטודנט")


# קלט: עדכון מרוכז של קודי צוות לכלל הסטודנטים בקבוצה
class BulkUpdateTeamsSchema(BaseModel):
    students_teams: List[Dict[str, Any]] = Field(
        ..., 
        description="רשימה של אובייקטים המכילים id_number (ת.ז) ו-team_code (קוד צוות חדש)"
    )

class StudentTeamAssignment(BaseModel):
    id_number: str
    team_code: Optional[str] = None

class BulkUpdateTeamsSchema(BaseModel):
    assignments: List[StudentTeamAssignment] = Field(..., description="רשימת שיבוצי צוותים לפי תעודת זהות")


# ==========================================
# Helper Functions
# ==========================================

def get_lab_group_or_404(db: Session, group_id: int) -> LabGroup:
    """מחזיר את קבוצת המעבדה או זורק שגיאת 404 אם אינה קיימת"""
    group = db.query(LabGroup).filter(LabGroup.group_id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"קבוצת מעבדה עם מזהה {group_id} לא נמצאה"
        )
    return group

def verify_lab_access(group: LabGroup, current_user: User):
    """מוודא שלמשתמש יש הרשאה לגשת לקבוצת המעבדה הספציפית (אדמין או משוייך לקבוצה)"""
    if current_user.role == "admin":
        return
    if group.lecturer_id != current_user.user_id and group.instructor_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="אין לך הרשאה לגשת לקבוצת מעבדה זו"
        )
    
def get_user_by_id_number(db: Session, id_number: str) -> User:
    """מחזיר משתמש לפי תעודת זהות או זורק שגיאת 404"""
    user = db.query(User).filter(User.id_number == id_number).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"סטודנט עם תעודת זהות {id_number} לא נמצא במערכת"
        )
    return user


# ==========================================
# Endpoints
# ==========================================

# GET all lab groups and their settings

@router.get("/", response_model=List[LabGroupResponseSchema])
def get_all_lab_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    """שולף רשימה של קבוצות המעבדה הרלוונטיות למשתמש (אדמין רואה הכל, סגל רואה את שלהם)"""
    if current_user.role == "admin":
        groups = db.query(LabGroup).all()
    else:
        groups = db.query(LabGroup).filter(
            (LabGroup.lecturer_id == current_user.user_id) | 
            (LabGroup.instructor_id == current_user.user_id)
        ).all()
    return groups


# Create a new lab group

@router.post("/", response_model=LabGroupResponseSchema, status_code=status.HTTP_201_CREATED)
def create_lab_group(
    group_data: LabGroupCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    """יוצר קבוצת מעבדה חדשה לפי קורס, קוד קבוצה, יום ושעה"""
    # בדיקה האם הקורס קיים
    course = db.query(Course).filter(Course.course_id == group_data.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"קורס עם מזהה {group_data.course_id} לא נמצא"
        )

    new_group = LabGroup(
        course_id=group_data.course_id,
        group_code=group_data.group_code,
        day=group_data.day,
        time=group_data.time,
        instructor_id=group_data.instructor_id,
        lecturer_id=group_data.lecturer_id
    )
    
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group


# Update an existing lab group's details

@router.put("/{id}", response_model=LabGroupResponseSchema)
def update_lab_group(
    id: int,
    group_data: LabGroupUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    """מעדכן את פרטיה של קבוצת מעבדה קיימת (שעות, ימים, מדריכים וכו')"""
    group = get_lab_group_or_404(db, id)
    verify_lab_access(group, current_user)

    update_data = group_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(group, key, value)

    db.commit()
    db.refresh(group)
    return group


# Delete or close a lab group
@router.delete("/{id}", response_model=MessageResponse)
def delete_lab_group(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """מוחק או סוגר קבוצת מעבדה מהמערכת (לשימוש מנהלים בלבד)"""
    group = get_lab_group_or_404(db, id)

    db.delete(group)
    db.commit()
    return {"message": f"קבוצת המעבדה עם מזהה {id} נמחקה בהצלחה"}


# ==========================================
# 2. Lab Students Endpoints
# ==========================================

# # Get all students enrolled in a specific lab group

# @router.get("/{lab_id}/students", response_model=List[LabStudentViewSchema])
# def get_lab_students(
#     lab_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
# ):
#     """רשימת הסטודנטים הרשומים לאותה מעבדה"""
#     group = get_lab_group_or_404(db, lab_id)
#     verify_lab_access(group, current_user)
    
#     # שליפת הסטודנטים מתוך טבלת הקשר (group_students) יחד עם קוד הצוות שלהם
#     students_query = db.query(
#         User.user_id,
#         User.id_number,
#         User.first_name,
#         User.last_name,
#         User.email,
#         User.is_miluim,
#         group_students.c.team_code
#     ).join(
#         group_students, User.user_id == group_students.c.student_id
#     ).filter(
#         group_students.c.group_id == lab_id
#     ).all()

#     # המרה לפורמט שהסכימה מצפה לו
#     result = []
#     for s in students_query:
#         result.append({
#             "user_id": s.user_id,
#             "id_number": s.id_number,
#             "first_name": s.first_name,
#             "last_name": s.last_name,
#             "email": s.email,
#             "is_miluim": s.is_miluim,
#             "team_code": s.team_code
#         })
#     return result


@router.get("/students", response_model=List[LabStudentViewSchema])
def get_all_or_filtered_students(
    lab_id: Optional[int] = Query(None, description="סינון לפי מזהה קבוצת מעבדה ספציפית"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    """
    שליפת רשימת סטודנטים:
    - אדמין: רואה את כולם (או סינון לפי lab_id אם התקבל).
    - מרצה/מדריך: רואה רק את הסטודנטים בקבוצות המעבדה המשויכות אליו (או סינון מדויק אם התקבל lab_id תקין).
    """
    
    # בסיס השאילתה - שליפת משתמשים מטבלת הקשר יחד עם פרטי המעבדה, הצוות וקוד הקבוצה
    query = db.query(
        User.user_id,
        User.id_number,
        User.first_name,
        User.last_name,
        User.email,
        User.is_miluim,
        group_students.c.team_code,
        group_students.c.group_id,
        LabGroup.group_code  # הוספת קוד הקבוצה מהטבלה
    ).join(
        group_students, User.user_id == group_students.c.student_id
    ).join(
        LabGroup, group_students.c.group_id == LabGroup.group_id  # חיבור לטבלת המעבדות כדי לשלוף את ה-group_code
    )

    # סינון לפי הרשאות משתמש (נשמר בדיוק כמו שהיה!)
    if current_user.role in ["lecturer", "instructor"]:
        authorized_lab_ids = [g.group_id for g in current_user.lab_groups]
        
        if lab_id:
            if lab_id not in authorized_lab_ids:
                raise HTTPException(status_code=403, detail="אין הרשאה לצפות בסטודנטים של מעבדה זו")
            query = query.filter(group_students.c.group_id == lab_id)
        else:
            query = query.filter(group_students.c.group_id.in_(authorized_lab_ids))
    
    else: # אדמין
        if lab_id:
            query = query.filter(group_students.c.group_id == lab_id)

    students_query = query.all()

    # המרה לפורמט שהסכימה מצפה לו (כולל group_code)
    result = []
    seen_students = set() # למניעת כפילויות במידת הצורך
    
    for s in students_query:
        result.append({
            "user_id": s.user_id,
            "id_number": s.id_number,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "email": s.email,
            "is_miluim": s.is_miluim,
            "team_code": s.team_code,
            "lab_id": s.group_id,
            "group_code": s.group_code  # מועבר החוצה כדי שה-Frontend יציג את שם הקבוצה (כמו C-A1)
        })
        
    return result

# Get specific student details within a lab group

@router.get("/{lab_id}/students/{student_id}", response_model=LabStudentViewSchema)
def get_lab_student_by_id(
    lab_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    """קבלת סטודנט ספציפי לפי מזהה (או ת.ז) הרשום למעבדה"""
    group = get_lab_group_or_404(db, lab_id)
    verify_lab_access(group, current_user)
    
    student_info = db.query(
        User.user_id,
        User.id_number,
        User.first_name,
        User.last_name,
        User.email,
        User.is_miluim,
        group_students.c.team_code
    ).join(
        group_students, User.user_id == group_students.c.user_id
    ).filter(
        group_students.c.group_id == lab_id,
        User.user_id == student_id
    ).first()

    if not student_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"הסטודנט לא נמצא רשום בקבוצת מעבדה זו"
        )

    return {
        "user_id": student_info.user_id,
        "id_number": student_info.id_number,
        "first_name": student_info.first_name,
        "last_name": student_info.last_name,
        "email": student_info.email,
        "is_miluim": student_info.is_miluim,
        "team_code": student_info.team_code
    }


# Enroll or assign a single student to a lab group

@router.post("/{lab_id}/students", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def add_student_to_lab(
    lab_id: int,
    student_data: AddStudentToLabSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    """הוספה או העברת סטודנט בודד למעבדה (לפי ת"ז)"""
    group = get_lab_group_or_404(db, lab_id)
    verify_lab_access(group, current_user)
    
    user = get_user_by_id_number(db, student_data.id_number)

    # 1. בדיקה האם הסטודנט כבר רשום *בדיוק* לאותה קבוצה
    existing_link = db.execute(
        group_students.select().where(
            (group_students.c.group_id == lab_id) & 
            (group_students.c.student_id == user.user_id)
        )
    ).first()

    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"הסטודנט עם ת.ז {student_data.id_number} כבר רשום לקבוצת מעבדה זו"
        )

    # 2. אם הוא רשום לקבוצה *אחרת*, נמוק את השיוך הישן שלו כדי לעדכן אותו לקבוצה החדשה
    db.execute(
        group_students.delete().where(
            group_students.c.student_id == user.user_id
        )
    )

    # 3. הוספה לקבוצה החדשה (עם קוד הצוות אם קיים)
    db.execute(
        group_students.insert().values(
            group_id=lab_id,
            student_id=user.user_id,
            team_code=student_data.team_code
        )
    )
    db.commit()
    return {"message": f"הסטודנט שויך בהצלחה לקבוצת המעבדה"}


# Remove a student's enrollment from a lab group

@router.delete("/{lab_id}/students/{student_id}", response_model=MessageResponse)
def remove_student_from_lab(
    lab_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    """הסרת שיוך סטודנט ספציפי מקבוצת מעבדה"""
    group = get_lab_group_or_404(db, lab_id)
    verify_lab_access(group, current_user)

    # בדיקה האם השיוך קיים
    existing_link = db.execute(
        group_students.select().where(
            (group_students.c.group_id == lab_id) & 
            (group_students.c.student_id == student_id)
        )
    ).first()

    if not existing_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"הסטודנט אינו רשום בקבוצת מעבדה זו"
        )

    # מחיקה מטבלת הקשר
    db.execute(
        group_students.delete().where(
            (group_students.c.group_id == lab_id) & 
            (group_students.c.student_id == student_id)
        )
    )
    db.commit()
    return {"message": f"הסטודנט הוסר בהצלחה מקבוצת המעבדה"}


# ==========================================
# 3. Excel Import & Teams Endpoints
# ==========================================


# Upload an Excel file for bulk student import and lab assignment

@router.post("/{lab_id}/students/import-excel", response_model=MessageResponse)
def import_lab_students_excel(
    lab_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    """העלאת קובץ אקסל לייבוא ושיבוץ מרוכז של סטודנטים לקבוצת מעבדה"""
    group = get_lab_group_or_404(db, lab_id)
    verify_lab_access(group, current_user)
    
    try:
        contents = file.file.read()
        df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"שגיאה בקריאת קובץ האקסל: {str(e)}"
        )
    
    imported_count = 0
    for _, row in df.iterrows():
        # עמודה A: ת.ז, עמודה B: שם משפחה, עמודה C: שם פרטי
        id_number = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        last_name = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
        first_name = str(row.iloc[2]).strip() if len(row) > 2 and pd.notna(row.iloc[2]) else ""
        
        if not id_number or id_number == "nan":
            continue
        
        # בדיקה האם הסטודנט קיים בטבלת ה-users, ואם לא – יצירה אוטומטית שלו
        user = db.query(User).filter(User.id_number == id_number).first()
        if not user:
            user = User(
                id_number=id_number,
                first_name=first_name,
                last_name=last_name,
                role="student",
                is_active=True
            )
            db.add(user)
            db.flush() # כדי לקבל את ה-user_id החדש
        
        # בדיקה האם הסטודנט כבר רשום לקבוצת מעבדה זו
        existing_link = db.execute(
            group_students.select().where(
                (group_students.c.group_id == lab_id) & 
                (group_students.c.student_id == user.user_id)
            )
        ).first()
        
        if not existing_link:
            db.execute(
                group_students.insert().values(
                    group_id=lab_id,
                    student_id=user.user_id,
                    team_code=None
                )
            )
        imported_count += 1
        
    db.commit()
    return {"message": f"הייבוא הושלם בהצלחה. סה\"כ עובדו {imported_count} רשומות מהאקסל."}


# Bulk update team codes for all students in a lab group

@router.put("/{group_id}/students/teams", response_model=MessageResponse)
def bulk_update_student_teams(
    group_id: int,
    payload: BulkUpdateTeamsSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    """עדכון מרוכז של קודי צוות לכלל הסטודנטים בקבוצת מעבדה"""
    group = get_lab_group_or_404(db, group_id)
    verify_lab_access(group, current_user)
    
    for item in payload.assignments:
        user = db.query(User).filter(User.id_number == item.id_number).first()
        if not user:
            continue
        
        # עדכון קוד הצוות בטבלת הקישור
        db.execute(
            group_students.update().where(
                (group_students.c.group_id == group_id) &
                (group_students.c.student_id == user.user_id)
            ).values(team_code=item.team_code)
        )
    
    db.commit()
    return {"message": "קודי הצוות עודכנו בהצלחה עבור הסטודנטים בקבוצה"}


# Update a single student's team code in a lab group

@router.put("/{group_id}/students/{student_id}/team", response_model=MessageResponse)
def update_single_student_team(
    group_id: int,
    student_id: int,
    payload: UpdateStudentTeamSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    """עדכון קוד צוות לסטודנט בודד בקבוצת מעבדה (למקרי החלפה/שינוי)"""
    group = get_lab_group_or_404(db, group_id)
    verify_lab_access(group, current_user)
    
    # בדיקה שהסטודנט אכן משויך לקבוצה זו
    existing_link = db.execute(
        group_students.select().where(
            (group_students.c.group_id == group_id) &
            (group_students.c.student_id == student_id)
        )
    ).first()
    
    if not existing_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="הסטודנט אינו רשום בקבוצת מעבדה זו"
        )
        
    db.execute(
        group_students.update().where(
            (group_students.c.group_id == group_id) &
            (group_students.c.student_id == student_id)
        ).values(team_code=payload.team_code)
    )
    db.commit()
    return {"message": "קוד הצוות של הסטודנט עודכן בהצלחה"}