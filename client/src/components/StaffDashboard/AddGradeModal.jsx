// src/components/StaffDashboard/AddGradeModal.jsx
import React, { useState, useEffect } from 'react';
import { getLabGroups, gradeTeam } from '../../services/staffService';
import { toast } from 'react-toastify'; // ייבוא Toastify

const FIXED_LAB_SCHEDULES = [
  { id: 1, name: "מבוא והדגמה" },
  { id: 2, name: "רובוטיקה 1" },
  { id: 3, name: "רובוטיקה 2" },
  { id: 4, name: "רובוטיקה 3" },
  { id: 5, name: "רובוטיקה 4" },
  { id: 6, name: "PLC" },
  { id: 7, name: "CNC כרסומת" },
  { id: 8, name: "CNC מחרטה" },
  { id: 9, name: "CIM" },
  { id: 10, name: "מעבדה מסכמת" }
];

const ALL_TEAMS = ['A1', 'B1', 'A2', 'B2'];

function AddGradeModal({ show, onClose, onGradeAdded }) {
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState('');
  const [selectedTeam, setSelectedTeam] = useState('');
  const [selectedSchedule, setSelectedSchedule] = useState('');

  // ציונים
  const [prepGrade, setPrepGrade] = useState('');
  const [labWorkGrade, setLabWorkGrade] = useState('');
  const [summaryGrade, setSummaryGrade] = useState('');
  
  // תאריך והערות
  const todayStr = new Date().toISOString().split('T')[0];
  const [gradeDate, setGradeDate] = useState(todayStr);
  const [internalNotes, setInternalNotes] = useState('');
  const [studentFeedback, setStudentFeedback] = useState('');

  useEffect(() => {
    if (show) {
      loadGroups();
      setSelectedGroup('');
      setSelectedTeam('');
      setSelectedSchedule('');
      setPrepGrade('');
      setLabWorkGrade('');
      setSummaryGrade('');
      setInternalNotes('');
      setStudentFeedback('');
    }
  }, [show]);

  const loadGroups = async () => {
    try {
      const data = await getLabGroups();
      setGroups(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Error loading lab groups:", err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedGroup || !selectedSchedule || !selectedTeam) {
      toast.error("נא לבחור קבוצה, צוות ומעבדה");
      return;
    }

    try {
      const payload = {
        schedule_id: Number(selectedSchedule),
        team_code: selectedTeam,
        attendance_status: "present",
        lab_work_grade: labWorkGrade !== '' ? Number(labWorkGrade) : null,
        prep_report_grade: prepGrade !== '' ? Number(prepGrade) : null,
        summary_report_grade: summaryGrade !== '' ? Number(summaryGrade) : null,
        internal_notes: internalNotes || `הזנה קבוצתית לצוות ${selectedTeam}`,
        student_feedback: studentFeedback || null
      };

      await gradeTeam(payload);
      
      // הצגת הודעת הצלחה יפהפייה עם Toastify
      toast.success("הציונים נשמרו בהצלחה!");
      
      // קריאה לפונקציה שמעדכנת את הסטייט בדשבורד הראשי (מונע את הצורך בריענון ידני)
      if (onGradeAdded) {
        onGradeAdded();
      }
      
      onClose();
    } catch (err) {
      console.error("Error saving grades:", err);
      toast.error("שגיאה בשמירת הציונים מול השרת.");
    }
  };

  if (!show) return null;

  return (
    <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 1050 }}>
      <div className="modal-dialog modal-dialog-centered modal-dialog-scrollable" style={{ maxHeight: '90vh' }}>
        <div className="modal-content shadow border-0 text-end d-flex flex-column" dir="rtl" style={{ maxHeight: '90vh' }}>
          
          <div className="modal-header bg-primary text-white flex-shrink-0">
            <h5 className="modal-title fw-bold">📝 הוספת ציון</h5>
            <button type="button" className="btn-close m-0 bg-white rounded" onClick={onClose}></button>
          </div>

          <form onSubmit={handleSubmit} className="d-flex flex-column overflow-hidden flex-grow-1">
            
            <div className="modal-body p-4 overflow-auto flex-grow-1">
              
              {/* קבוצת מעבדה */}
              <div className="mb-3">
                <label className="form-label fw-bold text-secondary small">קבוצת מעבדה</label>
                <select 
                  className="form-select" 
                  value={selectedGroup} 
                  onChange={(e) => setSelectedGroup(e.target.value)}
                  required
                >
                  <option value="">בחַר קבוצה...</option>
                  {groups.map((g, idx) => (
                    <option key={idx} value={g.group_id || g.id}>
                      {g.group_code || g.name || `קבוצה ${g.group_id || g.id}`}
                    </option>
                  ))}
                </select>
              </div>

              {/* צוות */}
              <div className="mb-3">
                <label className="form-label fw-bold text-secondary small">צוות</label>
                <select 
                  className="form-select" 
                  value={selectedTeam} 
                  onChange={(e) => setSelectedTeam(e.target.value)}
                  required
                >
                  <option value="">בחַר צוות...</option>
                  {ALL_TEAMS.map((t, idx) => (
                    <option key={idx} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              {/* מעבדה */}
              <div className="mb-3">
                <label className="form-label fw-bold text-secondary small">מעבדה</label>
                <select 
                  className="form-select" 
                  value={selectedSchedule} 
                  onChange={(e) => setSelectedSchedule(e.target.value)}
                  required
                >
                  <option value="">בחַר מעבדה...</option>
                  {FIXED_LAB_SCHEDULES.map((lab) => (
                    <option key={lab.id} value={lab.id}>
                      {lab.id} - {lab.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* הזנת ציונים לכל הצוות */}
              <div className="p-3 bg-light rounded mb-3 border">
                <h6 className="fw-bold text-primary mb-2 small">הזנת ציונים לכל הצוות:</h6>
                <div className="row g-2">
                  <div className="col-4">
                    <span className="small text-muted">דו"ח מכין:</span>
                    <input 
                      type="number" 
                      className="form-control form-control-sm mt-1" 
                      placeholder="ציון..." 
                      min="0" max="100"
                      value={prepGrade}
                      onChange={(e) => setPrepGrade(e.target.value)}
                    />
                  </div>
                  <div className="col-4">
                    <span className="small text-muted">עבודה במעבדה:</span>
                    <input 
                      type="number" 
                      className="form-control form-control-sm mt-1" 
                      placeholder="ציון..." 
                      min="0" max="100"
                      value={labWorkGrade}
                      onChange={(e) => setLabWorkGrade(e.target.value)}
                    />
                  </div>
                  <div className="col-4">
                    <span className="small text-muted">דו"ח סיכום:</span>
                    <input 
                      type="number" 
                      className="form-control form-control-sm mt-1" 
                      placeholder="ציון..." 
                      min="0" max="100"
                      value={summaryGrade}
                      onChange={(e) => setSummaryGrade(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {/* תאריך */}
              <div className="mb-3">
                <label className="form-label fw-bold text-secondary small">תאריך</label>
                <input 
                  type="date" 
                  className="form-control" 
                  value={gradeDate} 
                  onChange={(e) => setGradeDate(e.target.value)}
                  required
                />
              </div>

              {/* הערות */}
              <div className="mb-3">
                <label className="form-label fw-bold text-secondary small">הערות</label>
                <textarea 
                  className="form-control" 
                  rows="2" 
                  placeholder="הערות לצוות..."
                  value={internalNotes}
                  onChange={(e) => setInternalNotes(e.target.value)}
                ></textarea>
              </div>

            </div>

            <div className="modal-footer bg-light justify-content-start gap-2 flex-shrink-0">
              <button type="submit" className="btn btn-primary px-4 fw-bold shadow-sm">
                שמור ציונים
              </button>
              <button type="button" className="btn btn-secondary px-4" onClick={onClose}>
                ביטול
              </button>
            </div>

          </form>

        </div>
      </div>
    </div>
  );
}

export default AddGradeModal;