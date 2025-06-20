import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    loginTime: '',
    sessionManagement: {
      databaseTracking: false,
      sessionId: ''
    },
    tokens: {
      accessToken: '',
      expiresIn: 0,
      refreshToken: '',
      sessionId: '',
      tokenType: '',
      expiresAt: null
    },
    userInfo: {
      department: '',
      displayName: '',
      email: '',
      isManager: false,
      permissions: [],
      samAccount: '',
      subordinates: [],
      subordinatesCount: 0,
      title: '',
      userId: '',
      username: ''
    },
    managerInfo: {
      department: '',
      displayName: '',
      dn: '',
      givenName: '',
      mail: '',
      mobile: '',
      phone: '',
      samAccount: '',
      surname: '',
      title: ''
    },
    message: '',
    success: false,
    // Thêm state cho Remember Me
    rememberMe: false,
    isLoading: false
  }),
  
  actions: {
    // Enhanced setUserData với Remember Me support
    setUserData(payload, rememberMe = false) {
      try {
        // Kiểm tra payload có tồn tại không
        if (!payload) {
          console.error('Payload is null or undefined')
          return
        }

        // Kiểm tra payload.data có tồn tại không
        if (!payload.data) {
          console.error('Payload.data is null or undefined')
          return
        }

        // Cập nhật thông tin login với safe access
        this.loginTime = payload.data.login_time || ''
        
        // Cập nhật session management với safe access
        if (payload.data.session_management) {
          this.sessionManagement = {
            databaseTracking: payload.data.session_management.database_tracking || false,
            sessionId: payload.data.session_management.session_id || ''
          }
        }
        
        // Cập nhật tokens với safe access
        if (payload.data.tokens) {
          // Tính thời gian hết hạn
          const expiresAt = Date.now() + ((payload.data.tokens.expires_in || 3600) * 1000)
          
          this.tokens = {
            accessToken: payload.data.tokens.access_token || '',
            expiresIn: payload.data.tokens.expires_in || 0,
            refreshToken: payload.data.tokens.refresh_token || '',
            sessionId: payload.data.tokens.session_id || '',
            tokenType: payload.data.tokens.token_type || '',
            expiresAt: expiresAt
          }
        }
        
        // Cập nhật thông tin user với safe access
        if (payload.data.user) {
          this.userInfo = {
            department: payload.data.user.department || '',
            displayName: payload.data.user.display_name || '',
            email: payload.data.user.email || '',
            isManager: payload.data.user.is_manager || false,
            permissions: payload.data.user.permissions || [],
            samAccount: payload.data.user.sam_account || '',
            subordinates: payload.data.user.subordinates || [],
            subordinatesCount: payload.data.user.subordinates_count || 0,
            title: payload.data.user.title || '',
            userId: payload.data.user.user_id || '',
            username: payload.data.user.username || ''
          }
          
          // Cập nhật thông tin manager với safe access
          if (payload.data.user.manager_info) {
            this.managerInfo = {
              department: payload.data.user.manager_info.department || '',
              displayName: payload.data.user.manager_info.display_name || '',
              dn: payload.data.user.manager_info.dn || '',
              givenName: payload.data.user.manager_info.given_name || '',
              mail: payload.data.user.manager_info.mail || '',
              mobile: payload.data.user.manager_info.mobile || '',
              phone: payload.data.user.manager_info.phone || '',
              samAccount: payload.data.user.manager_info.sam_account || '',
              surname: payload.data.user.manager_info.surname || '',
              title: payload.data.user.manager_info.title || ''
            }
          }
        }
        
        // Cập nhật message và success status
        this.message = payload.message || ''
        this.success = payload.success || false
        this.rememberMe = rememberMe

        // 🔑 REMEMBER ME LOGIC
        this.saveToStorage(rememberMe)
        
        // Setup auto token refresh
        this.setupAutoRefresh()

        console.log('✅ User data saved successfully', {
          user: this.userInfo.displayName,
          rememberMe: rememberMe,
          storage: rememberMe ? 'localStorage' : 'sessionStorage'
        })

      } catch (error) {
        console.error('Error in setUserData:', error)
        console.error('Payload received:', payload)
      }
    },

    // 💾 Lưu vào storage based on Remember Me
    saveToStorage(rememberMe) {
      const userData = {
        loginTime: this.loginTime,
        sessionManagement: this.sessionManagement,
        tokens: this.tokens,
        userInfo: this.userInfo,
        managerInfo: this.managerInfo,
        message: this.message,
        success: this.success,
        rememberMe: rememberMe,
        savedAt: Date.now()
      }

      if (rememberMe) {
        // Lưu vào localStorage (persistent)
        localStorage.setItem('userData', JSON.stringify(userData))
        sessionStorage.removeItem('userData') // Xóa session storage nếu có
        console.log('💾 Data saved to localStorage')
      } else {
        // Chỉ lưu vào sessionStorage (temporary)
        sessionStorage.setItem('userData', JSON.stringify(userData))
        localStorage.removeItem('userData') // Xóa localStorage nếu có
        console.log('💾 Data saved to sessionStorage')
      }
    },

    // 🔄 Khôi phục dữ liệu từ storage
    restoreFromStorage() {
      try {
        // Kiểm tra localStorage trước (remember me)
        let savedData = localStorage.getItem('userData')
        let isFromLocalStorage = true

        // Nếu không có localStorage, kiểm tra sessionStorage
        if (!savedData) {
          savedData = sessionStorage.getItem('userData')
          isFromLocalStorage = false
        }

        if (savedData) {
          const userData = JSON.parse(savedData)
          
          // Kiểm tra token có hết hạn không
          if (userData.tokens?.expiresAt && Date.now() < userData.tokens.expiresAt) {
            // Restore state
            this.loginTime = userData.loginTime || ''
            this.sessionManagement = userData.sessionManagement || { databaseTracking: false, sessionId: '' }
            this.tokens = userData.tokens || {}
            this.userInfo = userData.userInfo || {}
            this.managerInfo = userData.managerInfo || {}
            this.message = userData.message || ''
            this.success = userData.success || false
            this.rememberMe = userData.rememberMe || false

            // Setup auto refresh
            this.setupAutoRefresh()

            console.log('✅ User data restored from:', isFromLocalStorage ? 'localStorage' : 'sessionStorage')
            console.log('👤 Welcome back:', this.userInfo.displayName)
            
            return true
          } else {
            // Token hết hạn, xóa storage
            console.log('⚠️ Token expired, clearing storage')
            this.clearStorage()
            return false
          }
        }
        
        return false
      } catch (error) {
        console.error('❌ Error restoring user data:', error)
        this.clearStorage() // Clear corrupted data
        return false
      }
    },

    // 🗑️ Xóa storage
    clearStorage() {
      localStorage.removeItem('userData')
      sessionStorage.removeItem('userData')
    },
    
    // Enhanced clearUserData với storage cleanup
    clearUserData() {
      this.loginTime = ''
      this.sessionManagement = {
        databaseTracking: false,
        sessionId: ''
      }
      this.tokens = {
        accessToken: '',
        expiresIn: 0,
        refreshToken: '',
        sessionId: '',
        tokenType: '',
        expiresAt: null
      }
      this.userInfo = {
        department: '',
        displayName: '',
        email: '',
        isManager: false,
        permissions: [],
        samAccount: '',
        subordinates: [],
        subordinatesCount: 0,
        title: '',
        userId: '',
        username: ''
      }
      this.managerInfo = {
        department: '',
        displayName: '',
        dn: '',
        givenName: '',
        mail: '',
        mobile: '',
        phone: '',
        samAccount: '',
        surname: '',
        title: ''
      }
      this.message = ''
      this.success = false
      this.rememberMe = false
      this.isLoading = false

      // Clear storage và auto refresh
      this.clearStorage()
      this.clearAutoRefresh()
      
      console.log('🚪 User data cleared')
    },

    // 🔄 Auto refresh token logic
    setupAutoRefresh() {
      this.clearAutoRefresh() // Clear existing timer
      
      if (!this.tokens.expiresAt) return

      // Refresh token khi còn 5 phút nữa hết hạn
      const timeUntilRefresh = this.tokens.expiresAt - Date.now() - (5 * 60 * 1000)
      
      if (timeUntilRefresh > 0) {
        this._refreshTimer = setTimeout(() => {
          this.refreshToken()
        }, timeUntilRefresh)

        console.log('⏰ Auto refresh scheduled in:', Math.round(timeUntilRefresh / 1000 / 60), 'minutes')
      }
    },

    clearAutoRefresh() {
      if (this._refreshTimer) {
        clearTimeout(this._refreshTimer)
        this._refreshTimer = null
      }
    },

    // 🔄 Refresh token
    async refreshToken() {
      try {
        if (!this.tokens.refreshToken) {
          throw new Error('No refresh token available')
        }

        this.isLoading = true
        console.log('🔄 Refreshing token...')

        // TODO: Thay thế bằng API call thực tế
        const response = await fetch('/api/auth/refresh', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.tokens.refreshToken}`
          }
        })

        if (!response.ok) {
          throw new Error('Token refresh failed')
        }

        const refreshData = await response.json()
        
        // Cập nhật token mới
        const expiresAt = Date.now() + ((refreshData.expires_in || 3600) * 1000)
        
        this.tokens = {
          ...this.tokens,
          accessToken: refreshData.access_token,
          refreshToken: refreshData.refresh_token || this.tokens.refreshToken,
          expiresIn: refreshData.expires_in || 3600,
          expiresAt: expiresAt
        }

        // Cập nhật storage
        this.saveToStorage(this.rememberMe)
        
        // Setup next refresh
        this.setupAutoRefresh()
        
        console.log('✅ Token refreshed successfully')
        
      } catch (error) {
        console.error('❌ Token refresh failed:', error)
        // Auto logout khi refresh fail
        this.clearUserData()
        // Có thể redirect to login page ở đây
      } finally {
        this.isLoading = false
      }
    },

    // 🔐 Get Authorization header
    getAuthHeader() {
      return this.tokens.accessToken ? `${this.tokens.tokenType} ${this.tokens.accessToken}` : null
    },

    // 🔍 Check permission
    hasPermission(permission) {
      return this.userInfo.permissions?.includes(permission) || false
    }
  },
  
  getters: {
    // Getter để kiểm tra xem user có đăng nhập không (enhanced)
    isLoggedIn: (state) => {
      return !!(
        state.tokens.accessToken && 
        state.tokens.expiresAt && 
        Date.now() < state.tokens.expiresAt
      )
    },
    
    // Getter để lấy tên hiển thị
    displayName: (state) => state.userInfo.displayName,
    
    // Getter để kiểm tra xem user có phải manager không
    isManager: (state) => state.userInfo.isManager,
    
    // Getter để lấy permissions
    userPermissions: (state) => state.userInfo.permissions,
    
    // Getter để lấy thông tin manager
    managerDisplayName: (state) => state.managerInfo.displayName,

    // 🕐 Thời gian còn lại của token (minutes)
    tokenTimeRemaining: (state) => {
      if (!state.tokens.expiresAt) return 0
      const remaining = state.tokens.expiresAt - Date.now()
      return Math.max(0, Math.floor(remaining / 1000 / 60))
    },

    // 🔋 Token status
    tokenStatus: (state) => {
      if (!state.tokens.accessToken) return 'no-token'
      if (!state.tokens.expiresAt) return 'unknown'
      
      const remaining = state.tokens.expiresAt - Date.now()
      if (remaining <= 0) return 'expired'
      if (remaining <= 5 * 60 * 1000) return 'expiring-soon' // < 5 minutes
      return 'valid'
    },

    // 💾 Storage info
    storageInfo: (state) => ({
      type: state.rememberMe ? 'localStorage' : 'sessionStorage',
      rememberMe: state.rememberMe
    })
  }
})