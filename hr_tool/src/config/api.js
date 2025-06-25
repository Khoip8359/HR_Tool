// API Configuration
const API_CONFIG = {
  // Base URL - có thể thay đổi theo environment
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://192.168.1.70:5002',
  
  // API Endpoints
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/auth/login',
      LOGOUT: '/auth/logout',
      REFRESH: '/auth/refresh'
    },
    LEAVE: {
      ATTENDANCE: '/leave/attendance',
      TYPE: '/leave/type',
      SUBMIT: '/leave/submit'
    },
    USER: {
      PROFILE: '/user/profile',
      SUBORDINATES: '/user/subordinates'
    }
  },
  
  // Request timeout
  TIMEOUT: 30000,
  
  // Retry configuration
  RETRY: {
    MAX_ATTEMPTS: 3,
    DELAY: 1000
  }
}

// Helper function to build full URL
export const buildApiUrl = (endpoint) => {
  return `${API_CONFIG.BASE_URL}${endpoint}`
}

// Helper function to get endpoint
export const getEndpoint = (category, action) => {
  return API_CONFIG.ENDPOINTS[category]?.[action] || ''
}

export default API_CONFIG 