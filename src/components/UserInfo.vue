<template>
  <div>
    <!-- Debug info -->
    <div v-if="debugMode" class="alert alert-info mb-4">
      <h5 class="alert-heading">Debug Info:</h5>
      <p class="mb-1"><strong>userInfo:</strong> {{ JSON.stringify(userInfo) }}</p>
      <p class="mb-1"><strong>loginTime:</strong> {{ loginTime }}</p>
      <p class="mb-1"><strong>managerInfo:</strong> {{ JSON.stringify(managerInfo) }}</p>
      <p class="mb-1"><strong>tokens:</strong> {{ JSON.stringify(tokens) }}</p>
      <p class="mb-0"><strong>userId computed:</strong> {{ userId }}</p>
    </div>
    
    <!-- User Information Card -->
    <div v-if="userInfo && userInfo.displayName" class="card mb-4">
      <div class="card-header bg-primary text-white">
        <h4 class="card-title mb-0">Welcome, {{ userInfo.displayName || 'User' }}</h4>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-6">
            <p class="card-text"><strong>User ID:</strong> {{ username || 'N/A' }}</p>
            <p class="card-text"><strong>Login time:</strong> {{ formatLoginTime(loginTime) || 'N/A' }}</p>
            <p class="card-text"><strong>Manager:</strong> {{ userInfo.isManager ? 'Yes' : 'No' }}</p>
          </div>
          <div class="col-md-6">
            <p class="card-text"><strong>Department:</strong> {{ employee.DepartmentNameU || userInfo.department || 'N/A' }}</p>
            <p class="card-text"><strong>Phone:</strong> {{ userInfo.phone || 'N/A' }}</p>
            <p class="card-text"><strong>Title:</strong> {{ userInfo.title || 'N/A' }}</p>
          </div>  
        </div>
      </div>
    </div>

    <!-- Manager Information Card -->
    <div v-if="managerInfo && managerInfo.displayName" class="card mb-4">
      <div class="card-header bg-secondary text-white">
        <h5 class="card-title mb-0">Manager Information</h5>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-6">
            <p class="card-text"><strong>Name:</strong> {{ managerInfo.displayName }}</p>
            <p class="card-text"><strong>Email:</strong> {{ managerInfo.mail || 'N/A' }}</p>
            <p class="card-text"><strong>Department:</strong> {{ managerInfo.department || 'N/A' }}</p>
          </div>
          <div class="col-md-6">
            <p class="card-text"><strong>Phone:</strong> {{ managerInfo.phone || 'N/A' }}</p>
            <p class="card-text"><strong>Mobile:</strong> {{ managerInfo.mobile || 'N/A' }}</p>
            <p class="card-text"><strong>Title:</strong> {{ managerInfo.title || 'N/A' }}</p>
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
    
    <!-- Debug Toggle Button -->
    <div class="d-flex justify-content-end mt-4">
      <button @click="debugMode = !debugMode" class="btn btn-outline-info btn-sm">
        <i class="bi bi-bug me-1"></i>
        {{ debugMode ? 'Ẩn' : 'Hiện' }} Debug Info
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import { useAccountStore } from '@/stores/account'

// Debug mode
const debugMode = ref(false)

const userStore = useUserStore()
const accountStore = useAccountStore()
const { userInfo, managerInfo, loginTime, tokens, message } = storeToRefs(userStore)
const { username } = accountStore.loginCredentials

// Log để debug
console.log('UserStore:', userStore)
console.log('userInfo:', userInfo.value)
console.log('loginTime:', loginTime.value)
console.log('managerInfo:', managerInfo.value)

const employee = ref({})
const loading = ref(false)
const error = ref('')

// Computed userId với kiểm tra an toàn
const userId = computed(() => {
  console.log('Computing userId, userInfo:', username)

  if (!username || typeof username !== 'string') {
    console.log('No valid username found')
    return ''
  }
  
  console.log('Username found:', username)
  // Nếu username bắt đầu bằng 'u' thì bỏ ký tự đầu
  return username.startsWith('u') && username.length > 1 ? username.substring(1) : username
})

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

const fetchEmployee = async () => {
  console.log('fetchEmployee called, userId:', userId.value)
  
  if (!userId.value || !userId.value.trim()) {
    error.value = 'Không tìm thấy mã nhân viên hợp lệ'
    return
  }

  loading.value = true
  error.value = ''
  employee.value = {}

  try {
    const res = await fetch(`http://192.168.1.70:5002/api/employee/${userId.value}`)
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: Không tìm thấy dữ liệu hoặc lỗi server`)
    }
    
    const data = await res.json()
    console.log('Fetched employee data:', data)
    employee.value = data[0] || {}
  } catch (err) {
    console.error('Fetch employee error:', err)
    error.value = err.message
  } finally {
    loading.value = false
  }
}

// Watch userId changes
watch(userId, (newUserId) => {
  console.log('userId changed:', newUserId)
  if (newUserId && newUserId.trim()) {
    fetchEmployee()
  }
}, { immediate: true })

// Watch userInfo changes
watch(userInfo, (newUserInfo) => {
  console.log('userInfo changed:', newUserInfo)
  if (newUserInfo && (newUserInfo.username || newUserInfo.userId)) {
    fetchEmployee()
  }
}, { immediate: true, deep: true })

onMounted(() => {
  // Fallback để fetch employee sau 2 giây nếu có userId
  setTimeout(() => {
    if (userId.value) {
      console.log('Fallback employee fetch after 2 seconds')
      fetchEmployee()
    }
  }, 2000)
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

.bi {
  font-size: 1rem;
}
</style>