import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { getMyRegistrations, getMyGrades, lockScheduleSlot, unlockScheduleSlot, 
  registerToSchedule, getMyFinalGrades, getMyCompletedScheduleIds, cancelSwapRequest} from '../services/studentService';
import { useAuth } from '../context/AuthContext'; // הוספת הייבוא של ההזדהות
import api from '../services/api';

function StudentDashboard() {

  
  const { user } = useAuth(); // שליפת ה-user מהקונטקסט
  const [loading, setLoading] = useState(true);
  const [groupInfo, setGroupInfo] = useState({ code: '', day: '', time: '' });
  const [teamCode, setTeamCode] = useState(null);
  const [upcomingLabs, setUpcomingLabs] = useState([]);
  const [swapRequests, setSwapRequests] = useState([]);
  const [completedLabs, setCompletedLabs] = useState([]);

  // משתנים עבור מודל החלפת מעבדה
  const [showModal, setShowModal] = useState(false);
  const [selectedLab, setSelectedLab] = useState(null);
  const [availableSlots, setAvailableSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  
  const [modalStep, setModalStep] = useState(1);
  const [selectedTargetSlot, setSelectedTargetSlot] = useState(null);
  const [swapReason, setSwapReason] = useState('');

  const [lockedScheduleId, setLockedScheduleId] = useState(null);
  const [completedScheduleIds, setCompletedScheduleIds] = useState([]);

  const [cancelModalId, setCancelModalId] = useState(null); // שומר את ה-ID של הבקשה שרוצים לבטל

  // הגדרת הפונקציה מחוץ ל-useEffect כדי שאפשר לקרוא לה שוב
  const fetchData = async () => {
    try {
      const [regData, completedIds, gradesRes] = await Promise.all([
        getMyRegistrations(),
        getMyCompletedScheduleIds(),
        getMyGrades()
      ]);

      setCompletedScheduleIds(completedIds);
      setGroupInfo({
        group_id: regData.group_id,
        code: regData.group_code || '',
        day: regData.group_day || '',
        time: regData.group_time || ''
      });
      setTeamCode(regData.team_code);
      setSwapRequests(regData.swap_requests || [] );

      const allSchedules = regData.regular_schedules || [];
      let rawCompleted = gradesRes;
      if (!rawCompleted || rawCompleted.length === 0) {
        rawCompleted = (completedIds || []).map(id => {
          const found = allSchedules.find(s => s.schedule_id === id);
          return found || { schedule_id: id };
        });
      }

      const enrichedCompletedLabs = (rawCompleted || []).map((item, index) => {
        const scheduleInfo = allSchedules.find(s => s.schedule_id === item.schedule_id) || {};
        return {
          ...item,
          topic_name: item.topic_name || item.lab_name || scheduleInfo.topic_name || scheduleInfo.lab_name || `מעבדה מספר ${item.schedule_id || index + 1}`
        };
      });

      setCompletedLabs(enrichedCompletedLabs);

      const completedSet = new Set([
        ...(completedIds || []),
        ...(rawCompleted || []).map(g => g.schedule_id).filter(Boolean)
      ]);

      const filteredUpcoming = allSchedules.filter(
        lab => !completedSet.has(lab.schedule_id)
      );
      setUpcomingLabs(filteredUpcoming);

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast.error('שגיאה בטעינת נתוני הדשבורד מהשרת');
    } finally {
      setLoading(false);
    }
  };

useEffect(() => {
  fetchData();
}, []);

const [timeLeft,setTimeLeft] = useState(600); // 10 דקות בשניות

useEffect(() => {
  let timer = null;
  if (lockedScheduleId) {
    setTimeLeft(600); // איפוס ל-10 דקות כשנפתח מועד נעול
    timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          // כשהזמן נגמר אפשר לסגור או לשחרר אוטומטית
          handleCloseModal();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }
  return () => {
    if (timer) clearInterval(timer);
  };
}, [lockedScheduleId]);

// פונקציית עזר להמרת שניות לפורמט MM:SS
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
  const secs = (seconds % 60).toString().padStart(2, '0');
  return `${mins}:${secs}`;
};
   
const handleOpenSwapModal = async (lab) => {
    setSelectedLab(lab);
    setModalStep(1);
    setSelectedTargetSlot(null);
    setSwapReason('');
    setShowModal(true);
    setLoadingSlots(true);

    try {
      // מוודאים ששולפים לפי המזהה הנכון של הנושא/מעבדה
      const topicId = lab.topic_id || lab.lab_id;

      // 1. שליפת כל המועדים ששייכים לאותו נושא מעבדה (בכל הקבוצות)
      const topicPromise = topicId ? api.get('/api/schedules', {
        params: { topic_id: topicId }
      }) : Promise.resolve({ data: [] });

      // 2. שליפת כל מעבדות ההשלמה במערכת
      const completionPromise = api.get('/api/schedules', {
        params: { session_type: 'COMPLETION' }
      });

      const [topicRes, completionRes] = await Promise.all([topicPromise, completionPromise]);

      // איחוד התוצאות ומניעת כפילויות
      const allSlots = [...(topicRes.data || []), ...(completionRes.data || [])];
      const uniqueSlots = Array.from(
        new Map(allSlots.map(slot => [slot.schedule_id, slot])).values()
      );

      // סינון מדויק: מציגים רק את אותה מעבדה (בכל קבוצה שהיא) או מעבדות השלמה, ולא את המפגש הנוכחי עצמו
      const filteredSlots = uniqueSlots.filter(slot => {
        if (slot.schedule_id === lab.schedule_id) return false;

        const isSameTopic = topicId && Number(slot.topic_id || slot.lab_id) === Number(topicId);
        const isCompletion = slot.session_type === 'COMPLETION';

        return isSameTopic || isCompletion;
      });
      
      setAvailableSlots(filteredSlots);
    } catch (error) {
      console.error('Error fetching available slots for swap:', error);
      toast.error('שגיאה בטעינת מועדים חלופיים');
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };
 
  const handleCloseModal = async () => {
      // אם יש מועד שננעל ב-Redis, משחררים אותו בעת סגירת המודל או ביטול
      if (lockedScheduleId) {
        try {
          await unlockScheduleSlot(lockedScheduleId);
        } catch (err) {
          console.error('Error unlocking slot on close:', err);
        }
        setLockedScheduleId(null);
      }

      setShowModal(false);
      setSelectedLab(null);
      setAvailableSlots([]);
      setModalStep(1);
      setSelectedTargetSlot(null);
      setSwapReason('');
    };

  // פונקציה לחזרה לשלב הראשון ושחרור הנעילה ב-Redis
  const handleBackToStep1 = async () => {
    if (lockedScheduleId) {
      try {
        await unlockScheduleSlot(lockedScheduleId);
      } catch (err) {
        console.error('Error unlocking slot on back step:', err);
      }
      setLockedScheduleId(null);
    }
    setSelectedTargetSlot(null);
    setModalStep(1);
  };

  const renderStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED':
        return <span className="badge bg-success">אושר</span>;
      case 'REJECTED':
        return <span className="badge bg-danger">נדחה</span>;
      default:
        return <span className="badge bg-warning text-dark">ממתין לאישור</span>;
    }
  };

  const [showGradesModal, setShowGradesModal] = useState(false);
  const [grades, setGrades] = useState([]);
  const [finalGrade, setFinalGrade] = useState('-');
  const [loadingGrades, setLoadingGrades] = useState(false);

  const handleOpenGradesModal = async () => {
    setShowGradesModal(true);
    setLoadingGrades(true);
    try {
      const [gradesRes, finalRes] = await Promise.all([
        getMyGrades(),
        getMyFinalGrades()
      ]);

      setGrades(gradesRes);
      setFinalGrade(finalRes[0]?.final_score || '-');
      
    } catch (err) {
      console.error("Error fetching grades:", err);
      toast.error("שגיאה בטעינת הציונים");
    } finally {
      setLoadingGrades(false);
    }
  };

  if (loading) {
    return <div className="text-center py-5 text-muted">טוען נתונים...</div>;
  }

  // שלב 1: לחיצה על כפתור הביטול בכרטיסייה פותחת את המודל המעוצב
  const handleCancelClick = (requestId) => {
    setCancelModalId(requestId);
  };

  // שלב 2: לחיצה על אישור מתוך המודל מריצה את המחיקה מול השרת
  const confirmCancelSwap = async () => {
    if (!cancelModalId) return;

    try {
      await cancelSwapRequest(cancelModalId);
      setSwapRequests(prevRequests => prevRequests.filter(req => req.request_id !== cancelModalId));
      setCancelModalId(null); // סגירת המודל
    } catch (error) {
      alert(error.detail || "שגיאה בביטול הבקשה, נסי שוב מאוחר יותר");
      setCancelModalId(null);
    }
  };

  const pendingSwapLabIds = new Set(
    swapRequests
      .filter(req => req.status === 'PENDING')
      .map(req => req.current_date ? new Date(req.current_date).toISOString().split('T')[0] : null)
  );

  return (
    <div>
      {/* תצוגת פרטי הקבוצה והשעה מתחת לנאוובאר */}
      <div className="alert alert-light border shadow-sm d-flex justify-content-between align-items-center mb-4 py-2">
        <div>
          <span className="me-4">
            קבוצת מעבדה: <strong className="text-primary"> יום {groupInfo.day} {groupInfo.time}</strong>
          </span>
          <span> | צוות מעבדה: <strong className="text-primary">{teamCode || 'לא הוגדר'}</strong></span>
        </div>
        <button 
          className="btn btn-outline-primary btn-sm me-2"
          onClick={handleOpenGradesModal}
        >
          📊 ציוני מעבדה
        </button>
      </div>

      {/* פריסת 3 הטורים */}
      <div className="row g-4 pt-2">
        
        {/* טור ימין: מעבדות לביצוע */}
        <div className="col-lg-4">
          <div className="card shadow-sm h-100 border-0">
            <div className="card-body">
              <h4 className="card-title fw-bold mb-3 text-primary border-bottom pb-2">מעבדות לביצוע</h4>
              {upcomingLabs.length === 0 ? (
                <p className="text-muted text-center py-4">אין מעבדות מיועדות</p>
              ) : (
                <div className="d-flex flex-column gap-3" style={{ maxHeight: '550px', overflowY: 'auto' }}>                  

                  {(() => {

                    const pendingSwapLabIds = new Set(
                      swapRequests
                        .filter(req => req.status === 'PENDING')
                        .map(req => req.current_schedule_id)
                    );

                    const approvedSwapsMap = new Map();
                    swapRequests
                      .filter(req => req.status === 'APPROVED')
                      .forEach(req => {
                        approvedSwapsMap.set(req.current_schedule_id, req);
                      });

                    const sortedLabs = [...upcomingLabs].sort((a, b) => {
                      const swapA = approvedSwapsMap.get(a.schedule_id);
                      const swapB = approvedSwapsMap.get(b.schedule_id);

                      const dateA = new Date(swapA ? swapA.target_date : a.lab_date);
                      const dateB = new Date(swapB ? swapB.target_date : b.lab_date);

                      return dateA - dateB;
                    });

                    return sortedLabs.map((lab) => {
                      const isPending = pendingSwapLabIds.has(lab.schedule_id);
                      const approvedSwap = approvedSwapsMap.get(lab.schedule_id);
                      const isApprovedSwap = Boolean(approvedSwap);

                      const targetDateObj = approvedSwap && approvedSwap.target_date ? new Date(approvedSwap.target_date) : null;
                      const originalDateObj = lab.lab_date ? new Date(lab.lab_date) : null;

                      const displayDate = originalDateObj ? originalDateObj.toLocaleDateString('he-IL') : '';

                      const formattedTargetDate = targetDateObj 
                        ? targetDateObj.toLocaleDateString('he-IL', { weekday: 'long', year: 'numeric', month: '2-digit', day: '2-digit' })
                        : '';
                      
                      // שימוש בטווח השעות שהגיע מהשרת (למשל "09:00 - 11:45"), ואם אין אז נציג ברירת מחדל
                      const displayTimeRange = approvedSwap && approvedSwap.target_time 
                        ? approvedSwap.target_time 
                        : (targetDateObj ? targetDateObj.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' }) : '');

                      let cardClass = "p-3 rounded border d-flex justify-content-between align-items-center ";
                      if (isApprovedSwap) {
                        cardClass += "bg-info-subtle border-info-subtle";
                      } else if (isPending) {
                        cardClass += "bg-warning-subtle border-warning";
                      } else {
                        cardClass += "bg-light";
                      }

                      return (
                        <div key={lab.schedule_id} className={cardClass}>
                          {/* צד ימין: שם המעבדה, תגית ותאריך */}
                          <div>
                            <div className="d-flex align-items-center gap-2 mb-1">
                              <h5 className="mb-0 fw-bold">{lab.topic_name || `נושא ${lab.topic_id}`}</h5>
                              {isApprovedSwap && (
                                <span className="badge bg-info text-dark px-2 py-1 fw-bold" style={{ fontSize: '0.75rem' }}>
                                  הוחלף בהצלחה
                                </span>
                              )}
                            </div>
                            
                           
                            {isApprovedSwap ? (
                              <small className="text-dark fw-semibold d-block">
                                מועד חדש: {formattedTargetDate} {displayTimeRange ? ` שעה: ${displayTimeRange}` : ''}
                              </small>
                            ) : (
                              <small className="text-muted d-block">
                                תאריך: {displayDate}
                              </small>
                            )}
                          </div>
                          
                          {/* צד שמאל: תגית ממתין לאישור או כפתור החלפה */}
                          {isPending ? (
                            <span className="badge bg-warning text-dark px-2 py-1 fw-bold" style={{ fontSize: '0.8rem' }}>
                              ממתין לאישור
                            </span>
                          ) : (!isApprovedSwap && lab.session_type !== 'COMPLETION' && (
                            <button 
                              className="btn btn-outline-primary btn-sm"
                              onClick={() => handleOpenSwapModal(lab)}
                            >
                              בקשת החלפה
                            </button>
                          ))}
                        </div>
                      );
                    });
                  })()}

                </div>
              )}
            </div>
          </div>
        </div>

        {/* טור אמצע: מעבדות שבוצעו */}
        <div className="col-lg-4">
          <div className="card shadow-sm h-100 border-0">
            <div className="card-body">
              <h4 className="card-title fw-bold mb-3 text-secondary border-bottom pb-2">מעבדות שבוצעו</h4>
              {completedLabs.length === 0 ? (
                <p className="text-muted text-center py-4">טרם הושלמו מעבדות</p>
              ) : (
                <div className="d-flex flex-column gap-3" style={{ maxHeight: '550px', overflowY: 'auto' }}>
                  {completedLabs.map((gradeItem, index) => {                    
                    // בדיקת כל האפשרויות האפשריות לשם המעבדה או הנושא
                    const labDisplayName = gradeItem.topic_name || gradeItem.lab_name || gradeItem.name || gradeItem.title || `מעבדה מספר ${gradeItem.schedule_id || index + 1}`;

                    return (
                      <div key={gradeItem.grade_id || index} className="p-3 bg-light rounded border-start border-4 border-success d-flex justify-content-between align-items-center">
                        <div>
                          <span className="fw-bold d-block text-dark">{labDisplayName}</span>
                        </div>
                        <span className="badge bg-success fs-6">
                          הושלם
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* טור שמאל: בקשות החלפה */}
        <div className="col-lg-4">
          <div className="card shadow-sm h-100 border-0">
            <div className="card-body">
              <h4 className="card-title fw-bold mb-3 text-secondary border-bottom pb-2">בקשות החלפה</h4>
              {swapRequests.length === 0 ? (
                <p className="text-muted text-center py-4">טרם הוגשו בקשות</p>
              ) : (
                <div className="d-flex flex-column gap-3" style={{ maxHeight: '550px', overflowY: 'auto' }}>
                  {[...swapRequests]
                    .sort((a, b) => b.request_id - a.request_id) // מיון: החדש ביותר מופיע למעלה
                    .map((req) => (
                      <div key={req.request_id} className="p-3 bg-light rounded border">
                        <div className="d-flex justify-content-between align-items-center mb-2">
                          <span className="fw-bold text-primary">{req.current_topic_name}</span>
                          {renderStatusBadge(req.status)}
                        </div>

                        <div className="small text-secondary mb-1">
                          <div><strong>מועד מקורי:</strong> {req.current_date ? new Date(req.current_date).toLocaleDateString('he-IL') : 'לא צויין'}</div>
                          <div>
                            <strong>מועד מבוקש:</strong> {req.target_date ? new Date(req.target_date).toLocaleDateString('he-IL') : 'לא צויין'} 
                            {req.target_date ? ` (${new Date(req.target_date).toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })})` : ''}
                          </div>
                        </div>
                        <p className="text-muted small mb-1">סיבה: {req.reason}</p>
                        
                        {req.reviewer_notes && (
                          <div className="alert alert-secondary p-1 mb-0 small mt-2">
                            <strong>הערת סגל:</strong> {req.reviewer_notes}
                          </div>
                        )}

                        {/* כפתור ביטול מורחב בתחתית הכרטיסייה, מוצג רק אם הבקשה ממתינה לאישור */}
                        {req.status === 'PENDING' && (
                          <button
                            className="btn btn-outline-danger btn-sm w-100 mt-2 fw-semibold"
                            style={{ fontSize: '0.85rem' }}
                            onClick={() => handleCancelClick(req.request_id)}
                          >
                            ביטול בקשת החלפה
                          </button>
                        )}
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

      {showGradesModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header d-flex justify-content-between align-items-center" dir="rtl">
                <h5 className="modal-title fw-bold m-0">הציונים והמשוב שלי</h5>
                <button 
                  type="button" 
                  className="btn-close m-0" 
                  style={{ 
                    filter: 'invert(27%) sepia(51%) saturate(2878%) hue-rotate(346deg) brightness(104%) contrast(97%)' 
                  }}
                  onClick={() => setShowGradesModal(false)}
                  aria-label="Close"
                ></button>
              </div>
              <div className="modal-body">
                {loadingGrades ? (
                  <p className="text-center">טוען ציונים...</p>
                ) : (
                  <>
                    {/* הצגת ציונים סופיים אם קיימים */}
                    {finalGrade !== '-' && (
                      <div className="mb-4">
                        <h6>ציון סופי בקורס:</h6>
                        <div className="alert alert-success py-2 d-inline-block">
                          ציון סופי: <strong>{finalGrade}</strong>
                        </div>
                      </div>
                    )}

                    {/* הצגת ציוני מעבדות מפורטים */}
                    {grades.length > 0 ? (
                      <div className="table-responsive">
                        <table className="table table-striped table-bordered text-center">
                          <thead>
                            <tr>
                              <th>מפגש</th>                              
                              <th>דוח מכין</th>
                              <th>עבודה במעבדה</th>
                              <th>דוח מסכם</th>
                              <th>ציון משוקלל</th>
                              <th>משוב מרצה</th>
                            </tr>
                          </thead>
                          <tbody>
                            {grades.map((g) => (
                              <tr key={g.grade_id}>
                                <td>{g.schedule_id}</td>                                
                                <td>{g.prep_report_grade ?? '-'}</td>
                                <td>{g.lab_work_grade ?? '-'}</td>
                                <td>{g.summary_report_grade ?? '-'}</td>
                                <td><strong>{g.final_calculated_grade ?? '-'}</strong></td>
                                <td>{g.student_feedback || 'אין הערות'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="alert alert-info text-center" role="alert">
                        הציונים טרם פורסמו. הם יפורסמו ויעודכנו על ידי המרצים בסוף הסמסטר.
                      </div>
                    )}
                  </>
                )}
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowGradesModal(false)}>
                  סגור
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* מודל בקשת החלפה דינמי */}
      {showModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered" dir="rtl">
            <div className="modal-content">              
              <div className="modal-header d-flex justify-content-between align-items-center" dir="rtl">
                <div className="d-flex align-items-center gap-3">
                  <h5 className="modal-title fw-bold m-0">
                    {modalStep === 1 ? `בקשת החלפה ל- ${selectedLab?.topic_name}` : 'פרטי בקשת ההחלפה'}
                  </h5>
                  
                  {/* טיימר מעוצב שרץ לאחור */}
                  {lockedScheduleId && (
                    <div className="badge bg-light text-dark border px-2 py-1 fs-6 rounded-3 d-flex align-items-center gap-1 shadow-sm">
                      <span>⏱️</span>
                      <span className="fw-bold text-danger">{formatTime(timeLeft)}</span>
                    </div>
                  )}
                </div>

                <button 
                  type="button" 
                  className="btn-close m-0" 
                  style={{ 
                    filter: 'invert(27%) sepia(51%) saturate(2878%) hue-rotate(346deg) brightness(104%) contrast(97%)' 
                  }}
                  onClick={handleCloseModal}
                  aria-label="Close"
                ></button>
              </div>
              
              <div className="modal-body">
                {modalStep === 1 ? (
                  <>
                    <p className="text-muted mb-3">בחר מועד חלופי זמין מהמערכת:</p>
                    {loadingSlots ? (
                      <div className="text-center py-4 text-muted">טוען מועדים זמינים...</div>
                    ) : availableSlots.length === 0 ? (
                      <div className="alert alert-warning text-center">אין מועדים נוספים זמינים עבור נושא זה כרגע.</div>
                    ) : (
                      <div className="d-flex flex-column gap-2" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        {availableSlots.map((slot) => {
                          const dateObj = new Date(slot.lab_date);
                          const dateStr = dateObj.toLocaleDateString('he-IL');
                          const timeStr = dateObj.toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' });

                          return (                           
                            <button 
                                key={slot.schedule_id}
                                className="btn btn-outline-secondary text-start p-2 d-flex justify-content-between align-items-center"
                                onClick={async () => {
                                  try {
                                    // אם כבר היה מועד נעול קודם, נשחרר אותו לפני שנעולים חדש
                                    if (lockedScheduleId && lockedScheduleId !== slot.schedule_id) {
                                      await unlockScheduleSlot(lockedScheduleId);
                                    }

                                    // מנסים לנעול את המועד החדש ב-Redis (אם תפוס, השרת יזרוק שגיאת 409)
                                    await lockScheduleSlot(slot.schedule_id);

                                    setLockedScheduleId(slot.schedule_id);
                                    setSelectedTargetSlot(slot);
                                    setModalStep(2);
                                  } catch (error) {
                                    const errorMsg = error.response?.detail || error.detail || 'המועד נתפס כרגע על ידי סטודנט אחר, בחר מועד אחר';
                                    toast.error(errorMsg);
                                  }
                                }}
                              >
                                <span>📅 {dateStr} | 🕒 {timeStr}</span>
                                <span className={`badge ${slot.session_type === 'COMPLETION' ? 'bg-warning text-dark' : 'bg-primary'}`}>
                                  {slot.session_type === 'COMPLETION' ? 'השלמה' : `קבוצה ${slot.group_id}`}
                                </span>
                              </button>
                          );
                        })}
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    <div className="alert alert-info py-2 small mb-3">
                      <strong>בחרת מועד חלופי:</strong> {new Date(selectedTargetSlot?.lab_date).toLocaleDateString('he-IL')} בשעה {new Date(selectedTargetSlot?.lab_date).toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })} (קבוצה {selectedTargetSlot?.group_id})
                    </div>
                    <div className="mb-3">
                      <label className="form-label fw-bold small">סיבה לבקשה:</label>
                      <textarea 
                        className="form-control" 
                        rows="3" 
                        placeholder="פרט את הסיבה לבקשת ההחלפה..."
                        value={swapReason}
                        onChange={(e) => setSwapReason(e.target.value)}
                      ></textarea>
                    </div>
                  </>
                )}
              </div>

              <div className="modal-footer">
                {modalStep === 2 ? (
                  <>
                    <button 
                      type="button" 
                      className="btn btn-secondary btn-sm" 
                      onClick={handleBackToStep1}
                    >
                      חזרה לבחירת מועד
                    </button>
                    <button 
                      type="button" 
                      className="btn btn-primary btn-sm" 
                      onClick={async () => {
                        if (!swapReason.trim()) {
                          toast.error('נא להזין סיבה לבקשה');
                          return;
                        }

                        try {
                          await registerToSchedule({
                            schedule_id: selectedTargetSlot.schedule_id,    
                            current_schedule_id: selectedLab.schedule_id,   
                            reason: swapReason,
                            is_team_swap: true 
                          });

                          toast.success('בקשת ההחלפה נשלחה בהצלחה וממתינה לאישור!');
                          await fetchData();
                          handleCloseModal();
                        } catch (err) {
                          console.error('Error registering to schedule:', err);
                          toast.error('שליחת הבקשה נכשלה');
                        }
                      }}
                    >
                      שליחת בקשה
                    </button>
                  </>
                ) : null}
              </div>        
              
            </div>
          </div>
        </div>
      )}

      {/* מודל ביטול בקשת החלפה */}
      {cancelModalId && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered" dir="rtl">
            <div className="modal-content">
              <div className="modal-header d-flex justify-content-between align-items-center">
                <h5 className="modal-title fw-bold">ביטול בקשת החלפה</h5>
                <button 
                  type="button" 
                  className="btn-close m-0" 
                  style={{ 
                    filter: 'invert(27%) sepia(51%) saturate(2878%) hue-rotate(346deg) brightness(104%) contrast(97%)',
                    marginLeft: '0',
                    marginRight: 'auto'
                  }}
                  onClick={() => setCancelModalId(null)}
                  aria-label="Close"
                ></button>
              </div>
              <div className="modal-body text-end">
                <p className="mb-0">האם ברצונך לבטל את בקשת ההחלפה?</p>
              </div>
              <div className="modal-footer justify-content-start">
                <button type="button" className="btn btn-danger btn-sm" onClick={confirmCancelSwap}>
                  כן, בטל בקשה
                </button>
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setCancelModalId(null)}>
                  סגור
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default StudentDashboard;