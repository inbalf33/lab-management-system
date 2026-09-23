// src/components/StaffDashboard/GrgradesList.jsx
import React, { useState } from 'react';
import { deleteGrade } from '../../services/staffService';
import AddGradeModal from './AddGradeModal';

function GrgradesList({ 
  selectedStudent, 
  onAddGrade, 
  onEditGrade, 
  onGradeDeleted,
  onGradeAdded // הוספנו את זה לוודא שזה מתקבל בצורה מסודרת מהאב
}) {
  // סטייט לניהול מודל האישור למחיקה
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [labToDelete, setLabToDelete] = useState(null);

  const [showAddModal, setShowAddModal] = useState(false);

  // סינון מעבדות של הסטודנט שנבחר בלבד
  const performedLabs = selectedStudent && selectedStudent.labs ? selectedStudent.labs.filter(lab => {
    const finalScore = lab.final_calculated_grade ?? lab.summary ?? lab.summary_report_grade;
    return finalScore !== null && finalScore !== undefined && finalScore !== '-';
  }) : [];

  const handleOpenDeleteModal = (lab) => {
    if (!lab.grade_id) {
      alert("שגיאה: מזהה הציון (grade_id) אינו זמין עבור מעבדה זו.");
      return;
    }
    setLabToDelete(lab);
    setShowDeleteModal(true);
  };

  const handleConfirmDelete = async () => {
    if (!labToDelete) return;

    try {
      await deleteGrade(labToDelete.grade_id);
      setShowDeleteModal(false);
      setLabToDelete(null);
      
      if (onGradeDeleted) {
        onGradeDeleted();
      } else {
        window.location.reload();
      }
    } catch (error) {
      console.error("Error deleting grade:", error);
      alert("שגיאה במחיקת הציון מול השרת.");
    }
  };

  return (
    <div className="card shadow-sm border-0 h-100 position-relative">
      <div className="card-body d-flex flex-column p-3">
        
        {/* כותרת מימין וכפתור פלוס משמאל */}
        <div className="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2">
          <h5 className="card-title fw-bold text-primary m-0">
            📊 ציונים
          </h5>
          
          <button
            type="button"
            className="btn btn-success btn-sm d-flex align-items-center gap-1 px-3 shadow-sm fw-bold"
            onClick={() => setShowAddModal(true)}
            title="הוסף ציון חדש"
          >
            <span className="fs-5 lh-1">+</span> הוסף ציון
          </button>
        </div>

        {/* אם לא נבחר סטודנט */}
        {!selectedStudent ? (
          <div className="text-center text-muted py-5 my-auto">
            <div className="display-4 mb-2">🎯</div>
            <p className="fw-medium text-secondary">בחר סטודנט מהרשימה כדי לצפות בציונים שלו</p>
          </div>
        ) : (
          /* מצב סטודנט ספציפי שנבחר */
          <div className="d-flex flex-column flex-grow-1">
            <div className="mb-3 text-end bg-light p-2 rounded">
              <h6 className="fw-bold text-primary mb-1">
                {selectedStudent.full_name || `${selectedStudent.first_name || ''} ${selectedStudent.last_name || ''}`.trim()}
              </h6>
              <div className="text-muted small">
                צוות: {selectedStudent.team_code || 'ללא'} | מילואים: {selectedStudent.is_miluim ? 'כן 🛡️' : 'לא'}
              </div>
            </div>

            <h6 className="fw-bold text-dark mb-2 text-end">מעבדות וציונים:</h6>
            
            <div className="list-group list-group-flush flex-grow-1" style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {performedLabs.length > 0 ? (
                performedLabs.map((lab, idx) => {
                  const rawLabScore = Number(lab.final_calculated_grade ?? lab.summary ?? lab.summary_report_grade);
                  const finalLabScore = !isNaN(rawLabScore) ? Math.round(rawLabScore) : '-';
                  const labTitle = lab.topic_name || `מעבדה ${lab.schedule_id || (idx + 1)}`;

                  return (
                    <div key={idx} className="d-flex align-items-center justify-content-between p-2 mb-2 rounded border bg-white border-light shadow-sm">
                      
                      {/* צד ימין: שם המעבדה ומזהה מפגש */}
                      <div className="text-end">
                        <div className="fw-bold text-dark">{labTitle}</div>
                        {lab.schedule_id && <div className="text-muted" style={{ fontSize: '0.75rem' }}>מזהה מפגש: {lab.schedule_id}</div>}
                      </div>

                      {/* צד שמאל: הציון וכפתורי עריכה ומחיקה */}
                      <div className="d-flex align-items-center gap-2">
                        <span className="fw-bold fs-4 text-primary" style={{ minWidth: '35px', textAlign: 'center' }}>
                          {finalLabScore}
                        </span>

                        <div className="d-flex gap-1 bg-light p-1 rounded border">
                          <button
                            className="btn btn-sm btn-light py-0 px-1 border-0"
                            onClick={() => {
                              if (onEditGrade) onEditGrade(lab);
                            }}
                            title="ערוך ציון"
                            style={{ fontSize: '1rem' }}
                          >
                            ✏️
                          </button>
                          
                          <button
                            className="btn btn-sm btn-light py-0 px-1 border-0 text-danger"
                            onClick={() => handleOpenDeleteModal(lab)}
                            title="מחק ציון"
                            style={{ fontSize: '1rem' }}
                          >
                            🗑️
                          </button>
                        </div>
                      </div>

                    </div>
                  );
                })
              ) : (
                <div className="text-center text-muted py-4 my-auto">
                  <p>אין ציונים רשומים לסטודנט זה עדיין</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* מודל מחיקה מעוצב בסגנון Bootstrap */}
      {showDeleteModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content shadow border-0 text-end" dir="rtl">
              <div className="modal-header bg-danger text-white">
                <h5 className="modal-title fw-bold">⚠️ אישור מחיקת ציון</h5>
                <button 
                  type="button" 
                  className="btn-close m-0" 
                  onClick={() => setShowDeleteModal(false)}
                ></button>
              </div>
              <div className="modal-body py-4">
                <p className="mb-1">האם את בטוחה שברצונך למחוק את הציון עבור:</p>
                <p className="fw-bold text-primary fs-5 mb-0">
                  {labToDelete?.topic_name || 'מעבדה נבחרת'}
                </p>
                <p className="text-muted small mt-2 mb-0">פעולה זו תמחק את הרשומה לצמיתות ממאגר הנתונים.</p>
              </div>
              <div className="modal-footer justify-content-start gap-2 bg-light">
                <button 
                  type="button" 
                  className="btn btn-danger px-4 fw-bold" 
                  onClick={handleConfirmDelete}
                >
                  מחק לצמיתות
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary px-4" 
                  onClick={() => setShowDeleteModal(false)}
                >
                  ביטול
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* מודל הוספת ציון */}
      <AddGradeModal 
        show={showAddModal} 
        onClose={() => setShowAddModal(false)} 
        onGradeAdded={() => {
          setShowAddModal(false);
          // קריאה לפונקציות העדכון של האב (גם onGradeAdded וגם onGradeDeleted לצורך גיבוי)
          if (onGradeAdded) onGradeAdded();
          if (onGradeDeleted) onGradeDeleted();
        }}
        selectedStudent={selectedStudent}
      />

    </div>
  );
}

GrgradesList.defaultProps = {
  onGradeAdded: () => {}
};

export default GrgradesList;