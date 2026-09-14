from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from app.database import get_db
from app.models import User
from app.core.security import verify_password, hash_password, create_access_token
from app.api.deps import get_current_user, require_roles

router = APIRouter()

# ==========================================
# Pydantic Schemas (מבני הנתונים לקלט ופלט)
# ==========================================

class MessageResponse(BaseModel):
    message: str

# פלט: פרופיל המשתמש המחובר
class UserProfileResponse(BaseModel):
    id_number: str
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    role: str

    class Config:
        from_attributes = True


# קלט: עדכון פרטים אישיים בפרופיל
class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


# קלט: שינוי סיסמה יזום מתוך הפרופיל
class ChangePasswordSchema(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)

# קלט: עדכון ת.ז על ידי מרצה/אדמין
class UpdateIdNumberSchema(BaseModel):
    new_id_number: str = Field(..., min_length=8, max_length=9, description="תעודת זהות חדשה (8-9 ספרות)")

# קלט: עדכון תפקיד על ידי אדמין
class UserRoleUpdate(BaseModel):
    role: str = Field(..., description="תפקיד חדש: student, instructor, lecturer, admin")

# סכימה להצגת מידע מורחב על משתמש (עבור רשימות ניהול, חיפוש ושליפת משתמש לפי מזהה)
class UserDetailResponse(BaseModel):
    user_id: int
    id_number: str
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    role: str
    is_miluim: bool
    is_active: bool

    class Config:
        from_attributes = True


# ==========================================
# Endpoints
# ==========================================

# Get user profile

@router.get("/profile", response_model=UserProfileResponse)
def get_user_profile(current_user: User = Depends(get_current_user)):

    return current_user


# Update user profile (PUT)

@router.put("/profile", response_model=UserProfileResponse)
def update_user_profile(
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):

    if data.email:
        existing_email = db.query(User).filter(User.email == data.email).first()
        if existing_email and existing_email.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="האימייל הזה כבר קיים במערכת"
            )
    # מכניס למילון רק שדות שהיוזר שלח בבקשה
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)

    return current_user


# Change password while user connect (POST)

@router.post("/change-password", response_model=MessageResponse)
def update_user_profile(
    data: ChangePasswordSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):

    is_password_valid = verify_password(data.current_password, current_user.password)

    if not is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="הסיסמה הנוכחית שגויה"
        )

    new_hash = hash_password(data.new_password)
    current_user.password = new_hash
    db.commit()

    return {"message": "הסיסמה שונתה בהצלחה"}
        
    
# Get all users (Lecturer / Admin only)

@router.get("", response_model=list[UserDetailResponse])
def get_all_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_miluim: Optional[bool] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
                User.id_number.ilike(search_pattern)
            )
        )

    if is_miluim is not None:
        query = query.filter(User.is_miluim == is_miluim)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    return query.all()


# Get specific user - by ID (Lecturer / Admin only)

@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="המשתמש לא נמצא"
        )
    
    return target_user


# Update user ID number (Lecturer / Admin only)

@router.patch("/{user_id}/id-number", response_model=UserDetailResponse)
def update_user_id_number(
    user_id: int,
    data: UpdateIdNumberSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    # 1. שליפת היוזר שרוצים לעדכן
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="המשתמש לא נמצא"
        )
    
    # 2. בדיקה שתעודת הזהות החדשה אינה תפוסה על ידי משתמש אחר
    existing_user = db.query(User).filter(User.id_number == data.new_id_number).first()
    if existing_user and existing_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="תעודת הזהות הזו כבר קיימת במערכת"
        )
    
    # 3. עדכון ושמירה
    target_user.id_number = data.new_id_number
    db.commit()
    db.refresh(target_user)
    
    return target_user


# Update user Role - by ID (Admin only)

@router.patch("/{user_id}/role", response_model=UserDetailResponse)
def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    
    # 2. שליפת היוזר שרוצים לעדכן
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="המשתמש לא נמצא"
        )
    # מקרה קצה - שאדמין לא ישנה בטעות תפקיד לעצמו
    if current_user.user_id == target_user.user_id and data.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="אינך יכול לשנות את התפקיד של עצמך"
        )

    target_user.role = data.role
    db.commit()
    db.refresh(target_user)
    
    return target_user


# Soft Delete User - Toggle is_active to False (Admin only)
@router.delete("/{user_id}", response_model=UserDetailResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):  
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="המשתמש לא נמצא"
        )
    
    # מקרה קצה - למנוע מאדמין למחוק/להקפיא את עצמו
    if current_user.user_id == target_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="אינך יכול למחוק את החשבון של עצמך"
        )
    
    # מחיקה לוגית (Soft Delete)
    target_user.is_active = False
    db.commit()
    db.refresh(target_user)
    
    return target_user

# Reactivate user account (Admin only)

@router.patch("/{user_id}/activate", response_model=UserDetailResponse)
def reactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="המשתמש לא נמצא"
        )
    
    target_user.is_active = True
    db.commit()
    db.refresh(target_user)
    
    return target_user