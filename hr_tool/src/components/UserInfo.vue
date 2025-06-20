<template>
  <div>
    <!-- User Information Card -->
    <div v-if="userInfo && userInfo.displayName" class="card mb-4 shadow-sm">
      <div class="card-header text-white rounded-top d-flex align-items-center justify-content-between px-4 py-2"
          style="background-color: rgba(0, 123, 255, 0.2); backdrop-filter: blur(6px); border-bottom: 1px solid rgba(0, 0, 0, 0.05);">
        <div class="d-flex align-items-center gap-3">
          <RouterLink to="/home/list" class="d-inline-block">
            <img src="@/assets/img/logo_v.png" alt="Logo" style="height: 40px;">
          </RouterLink>
          <h4 class="card-title mb-0 text-dark">👋 Welcome, {{ userInfo.displayName || 'User' }}</h4>
        </div>
      </div>

      <div class="card-body">
        <div class="row">
          <!-- Cột thông tin cá nhân -->
          <div class="col-md-4">
            <p class="card-text"><strong>User ID:</strong> {{ userInfo.samAccount || 'N/A' }}</p>
            <p class="card-text"><strong>Login time:</strong> {{ formatLoginTime(loginTime) || 'N/A' }}</p>
            <p class="card-text"><strong>Manager:</strong> {{ userInfo.isManager ? 'Yes' : 'No' }}</p>
          </div>
          <div class="col-md-4">
            <p class="card-text"><strong>Department:</strong> {{ userInfo.department || 'N/A' }}</p>
            <p class="card-text"><strong>Phone:</strong> {{ userInfo.phone || 'N/A' }}</p>
            <p class="card-text"><strong>Title:</strong> {{ userInfo.title || 'N/A' }}</p>
          </div> 

          <!-- Cột chức năng -->
          <div class="col-md-2 d-flex flex-column align-items-start gap-2">
            <!-- Nút đăng xuất -->
            <button 
              @click="handleLogout"
              :disabled="isLoggingOut"
              class="btn btn-outline-danger btn-sm w-100">
              <i class="bi bi-box-arrow-right me-1"></i>
              {{ isLoggingOut ? 'Đang đăng xuất...' : 'Đăng xuất' }}
            </button>

            <!-- Dropdown chọn chế độ xem -->
            <select 
              class="form-select form-select-sm w-100"
              v-model="selectedView" 
              @change="navigateView">
              <option value="/home/list">📋 Danh sách</option>
              <option value="/home/calendar">📅 Dạng lịch</option>
            </select>

            <!-- Nút viết đơn -->
            <RouterLink to="/home/add" class="w-100">
              <button class="btn btn-primary btn-sm w-100">
                <i class="bi bi-plus-circle me-1"></i> Viết đơn mới
              </button>
            </RouterLink>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="alert alert-danger" role="alert">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>
      {{ error }}
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="d-flex justify-content-center align-items-center py-5">
      <div class="spinner-border text-primary me-3" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <span class="text-muted">Đang tải thông tin nhân viên...</span>
    </div>

    <!-- No User Info -->
    <div v-if="!userInfo || !userInfo.displayName" class="d-flex justify-content-center align-items-center py-5">
      <div class="text-center">
        <i class="bi bi-person-exclamation text-muted" style="font-size: 3rem;"></i>
        <p class="text-muted mt-2">Chưa có thông tin người dùng</p>
        <small class="text-muted">Vui lòng đăng nhập lại</small>
      </div>
    </div>
    
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'

const debugMode = ref(false)
const isLoggingOut = ref(false)
const router = useRouter()

const userStore = useUserStore()
const { userInfo, managerInfo, loginTime, tokens, message } = storeToRefs(userStore)

const loading = ref(false)
const error = ref('')

const userId = computed(() => {
  console.log('Computing userId, userInfo:', userInfo.value?.samAccount)
  if (!userInfo.value?.samAccount || typeof userInfo.value.samAccount !== 'string') {
    console.log('No valid samAccount found')
    return ''
  }

  console.log('samAccount found:', userInfo.value.samAccount)
  return userInfo.value.samAccount.startsWith('u') && userInfo.value.samAccount.length > 1 
    ? userInfo.value.samAccount.substring(1) 
    : userInfo.value.samAccount
})

const selectedView = ref(router.currentRoute.value.path)

const navigateView = () => {
  if (selectedView.value !== router.currentRoute.value.path) {
    router.push(selectedView.value)
  }
}


// Format login time
const formatLoginTime = (loginTime) => {
  if (!loginTime) return ''
  try {
    const date = new Date(loginTime)
    return date.toLocaleString('vi-VN', {
      year: 'numeric',
      month: '2-digit', 
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (err) {
    return loginTime
  }
}

// Handle logout - FIXED VERSION
const handleLogout = async () => {
  if (isLoggingOut.value) return
  
  isLoggingOut.value = true
  
  try {
    console.log('🚪 Starting logout process...')
    
    // Gọi API logout nếu có token
    if (tokens.value?.accessToken) {
      try {
        const response = await fetch('http://192.168.1.70:5002/auth/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${tokens.value.accessToken}`
          }
        })

        const result = await response.json()

        if (response.ok && result.success) {
          console.log('✅ Server logout successful:', result)
        } else {
          console.warn('⚠️ Server logout failed:', result.message || 'Unknown error')
        }
      } catch (apiError) {
        console.error('❌ Logout API error:', apiError)
        // Tiếp tục logout local dù API fail
      }
    }

    // Đánh dấu đã logout để tránh auto-login
    sessionStorage.setItem('justLoggedOut', 'true')
    
    // Clear tất cả dữ liệu
    console.log('🧹 Clearing all user data and storage...')
    userStore.clearUserData()
    
    // Clear storage hoàn toàn
    localStorage.clear()

    console.log('✅ Logout completed, redirecting to login...')
    
    // Redirect về login
    await router.push('/')
    
  } catch (error) {
    console.error('💥 Logout error:', error)
    // Vẫn clear data và redirect dù có lỗi
    sessionStorage.setItem('justLoggedOut', 'true')
    userStore.clearUserData()
    localStorage.clear()
    router.push('/')
  } finally {
    isLoggingOut.value = false
  }
}

onMounted(() => {
  userStore.restoreFromStorage()
})
</script>

<style scoped>
/* Custom styles to enhance Bootstrap */
.card {
  transition: box-shadow 0.15s ease-in-out;
  border: none;
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.card:hover {
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.spinner-border {
  width: 1.5rem;
  height: 1.5rem;
}

.alert {
  border: none;
  border-radius: 0.5rem;
}

.card-header {
  border-radius: 0.5rem 0.5rem 0 0 !important;
}

.text-primary {
  color: #0d6efd !important;
}

.text-warning {
  color: #fd7e14 !important;
}

.text-success {
  color: #198754 !important;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>