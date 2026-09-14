from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models import User, Grade, CourseFinalGrade, LabGroup, LabSchedule, Course, group_students, CmsContent
from app.api.deps import get_current_user, require_roles

from typing import Optional, List, Dict, Any, Optional

router = APIRouter()

# ==========================================
# Pydantic Schemas for CMS
# ==========================================




class CmsContentBase(BaseModel):
    key_name: str
    content_value: str
    description: Optional[str] = None
    is_active: bool = True

class CmsContentCreate(CmsContentBase):
    pass

class CmsContentUpdate(BaseModel):
    content_value: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CmsContentResponse(CmsContentBase):
    content_id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==========================================
# Endpoints
# ==========================================

# Get All CMS Content

@router.get("/content", response_model=List[CmsContentResponse])
def get_all_cms_content(db: Session = Depends(get_db)):
    """שליפת כל תכני המערכת והתוויות לשימוש האתר"""
    contents = db.query(CmsContent).all()
    return contents

# Update CMS Content Item

@router.put("/content/{content_id}", response_model=CmsContentResponse)
def update_cms_content(
    content_id: int,
    payload: CmsContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "lecturer"]))
):
    """עדכון תוכן קיים בטבלת ה-CMS (כותרות, באנרים וטקסטים)"""
    content_item = db.query(CmsContent).filter(CmsContent.content_id == content_id).first()
    
    if not content_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="תוכן המבוקש לא נמצא במערכת"
        )
        
    # עדכון השדות רק אם הועברו ב-payload
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(content_item, key, value)
        
    # עדכון חותמת הזמן הנוכחית
    content_item.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(content_item)
    return content_item