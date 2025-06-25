<template>
  <div class="card">
    <div class="card-header bg-secondary text-white d-flex justify-content-between align-items-center">
      <h5 class="card-title mb-0">Thông tin nghỉ phép</h5>
      <div v-if="leaveLetter.length > 0" class="text-white-50 small">
        Tổng: {{ totalRecords }} bản ghi
      </div>
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
      <div v-if="error && !loading" class="alert alert-danger" role="alert">
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        {{ error }}
      </div>
      
      <!-- Leave Data Table -->
      <div v-if="currentYearData.length > 0 && !loading" class="table-responsive">
        <!-- Controls Row -->
        <div class="row mb-3 align-items-center">
          <div class="col-md-4">
            <div class="d-flex align-items-center">
              <label class="form-label me-2 mb-0 text-nowrap">Năm:</label>
              <select 
                v-model="selectedYear" 
                class="form-select form-select-sm"
                style="width: 100px;"
              >
                <option v-for="year in availableYears" :key="year" :value="year">
                  {{ year }}
                </option>
              </select>
              <span class="ms-2 text-muted small">
                ({{ getYearRecordCount(selectedYear) }} bản ghi)
              </span>
            </div>
          </div>
          
          <div class="col-md-4 text-center">
            <div class="text-muted small">
              <strong>Năm {{ selectedYear }}</strong>
            </div>
          </div>
          
          <div class="col-md-4">
            <div class="d-flex justify-content-end">
              <div class="input-group" style="max-width: 280px;">
                <input 
                  v-model="searchTerm" 
                  type="text" 
                  class="form-control form-control-sm" 
                  placeholder="Tìm kiếm"
                >
              </div>
            </div>
          </div>
        </div>

        <!-- Year Summary Stats -->
        <div class="row mb-3">
          <div class="col-12">
            <div class="d-flex flex-wrap gap-3">
              <div class="bg-light rounded p-2 border">
                <strong class="text-muted">Tổng nghỉ phép</strong>
                <div class="fw-bold text-primary">{{ yearStats.totalLeaves }} lần</div>
              </div>
              <div class="bg-light rounded p-2 border" v-if="yearStats.leaveTypes.length > 0">
                <strong class="text-muted">Loại phép phổ biến</strong>
                <div class="fw-bold text-success">{{ yearStats.mostCommonLeaveType }}</div>
              </div>
              <div class="bg-light rounded p-2 border">
                <strong class="text-muted">Số ngày nghỉ còn lại</strong>
                <div class="fw-bold text-warning">{{ remain }} ngày ( {{ remain*8 }} giờ )</div>
              </div>
              <div class="bg-light rounded p-2 border">
                <strong class="text-muted">Số phép phụ nữ còn lại</strong>
                <div class="fw-bold text-danger">{{ PPN_count }} phép ( {{ PPN_count*0.5 }} giờ )</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Monthly Breakdown -->
        <div class="row mb-3" v-if="monthlyData.length > 0">
          <div class="col-11">
            <h6 class="text-muted mb-2">
              <i class="bi bi-calendar3 me-2"></i>Thống kê theo tháng
            </h6>
            <div class="d-flex flex-wrap gap-2">
              <button
                v-for="month in monthlyData" 
                :key="month.month"
                @click="selectedMonth = selectedMonth === month.month ? null : month.month"
                class="btn btn-sm"
                :class="selectedMonth === month.month ? 'btn-primary' : 'btn-outline-primary'"
              >
                T{{ month.month }} ({{ month.count }})
              </button>
              <button
                v-if="selectedMonth"
                @click="selectedMonth = null"
                class="btn btn-sm btn-outline-secondary"
              >
                <i class="bi bi-x"></i> Tất cả
              </button>
            </div>
          </div>
        </div>

        <!-- Data Table -->
        <table class="table table-hover table-striped align-middle">
          <thead class="table-dark">
            <tr>
              <th scope="col" class="text-center" style="width: 60px;">STT</th>
              <th scope="col" style="width: 100px;" class="text-center">
                <i class="bi bi-card-text me-2"></i>Mã NV
              </th>
              <th scope="col" style="width: 120px;" class="text-center">
                <i class="bi bi-calendar-event me-2"></i>Ngày nghỉ
              </th>
              <th scope="col" style="width: 100px;" class="text-center">
                <i class="bi bi-clock me-2"></i>Thời gian nghỉ
              </th>
              <th scope="col" style="width: 80px;" class="text-center">
                <i class="bi bi-calendar2-month me-2"></i>Tháng
              </th>
              <th scope="col" style="width: 120px;" class="text-center">
                <i class="bi bi-file-text me-2"></i>Loại phép
              </th>
              <th scope="col" style="width: 150px;" class="text-center">
                <i class="bi bi-info-circle me-2"></i>Tên loại phép
              </th>
              <th scope="col" style="width: 80px;" class="text-center">
                <i class="bi bi-calendar-date me-2"></i>Năm
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in filteredData" :key="`${item.EmployeeID}-${item.LeaveDate}-${index}`">
              <td class="text-center">
                <span class="badge bg-primary">{{ index + 1 }}</span>
              </td>
              <td class="text-center">
                <span class="fw-semibold">{{ item.EmployeeID || 'N/A' }}</span>
              </td>
              <td class="text-center">
                <span class="fw-semibold">{{ formatDate(item.LeaveDate) }}</span>
              </td>
              <td class="text-center">
                <span class="fw-semibold text-primary">{{ formatQuantity(item.Quantity) }}</span>
              </td>
              <td class="text-center">
                <span class="fw-semibold">{{ getMonth(item.LeaveDate) }}</span>
              </td>
              <td class="text-center">
                <span class="badge bg-info text-dark">{{ item.LeaveTypeID || 'N/A' }}</span>
              </td>
              <td class="text-center">
                <span class="fw-semibold text-success">{{ item.LeaveTypeNameU || 'N/A' }}</span>
              </td>
              <td class="text-center">
                <span class="fw-semibold">{{ item.TranYear || 'N/A' }}</span>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Display Info -->
        <div class="row align-items-center mt-3">
          <div class="col-12 text-center">
            <div class="text-muted small">
              {{ displayInfoText }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- No Data State -->
      <div v-else-if="!loading && !error && hasAttemptedFetch && leaveLetter.length === 0" class="text-center py-5">
        <i class="bi bi-inbox display-1 text-muted mb-3"></i>
        <h5 class="text-muted">Không có dữ liệu nghỉ phép</h5>
        <p class="text-muted small">Chưa có thông tin nghỉ phép nào được ghi nhận</p>
      </div>

      <!-- No Data for Selected Year -->
      <div v-else-if="!loading && !error && leaveLetter.length > 0 && currentYearData.length === 0" class="text-center py-5">
        <i class="bi bi-calendar-x display-1 text-muted mb-3"></i>
        <h5 class="text-muted">Không có dữ liệu cho năm {{ selectedYear }}</h5>
        <p class="text-muted">Hãy chọn năm khác để xem dữ liệu nghỉ phép</p>
      </div>

      <!-- No Search Results -->
      <div v-else-if="!loading && !error && currentYearData.length > 0 && filteredData.length === 0 && searchTerm" class="text-center py-5">
        <i class="bi bi-search display-1 text-muted mb-3"></i>
        <h5 class="text-muted">Không tìm thấy kết quả</h5>
        <p class="text-muted">Không có kết quả nào trong năm {{ selectedYear }} phù hợp với từ khóa <strong>"{{ searchTerm }}"</strong></p>
        <button @click="clearSearch" class="btn btn-outline-secondary btn-sm">
          <i class="bi bi-x-circle me-1"></i>Xóa tìm kiếm
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'

const props = defineProps({
  userId: {
    type: String,
    default: ''
  }
})

const userStore = useUserStore()
const { authInfo, userInfo } = storeToRefs(userStore)

const leaveLetter = ref([])
const loading = ref(false)
const error = ref('')
const hasAttemptedFetch = ref(false)

// Year-based states
const selectedYear = ref(new Date().getFullYear())
const selectedMonth = ref(null)
const searchTerm = ref('')
const remain = ref('')
const PPN_count = ref('')

// Computed userId từ store
const computedUserId = computed(() => {
  if (!userInfo.value.samAccount || typeof userInfo.value.samAccount !== 'string') {
    return ''
  }

  return userInfo.value.samAccount.length > 1 
    ? "0" + userInfo.value.samAccount.substring(1) 
    : userInfo.value.samAccount
})

// Get available years from data - sử dụng TranYear hoặc LeaveDate
const availableYears = computed(() => {
  const years = new Set()
  leaveLetter.value.forEach(item => {
    // Ưu tiên TranYear, fallback về LeaveDate
    let year = item.TranYear
    if (!year && item.LeaveDate) {
      year = new Date(item.LeaveDate).getFullYear()
    }
    if (year && !isNaN(year)) {
      years.add(year)
    }
  })
  return Array.from(years).sort((a, b) => b - a) // Descending order
})

// Get data for selected year - sử dụng TranYear
const currentYearData = computed(() => {
  return leaveLetter.value.filter(item => {
    // Ưu tiên TranYear, fallback về LeaveDate
    let year = item.TranYear
    if (!year && item.LeaveDate) {
      year = new Date(item.LeaveDate).getFullYear()
    }
    return year === selectedYear.value
  })
})

// Filter by selected month if any - sử dụng LeaveDate
const monthFilteredData = computed(() => {
  if (!selectedMonth.value) return currentYearData.value
  
  return currentYearData.value.filter(item => {
    if (!item.LeaveDate) return false
    
    const itemMonth = new Date(item.LeaveDate).getMonth() + 1
    return itemMonth === selectedMonth.value
  })
})

// Apply search filter - cập nhật để search theo các trường mới
const filteredData = computed(() => {
  if (!searchTerm.value) {
    return monthFilteredData.value
  }
  
  const term = searchTerm.value.toLowerCase().trim()
  return monthFilteredData.value.filter(item => 
    (item.EmployeeID && item.EmployeeID.toLowerCase().includes(term)) ||
    (item.LeaveTypeID && item.LeaveTypeID.toLowerCase().includes(term)) ||
    (item.LeaveTypeNameU && item.LeaveTypeNameU.toLowerCase().includes(term)) ||
    (item.TranYear && item.TranYear.toString().includes(term))
  )
})

// Monthly data summary - sử dụng LeaveDate
const monthlyData = computed(() => {
  const monthCounts = {}
  currentYearData.value.forEach(item => {
    if (item.LeaveDate) {
      const month = new Date(item.LeaveDate).getMonth() + 1
      monthCounts[month] = (monthCounts[month] || 0) + 1
    }
  })
  
  return Object.entries(monthCounts)
    .map(([month, count]) => ({ month: parseInt(month), count }))
    .sort((a, b) => a.month - b.month)
})

// Year statistics - cập nhật để tính tổng số ngày nghỉ và loại phép phổ biến
const yearStats = computed(() => {
  const data = currentYearData.value
  
  // Total leaves
  const totalLeaves = data.length

  // Most common leave type - sử dụng LeaveTypeNameU
  const leaveTypes = {}
  data.forEach(item => {
    if (item.LeaveTypeNameU) {
      leaveTypes[item.LeaveTypeNameU] = (leaveTypes[item.LeaveTypeNameU] || 0) + 1
    }
  })
  
  const mostCommonLeaveType = Object.entries(leaveTypes)
    .sort(([,a], [,b]) => b - a)[0]?.[0] || 'N/A'
  
  return {
    totalLeaves,
    leaveTypes: Object.keys(leaveTypes),
    mostCommonLeaveType
  }
})

// Total records after all filtering
const totalRecords = computed(() => filteredData.value.length)

// Display info text
const displayInfoText = computed(() => {
  if (totalRecords.value === 0) return 'Không có dữ liệu để hiển thị'
  
  let text = `Hiển thị ${totalRecords.value} bản ghi`
  
  if (selectedMonth.value) {
    text += ` trong tháng ${selectedMonth.value}`
  }
  text += ` năm ${selectedYear.value}`
  
  if (searchTerm.value) {
    text += ` (tìm kiếm: "${searchTerm.value}")`
  }
  
  return text
})

// Utility functions
const getYearRecordCount = (year) => {
  return leaveLetter.value.filter(item => {
    let itemYear = item.TranYear
    if (!itemYear && item.LeaveDate) {
      itemYear = new Date(item.LeaveDate).getFullYear()
    }
    return itemYear === year
  }).length
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('vi-VN')
  } catch {
    return 'N/A'
  }
}

const getMonth = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return `T${date.getMonth() + 1}`
  } catch {
    return 'N/A'
  }
}

const formatQuantity = (quantity) => {
  if (!quantity) return '0'
  const num = parseFloat(quantity)
  if (isNaN(num)) return '0'
  
  if (num === 0.0625) return '30 phút (nửa giờ)'
  if (num === 0.5) return '0.5 ngày (4 giờ)'
  if (num === 1) return '1 ngày (8 giờ)'
  
  return num < 1 ? `${(num * 8).toFixed(1)} giờ` : `${num.toFixed(1)} ngày`
}

const clearSearch = () => {
  searchTerm.value = ''
}

// Watchers
watch(selectedYear, () => {
  selectedMonth.value = null
})

// Initialize selected year when data is loaded
watch(availableYears, (newYears) => {
  if (newYears.length > 0 && !newYears.includes(selectedYear.value)) {
    selectedYear.value = newYears[0] // Select the most recent year
  }
}, { immediate: true })

// API functions - CẬP NHẬT ĐỂ XỬ LÝ ĐÚNG CẤU TRÚC DỮ LIỆU
const fetchLeaveData = async () => {
  console.log('🟡 fetchLeaveData called. User ID:', computedUserId.value)

  const userId = computedUserId.value?.trim()

  if (!userId) {
    error.value = '❌ Không tìm thấy mã nhân viên hợp lệ.'
    hasAttemptedFetch.value = true
    return
  }

  loading.value = true
  error.value = ''
  leaveLetter.value = []

  try {
    const res = await fetch('http://192.168.1.70:5002/leave/attendance', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': userStore.getAuthHeader()
      },
      body: JSON.stringify({
        employee_id: userId
      })
    })

    if (!res.ok) {
      const msg = `HTTP ${res.status}: Không tìm thấy dữ liệu hoặc lỗi máy chủ.`
      console.error('❌ Fetch error:', msg)
      throw new Error(msg)
    }

    const data = await res.json()
    console.log('✅ Dữ liệu nghỉ phép nhận được:', data)

    // XỬ LÝ CẤU TRÚC DỮ LIỆU MỚI
    if (data.success && Array.isArray(data.records)) {
      leaveLetter.value = data.records
      console.log(`✅ Đã load ${data.count} bản ghi nghỉ phép`)
      remain.value = leaveLetter.value?.[0]?.remain ?? 0;
      PPN_count.value = Number(leaveLetter.value?.[0]?.PPN_count) ?? 0;
    } else {
      console.warn('⚠️ Dữ liệu không có định dạng mong đợi:', data)
      leaveLetter.value = []
    }

  } catch (err) {
    console.error('❌ Lỗi khi lấy dữ liệu nghỉ phép:', err)
    error.value = err.message || 'Đã xảy ra lỗi không xác định.'
  } finally {
    loading.value = false
    hasAttemptedFetch.value = true
  }
}

// Watch for userId changes
watch([() => props.userId, computedUserId], ([propUserId, compUserId]) => {
  const userId = propUserId || compUserId
  console.log('userId changed:', userId)
  if (userId && userId.trim()) {
    fetchLeaveData()
  }
}, { immediate: true })

onMounted(() => {
  setTimeout(() => {
    if (!hasAttemptedFetch.value && computedUserId.value) {
      console.log('Fallback leave data fetch after 2 seconds')
      fetchLeaveData()
    }
  }, 2000)
})

// Expose methods and properties
defineExpose({
  fetchLeaveData,
  loading,
  error,
  leaveLetter,
  selectedYear,
  selectedMonth,
  totalRecords,
  searchTerm,
  availableYears,
  clearSearch
})
</script>

<style scoped>
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

.input-group .btn {
  border-left: 0;
}

.table-responsive {
  border-radius: 0.375rem;
  overflow: hidden;
}

.table th {
  background-color: #212529 !important;
  color: white !important;
  font-weight: 600;
  border: none;
  padding: 1rem 0.75rem;
}

.table td {
  padding: 0.875rem 0.75rem;
  vertical-align: middle;
}

.table-hover tbody tr:hover {
  background-color: rgba(13, 110, 253, 0.05);
}

.badge {
  font-size: 0.75rem;
  padding: 0.5rem 0.75rem;
}

.bg-light {
  transition: all 0.2s ease-in-out;
}

.bg-light:hover {
  background-color: #f8f9fa !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.btn-sm {
  transition: all 0.2s ease-in-out;
}

.btn-sm:hover {
  transform: translateY(-1px);
}

.font-monospace {
  font-family: 'Courier New', monospace;
  font-size: 0.85em;
}

@media (max-width: 768px) {
  .row.align-items-center > .col-md-4,
  .row.align-items-center > .col-md-6 {
    margin-bottom: 1rem;
  }
  
  .d-flex.flex-wrap.gap-3,
  .d-flex.flex-wrap.gap-2 {
    justify-content: center;
  }
}
</style>