<template>
  <div class="container-fluid py-4">
    <!-- Debug info -->
    <div v-if="debugMode" class="alert alert-info mb-4">
      <h5 class="alert-heading">Debug Info:</h5>
      <p class="mb-1"><strong>userInfo:</strong> {{ JSON.stringify(userInfo) }}</p>
      <p class="mb-1"><strong>authInfo:</strong> {{ JSON.stringify(authInfo) }}</p>
      <p class="mb-0"><strong>userId computed:</strong> {{ userId }}</p>
    </div>
    
    <!-- User Information Card -->
    <div v-if="userInfo" class="card mb-4">
      <div class="card-header bg-primary text-white">
        <h4 class="card-title mb-0">🎉 Welcome, {{ userInfo.display_name || 'User' }}</h4>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-6">
            <p class="card-text"><strong>Username:</strong> {{ authInfo?.username || 'N/A' }}</p>
            <p class="card-text"><strong>Login time:</strong> {{ authInfo?.login_time || 'N/A' }}</p>
            <p class="card-text"><strong>Email:</strong> {{ userInfo.upn || 'N/A' }}</p>
          </div>
          <div class="col-md-6">
            <p class="card-text"><strong>Department:</strong> {{ userInfo.department || 'N/A' }}</p>
            <p class="card-text"><strong>Phone:</strong> {{ userInfo.phone || 'N/A' }}</p>
            <p class="card-text"><strong>Message:</strong> {{ message || 'N/A' }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="d-flex justify-content-center align-items-center py-5">
      <div class="spinner-border text-primary me-3" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <span class="text-muted">Đang tải thông tin người dùng...</span>
    </div>
    
    <!-- Leave Data Section -->
    <div class="card">
      <div class="card-header bg-secondary text-white">
        <h5 class="card-title mb-0">Thông tin nghỉ phép</h5>
      </div>
      <div class="card-body">
        <!-- Loading State -->
        <div v-if="loading" class="d-flex justify-content-center align-items-center py-4">
          <div class="spinner-border text-primary me-3" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <span class="text-muted">Đang tải dữ liệu nghỉ phép...</span>
        </div>
        
        <!-- Error State -->
        <div v-if="error" class="alert alert-danger" role="alert">
          <i class="bi bi-exclamation-triangle-fill me-2"></i>
          {{ error }}
        </div>
        
        <!-- Leave Data Table -->
        <div v-if="leaveLetter.length > 0" class="table-responsive">
          <table class="table table-hover table-striped align-middle">
            <thead class="table-dark">
              <tr>
                <th scope="col" class="text-center">STT</th>
                <th scope="col">
                  <i class="bi bi-person-circle me-2"></i>Tên nhân viên
                </th>
                <th scope="col">
                  <i class="bi bi-card-text me-2"></i>Mã NV
                </th>
                <th scope="col">
                  <i class="bi bi-calendar-event me-2"></i>Ngày nghỉ
                </th>
                <th scope="col">
                  <i class="bi bi-building me-2"></i>Phòng ban
                </th>
                <th scope="col">
                  <i class="bi bi-file-text me-2"></i>Loại phép
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in leaveLetter" :key="index">
                <td class="text-center">
                  <span class="badge bg-primary">{{ index + 1 }}</span>
                </td>
                <td>
                  <strong class="text-dark">{{ item.EmployeeName }}</strong>
                </td>
                <td>
                  <span class="text fw-semibold">{{ item.EmployeeID }}</span>
                </td>
                <td>
                  <span class="text fw-semibold">{{ item.LeaveDate }}</span>
                </td>
                <td>
                  <span class="text fw-semibold">{{ item.DepartmentNameU }}</span>
                </td>
                <td>
                  <span class="text fw-semibold">{{ item.LeaveTypeNameU }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- No Data State -->
        <div v-else-if="!loading && !error && hasAttemptedFetch" class="text-center py-5">
          <i class="bi bi-inbox display-1 text-muted mb-3"></i>
          <p class="text-muted">Không có dữ liệu nghỉ phép</p>
        </div>
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
import { ref, onMounted, computed, watch } from 'vue'
import { useUserStore } from '@/stores/user'

// Debug mode
const debugMode = ref(false)

const userStore = useUserStore()
const { authInfo, userInfo, message } = userStore

// Log để debug
console.log('UserStore:', userStore)
console.log('userInfo:', userInfo)
console.log('authInfo:', authInfo)

const leaveLetter = ref([])
const loading = ref(false)
const error = ref('')
const hasAttemptedFetch = ref(false)

// Computed userId với kiểm tra an toàn
const userId = computed(() => {
  console.log('Computing userId, userInfo:', userInfo)
  
  // Kiểm tra nhiều trường hợp có thể
  const username = userInfo?.username || authInfo?.username
  
  if (!username || typeof username !== 'string') {
    console.log('No valid username found')
    return ''
  }
  
  console.log('Username found:', username)
  return username.length > 1 ? username.substring(1) : username
})

const fetchLeaveDate = async () => {
  console.log('fetchLeaveDate called, userId:', userId.value)
  
  if (!userId.value || !userId.value.trim()) {
    error.value = 'Không tìm thấy mã nhân viên hợp lệ'
    hasAttemptedFetch.value = true
    return
  }

  loading.value = true
  error.value = ''
  leaveLetter.value = []

  try {
    console.log('Fetching data for userId:', userId.value)
    const res = await fetch(`http://192.168.1.70:5001/api/leave/${userId.value}`)
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: Không tìm thấy dữ liệu hoặc lỗi server`)
    }
    
    const data = await res.json()
    console.log('Fetched data:', data)
    leaveLetter.value = data
  } catch (err) {
    console.error('Fetch error:', err)
    error.value = err.message
  } finally {
    loading.value = false
    hasAttemptedFetch.value = true
  }
}

// Watch userId thay vì dùng onMounted
watch(userId, (newUserId) => {
  console.log('userId changed:', newUserId)
  if (newUserId && newUserId.trim()) {
    fetchLeaveDate()
  }
}, { immediate: true })

// Fallback: nếu sau 2 giây vẫn không có userId, thử fetch một lần
onMounted(() => {
  setTimeout(() => {
    if (!hasAttemptedFetch.value && userId.value) {
      console.log('Fallback fetch after 2 seconds')
      fetchLeaveDate()
    }
  }, 2000)
})
</script>

<style scoped>
/* Custom styles to enhance Bootstrap */
.border-start {
  border-left-width: 4px !important;
}

.card {
  transition: box-shadow 0.15s ease-in-out;
}

.card:hover {
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.spinner-border {
  width: 1.5rem;
  height: 1.5rem;
}

.display-1 {
  font-size: 4rem;
  opacity: 0.3;
}
</style>