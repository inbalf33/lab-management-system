from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
# ייבוא המודלים המדויקים מתוך models.py שלך
from app.models import LabSchedule, SwapRequest, User, LabGroup, group_students
from app.api.deps import get_current_user, require_roles

import os
import redis

REDIS_URL = os.getenv("REDIS_URL")

try:
    if REDIS_URL:
        redis_client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True
        )
        redis_client.ping()  # בודק חיבור בפועל
    else:
        redis_client = None
except Exception:
    redis_client = None

router = APIRouter()

# ==========================================
# Pydantic Schemas 
# ==========================================

class MessageResponse(BaseModel):
    message: str

# קלט: נעילת מועד ב-Redis
class ScheduleLockSchema(BaseModel):
    schedule_id: int

# פלט: פרטי מועד מעבדה בלוח הזמנים
class LabScheduleResponse(BaseModel):
    schedule_id: int
    group_id: int
    topic_id: int
    lab_date: datetime
    week_number: int
    session_type: str

    class Config:
        from_attributes = True


# קלט: יצירת מועד מעבדה חדש בלוח הזמנים (למשל מה-CMS)
class LabScheduleCreate(BaseModel):
    group_id: int
    topic_id: int
    lab_date: datetime
    week_number: int
    session_type: str = Field(default="REGULAR", description="INTRO / REGULAR / FINAL_LAB / COMPLETION")

# קלט: עדכון/עריכת מועד מעבדה קיים (כל השדות אופציונליים לעדכון חלקי)
class LabScheduleUpdate(BaseModel):
    group_id: Optional[int] = None
    topic_id: Optional[int] = None
    lab_date: Optional[datetime] = None
    week_number: Optional[int] = None
    session_type: Optional[str] = None

# קלט: יצירה מרוכזת של כל לוח הזמנים לקבוצת מעבדה (Bulk)
class LabScheduleBulkCreate(BaseModel):
    schedules: List[LabScheduleCreate]


# עבור הרשמה לבקשת החלפה למעבדה
class RegisterScheduleRequest(BaseModel):
    schedule_id: int
    current_schedule_id: int
    reason: str = "הרשמה/מעבר למועד מעבדה"
    is_team_swap: bool = Field(True, description="האם ההחלפה היא צוותית (True) או אישית (False)")


# קלט: יצירת בקשת החלפה בין מועדים
class SwapRequestCreateSchema(BaseModel):
    current_schedule_id: int = Field(..., description="מזהה הלוז הנוכחי של הסטודנט")
    target_schedule_id: int = Field(..., description="מזהה הלוז המבוקש להחלפה")
    reason: str = Field(..., min_length=3, description="חובה לציין את סיבת ההחלפה")
    is_team_swap: bool = Field(True, description="האם ההחלפה היא צוותית (True) או אישית (False)")



# פלט: פרטי בקשת החלפה
class SwapRequestResponse(BaseModel):
    request_id: int
    student_id: int
    student_name: Optional[str] = None # שם הסטודנט
    team_code: Optional[str] = None    # קוד הצוות (למשל A1)
    current_schedule_id: int
    target_schedule_id: int
    is_team_swap: bool
    status: str
    reason: str
    reviewer_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# קלט: אישור/דחיית בקשת החלפה ע"י מרצה/אדמין

class SwapApprovalSchema(BaseModel):
    approve: bool
    reviewer_notes: Optional[str] = Field(None, description="הערות המרצה/הסגל לבקשה")


# ==========================================
# Endpoints
# ==========================================

# Get all lab schedules

@router.get("", response_model=List[LabScheduleResponse])
def get_schedules(
    group_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(LabSchedule)

    # 1. אם נשלח group_id ספציפי (תופס לכולם - סגל שבוחר קבוצה או סטודנט שרוצה לראות קבוצה)
    if group_id:
        query = query.filter(LabSchedule.group_id == group_id)

    # 2. אם לא נשלח group_id, נפעיל ברירת מחדל לפי תפקיד המשתמש (כל עוד לא ביקשו topic_id להחלפה)
    elif not topic_id:
        if current_user.role == "student":
            user_group = db.query(LabGroup).filter(LabGroup.students.any(user_id=current_user.user_id)).first()
            if user_group:
                query = query.filter(LabSchedule.group_id == user_group.group_id)
        
        elif current_user.role in ["instructor", "lecturer"]:
            # שליפת כל קבוצות המעבדה שהמשתמש הזה משויך אליהן כמדריך או כמרצה
            staff_groups = db.query(LabGroup.group_id).filter(
                (LabGroup.instructor_id == current_user.user_id) | 
                (LabGroup.lecturer_id == current_user.user_id)
            ).all()
            
            group_ids = [g[0] for g in staff_groups]
            # סינון הלו"ז כך שיציג רק את המעבדות של הקבוצות של המדריך/מרצה
            query = query.filter(LabSchedule.group_id.in_(group_ids))
            
        # אדמין (admin) שלא שלח group_id - יקבל פשוט את כל הלו"זים במערכת בלי סינון.

    # 3. סינון לפי topic_id (עבור מודל החלפת מעבדה)
    if topic_id:
        query = query.filter(LabSchedule.topic_id == topic_id)

    return query.all()



# Lock a schedule slot temporarily in Redis for 10 minutes

@router.post("/lock", response_model=MessageResponse)
def lock_schedule_slot(
    data: ScheduleLockSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="שירות הנעילות הזמני (Redis) אינו זמין"
        )

    schedule = db.query(LabSchedule).filter(LabSchedule.schedule_id == data.schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="מועד המעבדה המבוקש לא נמצא"
        )

    lock_key = f"lock:schedule:{data.schedule_id}"
    
    # ניסיון נעילה ב-Redis ל-10 דקות (600 שניות)
    is_set = redis_client.set(lock_key, str(current_user.user_id), ex=600, nx=True)
    
    if not is_set:
        existing_locker = redis_client.get(lock_key)
        if existing_locker and str(existing_locker) == str(current_user.user_id):
            return {"message": "המועד כבר ננעל עבורך בעבר ועדיין בתוקף"}
            
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="המועד נתפס כרגע על ידי סטודנט אחר, נסה שוב בעוד מספר דקות"
        )

    return {"message": "המקום ננעל עבורך בהצלחה ל-10 דקות"}



# Unlock a schedule slot

@router.delete("/lock/{schedule_id}", response_model=MessageResponse)
def unlock_schedule_slot(
    schedule_id: int,
    current_user: User = Depends(get_current_user)
):
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="שירות הנעילות הזמני (Redis) אינו זמין"
        )

    lock_key = f"lock:schedule:{schedule_id}"
    existing_locker = redis_client.get(lock_key)

    if existing_locker and str(existing_locker) == str(current_user.user_id):
        redis_client.delete(lock_key)
        return {"message": "הנעילה שוחררה בהצלחה"}

    return {"message": "לא נמצאה נעילה פעילה שניתן לשחרר"}




# Confirm lab registration (after Redis lock)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_to_schedule(
    data: RegisterScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lock_key = f"lock:schedule:{data.schedule_id}"

    # בדיקה שיש נעילה תקפה ב-Redis עבור המשתמש
    if redis_client:
        existing_locker = redis_client.get(lock_key)
        if not existing_locker or str(existing_locker) != str(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="אין לך נעילה בתוקף למועד זה. נא לבצע נעילה מחדש"
            )

    # בדיקה שמועד היעד קיים ב-DB
    target_schedule = db.query(LabSchedule).filter(LabSchedule.schedule_id == data.schedule_id).first()
    if not target_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="מועד המעבדה המבוקש לא נמצא"
        )

    #חישוב תפוסה בפועל במועד היעד (צוותים קבועים - יציאות + כניסות)
    base_teams_count = db.query(func.count(func.distinct(group_students.c.team_code)))\
        .filter(group_students.c.group_id == target_schedule.group_id)\
        .scalar() or 0

    leaving_teams = db.query(SwapRequest)\
        .filter(SwapRequest.current_schedule_id == data.schedule_id, SwapRequest.status == "APPROVED")\
        .count()

    joining_teams = db.query(SwapRequest)\
        .filter(SwapRequest.target_schedule_id == data.schedule_id, SwapRequest.status == "APPROVED")\
        .count()

    active_teams_count = base_teams_count - leaving_teams + joining_teams

    if active_teams_count >= 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="המעבדה מלאה (הגיעה לקיבולת המרבית של 7 צוותים)"
        )
    # 4. יצירת בקשת הרשמה/החלפה ב-Swap_Requests
    new_request = SwapRequest(
        student_id=current_user.user_id,
        current_schedule_id=data.current_schedule_id,
        target_schedule_id=data.schedule_id,
        is_team_swap=data.is_team_swap,
        status="PENDING",
        reason=data.reason,
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_request)
    db.commit()

    # שחרור הנעילה מ-Redis
    if redis_client:
        redis_client.delete(lock_key)

    return {"message": "הבקשה להרשמה/החלפה נרשמה בהצלחה וממתינה לאישור"}



# Get student's schedule and swap request status
@router.get("/my-registrations")
def get_my_registrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    student_group_row = db.query(group_students).filter(group_students.c.student_id == current_user.user_id).first()
    if not student_group_row:
        return {
            "group_code": None,
            "group_day": None,
            "group_time": None,
            "team_code": None,
            "regular_schedules": [],
            "completion_schedules": [],
            "swap_requests": []
        }

    group_id = student_group_row.group_id
    team_code = student_group_row.team_code

    # שליפת פרטי קבוצת המעבדה מטבלת LabGroup (כולל day ו־time)
    group_obj = db.query(LabGroup).filter(LabGroup.group_id == group_id).first()
    group_code = group_obj.group_code if group_obj else None
    group_day = group_obj.day if group_obj else None
    group_time = group_obj.time if group_obj else None

    regular_schedules_raw = db.query(LabSchedule).filter(
        LabSchedule.group_id == group_id
    ).all()

    regular_schedules = []
    for sch in regular_schedules_raw:
        sch_dict = LabScheduleResponse.from_orm(sch).dict()
        sch_dict["topic_name"] = sch.topic.topic_name if sch.topic else f"נושא {sch.topic_id}"
        regular_schedules.append(sch_dict)

    team_student_ids = [current_user.user_id]
    if team_code:
        team_rows = db.query(group_students.c.student_id).filter(
            group_students.c.group_id == group_id,
            group_students.c.team_code == team_code
        ).all()
        team_student_ids = [row.student_id for row in team_rows]

    swap_requests_raw = db.query(SwapRequest).filter(
        (SwapRequest.student_id == current_user.user_id) | 
        (SwapRequest.student_id.in_(team_student_ids) & (SwapRequest.is_team_swap == True))
    ).all()

    swap_requests = []
    for req in swap_requests_raw:
        curr_sch = db.query(LabSchedule).filter(LabSchedule.schedule_id == req.current_schedule_id).first()
        target_sch = db.query(LabSchedule).filter(LabSchedule.schedule_id == req.target_schedule_id).first()
        
        swap_requests.append({
            "request_id": req.request_id,
            "status": req.status,
            "reason": req.reason,
            "reviewer_notes": req.reviewer_notes,
            "current_schedule_id": req.current_schedule_id, # <--- הוסיפי את זה לנוחות ההתאמה
            "target_schedule_id": req.target_schedule_id,   # <--- הוסיפי את זה לנוחות ההתאמה
            "current_date": curr_sch.lab_date if curr_sch else None,
            "current_topic_name": curr_sch.topic.topic_name if curr_sch and curr_sch.topic else "מעבדה",
            "target_date": target_sch.lab_date if target_sch else None,
            "target_topic_name": target_sch.topic.topic_name if target_sch and target_sch.topic else "מעבדה יעד",
            # "target_time": target_sch.group.time if target_sch and target_sch.group else None
        })

    return {
        "group_code": group_code,
        "group_day": group_day,
        "group_time": group_time,
        "team_code": team_code,
        "regular_schedules": regular_schedules,
        "completion_schedules": [],
        "swap_requests": swap_requests
    }

# Cancel a pending swap request

@router.delete("/registrations/{id}")
def cancel_registration(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # חיפוש הבקשה ב-SwapRequest לפי ה-request_id
    request = db.query(SwapRequest).filter(
        SwapRequest.request_id == id,
        SwapRequest.student_id == current_user.user_id
    ).first()

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="בקשת ההחלפה לא נמצאה או שאינה שייכת לך"
        )

    if request.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ניתן לבטל רק בקשות שנמצאות בסטטוס ממתין (PENDING)"
        )

    db.delete(request)
    db.commit()

    return {"message": "בקשת ההחלפה/הרשמה בוטלה בהצלחה"}





# ========================

# Get all swap requests

@router.get("/swap-requests", response_model=List[SwapRequestResponse])
def get_all_swap_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
):
    query = db.query(SwapRequest)

    # סינון מבוסס תפקיד עבור מרצים ומדריכים (אדמין מקבל הכל)
    if current_user.role in ["lecturer", "instructor"]:
        role_column = LabGroup.lecturer_id if current_user.role == "lecturer" else LabGroup.instructor_id
        
        group_ids = db.query(LabGroup.group_id).filter(
            role_column == current_user.user_id
        ).subquery()
        
        query = query.filter(
            (SwapRequest.current_schedule_id.in_(
                db.query(LabSchedule.schedule_id).filter(LabSchedule.group_id.in_(group_ids))
            )) |
            (SwapRequest.target_schedule_id.in_(
                db.query(LabSchedule.schedule_id).filter(LabSchedule.group_id.in_(group_ids))
            ))
        )

    requests_raw = query.all()
    response_data = []

    for req in requests_raw:
        # שליפת שם הסטודנט מטבלת Users (נניח ויש שדה full_name או name)
        student_obj = db.query(User).filter(User.user_id == req.student_id).first()
        student_name = getattr(student_obj, "full_name", None) or getattr(student_obj, "name", "סטודנט")

        # שליפת קוד הצוות של הסטודנט מטבלת group_students
        group_student_row = db.query(group_students).filter(
            group_students.c.student_id == req.student_id
        ).first()
        team_code = group_student_row.team_code if group_student_row else None

        # בניית אובייקט התשובה המלא לסכמה
        req_dict = {
            "request_id": req.request_id,
            "student_id": req.student_id,
            "student_name": student_name,
            "team_code": team_code,
            "current_schedule_id": req.current_schedule_id,
            "target_schedule_id": req.target_schedule_id,
            "is_team_swap": req.is_team_swap,
            "status": req.status,
            "reason": req.reason,
            "reviewer_notes": req.reviewer_notes,
            "created_at": req.created_at
        }
        response_data.append(req_dict)

    return response_data

# @router.get("/swap-requests", response_model=List[SwapRequestResponse])
# def get_all_swap_requests(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(require_roles(["admin", "lecturer", "instructor"]))
# ):
#     query = db.query(SwapRequest)

#     # סינון מבוסס תפקיד עבור מרצים ומדריכים (אדמין מקבל הכל)
#     if current_user.role in ["lecturer", "instructor"]:
#         role_column = LabGroup.lecturer_id if current_user.role == "lecturer" else LabGroup.instructor_id
        
#         group_ids = db.query(LabGroup.group_id).filter(
#             role_column == current_user.user_id
#         ).subquery()
        
#         query = query.filter(
#             (SwapRequest.current_schedule_id.in_(
#                 db.query(LabSchedule.schedule_id).filter(LabSchedule.group_id.in_(group_ids))
#             )) |
#             (SwapRequest.target_schedule_id.in_(
#                 db.query(LabSchedule.schedule_id).filter(LabSchedule.group_id.in_(group_ids))
#             ))
#         )

#     return query.all()


@router.post("/swap-requests/{id}/approve")
def approve_or_reject_swap_request(
    id: int,
    data: SwapApprovalSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    # אכיפה: אם המרצה בחר לדחות, חובה להזין הערה/סיבה לסטודנט
    if not data.approve and not data.reviewer_notes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="חובה לציין הערה או סיבה לדחיית הבקשה עבור הסטודנט"
        )

    # איתור בקשת ההחלפה
    swap_request = db.query(SwapRequest).filter(SwapRequest.request_id == id).first()
    if not swap_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="בקשת ההחלפה לא נמצאה"
        )

    if swap_request.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ניתן לטפל אך ורק בבקשות הנמצאות בסטטוס ממתין (PENDING)"
        )

    # בדיקת שיוך קבוצה למרצה (אדמין רשאי להכול)
    if current_user.role == "lecturer":
        target_sched = db.query(LabSchedule).filter(LabSchedule.schedule_id == swap_request.target_schedule_id).first()
        if target_sched:
            group_check = db.query(LabGroup).filter(
                LabGroup.group_id == target_sched.group_id,
                LabGroup.lecturer_id == current_user.user_id
            ).first()
            if not group_check:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="אין לך הרשאה לאשר בקשות עבור קבוצה זו"
                )

    # עדכון סטטוס והרצת וולידציית קיבולת באישור
    if data.approve:
        target_schedule = db.query(LabSchedule).filter(LabSchedule.schedule_id == swap_request.target_schedule_id).first()
        if target_schedule:
            base_teams_count = db.query(func.count(func.distinct(group_students.c.team_code)))\
                .filter(group_students.c.group_id == target_schedule.group_id)\
                .scalar() or 0

            leaving_teams = db.query(SwapRequest)\
                .filter(SwapRequest.current_schedule_id == swap_request.target_schedule_id, SwapRequest.status == "APPROVED")\
                .count()

            joining_teams = db.query(SwapRequest)\
                .filter(SwapRequest.target_schedule_id == swap_request.target_schedule_id, SwapRequest.status == "APPROVED")\
                .count()

            if (base_teams_count - leaving_teams + joining_teams) >= 7:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="לא ניתן לאשר את הבקשה: המעבדה הגיעה לתפוסה המקסימלית של 7 צוותים"
                )

        swap_request.status = "APPROVED"
    else:
        swap_request.status = "REJECTED"

    swap_request.reviewer_notes = data.reviewer_notes
    db.commit()

    action_text = "אושרה" if data.approve else "נדחתה"
    return {"message": f"בקשת ההחלפה {action_text} בהצלחה"}


# ==========================================
# CMS Lab Schedule Management Endpoints
# ==========================================

# שליפת כל לוח הזמנים של קבוצת מעבדה ספציפית
@router.get("/group/{group_id}", response_model=List[LabScheduleResponse])
def get_group_schedule(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    schedules = db.query(LabSchedule).filter(LabSchedule.group_id == group_id).order_by(LabSchedule.week_number).all()
    return schedules

# הוספת מפגש יחיד ללוח הזמנים (מרצה/אדמין בלבד)
@router.post("", response_model=LabScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_lab_schedule(
    schedule_data: LabScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    new_schedule = LabSchedule(
        group_id=schedule_data.group_id,
        topic_id=schedule_data.topic_id,
        lab_date=schedule_data.lab_date,
        week_number=schedule_data.week_number,
        session_type=schedule_data.session_type
    )
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    return new_schedule

# יצירה מרוכזת של כל לוח הזמנים לקבוצה (Bulk - לדוגמה כל 13 השבועות בבת אחת)
@router.post("/group/{group_id}/bulk", status_code=status.HTTP_201_CREATED)
def create_bulk_schedule(
    group_id: int,
    bulk_data: LabScheduleBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    created_schedules = []
    for item in bulk_data.schedules:
        db_schedule = LabSchedule(
            group_id=group_id,
            topic_id=item.topic_id,
            lab_date=item.lab_date,
            week_number=item.week_number,
            session_type=item.session_type
        )
        db.add(db_schedule)
        created_schedules.append(db_schedule)
    
    db.commit()
    return {"message": f"Successfully created {len(created_schedules)} schedule items for group {group_id}"}

# עריכה / עדכון מפגש קיים (למשל דחיית תאריך או שינוי נושא)
@router.put("/{schedule_id}", response_model=LabScheduleResponse)
def update_lab_schedule(
    schedule_id: int,
    schedule_data: LabScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    schedule = db.query(LabSchedule).filter(LabSchedule.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule item not found")

    # עדכון רק של השדות שנשלחו בפועל
    update_data = schedule_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(schedule, key, value)

    db.commit()
    db.refresh(schedule)
    return schedule

# מחיקת מפגש מלוח הזמנים
@router.delete("/{schedule_id}", status_code=status.HTTP_200_OK)
def delete_lab_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    schedule = db.query(LabSchedule).filter(LabSchedule.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule item not found")

    db.delete(schedule)
    db.commit()
    return {"message": f"Schedule item {schedule_id} deleted successfully"}