import { useState } from 'react';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { loginUser } from '../services/userService';
import { toast } from 'react-toastify';

// פונקציית עזר קטנה לפענוח ה-Role מתוך ה-JWT
const parseJwt = (token) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
};

function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const formik = useFormik({
    initialValues: {
      identifier: '',
      password: '',
    },
    validationSchema: Yup.object({
      identifier: Yup.string().required('שדה חובה (אימייל או תעודת זהות)'),
      password: Yup.string()
        .min(6, 'הסיסמה חייבת להכיל לפחות 6 תווים')
        .required('שדה חובה'),
    }),
    onSubmit: async (values) => {
      try {
        const response = await loginUser(values);
        const token = response.data?.token || response.data?.access_token || response.data;
        
        // פענוח הטוקן כדי לחלץ את ה-Role וה-ID של המשתמש
        const decodedToken = parseJwt(token);
        const userRole = decodedToken?.role || 'student';

        const userData = {
          userId: decodedToken?.sub,
          role: userRole,
        };

        // שמירה ב-localStorage וב-AuthContext
        localStorage.setItem('user', JSON.stringify(userData));
        login(token, userData);

        toast.success('התחברת בהצלחה!');

        // ניווט חכם לפי תפקיד
        if (userRole === 'student') {
          navigate('/student');
        } else {
          navigate('/dashboard'); // דשבורד ניהול מעבדות לסגל/אדמין
        }
      } catch (err) {
        toast.error(
          err.response?.data?.detail ||
            err.response?.data?.message ||
            'שגיאה בפרטי ההתחברות'
        );
      }
    },
  });

  return (
    <div className="container mt-5" style={{ maxWidth: '420px', direction: 'rtl' }}>
      <div className="card shadow border-0 p-4 rounded-4 text-end">
        {/* Header Section */}
        <div className="text-center mb-4">
          <div
            className="bg-primary bg-opacity-10 text-primary rounded-circle d-inline-flex align-items-center justify-content-center mb-3"
            style={{ width: '60px', height: '60px', fontSize: '1.8rem' }}
          >
            <i className="fa-solid fa-flask"></i>
          </div>
          <h3 className="fw-bold m-0">LabFlow</h3>
          <p className="text-muted small mt-1">התחבר למערכת</p>
        </div>

        {/* Form Section */}
        <form onSubmit={formik.handleSubmit}>
          {/* Identifier Input */}
          <div className="form-floating mb-3 text-end" dir="rtl">
            <input
              type="text"
              name="identifier"
              id="floatingIdentifier"
              className={`form-control text-end ${
                formik.touched.identifier && formik.errors.identifier
                  ? 'is-invalid'
                  : ''
              }`}
              placeholder="אימייל או תעודת זהות"
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              value={formik.values.identifier}
            />
            <label
              htmlFor="floatingIdentifier"
              style={{ right: 0, left: 'auto', textAlign: 'right', paddingRight: '1rem' }}
            >
              אימייל / ת.ז
            </label>
            {formik.touched.identifier && formik.errors.identifier && (
              <div className="invalid-feedback text-start">
                {formik.errors.identifier}
              </div>
            )}
          </div>

          {/* Password Input */}

          <div className="form-floating mb-3 position-relative" dir="rtl">
            <input
              type={showPassword ? "text" : "password"}
              name="password"
              id="floatingPassword"
              className={`form-control text-end ps-5 ${ // ps-5 נותן מרווח בצד שמאל כדי שהטקסט לא יתחתן עם הכפתור
                formik.touched.password && formik.errors.password ? 'is-invalid' : ''
              }`}
              placeholder="סיסמה"
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              value={formik.values.password}
            />
            <label
              htmlFor="floatingPassword"
              style={{ right: 0, left: 'auto', textAlign: 'right', paddingRight: '1rem' }}
            >
              סיסמה
            </label>
            
            <button
              type="button"
              className="btn position-absolute top-50 start-0 translate-middle-y border-0 bg-transparent shadow-none"
              style={{ left: '10px', zIndex: 10, opacity: 0.6 }}
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"></path>
                  <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"></path>
                  <path d="M6.61 6.61A13.52 13.52 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"></path>
                  <line x1="2" y1="2" x2="22" y2="22"></line>
                </svg>
              ) : (
                /* אייקון עין רגיל (גלוי) */
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
              )}
            </button>

            {formik.touched.password && formik.errors.password && (
              <div className="invalid-feedback text-start">
                {formik.errors.password}
              </div>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="btn btn-primary w-100 py-2 fw-bold mt-2 rounded-3"
          >
            התחבר
          </button>
        </form>

        {/* Register Link */}
        <div className="text-center mt-4 pt-2 border-top">
          <span className="text-muted small">אין לך חשבון עדיין? </span>
          <Link to="/register" className="text-decoration-none fw-bold small">
            הירשם
          </Link>
        </div>
      </div>
    </div>
  );
}

export default Login;