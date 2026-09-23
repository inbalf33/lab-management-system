import axios from "axios";
import { toast } from "react-toastify";

console.log("My API URL is:", import.meta.env.VITE_API_URL);

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

// Add Authorization header to requests if token exists
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 Unauthorized globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      toast.error('פג תוקף ההתחברות. נא להתחבר מחדש.');
      localStorage.removeItem("token");
      
      // הפניה אוטומטית לדף ההתחברות אחרי שנייה וחצי
      setTimeout(() => {
        window.location.href = '/login'; 
      }, 1500);
    }
    return Promise.reject(error);
  }
);

export default api;