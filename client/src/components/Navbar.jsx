import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getMyProfile } from '../services/studentService'; 
import { toast } from 'react-toastify';

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [userName, setUserName] = useState('');

  useEffect(() => {
    const fetchUserProfile = async () => {
      // ננסה קודם לשלוף מהאובייקט הקיים אם יש שם מלא
      if (user?.first_name) {
        setUserName(`${user.first_name} ${user.last_name || ''}`.trim());
        return;
      }
      if (user?.name) {
        setUserName(user.name);
        return;
      }
      
      // אם אין באובייקט user, נשלוף מהשרת כמו שעשינו בדשבורד
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

const isStudent = user?.role === 'student';

const isStaff = user?.role === 'lecturer' || user?.role === 'instructor' || user?.role === 'admin';
  return (
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

        {/* צד שמאל: שם המשתמש מהשרת וכפתור התנתקות */}
        <div className="d-flex align-items-center gap-3">
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
  );
}

export default Navbar;