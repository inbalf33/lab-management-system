import api from "./api";

const PATH = "/api/auth";

// Register
export function registerUser(userData) {
    return api.post(`${PATH}/register`, userData);
};

// Login
export function loginUser(credentials) {
    return api.post(`${PATH}/login`, credentials);
};