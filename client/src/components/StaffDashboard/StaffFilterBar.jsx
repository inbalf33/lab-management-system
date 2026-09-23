import React, { useState } from 'react';

function StaffFilterBar({ 
  labGroups, 
  selectedGroup, 
  setSelectedGroup, 
  reserveFilter, 
  setReserveFilter, 
  pendingCount, 
  onOpenSwapModal 
}) {
  const [isMiluimHovered, setIsMiluimHovered] = useState(false);
  const [isClearHovered, setIsClearHovered] = useState(false);
  const [isSwapHovered, setIsSwapHovered] = useState(false);

  // פונקציה לניקוי המסננים
  const handleClearFilters = () => {
    setSelectedGroup('');
    setReserveFilter(false);
  };

  // בדיקה האם יש מסנן פעיל כדי לדעת אם להציג את כפתור הניקוי
  const hasActiveFilters = selectedGroup !== '' || reserveFilter;

  return (
    <div className="card shadow-sm border-0 mb-4 bg-light">
      <div className="card-body d-flex flex-wrap align-items-center justify-content-between gap-3 py-3 px-4">
        
        {/* צד ימין: בחירת קבוצה, כפתור מילואים מעוצב, וכפתור ניקוי מסננים */}
        <div className="d-flex align-items-center flex-wrap gap-3">
          
          {/* סינון לפי קבוצה - רוחב מורחב למניעת חיתוך טקסט */}
          <div className="d-flex align-items-center gap-2">
            <label className="form-label small fw-bold mb-0 text-nowrap text-secondary">קבוצת מעבדה:</label>
            <select 
              className="form-select form-select-sm bg-white shadow-none"
              style={{ width: '230px', borderRadius: '8px' }}
              value={selectedGroup}
              onChange={(e) => setSelectedGroup(e.target.value)}
            >
              <option value="">כל הקבוצות</option>
              {Array.isArray(labGroups) && labGroups.map((group) => (
                <option key={group.group_id || group.id} value={group.group_id || group.id}>
                  {group.day ? `יום ${group.day}` : ''} {group.time ? `| ${group.time}` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* כפתור מילואים מעוצב עם טיפול נכון בריחוף */}
          <button 
            type="button"
            className="btn btn-sm px-3 py-1.5 fw-semibold d-flex align-items-center gap-2"
            style={{ 
              borderRadius: '20px', 
              border: '1.5px solid #0d6efd',
              backgroundColor: reserveFilter ? '#0d6efd' : (isMiluimHovered ? '#e9ecef' : '#ffffff'),
              color: reserveFilter ? '#ffffff' : '#0d6efd',
              transition: 'all 0.2s ease-in-out'
            }}
            onMouseEnter={() => setIsMiluimHovered(true)}
            onMouseLeave={() => setIsMiluimHovered(false)}
            onClick={() => setReserveFilter(!reserveFilter)}
          >
            <span>🪖</span>
            <span>{reserveFilter ? 'מציג: מילואים בלבד' : 'סנן מילואים'}</span>
          </button>

          {/* כפתור ניקוי כל המסננים עם חיווי ריחוף מעוצב */}
          {hasActiveFilters && (
            <button 
              type="button"
              className="btn btn-sm text-decoration-none fw-semibold d-flex align-items-center gap-1 px-2 py-1 ms-2"
              style={{ 
                borderRadius: '6px',
                backgroundColor: isClearHovered ? '#fee2e2' : 'transparent',
                color: '#dc2626',
                border: 'none',
                transition: 'background-color 0.2s ease'
              }}
              onMouseEnter={() => setIsClearHovered(true)}
              onMouseLeave={() => setIsClearHovered(false)}
              onClick={handleClearFilters}
            >
              <span>❌</span>
              <span>ניקוי כל המסננים</span>
            </button>
          )}
        </div>

        {/* צד שמאל: כפתור בקשות החלפה */}
        <div>
          <button 
            type="button" 
            className="btn btn-sm position-relative fw-bold px-3 py-2"
            style={{
              backgroundColor: isSwapHovered ? '#f1f3f5' : '#ffffff',
              color: '#495057',
              border: '1px solid #ced4da',
              borderRadius: '8px',
              transition: 'all 0.2s ease-in-out'
            }}
            onMouseEnter={() => setIsSwapHovered(true)}
            onMouseLeave={() => setIsSwapHovered(false)}
            onClick={onOpenSwapModal}
          >
            🔄 בקשות החלפה
            {pendingCount > 0 && (
              <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">
                {pendingCount}
              </span>
            )}
          </button>
        </div>

      </div>
    </div>
  );
}

export default StaffFilterBar;