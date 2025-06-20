import { defineStore } from 'pinia'

export const useAccountStore = defineStore('account', {
  state: () => ({
    username: '',
    password: '',
    rememberMe: false,
    isLoading: false,
    error: null
  }),

  getters: {
    // Kiểm tra có thông tin tài khoản đã lưu không
    hasStoredAccount: (state) => !!(state.username && state.password),
    
    // Lấy thông tin đăng nhập
    loginCredentials: (state) => ({
      username: state.username,
      password: state.password
    })
  },
  
  actions: {
    // Lưu thông tin tài khoản
    saveAccount(username, password, rememberMe = false) {
      this.username = username
      this.password = password
      this.rememberMe = rememberMe
      this.error = null
    },

    // Xóa thông tin tài khoản đã lưu
    clearAccount() {
      this.username = ''
      this.password = ''
      this.rememberMe = false
      this.error = null
    },

    // Set error
    setError(error) {
      this.error = error
    },

    // Clear error
    clearError() {
      this.error = null
    },

    // Set loading state
    setLoading(loading) {
      this.isLoading = loading
    }
  }
})