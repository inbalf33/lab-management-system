from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

from app.routers import auth , users, schedules, grades, labs, cms

from app.logger.logger_service import get_logger_middleware

app = FastAPI(title="Lab Management API")

# מאפשר לכל נתיב שמוגדר בקובץ auth.py יהיה זמין
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])

# מאפשר לכל נתיב שמוגדר בקובץ users.py יהיה זמין
app.include_router(users.router, prefix="/api/users", tags=["Users"])

# schedules.py
app.include_router(schedules.router, prefix="/api/schedules", tags=["Schedules"])

# grades.py
app.include_router(grades.router, prefix="/api/grades", tags=["Grades"])

# labs.py
app.include_router(labs.router, prefix="/api/labs", tags=["Labs"])

# cms.py
app.include_router(cms.router, prefix="/api/cms", tags=["Cms"])

# רישום ה-Middleware מתוך ה-Service
app.middleware("http")(get_logger_middleware())


####################

@app.get("/")
def read_root():
    return {"message": "Server is up and running!"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Try running a lightweight query to test the DB connection
        db.execute(text("SELECT 1"))
        return {"status": "success", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}