import React from 'react';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css'; 
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";

import MainLayout from './layouts/MainLayout';
import Login from "./pages/Login";
import Register from "./pages/Register"; 
import StudentDashboard from "./pages/StudentDashboard";
import StaffDashboard from "./pages/StaffDashboard"; // קובץ הסגל החדש
import ProtectedRoute from "./components/ProtectedRoute";


function App() {
  return (
    <>
      <ToastContainer position="top-right" autoClose={3000} dir="rtl" />
      <Router>
        <AuthProvider>
          <Routes>
            {/* מסך התחברות והרשמה (עצמאיים) */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* עמודים שכוללים את ה-MainLayout (עם Navbar ו-Footer) */}
            <Route element={<MainLayout />}>
              {/* דשבורד סטודנט מוגן (רק לסטודנטים) */}
              <Route 
                path="/student" 
                element={
                  <ProtectedRoute allowedRole="student">
                    <StudentDashboard />
                  </ProtectedRoute>
                } 
              />

              {/* דשבורד ניהול מעבדות / סגל מוגן */}
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <StaffDashboard />
                  </ProtectedRoute>
                } 
              />
            </Route>

            {/* ברירת מחדל מעבר ללוגין */}
            <Route path="*" element={<Login />} />
          </Routes>
        </AuthProvider>
      </Router>
    </>
  );
}

export default App;