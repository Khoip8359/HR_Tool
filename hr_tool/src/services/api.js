import API_CONFIG, { buildApiUrl, getEndpoint } from '@/config/api'

// API Service class
class ApiService {
  constructor() {
    this.baseURL = API_CONFIG.BASE_URL
    this.timeout = API_CONFIG.TIMEOUT
  }

  // Generic request method with retry logic
  async request(endpoint, options = {}) {
    const url = buildApiUrl(endpoint)
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      timeout: this.timeout,
      ...options
    }

    let lastError
    for (let attempt = 1; attempt <= API_CONFIG.RETRY.MAX_ATTEMPTS; attempt++) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), this.timeout)
        
        const response = await fetch(url, {
          ...config,
          signal: controller.signal
        })
        
        clearTimeout(timeoutId)
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        return await response.json()
        
      } catch (error) {
        lastError = error
        console.warn(`API request attempt ${attempt} failed:`, error.message)
        
        if (attempt < API_CONFIG.RETRY.MAX_ATTEMPTS) {
          await this.delay(API_CONFIG.RETRY.DELAY * attempt)
        }
      }
    }
    
    throw lastError
  }

  // Helper method for delay
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  // Auth methods
  async login(credentials) {
    return this.request(getEndpoint('AUTH', 'LOGIN'), {
      method: 'POST',
      body: JSON.stringify(credentials)
    })
  }

  async logout(token) {
    return this.request(getEndpoint('AUTH', 'LOGOUT'), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  }

  async refreshToken(refreshToken) {
    return this.request(getEndpoint('AUTH', 'REFRESH'), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refreshToken}`
      }
    })
  }

  // Leave methods
  async getLeaveAttendance(employeeId, token) {
    return this.request(getEndpoint('LEAVE', 'ATTENDANCE'), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ employee_id: employeeId })
    })
  }

  async getLeaveTypes(token) {
    return this.request(getEndpoint('LEAVE', 'TYPE'), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  }

  async submitLeave(leaveData, token) {
    return this.request(getEndpoint('LEAVE', 'SUBMIT'), {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(leaveData)
    })
  }

  // User methods
  async getUserProfile(token) {
    return this.request(getEndpoint('USER', 'PROFILE'), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  }

  async getSubordinates(token) {
    return this.request(getEndpoint('USER', 'SUBORDINATES'), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  }
}

// Create singleton instance
const apiService = new ApiService()

export default apiService 