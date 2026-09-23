import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

import { 
  getSwapRequests, 
  updateSwapRequestStatus, 
  getStudentsList, 
  getLabGroups, 
  gradeSingleStudent, 
  gradeTeam 
} from '../services/staffService';
import { useAuth } from '../context/AuthContext';

const getStudentId = (student, index = 0) => {
  if (!student) return `fallback-${index}`;
  return student.student_id ?? student.id ?? student._id ?? student.email ?? `student-${index}`;
};

function StaffDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);

  const [swapRequests, setSwapRequests] = useState([]);
  const [students, setStudents] = useState([]);
  const [labGroups, setLabGroups] = useState([]);
  const [scheduleList, setScheduleList] = useState([]);

  const [selectedStudentId, setSelectedStudentId] = useState(null);

  const [selectedGroup, setSelectedGroup] = useState('');
  const [reserveFilter, setReserveFilter] = useState(false);

  // טופס הזנת ציון מעודכן עם שדות חובה לפי ה-Backend
  const [gradeType, setGradeType] = useState('single'); 
  const [gradeForm, setGradeForm] = useState({
    schedule_id: '',
    attendance_status: 'present', // ברירת מחדל חובה
    prep_report_grade: '',
    lab_work_grade: '',
    summary_report_grade: '',
    internal_notes: 'הוזן דרך דשבורד הסגל', // שדה חובה ב-Backend
    student_feedback: ''
  });

  const [actionModal, setActionModal] = useState({ show: false, requestId: null, status: '', reason: '' });

  useEffect(() => {
    fetchStaffData();
  }, [selectedGroup]);

  const fetchStaffData = async () => {
    setLoading(true);
    try {
      const filters = {};
      if (selectedGroup) filters.lab_id = selectedGroup;

      const [requestsRes, studentsRes, groupsRes] = await Promise.all([
        getSwapRequests(filters),
        getStudentsList(filters),
        getLabGroups()
      ]);

      const rawRequests = Array.isArray(requestsRes) ? requestsRes : (requestsRes?.requests || requestsRes?.data || []);
      const pendingRequests = rawRequests.filter(req => req.status === 'PENDING');
      setSwapRequests(pendingRequests);
      
      const loadedStudents = Array.isArray(studentsRes) ? studentsRes : (studentsRes?.users || studentsRes?.students || studentsRes?.data || []);
      setStudents(loadedStudents);

      if (loadedStudents.length > 0 && !selectedStudentId) {
        const firstId = getStudentId(loadedStudents[0], 0);
        setSelectedStudentId(String(firstId));
      }

      setLabGroups(Array.isArray(groupsRes) ? groupsRes : (groupsRes?.groups || groupsRes?.data || []));

      const extractedSchedules = [];
      loadedStudents.forEach(st => {
        if (st.labs && Array.isArray(st.labs)) {
          st.labs.forEach(l => {
            if (!extractedSchedules.some(item => item.schedule_id === l.schedule_id)) {
              extractedSchedules.push({ schedule_id: l.schedule_id, topic_name: l.topic_name || `מעבדה ${l.schedule_id}` });
            }
          });
        }
      });
      setScheduleList(extractedSchedules.length > 0 ? extractedSchedules : [
        { schedule_id: 1, topic_name: 'CNC' },
        { schedule_id: 2, topic_name: 'PLC' },
        { schedule_id: 3, topic_name: 'רובוטיקה' },
        { schedule_id: 4, topic_name: 'מיקרו-בקרים' }
      ]);

    } catch (error) {
      console.error('Error loading staff dashboard data:', error);
      toast.error('שגיאה בטעינת נתוני הדשבורד מהשרת');
    } finally {
      setLoading(false);
    }
  };

  const filteredStudents = students.filter(student => {
    if (reserveFilter) {
      return Boolean(student.is_reserve || student.is_miluim || student.reserve);
    }
    return true;
  });

  const selectedStudent = students.find((s, idx) => {
    const sId = String(getStudentId(s, idx));
    return sId === String(selectedStudentId);
  });

  const handleSelectStudent = (student, index) => {
    const sId = String(getStudentId(student, index));
    // אם הסטודנט הנוכחי כבר נבחר – לחיצה נוספת תבטל את הבחירה
    if (selectedStudentId === sId) {
      setSelectedStudentId(null);
    } else {
      setSelectedStudentId(sId);
    }
  };

  // טיפול באישור או דחיית בקשת החלפה מול השרת
  const handleSwapActionSubmit = async () => {
    try {
      const isApproved = actionModal.status === 'APPROVED';
      // אכיפה מה-Backend: דורש הערה אם נדחה
      if (!isApproved && !actionModal.reason) {
        toast.error('חובה לציין הערה או סיבה לדחיית הבקשה עבור הסטודנט');
        return;
      }

      await updateSwapRequestStatus(actionModal.requestId, isApproved, actionModal.reason);
      toast.success(isApproved ? 'בקשת ההחלפה אושרה בהצלחה' : 'בקשת ההחלפה נדחתה');
      setActionModal({ show: false, requestId: null, status: '', reason: '' });
      fetchStaffData();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'שגיאה בעדכון סטטוס הבקשה';
      toast.error(errorMsg);
    }
  };

  // שליחת ציונים לסטודנט בודד או לצוות מול השרת
  const handleGradeSubmit = async (e) => {
    e.preventDefault();
    if (!selectedStudent) return;

    try {
      const payload = {
        schedule_id: Number(gradeForm.schedule_id),
        attendance_status: gradeForm.attendance_status,
        prep_report_grade: gradeForm.prep_report_grade !== '' ? Number(gradeForm.prep_report_grade) : null,
        lab_work_grade: gradeForm.lab_work_grade !== '' ? Number(gradeForm.lab_work_grade) : null,
        summary_report_grade: gradeForm.summary_report_grade !== '' ? Number(gradeForm.summary_report_grade) : null,
        internal_notes: gradeForm.internal_notes || 'הוזן דרך המערכת',
        student_feedback: gradeForm.student_feedback || null
      };

      if (gradeType === 'single') {
        payload.student_id = Number(selectedStudent.student_id || selectedStudent.id || selectedStudent._id);
        await gradeSingleStudent(payload);
        toast.success('הציון לסטודנט עודכן בהצלחה!');
      } else {
        payload.team_code = selectedStudent.team_code;
        await gradeTeam(payload);
        toast.success(`הציון לכל צוות ${selectedStudent.team_code} עודכן בהצלחה!`);
      }

      setGradeForm({
        schedule_id: '',
        attendance_status: 'present',
        prep_report_grade: '',
        lab_work_grade: '',
        summary_report_grade: '',
        internal_notes: 'הוזן דרך דשבורד הסגל',
        student_feedback: ''
      });
      fetchStaffData();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'שגיאה בשמירת הציונים';
      toast.error(errorMsg);
    }
  };

  const renderStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED': return <span className="badge bg-success">אושר</span>;
      case 'REJECTED': return <span className="badge bg-danger">נדחה</span>;
      default: return <span className="badge bg-warning text-dark">ממתין לאישור</span>;
    }
  };

  return (
    <div className="container-fluid py-4" dir="rtl">
      
      {/* סרגל מסננים עליון */}
      <div className="card shadow-sm border-0 mb-4 bg-light">
        <div className="card-body d-flex flex-wrap align-items-center justify-content-start gap-4">
          <div className="d-flex align-items-center gap-2">
            <label className="form-label small fw-bold mb-0 text-nowrap">סינון לפי קבוצה:</label>
            <select 
              className="form-select form-select-sm"
              style={{ width: '180px' }}
              value={selectedGroup}
              onChange={(e) => setSelectedGroup(e.target.value)}
            >
              <option value="">כל הקבוצות</option>
              {Array.isArray(labGroups) && labGroups.map((group) => (
                <option key={group.group_id || group.id} value={group.group_id || group.id}>
                {group.day ? `יום ${group.day}` : ''}   |   {group.time ? group.time : ''}
                </option>
              ))}
            </select>
          </div>

          <div className="form-check mb-0">
            <input 
              className="form-check-input" 
              type="checkbox" 
              id="reserveCheck"
              checked={reserveFilter}
              onChange={(e) => setReserveFilter(e.target.checked)}
            />
            <label className="form-check-label small fw-bold" htmlFor="reserveCheck">
              🛡️ סטודנטים במילואים בלבד
            </label>
          </div>
        </div>
      </div>

      {/* פריסה ראשית */}
      <div className="row g-4">
        
        {/* טור 1 (ימין): רשימת הסטודנטים */}
        <div className="col-lg-4">
          <div className="card shadow-sm border-0 h-100">
            <div className="card-body">
              <h5 className="card-title fw-bold text-primary border-bottom pb-2 mb-3">
                👥 סטודנטים ({filteredStudents.length})
              </h5>

              {filteredStudents.length === 0 ? (
                <p className="text-muted text-center py-4">אין סטודנטים תחת המסננים שנבחרו</p>
              ) : (
                <div className="list-group list-group-flush" style={{ maxHeight: '550px', overflowY: 'auto' }}>
                  {filteredStudents.map((student, index) => {
                    const studentId = String(getStudentId(student, index));
                    const isSelected = studentId === String(selectedStudentId);

                    return (
                      <div
                        key={studentId}
                        className={`d-flex justify-content-between align-items-center p-2 mb-2 rounded border transition-all ${
                          isSelected ? 'border-primary bg-primary bg-opacity-10 shadow-sm' : 'bg-white border-light'
                        }`}
                        style={{ cursor: 'pointer' }}
                        onClick={() => handleSelectStudent(student, index)}
                      >
                        <div>
                          <div className={`fw-bold ${isSelected ? 'text-primary' : 'text-dark'}`}>
                            {student.full_name || student.name}
                          </div>
                          <div className="small text-muted mt-1">
                            צוות: <span className="badge bg-secondary">{student.team_code || 'ללא'}</span>
                            { (student.is_reserve || student.is_miluim || student.reserve) && <span className="badge bg-warning text-dark ms-2">מילואים</span>}
                          </div>
                        </div>
                        <button 
                          type="button"
                          className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-outline-primary'}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSelectStudent(student, index);
                          }}
                        >
                          {isSelected ? 'נבחר ✓' : 'בחר →'}
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* טור 2 (אמצע): פירוט מעבדות והזנת ציונים לסטודנט הנבחר */}
        <div className="col-lg-5">
          <div className="card shadow-sm border-0 h-100">
            <div className="card-body">
              <h5 className="card-title fw-bold text-success border-bottom pb-2 mb-3">
                📊 מעבדות וציונים {selectedStudent ? `- ${selectedStudent.full_name || selectedStudent.name}` : ''}
              </h5>

              {!selectedStudent ? (
                <div className="text-center text-muted py-5 my-4">
                  <div className="display-4 mb-2">👉</div>
                  <p>בחר סטודנט מהרשימה מימין כדי לצפות במעבדות שלו ולהזין ציונים</p>
                </div>
              ) : (
                <div>
                  <div className="bg-light p-3 rounded mb-3 small">
                    <div className="row">
                      <div className="col-6"><strong>צוות:</strong> {selectedStudent.team_code || 'ללא'}</div>
                      <div className="col-6"><strong>מילואים:</strong> {selectedStudent.is_reserve || selectedStudent.is_miluim || selectedStudent.reserve ? 'כן 🛡️' : 'לא'}</div>
                    </div>
                  </div>

                  <h6 className="fw-bold text-dark mb-2">מעבדות וסטטוס הגשה:</h6>
                  <div className="table-responsive mb-4" style={{ maxHeight: '180px', overflowY: 'auto' }}>
                    <table className="table table-sm table-bordered text-center small align-middle">
                      <thead className="table-light">
                        <tr>
                          <th>מעבדה</th>
                          <th>ציונים קיימים (מכין/עבודה/מסכם)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedStudent.labs && selectedStudent.labs.length > 0 ? (
                          selectedStudent.labs.map((lab, idx) => (
                            <tr key={idx}>
                              <td>{lab.topic_name || `מעבדה ${lab.schedule_id}`}</td>
                              <td>
                                {lab.prep ?? '-'} / {lab.lab_work ?? '-'} / {lab.summary ?? '-'}
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan="2" className="text-muted">
                              {selectedStudent.grades ? (
                                <span>מכין: {selectedStudent.grades.prep ?? '-'} | מעבדה: {selectedStudent.grades.lab ?? '-'} | מסכם: {selectedStudent.grades.summary ?? '-'}</span>
                              ) : (
                                'אין עדיין נתוני מעבדות מפורטים, ניתן להזין למטה.'
                              )}
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  <form onSubmit={handleGradeSubmit} className="border p-3 rounded bg-white shadow-sm">
                    <h6 className="fw-bold text-primary mb-3">✏️ הזנת / עדכון ציון למעבדה</h6>
                    
                    <div className="mb-2">
                      <label className="form-label small fw-bold">רמת הזנה:</label>
                      <div className="d-flex gap-3">
                        <div className="form-check">
                          <input 
                            className="form-check-input" 
                            type="radio" 
                            name="gradeTypeRadio" 
                            id="typeSingle" 
                            checked={gradeType === 'single'}
                            onChange={() => setGradeType('single')}
                          />
                          <label className="form-check-label small" htmlFor="typeSingle">סטודנט נוכחי בלבד</label>
                        </div>
                        <div className="form-check">
                          <input 
                            className="form-check-input" 
                            type="radio" 
                            name="gradeTypeRadio" 
                            id="typeTeam" 
                            checked={gradeType === 'team'}
                            onChange={() => setGradeType('team')}
                          />
                          <label className="form-check-label small" htmlFor="typeTeam">לכל צוות {selectedStudent.team_code || ''}</label>
                        </div>
                      </div>
                    </div>

                    <div className="mb-2">
                      <label className="form-label small fw-bold">בחר מעבדה:</label>
                      <select 
                        className="form-select form-select-sm"
                        required
                        value={gradeForm.schedule_id}
                        onChange={(e) => setGradeForm({ ...gradeForm, schedule_id: e.target.value })}
                      >
                        <option value="">בחר מעבדה מהרשימה...</option>
                        {scheduleList.map((sch) => (
                          <option key={sch.schedule_id} value={sch.schedule_id}>
                            {sch.topic_name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="mb-2">
                      <label className="form-label small fw-bold">סטטוס נוכחות:</label>
                      <select 
                        className="form-select form-select-sm"
                        value={gradeForm.attendance_status}
                        onChange={(e) => setGradeForm({ ...gradeForm, attendance_status: e.target.value })}
                      >
                        <option value="present">נוכח (present)</option>
                        <option value="absent">נעדר (absent)</option>
                        <option value="miluim">מילואים (miluim)</option>
                        <option value="justified">מוצדק (justified)</option>
                      </select>
                    </div>

                    <div className="row g-2 mb-2">
                      <div className="col-4">
                        <label className="form-label small">דוח מכין</label>
                        <input 
                          type="number" 
                          className="form-control form-control-sm" 
                          min="0" max="100"
                          value={gradeForm.prep_report_grade}
                          onChange={(e) => setGradeForm({ ...gradeForm, prep_report_grade: e.target.value })}
                        />
                      </div>
                      <div className="col-4">
                        <label className="form-label small">עבודה במעבדה</label>
                        <input 
                          type="number" 
                          className="form-control form-control-sm" 
                          min="0" max="100"
                          value={gradeForm.lab_work_grade}
                          onChange={(e) => setGradeForm({ ...gradeForm, lab_work_grade: e.target.value })}
                        />
                      </div>
                      <div className="col-4">
                        <label className="form-label small">דוח מסכם</label>
                        <input 
                          type="number" 
                          className="form-control form-control-sm" 
                          min="0" max="100"
                          value={gradeForm.summary_report_grade}
                          onChange={(e) => setGradeForm({ ...gradeForm, summary_report_grade: e.target.value })}
                        />
                      </div>
                    </div>

                    <div className="mb-2">
                      <label className="form-label small">הערות פנימיות (חובה):</label>
                      <input 
                        type="text" 
                        className="form-control form-control-sm" 
                        required
                        value={gradeForm.internal_notes}
                        onChange={(e) => setGradeForm({ ...gradeForm, internal_notes: e.target.value })}
                        placeholder="הערות פנימיות..."
                      />
                    </div>

                    <div className="mb-3">
                      <label className="form-label small">משוב לסטודנט:</label>
                      <input 
                        type="text" 
                        className="form-control form-control-sm" 
                        value={gradeForm.student_feedback}
                        onChange={(e) => setGradeForm({ ...gradeForm, student_feedback: e.target.value })}
                        placeholder="משוב אופציונלי..."
                      />
                    </div>

                    <button type="submit" className="btn btn-primary btn-sm w-100 fw-bold">
                      שמור ציון ל{gradeType === 'single' ? 'סטודנט' : 'צוות'}
                    </button>
                  </form>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* טור 3 (שמאל): בקשות החלפה ממתינות */}
        <div className="col-lg-3">
          <div className="card shadow-sm border-0 h-100">
            <div className="card-body">
              <h5 className="card-title fw-bold text-secondary border-bottom pb-2 mb-3">
                🔄 בקשות החלפה ({Array.isArray(swapRequests) ? swapRequests.length : 0})
              </h5>

              {!Array.isArray(swapRequests) || swapRequests.length === 0 ? (
                <p className="text-muted text-center py-4 small">אין בקשות החלפה ממתינות</p>
              ) : (
                <div className="d-flex flex-column gap-3" style={{ maxHeight: '550px', overflowY: 'auto' }}>
                  {swapRequests.map((req) => {
                    const reqId = req.request_id || req.id;
                    return (
                      <div key={reqId} className="p-3 bg-light rounded border small">
                        <div className="d-flex justify-content-between align-items-center mb-1">
                          <span className="fw-bold text-dark">{req.student_name || 'סטודנט'}</span>
                          {renderStatusBadge(req.status)}
                        </div>
                        <div className="text-secondary mb-2">
                          <div><strong>נוכחית:</strong> {req.current_topic_name || req.current_schedule_id}</div>
                          <div><strong>מבוקשת:</strong> {req.target_topic_name || req.target_schedule_id}</div>
                          <div className="text-muted mt-1"><strong>סיבה:</strong> {req.reason}</div>
                        </div>

                        {req.status === 'PENDING' && (
                          <div className="d-flex gap-2 pt-2 border-top">
                            <button 
                              type="button"
                              className="btn btn-success btn-sm flex-fill py-1"
                              onClick={() => setActionModal({ show: true, requestId: reqId, status: 'APPROVED', reason: '' })}
                            >
                              אשר ✓
                            </button>
                            <button 
                              type="button"
                              className="btn btn-danger btn-sm flex-fill py-1"
                              onClick={() => setActionModal({ show: true, requestId: reqId, status: 'REJECTED', reason: '' })}
                            >
                              דחה ✕
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

      {/* מודל הזנת סיבה לאישור/דחיית בקשת החלפה */}
      {actionModal.show && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered" dir="rtl">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title fw-bold">
                  {actionModal.status === 'APPROVED' ? 'אישור בקשת החלפה' : 'דחיית בקשת החלפה'}
                </h5>
                <button type="button" className="btn-close m-0" onClick={() => setActionModal({ show: false, requestId: null, status: '', reason: '' })}></button>
              </div>
              <div className="modal-body">
                <div className="mb-3">
                  <label className="form-label small fw-bold">
                    הערה / סיבה {actionModal.status === 'REJECTED' ? '(חובה לדחייה)' : '(אופציונלי)'}:
                  </label>
                  <textarea 
                    className="form-control form-control-sm" 
                    rows="3"
                    value={actionModal.reason}
                    onChange={(e) => setActionModal({ ...actionModal, reason: e.target.value })}
                    placeholder="הכנס הערה לסטודנט..."
                  ></textarea>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setActionModal({ show: false, requestId: null, status: '', reason: '' })}>ביטול</button>
                <button 
                  type="button" 
                  className={`btn btn-sm ${actionModal.status === 'APPROVED' ? 'btn-success' : 'btn-danger'}`}
                  onClick={handleSwapActionSubmit}
                >
                  {actionModal.status === 'APPROVED' ? 'אשר בקשה סופית' : 'דחה בקשה סופית'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default StaffDashboard;