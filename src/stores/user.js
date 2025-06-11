import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    authInfo: {
      domain: '',
      login_time: '',
      username: ''
    },
    userInfo: {
      account: '',
      company: '',
      department: '',
      display_name: '',
      dn: '',
      email: '',
      employee_id: '',
      first_name: '',
      last_name: '',
      mobile: '',
      phone: '',
      title: '',
      upn: ''
    },
    message: ''
  }),
  actions: {
    setUserData(payload) {
      this.authInfo = payload.data.auth_info
      this.userInfo = payload.data.user
      this.message = payload.message
    }
  }
})