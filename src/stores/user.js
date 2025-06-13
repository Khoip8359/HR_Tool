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
      tokenType: ''
    },
    userInfo: {
      department: '',
      displayName: '',
      email: '',
      isManager: false,
      permissions: [],
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
    success: false
  }),
  
  actions: {
    setUserData(payload) {
      // Cập nhật thông tin login
      this.loginTime = payload.data.login_time
      
      // Cập nhật session management
      this.sessionManagement = {
        databaseTracking: payload.data.session_management.database_tracking,
        sessionId: payload.data.session_management.session_id
      }
      
      // Cập nhật tokens
      this.tokens = {
        accessToken: payload.data.tokens.access_token,
        expiresIn: payload.data.tokens.expires_in,
        refreshToken: payload.data.tokens.refresh_token,
        sessionId: payload.data.tokens.session_id,
        tokenType: payload.data.tokens.token_type
      }
      
      // Cập nhật thông tin user
      this.userInfo = {
        department: payload.data.user.department,
        displayName: payload.data.user.display_name,
        email: payload.data.user.email,
        isManager: payload.data.user.is_manager,
        permissions: payload.data.user.permissions,
        subordinatesCount: payload.data.user.subordinates_count,
        title: payload.data.user.title,
        userId: payload.data.user.user_id,
        username: payload.data.user.username
      }
      
      // Cập nhật thông tin manager
      this.managerInfo = {
        department: payload.data.user.manager_info.department,
        displayName: payload.data.user.manager_info.display_name,
        dn: payload.data.user.manager_info.dn,
        givenName: payload.data.user.manager_info.given_name,
        mail: payload.data.user.manager_info.mail,
        mobile: payload.data.user.manager_info.mobile,
        phone: payload.data.user.manager_info.phone,
        samAccount: payload.data.user.manager_info.sam_account,
        surname: payload.data.user.manager_info.surname,
        title: payload.data.user.manager_info.title
      }
      
      // Cập nhật message và success status
      this.message = payload.message
      this.success = payload.success
    },
    
    // Action để clear user data khi logout
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
        tokenType: ''
      }
      this.userInfo = {
        department: '',
        displayName: '',
        email: '',
        isManager: false,
        permissions: [],
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
    }
  },
  
  getters: {
    // Getter để kiểm tra xem user có đăng nhập không
    isLoggedIn: (state) => !!state.tokens.accessToken,
    
    // Getter để lấy tên hiển thị
    displayName: (state) => state.userInfo.displayName,
    
    // Getter để kiểm tra xem user có phải manager không
    isManager: (state) => state.userInfo.isManager,
    
    // Getter để lấy permissions
    userPermissions: (state) => state.userInfo.permissions,
    
    // Getter để lấy thông tin manager
    managerDisplayName: (state) => state.managerInfo.displayName
  }
})  