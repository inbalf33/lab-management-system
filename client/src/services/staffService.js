// src/services/staffService.js
import axios from 'axios';
import api from './api';

export const getSwapRequests = async (filters = {}) => {
  const response = await api.get('/api/schedules/swap-requests', { params: filters });
  return response.data;
};

export const updateSwapRequestStatus = async (requestId, approve, reviewerNotes = '') => {
  const response = await api.post(`/api/schedules/swap-requests/${requestId}/approve`, {
    approve: approve,
    reviewer_notes: reviewerNotes
  });
  return response.data;
};

export const getLabGroups = async () => {
  const response = await api.get('/api/labs');
  return response.data;
};

export const getStudentsList = async (filters = {}) => {
  try {
    const params = {};
    if (filters.lab_id) {
      params.lab_id = filters.lab_id;
    }
    if (filters.course_id) {
      params.course_id = filters.course_id;
    }

    const [studentsRes, gradesRes, finalGradesRes, schedulesRes] = await Promise.all([
      api.get('/api/labs/students', { params }),
      api.get('/api/grades', { params }),
      api.get('/api/grades/final/', { params }),
      api.get('/api/schedules', { params }).catch(() => ({ data: [] }))
    ]);

    const rawStudents = Array.isArray(studentsRes.data) ? studentsRes.data : [];
    const allGrades = Array.isArray(gradesRes.data) ? gradesRes.data : [];
    const allFinalGrades = Array.isArray(finalGradesRes.data) ? finalGradesRes.data : [];
    const allSchedules = Array.isArray(schedulesRes.data) ? schedulesRes.data : [];

    return rawStudents.map(s => {
      const studentId = s.student_id || s.id || s.user_id;
      const studentGroupKey = s.group_id || s.group_code || s.lab_id || filters.lab_id;

      // סינון המפגשים השייכים לקבוצה של הסטודנט
      const groupSchedules = allSchedules.filter(sch => {
        const schGroup = sch.group_id || sch.group_code || sch.lab_id;
        const matchesGroup = studentGroupKey && schGroup ? 
          String(schGroup) === String(studentGroupKey) : 
          true; 

        const isNotIntroOrCompletion = 
          sch.session_type !== 'INTRO' && 
          sch.session_type !== 'COMPLETION';

        return matchesGroup && isNotIntroOrCompletion;
      });
      
      const totalLabs = groupSchedules.length > 0 ? groupSchedules.length : 9;
      const validScheduleIds = new Set(groupSchedules.map(sch => sch.schedule_id || sch.id));

      // שליפת כל הציונים של הסטודנט הספציפי הזה
      const studentGrades = allGrades.filter(g => 
        g.student_id === studentId && 
        (validScheduleIds.size === 0 || validScheduleIds.has(g.schedule_id || g.id))
      );

      // בניית מערך מעבדות מפורט עבור טבלת הציונים של הסטודנט
      const labsDetails = studentGrades.map(g => {
        const matchingSchedule = allSchedules.find(sch => (sch.schedule_id || sch.id) === g.schedule_id);
        return {
          grade_id: g.grade_id || g.id,
          schedule_id: g.schedule_id,
          topic_name: matchingSchedule ? matchingSchedule.topic_name : `מעבדה ${g.schedule_id}`,
          prep: g.prep_report_grade,
          lab_work: g.lab_work_grade,
          summary: g.summary_report_grade,
          attendance: g.attendance_status
        };
      });

      const completedLabs = studentGrades.filter(g => 
        g.lab_work_grade !== null && g.lab_work_grade !== undefined
      ).length;
      
      const finalRecord = allFinalGrades.find(f => f.student_id === studentId);
      const finalScore = finalRecord ? finalRecord.final_score : null;

      return {
        ...s,
        student_id: studentId,
        id_number: s.id_number || String(studentId),
        name: `${s.first_name || ''} ${s.last_name || ''}`.trim(),
        full_name: `${s.first_name || ''} ${s.last_name || ''}`.trim(),
        group_name: s.group_code || s.group_name || '-',
        group: s.group_code || s.group_name || '-',
        group_code: s.group_code || s.group_name || '-',
        team_code: s.team_code || '-', // וידוא הימצאות קוד צוות מתוך טבלת group_students
        miluim: s.is_miluim ? 'כן' : '-',
        labs: labsDetails, // מעבירים את פירוט המעבדות לטבלה ב-UI
        completed_labs: completedLabs,
        total_labs: totalLabs > 15 ? 9 : totalLabs,
        avg_score: finalScore !== null && finalScore !== undefined ? Math.round(finalScore) : '-'
      };
    });
  } catch (error) {
    console.error("Error fetching students list:", error);
    return [];
  }
};

export const gradeSingleStudent = async (gradeData) => {
  const response = await api.post(`/api/grades`, gradeData);
  return response.data;
};



export const deleteGrade = async (gradeId) => {
  const response = await api.delete(`/api/grades/${gradeId}`);
  return response.data;
};


// הוספת פונקציות הוספת/עדכון ציונים ב- staffService.js
export const gradeTeam = async (teamData) => {
  // שימוש ב-post כי בשרת הגדרת @router.post("/team")
  const response = await api.post('/api/grades/team', teamData);
  return response.data;
};

export const gradeBatch = async (batchData) => {
  const response = await api.post('/api/grades/batch', batchData);
  return response.data;
};


// פרסום או נעילת ציונים סופיים לקורס (לשימוש אדמין/מרצה)
export const publishCourseGrades = async (courseId, isPublished = true) => {
  try {
    const response = await api.post('/api/grades/publish', {
      course_id: courseId,
      is_published: isPublished
    });
    return response.data;
  } catch (error) {
    console.error("Error publishing course grades:", error);
    throw error;
  }
};
