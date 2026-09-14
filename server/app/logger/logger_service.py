import os
from fastapi import Request
from app.logger.providers.custom_logger import log_http_request

# טעינת סוג הלוגר מתוך משתני הסביבה (למשל: LOGGER=custom)
LOGGER_TYPE = os.getenv("LOGGER", "custom")

async def empty_middleware(request: Request, call_next):
    """ברירת מחדל במידה והלוגר כבוי - ממשיך הלאה בלי לרשום לוגים"""
    return await call_next(request)

def get_logger_middleware():
    if LOGGER_TYPE == "custom":
        return log_http_request
    
    return empty_middleware