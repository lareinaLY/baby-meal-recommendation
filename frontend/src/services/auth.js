/**
 * Authentication service
 * Handles login, registration, and token management
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';
const TOKEN_KEY = 'baby_meal_token';
const USER_KEY = 'baby_meal_user';

const authAPI = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authService = {
  /**
   * Register new user
   */
  register: async (email, password, phone = null) => {
    try {
      const response = await authAPI.post('/auth/register', {
        email,
        password,
        phone,
      });
      
      // Save token and user
      localStorage.setItem(TOKEN_KEY, response.data.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));
      
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  },

  /**
   * Login user
   */
  login: async (email, password) => {
    try {
      const response = await authAPI.post('/auth/login', {
        email,
        password,
      });
      
      // Save token and user
      localStorage.setItem(TOKEN_KEY, response.data.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));
      
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  },

  /**
   * Logout user
   */
  logout: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  /**
   * Get current token
   */
  getToken: () => {
    return localStorage.getItem(TOKEN_KEY);
  },

  /**
   * Get current user
   */
  getUser: () => {
    const userStr = localStorage.getItem(USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated: () => {
    return !!localStorage.getItem(TOKEN_KEY);
  },

  /**
   * Get current user info from server
   */
  getCurrentUser: async () => {
    try {
      const token = authService.getToken();
      if (!token) return null;

      const response = await authAPI.get('/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      return response.data;
    } catch (error) {
      // Token invalid, clear it
      authService.logout();
      return null;
    }
  },
};

export default authService;