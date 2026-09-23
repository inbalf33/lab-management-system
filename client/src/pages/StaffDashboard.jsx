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

// ייבוא הקומפוננטות
import StaffFilterBar from '../components/StaffDashboard/StaffFilterBar';
import StudentsListSidebar from '../components/StaffDashboard/StudentsListSidebar';
import GrgradesList from '../components/StaffDashboard/GrgradesList';
import DetailsView from '../components/StaffDashboard/DetailsView';

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

  // מודל ניהול בקשות החלפה
  const [showSwapModal, setShowSwapModal] = useState(false);

  // טופס הזנת ציון
  const [gradeType, setGradeType] = useState('single'); 
  const [gradeForm, setGradeForm] = useState({
    schedule_id: '',
    attendance_status: 'present',
    prep_report_grade: '',
    lab_work_grade: '',
    summary_report_grade: '',
    internal_notes: 'הוזן דרך דשבורד הסגל',
    student_feedback: ''
  });

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
    if (selectedStudentId === sId) {
      setSelectedStudentId(null);
    } else {
      setSelectedStudentId(sId);
    }
  };

  const handleActionClick = async (requestId, status) => {
    try {
      let reason = '';
      if (status === 'REJECTED') {
        reason = prompt('נא הזן סיבה לדחיית הבקשה:') || 'נדחה ע"י הסגל';
      }
      await updateSwapRequestStatus(requestId, status === 'APPROVED', reason);
      toast.success(status === 'APPROVED' ? 'בקשת ההחלפה אושרה' : 'בקשת ההחלפה נדחתה');
      fetchStaffData();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || 'שגיאה בעדכון סטטוס הבקשה';
      toast.error(errorMsg);
    }
  };

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

  return (
    <div className="container-fluid py-4" dir="rtl">
      
      {/* סרגל מסננים עליון */}
      <StaffFilterBar 
        labGroups={labGroups}
        selectedGroup={selectedGroup}
        setSelectedGroup={setSelectedGroup}
        reserveFilter={reserveFilter}
        setReserveFilter={setReserveFilter}
        pendingCount={swapRequests.length}
        onOpenSwapModal={() => setShowSwapModal(true)}
      />

      {/* פריסה ראשית ל-3 טורים (מימין לשמאל ב-RTL: סטודנטים -> ציונים -> פרטים נוספים) */}
      <div className="row g-4">
        
        {/* טור 1 (ימני ביותר): רשימת הסטודנטים */}
        <div className="col-lg-4">
          <StudentsListSidebar 
            students={filteredStudents}
            selectedStudentId={selectedStudentId}
            getStudentId={getStudentId}
            onSelectStudent={handleSelectStudent}
          />
        </div>

        {/* טור 2 (אמצעי): רשימת ציונים והזנת ציון */}
        <div className="col-lg-4">
          <GrgradesList 
            selectedStudent={selectedStudent}
            scheduleList={scheduleList}
            gradeType={gradeType}
            setGradeType={setGradeType}
            gradeForm={gradeForm}
            setGradeForm={setGradeForm}
            handleGradeSubmit={handleGradeSubmit}
          />
        </div>

        {/* טור 3 (שמאלי ביותר): פרטים נוספים */}
        <div className="col-lg-4">
          <div className="card shadow-sm border-0 h-100">
            <div className="card-header bg-white fw-bold py-3 text-secondary">
              <i className="bi bi-info-circle ms-2"></i>
              פירוט נוסף
            </div>
            <div className="card-body d-flex flex-column align-items-center justify-content-center text-center text-muted py-5">
              <i className="bi bi-lightbulb fs-1 text-warning mb-3"></i>
              <p className="mb-0">
                {selectedStudent 
                  ? `מציג פרטים נוספים עבור: ${selectedStudent.full_name || selectedStudent.name || 'סטודנט נבחר'}`
                  : 'כדי להתחיל סנן קבוצה או בחר סטודנט / ציון מהרשימה כדי לצפות בפרטים המלאים'
                }
              </p>
            </div>
          </div>
        </div>

      </div>

      {/* מודל ניהול בקשות החלפה */}
      <DetailsView 
        show={showSwapModal}
        onClose={() => setShowSwapModal(false)}
        swapRequests={swapRequests}
        onActionClick={handleActionClick}
      />

    </div>
  );
}

export default StaffDashboard;