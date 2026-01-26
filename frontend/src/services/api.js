/**
 * API service for communicating with Baby Meal backend.
 * Centralizes all API calls with error handling.
 */
import axios from 'axios';

// Base URL - update if backend runs on different port
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create axios instance with default config
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Error handler
const handleError = (error) => {
    if (error.response) {
        // Server responded with error
        console.error('API Error:', error.response.data);
        throw new Error(error.response.data.detail || 'An error occurred');
    } else if (error.request) {
        // Request made but no response
        console.error('Network Error:', error.request);
        throw new Error('Cannot connect to server. Is the backend running?');
    } else {
        // Something else happened
        console.error('Error:', error.message);
        throw error;
    }
};

// ============================================================================
// BABY ENDPOINTS
// ============================================================================

export const babyAPI = {
    /**
     * Get all babies
     */
    getAll: async () => {
        try {
            const response = await api.get('/babies/');
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },

    /**
     * Get baby by ID with stats
     */
    getById: async (babyId) => {
        try {
            const response = await api.get(`/babies/${babyId}`);
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },

    /**
     * Create new baby profile
     */
    create: async (babyData) => {
        try {
            const response = await api.post('/babies/', babyData);
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },

    /**
     * Update baby profile
     */
    update: async (babyId, updates) => {
        try {
            const response = await api.patch(`/babies/${babyId}`, updates);
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },
};

// ============================================================================
// RECOMMENDATION ENDPOINTS
// ============================================================================

export const recommendationAPI = {
    /**
     * Get basic rule-based recommendations
     */
    getBasic: async (babyId, count = 5, mealType = null) => {
        try {
            const response = await api.post('/recommendations/', {
                baby_id: babyId,
                count,
                meal_type: mealType,
                exclude_recently_recommended: true,
            });
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },

    /**
     * Get AI-enhanced smart recommendations
     */
    getSmart: async (babyId, count = 5, mealType = null) => {
        try {
            const response = await api.post('/recommendations/smart', {
                baby_id: babyId,
                count,
                meal_type: mealType,
                exclude_recently_recommended: true,
            });
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },

    /**
     * Submit feedback for a recipe
     */
    submitFeedback: async (feedbackData) => {
        try {
            const response = await api.post('/recommendations/feedback', feedbackData);
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },

    /**
     * Get nutrition analysis
     */
    getNutritionAnalysis: async (babyId, days = 7) => {
        try {
            const response = await api.get(`/recommendations/nutrition-analysis/${babyId}`, {
                params: { days },
            });
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },

    /**
     * Chat with AI assistant
     */
    chat: async (babyId, message, conversationHistory = []) => {
        try {
            const response = await api.post('/recommendations/chat', {
                baby_id: babyId,
                message,
                conversation_history: conversationHistory,
            });
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },

    /**
     * Check AI features status
     */
    getStatus: async () => {
        try {
            const response = await api.get('/recommendations/status');
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },
};

// ============================================================================
// RECIPE ENDPOINTS
// ============================================================================

export const recipeAPI = {
    /**
     * Get all recipes
     */
    getAll: async (filters = {}) => {
        try {
            const response = await api.get('/recipes/', { params: filters });
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },

    /**
     * Get recipe by ID
     */
    getById: async (recipeId) => {
        try {
            const response = await api.get(`/recipes/${recipeId}`);
            return response.data;
        } catch (error) {
            handleError(error);
        }
    },
};

// Health check
export const healthCheck = async () => {
    try {
        const response = await api.get('/health', { baseURL: 'http://localhost:8000' });
        return response.data;
    } catch (error) {
        return { status: 'error' };
    }
};

export default {
    baby: babyAPI,
    recommendation: recommendationAPI,
    recipe: recipeAPI,
    healthCheck,
};