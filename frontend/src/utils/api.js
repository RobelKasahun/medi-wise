import axios from 'axios';
import { API_BASE_URL, API_ENDPOINTS } from './config';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    withCredentials: true,
  },
  withCredentials: true, // Important for JWT cookies
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling token refresh
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't tried to refresh yet
    // Also skip refresh for auth endpoints to prevent infinite loops
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes('/auth/')
    ) {
      originalRequest._retry = true;

      try {
        // Try to refresh the token
        await api.post(API_ENDPOINTS.AUTH.REFRESH);
        // Retry the original request
        return api(originalRequest);
      } catch (refreshError) {
        // If refresh fails, only redirect if not already on login page
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    // For auth endpoint 401s, just reject without redirect
    if (error.response?.status === 401 && originalRequest.url.includes('/auth/')) {
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

// Auth API calls
export const authAPI = {
  login: async (email, password) => {
    const response = await api.post(API_ENDPOINTS.AUTH.LOGIN, {
      email,
      password,
    });
    return response.data;
  },

  signup: async (firstName, lastName, email, password) => {
    const response = await api.post(API_ENDPOINTS.AUTH.SIGNUP, {
      first_name: firstName,
      last_name: lastName,
      email,
      password,
    });
    return response.data;
  },

  refresh: async () => {
    const response = await api.post(API_ENDPOINTS.AUTH.REFRESH);
    return response.data;
  },
};

// Prompt API calls
export const promptAPI = {
  sendPrompt: async (userPrompt, conversationId = null) => {
    const response = await api.post(API_ENDPOINTS.PROMPT, {
      user_prompt: userPrompt,
      conversation_id: conversationId,
    });
    return response.data;
  },
};

// Conversation API calls
export const conversationAPI = {
  getConversations: async () => {
    const response = await api.get('/conversations');
    return response.data;
  },

  getConversation: async (conversationId) => {
    const response = await api.get(`/conversations/${conversationId}`);
    return response.data;
  },

  createConversation: async (title) => {
    const response = await api.post('/conversations', { title });
    return response.data;
  },

  deleteConversation: async (conversationId) => {
    const response = await api.delete(`/conversations/${conversationId}`);
    return response.data;
  },

  updateConversationTitle: async (conversationId, title) => {
    const response = await api.put(`/conversations/${conversationId}/title`, { title });
    return response.data;
  },
};

export default api;