import os
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from dotenv import load_dotenv

# טעינת משתני הסביבה מקובץ .env
load_dotenv()

# הגדרות מפתח סודי ואלגוריתם
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 4

# --- 1. הצפנה ואימות סיסמאות בעזרת bcrypt ---

def hash_password(password: str) -> str:
    """הצפנת סיסמה גלויה ל-Hash מוצפן"""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """אימות סיסמה גלויה מול Hash מוצפן מה-DB"""
    pwd_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

# --- 2. יצירה ופענוח של JWT (מקביל ל-jwt.js) ---

def create_access_token(data: dict) -> str:
    """יצירת טוקן JWT עם תוקף ל-4 שעות """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    """פענוח ואימות טוקן JWT """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None