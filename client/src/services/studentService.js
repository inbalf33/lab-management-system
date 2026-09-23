import api from "./api";

export const getMyRegistrations = async () => {
    const response = await api.get('/api/schedules/my-registrations');
    return response.data;
};

// שליפת הציונים של הסטודנט המחובר
export const getMyGrades = async () => {
    const response = await api.get('/api/grades/my-grades');
    return response.data;
};

// שליפת פרטי המשתמש המחובר
export const getMyProfile = async () => {
  const response = await api.get('/api/auth/me');
  return response.data;
};


export const lockScheduleSlot = async (scheduleId) => {
  try {
    const response = await api.post('/api/schedules/lock', { schedule_id: scheduleId });
    return response.data;
  } catch (error) {
    throw error.response?.data || error;
  }
};

export const unlockScheduleSlot = async (scheduleId) => {
  try {
    const response = await api.delete(`/api/schedules/lock/${scheduleId}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || error;
  }
};


export const registerToSchedule = async (requestData) => {
  try {
    const response = await api.post('/api/schedules/register', requestData);
    return response.data;
  } catch (error) {
    throw error.response?.data || error;
  }
};




export const getMyFinalGrades = async () => {
  try {
    const response = await api.get('/api/grades/final/my');
    return response.data;
  } catch (error) {
    throw error.response?.data || error;
  }
};



export const getMyCompletedScheduleIds = async () => {
  const response = await api.get('/api/grades/my-completed-schedule-ids'); // או לפי הנתיב המדויק שהגדרת בראוטר בשרת
  return response.data;
};


// ביטול בקשת החלפה ממתינה
export const cancelSwapRequest = async (requestId) => {
  try {
    const response = await api.delete(`/api/schedules/registrations/${requestId}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || error;
  }
};