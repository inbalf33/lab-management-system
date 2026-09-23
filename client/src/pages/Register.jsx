import { useState } from 'react';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-toastify';
// יש לוודא שהייבוא של פונקציית ההרשמה מנתיב השירותים שלך נכון
import { registerUser } from '../services/userService'; 

function Register() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const formik = useFormik({
    initialValues: {
      id_number: '',
      email: '',
      password: '',
    },
    validationSchema: Yup.object({
      id_number: Yup.string()
        .matches(/^\d{7,9}$/, 'תעודת זהות חייבת להכיל בין 7 ל-9 ספרות')
        .required('שדה תעודת זהות הוא חובה'),
      email: Yup.string()
        .email('כתובת אימייל לא שגויה')
        .required('שדה האימייל הוא חובה'),
      password: Yup.string()
        .min(6, 'הסיסמה חייבת להכיל לפחות 6 תווים')
        .required('שדה הסיסמה הוא חובה'),
    }),
    onSubmit: async (values) => {
      try {
        await registerUser(values);
        toast.success('החשבון הופעל בהצלחה! ניתן להתחבר למערכת');
        navigate('/login');
      } catch (err) {
        toast.error(
          err.response?.data?.detail || 'ההרשמה נכשלה. אנא בדוק את הפרטים ונסה שוב.'
        );
      }
    },
  });

  return (
    <div className="container mt-5 mb-5" style={{ maxWidth: '500px' }}>
      <div className="card shadow border-0 p-4 rounded-4">
        
        {/* Header */}
        <div className="text-center mb-4">
          <div 
            className="bg-primary bg-opacity-10 text-primary rounded-circle d-inline-flex align-items-center justify-content-center mb-3"
            style={{ width: '60px', height: '60px', fontSize: '1.8rem' }}
          >
            <i className="fa-solid fa-user-check"></i>
          </div>
          <h3 className="fw-bold m-0">הפעלת חשבון / הרשמה</h3>
          <p className="text-muted small mt-1">הזן את תעודת הזהות המאושרת שלך במערכת</p>
        </div>

        <form onSubmit={formik.handleSubmit}>
          
          {/* ID Number */}
          <div className="form-floating mb-3 text-start">
            <input
              type="text"
              name="id_number"
              id="floatingIdNumber"
              className={`form-control ${
                formik.touched.id_number && formik.errors.id_number ? 'is-invalid' : ''
              }`}
              placeholder="תעודת זהות"              
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              value={formik.values.id_number}
            />
            <label htmlFor="floatingIdNumber" style={{ right: 0, left: 'auto', textAlign: 'right', paddingRight: '1rem' }}>תעודת זהות *</label>
            {formik.touched.id_number && formik.errors.id_number && (
              <div className="invalid-feedback">{formik.errors.id_number}</div>
            )}
          </div>

          {/* Email */}
          <div className="form-floating mb-3">
            <input
              type="email"
              name="email"
              id="floatingEmail"
              className={`form-control ${
                formik.touched.email && formik.errors.email ? 'is-invalid' : ''
              }`}
              placeholder="name@example.com"              
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              value={formik.values.email}
            />
            <label htmlFor="floatingEmail" style={{ right: 0, left: 'auto', textAlign: 'right', paddingRight: '1rem' }}>כתובת אימייל *</label>
            {formik.touched.email && formik.errors.email && (
              <div className="invalid-feedback">{formik.errors.email}</div>
            )}
          </div>

          {/* Password */}
          <div className="form-floating mb-3 position-relative" dir="rtl">
            <input
              type={showPassword ? "text" : "password"}
              name="password"
              id="floatingPassword"
              className={`form-control text-end ps-5 ${
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
              סיסמה (6 תווים לפחות) *
            </label>

            {/* כפתור העין */}
            <button
              type="button"
              className="btn position-absolute top-50 start-0 translate-middle-y border-0 bg-transparent shadow-none"
              style={{ left: '10px', zIndex: 10, opacity: 0.6 }}
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                /* אייקון עין עם קו אלכסוני (מוסתר) */
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
              <div className="invalid-feedback text-start">{formik.errors.password}</div>
            )}
          </div>

          {/* Submit Button */}
          <button type="submit" className="btn btn-primary w-100 py-2 fw-bold mt-2 rounded-3">
            הפעל חשבון
          </button>
        </form>

        {/* Login Link */}
        <div className="text-center mt-4 pt-2 border-top">
          <span className="text-muted small">כבר הפעלת חשבון? </span>
          <Link to="/login" className="text-decoration-none fw-bold small text-primary">
            התחבר כאן
          </Link>
        </div>

      </div>
    </div>
  );
}

export default Register;