import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getMyProfile } from '../services/studentService'; 
import { publishCourseGrades } from '../services/staffService'; 
import { toast } from 'react-toastify';

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [userName, setUserName] = useState('');
  
  // סטייטים למודל פרסום / ביטול פרסום ציונים
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [courseIdInput, setCourseIdInput] = useState('1'); 
  const [isPublished, setIsPublished] = useState(false); // האם הקורס כרגע מפורסם או לא
  const [isPublishing, setIsPublishing] = useState(false);

  useEffect(() => {
    const fetchUserProfile = async () => {
      if (user?.first_name) {
        setUserName(`${user.first_name} ${user.last_name || ''}`.trim());
        return;
      }
      if (user?.name) {
        setUserName(user.name);
        return;
      }
      
      try {
        const profileData = await getMyProfile();
        if (profileData && profileData.first_name) {
          setUserName(`${profileData.first_name} ${profileData.last_name || ''}`.trim());
        }
      } catch (err) {
        console.error('Could not fetch profile name for navbar', err);
        setUserName(user?.email || 'משתמש');
      }
    };

    fetchUserProfile();
  }, [user]);

  const handleLogout = () => {
    logout();
    toast.info('התנתקת מהמערכת בהצלחה');
    navigate('/login');
  };

  // פונקציית שליחת בקשת פרסום או ביטול פרסום דרך ה־Service
  const handleConfirmPublish = async () => {
    try {
      setIsPublishing(true);
      const targetState = !isPublished; // אם כרגע לא מפורסם - נפרסם (true), ואם מפורסם - נבטל (false)
      
      await publishCourseGrades(parseInt(courseIdInput, 10) || 1, targetState);

      setIsPublished(targetState); // עדכון הסטייט המקומי
      
      if (targetState) {
        toast.success('הציונים פורסמו בהצלחה לסטודנטים! 🎉');
      } else {
        toast.info('פרסום הציונים בוטל (הציונים ננעלו) 🔒');
      }
      
      setShowPublishModal(false);
    } catch (error) {
      console.error('Error toggling publish status:', error);
      const errorMsg = error.response?.data?.detail || 'שגיאה בעדכון סטטוס פרסום הציונים מול השרת';
      toast.error(errorMsg);
    } finally {
      setIsPublishing(false);
    }
  };

  const isStudent = user?.role === 'student';
  const isPrivilegedStaff = user?.role === 'admin' || user?.role === 'lecturer';

  return (
    <>
      <nav className="navbar navbar-expand-lg shadow-sm py-2" style={{ backgroundColor: '#d0ebff', borderBottom: '1px solid #a5d8ff' }} dir="rtl">
        <div className="container-fluid px-4 d-flex justify-content-between align-items-center">
          
          {/* צד ימין: שם המערכת וסוג הדשבורד הדינמי */}
          <div className="d-flex align-items-center gap-3">
            <span className="fw-bold fs-5 text-primary">🔬 LabFlow</span>
            <span className="text-muted">|</span>
            <span className="fw-semibold text-secondary fs-6">
              {isStudent ? 'דשבורד סטודנט' : 'דשבורד ניהול מעבדות'}
            </span>

            {isStudent && user?.teamCode && (
              <span className="badge bg-info text-dark fs-6">
                קבוצה: {user.teamCode}
              </span>
            )}
          </div>

          {/* צד שמאל: כפתור פרסום/ביטול פרסום, שם המשתמש וכפתור התנתקות */}
          <div className="d-flex align-items-center gap-3">
            
            {/* כפתור דינמי שמשתנה לפי סטטוס הפרסום */}
            {isPrivilegedStaff && (
              <button
                onClick={() => setShowPublishModal(true)}
                className={`btn btn-sm fw-bold px-3 shadow-sm d-flex align-items-center gap-1 ${
                  isPublished ? 'btn-outline-danger bg-white text-danger' : 'btn-warning text-dark'
                }`}
                title={isPublished ? 'בטל פרסום ציונים לקורס' : 'פרסם ציונים סופיים לסטודנטים'}
              >
                {isPublished ? '🔒 ביטול פרסום ציונים' : '📢 פרסום ציונים'}
              </button>
            )}

            <span className="text-dark fw-medium">
              שלום, {userName || 'משתמש'}
            </span>
            
            <button 
              onClick={handleLogout} 
              className="btn btn-outline-danger btn-sm fw-bold px-3"
            >
              התנתק
            </button>
          </div>

        </div>
      </nav>

      {/* מודל אישור דינמי לפרסום או ביטול פרסום ציונים */}
      {showPublishModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} dir="rtl">
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content shadow border-0 text-end">
              <div className={`modal-header text-white ${isPublished ? 'bg-danger' : 'bg-primary'}`}>
                <h5 className="modal-title fw-bold">
                  {isPublished ? '🔒 אישור ביטול פרסום ציונים' : '📢 אישור פרסום ציוני קורס'}
                </h5>
                <button 
                  type="button" 
                  className="btn-close m-0" 
                  onClick={() => setShowPublishModal(false)}
                  disabled={isPublishing}
                ></button>
              </div>
              <div className="modal-body py-4">
                <p className="mb-3 text-secondary">
                  {isPublished 
                    ? 'פעולה זו תנעל חזרה את הציונים ותמנע מהסטודנטים לראות אותם במערכת.'
                    : 'פעולה זו תחשב מחדש את הציונים הסופיים ותפתח אותם לצפייה ישירה עבור כל הסטודנטים הרשומים בקורס.'}
                </p>
                
                <div className="mb-3">
                  <label htmlFor="courseId" className="form-label fw-bold text-dark">מזהה קורס (Course ID):</label>
                  <input 
                    type="number" 
                    id="courseId"
                    className="form-control" 
                    value={courseIdInput} 
                    onChange={(e) => setCourseIdInput(e.target.value)}
                    placeholder="הכנס מזהה קורס (למשל 1)"
                  />
                </div>

                <p className="text-danger small fw-bold mb-0">
                  ⚠️ האם את בטוחה שברצונך לבצע פעולה זו כעת?
                </p>
              </div>
              <div className="modal-footer justify-content-start gap-2 bg-light">
                <button 
                  type="button" 
                  className={`btn px-4 fw-bold text-white ${isPublished ? 'btn-danger' : 'btn-primary'}`}
                  onClick={handleConfirmPublish}
                  disabled={isPublishing}
                >
                  {isPublishing 
                    ? 'מעדכן...' 
                    : (isPublished ? 'כן, בטל פרסום' : 'כן, פרסם ציונים')}
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary px-4" 
                  onClick={() => setShowPublishModal(false)}
                  disabled={isPublishing}
                >
                  ביטול
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default Navbar;