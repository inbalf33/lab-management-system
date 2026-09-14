from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from app.database import get_db
from app.models import User
from app.core.security import verify_password, hash_password, create_access_token
from app.api.deps import get_current_user

# יצירת ה-Router של האבטחה (יוגדר עם prefix שייונייך ב-main.py או כאן)
router = APIRouter(tags=["Auth"])


# ==========================================
# Pydantic Schemas (מבני הנתונים לקלט ופלט)
# ==========================================

class MessageResponse(BaseModel):
    message: str

class LoginSchema(BaseModel):
    """קלט עבור התחברות - מקבל ת.ז או אימייל + סיסמה"""
    identifier: str  # יכול להכיל אימייל או ת.ז
    password: str


class RegisterSchema(BaseModel):
    """קלט עבור הפעלת חשבון/הרשמה ראשונית"""
    id_number: str
    email: EmailStr
    password: str = Field(..., min_length=6, description="סיסמה באורך 6 תווים לפחות")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    message: str = "התחברות למערכת בוצעה בהצלחה!"


class UserResponse(BaseModel):
    """פלט של פרטי המשתמש (למשל עבור נתיב me/)"""
    user_id: int
    id_number: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    role: str

    class Config: # מתרגם אוייבקט היוזר למבנה של גייסון
        from_attributes = True


class ForgotPasswordSchema(BaseModel):
    """קלט לבקשת איפוס סיסמה"""
    email_or_id: str


class ResetPasswordSchema(BaseModel):
    """קלט לעדכון סיסמה חדשה בפועל"""
    token: str
    new_password: str


# ==========================================
# Endpoints
# ==========================================

# Register

@router.post("/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id_number == data.id_number).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="תעודת הזהות אינה מופיעה ברשימת המשתמשים במערכת"
        )
    
    if user.password is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="החשבון כבר הופעל במערכת, ניתן לעבור למסך ההתחברות"
        )
    
    hashed_pw = hash_password(data.password)
    user.email = data.email
    user.password = hashed_pw

    db.commit()
    db.refresh(user)

    return {"message": "החשבון הופעל בהצלחה! ניתן להתחבר למערכת"}


        

# Login

@router.post("/login", response_model=TokenResponse)
def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(or_(User.id_number == data.identifier, User.email == data.identifier)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="פרטי ההתחברות אינם נכונים"
        )

    if not user.password or not user.password.startswith("$2b$"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="פרטי ההתחברות אינם נכונים"
        )

    is_password_valid = verify_password(data.password, user.password)
    
    if not is_password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="פרטי ההתחברות אינם נכונים"
        )
    access_token_data = {
        "sub": str(user.user_id),
        "role": user.role
    } 

    token = create_access_token(data=access_token_data)
   

    return {
        "access_token": token,
        "token_type": "bearer",
        "message": "התחברות למערכת בוצעה בהצלחה!"
    }


# ME - GET user details

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    מחזיר את פרטי המשתמש המחובר כעת לפי הטוקן שמועבר ב-Header
    """
    return current_user


# Logout

@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)):

    return {"message": "התנתקת מהמערכת בהצלחה"}

