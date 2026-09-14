import os
import time
from datetime import datetime
from fastapi import Request

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
os.makedirs(LOG_DIR, exist_ok=True)

async def log_http_request(request: Request, call_next):
    start_time = time.time()
    
    # ביצוע הבקשה
    response = await call_next(request)
    
    # חישוב זמן ביצוע במאיות שנייה
    process_time = round((time.time() - start_time) * 1000, 2)
    
    # חילוץ תאריך ושעה נוכחיים בדיוק כמו ב-timeHelper
    now = datetime.now()
    date_file_name = now.strftime("%d-%m-%Y") # שם הקובץ: 01-09-2026.log
    time_stamp = now.strftime("%d/%m/%Y %H:%M:%S")
    
    # הרכבת שורת הלוג בפורמט זהה ל-Morgan
    status_code = response.status_code
    method = request.method
    url = str(request.url.path)
    
    log_message = f"[{time_stamp}] {method} {url} {status_code} | {process_time}ms"
    
    # בדיקה אם יש הודעת שגיאה מיוחדת שהוצמדה לבקשה
    error_text = getattr(request.state, "error_message", "")
    if error_text:
        log_message += f" || {error_text}"
        
    log_message += "\n"
    
    # כתיבה לטרמינל
    print(log_message.strip())
    
    # כתיבה לקובץ הלוג היומי (append mode)
    log_file_path = os.path.join(LOG_DIR, f"{date_file_name}.log")
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(log_message)
        
    return response