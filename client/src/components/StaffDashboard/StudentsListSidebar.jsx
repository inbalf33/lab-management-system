// src/components/StaffDashboard/StudentsListSidebar.jsx
import React, { useState } from 'react';

function StudentsListSidebar({ students, selectedStudentId, onSelectStudent, getStudentId }) {
  const [searchTerm, setSearchTerm] = useState('');

  // סינון הסטודנטים לפי שם או תעודת זהות
  const filteredStudents = students.filter(student => {
    const name = student.full_name || student.name || '';
    const idNum = String(student.id_number || student.student_id || '');
    const term = searchTerm.toLowerCase();
    
    return name.toLowerCase().includes(term) || idNum.includes(term) ||
           (student.team_code && student.team_code.toLowerCase().includes(term));
  });

  return (
    <div className="card shadow-sm border-0 h-100">
      <div className="card-body d-flex flex-column p-3">
        {/* כותרת */}
        <div className="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2">
          <h5 className="card-title fw-bold text-primary m-0">
            👥 סטודנטים ({filteredStudents.length})
          </h5>
        </div>

        {/* שורת חיפוש סטודנט/ית עם כפתור מחיקה (X) */}
        <div className="mb-3 position-relative">
          <input
            type="text"
            className="form-control form-control-sm text-end pe-4"
            placeholder="חיפוש לפי שם או ת.ז..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button
              type="button"
              className="btn btn-sm position-absolute top-50 translate-middle-y start-0 ms-1 border-0 bg-transparent text-muted"
              onClick={() => setSearchTerm('')}
              style={{ fontSize: '0.85rem' }}
            >
              ✕
            </button>
          )}
        </div>

        {/* רשימת הסטודנטים */}
        {filteredStudents.length === 0 ? (
          <p className="text-muted text-center py-4">אין סטודנטים תחת המסננים שנבחרו</p>
        ) : (
          <div className="list-group list-group-flush flex-grow-1" style={{ maxHeight: '520px', overflowY: 'auto' }}>
            {filteredStudents.map((student, index) => {
              const studentId = String(getStudentId(student, index));
              const isStudentSelected = studentId === String(selectedStudentId);
              
              const completedLabs = student.completed_labs || 0;
              const totalLabs = student.total_labs || 5;
              const progressPercent = totalLabs > 0 ? (completedLabs / totalLabs) * 100 : 0;
              const avgScore = student.avg_score !== undefined ? student.avg_score : '-';

              let progressColor = 'bg-secondary';
              if (completedLabs > 0) {
                progressColor = completedLabs === totalLabs ? 'bg-success' : 'bg-warning';
              }

              const isMiluim = student.is_reserve || student.is_miluim || student.reserve;

              return (
                <div
                  key={studentId}
                  className={`d-flex align-items-center justify-content-between p-2 mb-2 rounded border transition-all ${
                    isStudentSelected ? 'border-primary bg-primary bg-opacity-10 shadow-sm' : 'bg-white border-light'
                  }`}
                  style={{ cursor: 'pointer' }}
                  onClick={() => onSelectStudent(student, index)}
                >
                  {/* צד ימין: שם הסטודנט, צוות ותג מילואים */}
                  <div className="text-end">
                    <div className={`fw-bold ${isStudentSelected ? 'text-primary' : 'text-dark'}`}>
                      {student.full_name || student.name}
                    </div>
                    <div className="small text-muted mt-1 d-flex align-items-center justify-content-end gap-1">
                      <span>צוות {student.team_code || 'ללא'}</span>
                      {isMiluim && (
                        <span className="badge bg-warning text-dark d-flex align-items-center gap-1" style={{ fontSize: '0.7rem' }}>
                          🪖 מילואים
                        </span>
                      )}
                    </div>
                  </div>

                  {/* צד שמאל: ציון ופס התקדמות מעבדות (נכון לפי האב-טיפוס) */}
                  <div className="d-flex align-items-center gap-3">
                    <div style={{ width: '70px' }}>
                      <div className="small text-muted mb-1 text-center" style={{ fontSize: '0.75rem' }}>
                        ({completedLabs}/{totalLabs})
                      </div>
                      <div className="progress" style={{ height: '6px' }}>
                        <div
                          className={`progress-bar ${progressColor}`}
                          role="progressbar"
                          style={{ width: `${progressPercent}%` }}
                          aria-valuenow={completedLabs}
                          aria-valuemin="0"
                          aria-valuemax={totalLabs}
                        ></div>
                      </div>
                    </div>
                    <span className="fw-bold fs-5 text-dark" style={{ minWidth: '30px', textAlign: 'center' }}>
                      {avgScore}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default StudentsListSidebar;