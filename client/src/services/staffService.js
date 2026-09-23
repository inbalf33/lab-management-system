import axios from 'axios';
import api from './api';

export const getSwapRequests = async (filters = {}) => {
  const response = await api.get('/api/schedules/swap-requests', { params: filters });
  console.log("Swap requests raw data:", response.data);
  return response.data;
};

// אישור או דחיית בקשת החלפה
export const updateSwapRequestStatus = async (requestId, approve, reviewerNotes = '') => {
  const response = await axios.post(`/api/swap-requests/${requestId}/approve`, {
    approve: approve,
    reviewer_notes: reviewerNotes
  });
  return response.data;
};

export const getLabGroups = async () => {
  const response = await api.get('/api/labs');
  return response.data;
};

// שליפת סטודנטים מותאמת לנתיב שראינו בשרת (/api/{lab_id}/students)
export const getStudentsList = async (filters = {}) => {
  try {
    const params = {};
    if (filters.lab_id) {
      params.lab_id = filters.lab_id;
    }
    
    const response = await api.get('/api/labs/students', { params });
    const rawStudents = Array.isArray(response.data) ? response.data : [];

    // מיפוי השדות שמגיעים מהשרת לשדות שהטבלה מצפה להם
    return rawStudents.map(s => ({
      ...s,
      name: `${s.first_name || ''} ${s.last_name || ''}`.trim(),
      full_name: `${s.first_name || ''} ${s.last_name || ''}`.trim(),
      // שימוש ב-group_code שהגיע ישירות מהשרת עבור עמודת הקבוצה
      group_name: s.group_code || '-',
      group: s.group_code || '-',
      group_code: s.group_code || '-',
      miluim: s.is_miluim ? 'כן' : '-'
    }));
  } catch (error) {
    console.error("Error fetching students list:", error);
    return [];
  }
};

export const gradeSingleStudent = async (gradeData) => {
  const response = await axios.post(`/api/grades`, gradeData);
  return response.data;
};

export const gradeTeam = async (teamData) => {
  const response = await api.put(`/api//grades/team`, teamData);
  return response.data;
};


