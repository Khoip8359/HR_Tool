<template>
  <div class="login-container">
    <h2>🔐 AD Login Authentication</h2>

    <!-- Hiện khi đang tự động đăng nhập -->
    <div v-if="isAutoLogging" class="auto-login-loading">
      <div class="loading-spinner"></div>
      <p>🔄 Đang tự động đăng nhập...</p>
      <p class="auto-login-info">Đã tìm thấy phiên đăng nhập: <strong>{{ userStore.displayName }}</strong></p>
    </div>

    <!-- Hiện khi CHƯA có phiên đăng nhập -->
    <div v-else-if="!userStore.isLoggedIn" class="login-form">
      <div class="form-group">
        <label for="username">Tên đăng nhập - Username</label>
        <input
          id="username"
          v-model="username"
          type="text"
          placeholder="Nhập mã nhân viên - user id"
          :disabled="isLoading"
        />
      </div>

      <div class="form-group">
        <label for="password">Mật khẩu - Password</label>
        <input
          id="password"
          v-model="password"
          type="password"
          placeholder="Nhập mật khẩu - password"
          :disabled="isLoading"
          @keyup.enter="handleLogin"
        />
      </div>

      <div class="form-group checkbox-group">
        <input 
          type="checkbox" 
          id="rememberMe" 
          v-model="rememberMe"
          :disabled="isLoading"
        />
        <label for="rememberMe">Duy trì đăng nhập - Remember Me</label>
      </div>

      <button @click="handleLogin" :disabled="isLoading || !isFormValid">
        {{ isLoading ? 'Đang đăng nhập...' : 'Đăng nhập - Login' }}
      </button>
    </div>

    <!-- Hiện khi ĐÃ có phiên đăng nhập (chỉ hiện khi không tự động redirect) -->
    <div v-else-if="userStore.isLoggedIn && !autoRedirectEnabled" class="existing-session">
      <div class="session-info">
        <div class="user-welcome">
          <h3>👋 Chào mừng trở lại!</h3>
          <p class="user-name">🔐 Đã có phiên đăng nhập: <strong>{{ userStore.displayName }}</strong></p>
          <p class="token-time">⏰ Token còn: <strong>{{ userStore.tokenTimeRemaining }}</strong> phút</p>
          <p class="storage-info">💾 Lưu trữ: <strong>{{ userStore.storageInfo.type }}</strong></p>
          <div class="token-status" :class="getTokenStatusClass()">
            <span>🔋 Trạng thái: <strong>{{ getTokenStatusText() }}</strong></span>
          </div>
        </div>
        
        <div class="session-actions">
          <button @click="continueSession" class="continue-btn">
            ✅ Tiếp tục phiên làm việc
          </button>
          <button @click="clearAndLogin" class="clear-btn">
            🔄 Đăng nhập tài khoản khác
          </button>
        </div>
      </div>
    </div>

    <!-- Response message (hiện khi có thông báo) -->
    <div
      v-if="responseMessage"
      :class="['response-box', isSuccess ? 'success' : 'error']"
    >
      <pre>{{ responseMessage }}</pre>
    </div>
  </div>
</template>

<script setup>
import { useAccountStore } from '@/stores/account'
import { useUserStore } from '@/stores/user'
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const username = ref('')
const password = ref('')
const rememberMe = ref(false)
const responseMessage = ref('')
const isSuccess = ref(false)
const isLoading = ref(false)
const isAutoLogging = ref(false)
const autoRedirectEnabled = ref(true) // Bật tự động redirect
const router = useRouter()
const userStore = useUserStore()
const accountStore = useAccountStore()

// Development mode check
const showDebugInfo = ref(import.meta.env.DEV)

// Form validation
const isFormValid = computed(() => {
  return username.value.trim() !== '' && password.value.trim() !== ''
})

// Auto-restore saved credentials khi component mount
onMounted(async () => {
  // Kiểm tra xem có phải vừa logout không
  const justLoggedOut = sessionStorage.getItem('justLoggedOut')
  if (justLoggedOut) {
    console.log('🚪 Just logged out, clearing all data and showing login form')
    sessionStorage.removeItem('justLoggedOut')
    userStore.clearUserData()
    // Clear tất cả storage
    localStorage.clear()
    sessionStorage.clear()
    return
  }

  // Khôi phục session từ storage (localStorage hoặc sessionStorage)
  const restored = userStore.restoreFromStorage()
  
  if (restored && userStore.isLoggedIn) {
    console.log('👤 Existing valid session found for:', userStore.displayName)
    console.log('💾 Restored from:', userStore.storageInfo.type)
    console.log('⏰ Token expires in:', userStore.tokenTimeRemaining, 'minutes')
    
    // Kiểm tra token còn hợp lệ không và có access token không
    if ((userStore.tokenStatus === 'valid' || userStore.tokenStatus === 'expiring-soon') && 
        userStore.tokens?.accessToken) {
      // Tự động đăng nhập nếu token còn hợp lệ
      if (autoRedirectEnabled.value) {
        await handleAutoLogin()
      }
    } else {
      // Token đã hết hạn hoặc không có access token, xóa session cũ
      console.log('🔴 Token expired or invalid, clearing old session')
      userStore.clearUserData()
      localStorage.clear()
      sessionStorage.clear()
    }
  } else {
    console.log('📋 No valid session found, showing login form')
  }
})

// Xử lý tự động đăng nhập
const handleAutoLogin = async () => {
  isAutoLogging.value = true
  
  try {
    console.log('🔄 Starting auto-login for:', userStore.displayName)
    
    // Hiển thị thông báo tự động đăng nhập
    responseMessage.value = `🔄 Đang tự động đăng nhập với tài khoản: ${userStore.displayName}`
    isSuccess.value = true
    
    // Delay một chút để người dùng thấy thông báo
    // await new Promise(resolve => setTimeout(resolve, 1500))
    
    // Chuyển hướng tự động
    navigateToHome()
    
  } catch (error) {
    console.error('❌ Auto-login failed:', error)
    isAutoLogging.value = false
    showError('Tự động đăng nhập thất bại. Vui lòng đăng nhập lại.')
    userStore.clearUserData()
  }
}

// Tiếp tục phiên làm việc hiện tại
const continueSession = () => {
  navigateToHome()
}

// Xóa session cũ và đăng nhập mới
const clearAndLogin = () => {
  userStore.clearUserData()
  responseMessage.value = ''
  isSuccess.value = false
}

// Navigation logic
const navigateToHome = () => {
  const userData = userStore.userInfo
  
  setTimeout(() => {
    if (userData.isManager === true) {
      router.push('/home/manager/list')
    } else {
      router.push('/home/list')
    }
  }, 0)
}

// Main login handler
const handleLogin = async () => {
  // Validation
  if (!isFormValid.value) {
    showError('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu')
    return
  }

  // Reset state
  resetLoginState()
  isLoading.value = true

  try {
    console.log('🔐 Attempting login for:', username.value)
    
    const response = await fetch('http://192.168.1.70:5002/auth/login', {
      method: 'POST',
      credentials: "include",
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value,
        remember_me: rememberMe.value
      })
    })

    const responseData = await response.json()
    console.log('📡 API Response:', responseData)

    if (response.ok && responseData.success) {
      await handleLoginSuccess(responseData)
    } else {
      handleLoginError(responseData)
    }
  } catch (err) {
    handleLoginException(err)
  } finally {
    isLoading.value = false
  }
}

// Handle successful login
const handleLoginSuccess = async (responseData) => {
  try {
    // Validate response data
    if (!responseData.data) {
      throw new Error('Response data is missing')
    }

    if (!responseData.data.user) {
      throw new Error('User data is missing from response')
    }

    // Save to user store với remember me
    userStore.setUserData(responseData, rememberMe.value)
    
    if (accountStore.saveAccount) {
      accountStore.saveAccount(username.value, '', true) // Pass empty password
    }

    isSuccess.value = true
    responseMessage.value = `✅ Đăng nhập thành công!\n👋 Chào mừng: ${userStore.displayName}`
    
    console.log('✅ Login successful for:', userStore.displayName)
    console.log('💾 Storage type:', userStore.storageInfo.type)
    
    // Navigate to appropriate page
    navigateToHome()
    
  } catch (error) {
    console.error('❌ Error processing login success:', error)
    showError(`Lỗi xử lý đăng nhập: ${error.message}`)
  }
}

// Handle login error response
const handleLoginError = (responseData) => {
  isSuccess.value = false
  const errorMessage = responseData?.message || 'Lỗi không xác định'
  const errorCode = responseData?.error_code || 'N/A'
  
  responseMessage.value = `❌ Đăng nhập thất bại\n📝 Thông báo: ${errorMessage}\n🔢 Mã lỗi: ${errorCode}`
  
  console.error('🚫 Login failed:', { errorMessage, errorCode })
}

// Handle login exception
const handleLoginException = (err) => {
  isSuccess.value = false
  let errorMessage = 'Có lỗi xảy ra khi đăng nhập'
  
  if (err.name === 'TypeError' && err.message.includes('fetch')) {
    errorMessage = '🌐 Không thể kết nối đến server.\n📡 Vui lòng kiểm tra kết nối mạng.'
  } else if (err.message.includes('JSON')) {
    errorMessage = '📄 Server trả về dữ liệu không hợp lệ.'
  } else {
    errorMessage = err.message
  }
  
  responseMessage.value = `❌ Lỗi đăng nhập\n🔍 Chi tiết: ${errorMessage}`
  console.error('💥 Login exception:', err)
}

// Helper functions
const resetLoginState = () => {
  responseMessage.value = ''
  isSuccess.value = false
}

const showError = (message) => {
  responseMessage.value = `❌ ${message}`
  isSuccess.value = false
}

// Token status helpers
const getTokenStatusClass = () => {
  const status = userStore.tokenStatus
  return {
    'status-valid': status === 'valid',
    'status-expiring': status === 'expiring-soon',
    'status-expired': status === 'expired',
    'status-unknown': status === 'unknown' || status === 'no-token'
  }
}

const getTokenStatusText = () => {
  const status = userStore.tokenStatus
  switch (status) {
    case 'valid': return 'Hợp lệ'
    case 'expiring-soon': return 'Sắp hết hạn'
    case 'expired': return 'Đã hết hạn'
    case 'no-token': return 'Không có token'
    default: return 'Không xác định'
  }
}
</script>

<style scoped>
.login-container {
  max-width: 450px;
  margin: 40px auto;
  background: #fff;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #333;
}

/* Auto Login Loading Styles */
.auto-login-loading {
  text-align: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
  border-radius: 12px;
  border: 2px solid #bbdefb;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #2196f3;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.auto-login-loading p {
  margin: 8px 0;
  color: #1976d2;
  font-weight: 500;
}

.auto-login-info {
  font-size: 14px;
  color: #424242;
}

/* Login Form Styles */
.login-form {
  width: 100%;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #555;
}

input[type="text"],
input[type="password"] {
  width: 100%;
  padding: 12px;
  box-sizing: border-box;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s ease;
}

input[type="text"]:focus,
input[type="password"]:focus {
  outline: none;
  border-color: #007bff;
}

input[type="text"]:disabled,
input[type="password"]:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.checkbox-group {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
  margin-right: 8px;
  transform: scale(1.1);
}

.checkbox-group label {
  margin-bottom: 0;
  cursor: pointer;
  user-select: none;
}

button {
  width: 100%;
  padding: 12px;
  background: #007bff;
  color: white;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 16px;
}

button:hover:not(:disabled) {
  background: #0056b3;
  transform: translateY(-1px);
}

button:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
}

/* Token Status Styles */
.storage-info {
  margin: 8px 0;
  color: #0c5460;
  font-size: 14px;
}

.token-status {
  margin: 12px 0;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
}

.status-valid {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-expiring {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.status-expired {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.status-unknown {
  background: #f8f9fa;
  color: #6c757d;
  border: 1px solid #dee2e6;
}

.existing-session {
  width: 100%;
  padding: 20px;
  background: linear-gradient(135deg, #e8f4fd 0%, #f0f8ff 100%);
  border: 2px solid #bee5eb;
  border-radius: 12px;
  text-align: center;
}

.session-info {
  width: 100%;
}

.user-welcome h3 {
  margin: 0 0 16px 0;
  color: #0c5460;
  font-size: 20px;
}

.user-name, .token-time {
  margin: 12px 0;
  color: #0c5460;
  font-size: 16px;
}

.user-name strong, .token-time strong {
  color: #064d57;
}

.session-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
  flex-direction: column;
}

.continue-btn, .clear-btn {
  width: 100%;
  margin: 0;
  padding: 12px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.continue-btn {
  background: #28a745;
  color: white;
}

.continue-btn:hover {
  background: #218838;
  transform: translateY(-1px);
}

.clear-btn {
  background: #6c757d;
  color: white;
}

.clear-btn:hover {
  background: #545b62;
  transform: translateY(-1px);
}

.response-box {
  margin-top: 20px;
  padding: 16px;
  white-space: pre-wrap;
  border-left: 4px solid;
  background: #f8f9fa;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.success {
  border-left-color: #28a745;
  color: #155724;
  background: #d4edda;
}

.error {
  border-left-color: #dc3545;
  color: #721c24;
  background: #f8d7da;
}

.debug-info {
  margin-top: 20px;
  padding: 12px;
  background: #f1f3f4;
  border-radius: 8px;
  font-size: 12px;
  border: 1px solid #dee2e6;
}

.debug-info h4 {
  margin: 0 0 8px 0;
  color: #6c757d;
}

.debug-info p {
  margin: 4px 0;
  color: #6c757d;
}

/* Responsive */
@media (max-width: 480px) {
  .login-container {
    margin: 20px;
    padding: 20px;
  }
  
  .session-actions {
    gap: 8px;
  }
  
  .user-welcome h3 {
    font-size: 18px;
  }
  
  .user-name, .token-time {
    font-size: 14px;
  }
}

@media (min-width: 481px) {
  .session-actions {
    flex-direction: row;
  }
  
  .continue-btn, .clear-btn {
    width: 48%;
  }
}
</style>