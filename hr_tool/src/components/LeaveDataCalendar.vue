<template>
  <div class="card">
    <div class="card-header bg-secondary text-white d-flex justify-content-between align-items-center">
      <h5 class="card-title mb-0">Lịch nghỉ phép</h5>
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
      
      <!-- Calendar Controls -->
      <div v-if="currentYearData.length > 0 && !loading" class="mb-4">
        <div class="row align-items-center mb-3">
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
            <div class="d-flex align-items-center justify-content-center">
              <button @click="previousMonth" class="btn btn-outline-secondary btn-sm me-2">
                <
              </button>
              <h5 class="mb-0 mx-3">{{ monthNames[currentMonth] }} {{ currentYear }}</h5>
              <button @click="nextMonth" class="btn btn-outline-secondary btn-sm ms-2">
                >
              </button>
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
      </div>

      <!-- Calendar Grid -->
      <div v-if="currentYearData.length > 0 && !loading" class="calendar-grid">
        <!-- Calendar Header -->
        <div class="calendar-header">
          <div class="day-header" v-for="day in dayNames" :key="day">{{ day }}</div>
        </div>
        
        <!-- Calendar Body -->
        <div class="calendar-body">
          <div 
            v-for="(day, index) in calendarDays" 
            :key="index"
            class="calendar-day"
            :class="{
              'other-month': !day.isCurrentMonth,
              'today': day.isToday,
              'has-leave': day.leaves.length > 0,
              'weekend': day.isWeekend
            }"
          >
            <div class="day-number">{{ day.date }}</div>
            <div class="leave-items" v-if="day.leaves.length > 0">
              <div 
                v-for="leave in day.leaves" 
                :key="`${leave.EmployeeID}-${leave.LeaveDate}`"
                class="leave-item"
                :class="getLeaveTypeClass(leave.LeaveTypeNameU)"
                @click="showLeaveDetail(leave)"
                :title="`${leave.LeaveTypeNameU} - ${formatQuantity(leave.Quantity)}`"
              >
                <span class="leave-type">{{ leave.LeaveTypeID }}</span>
                <span class="leave-duration">{{ formatQuantity(leave.Quantity) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Leave Detail Modal -->
      <div v-if="selectedLeave" class="modal fade show d-block" style="background: rgba(0,0,0,0.5);" @click="closeLeaveDetail">
        <div class="modal-dialog modal-dialog-centered" @click.stop>
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Chi tiết nghỉ phép</h5>
              <button type="button" class="btn-close" @click="closeLeaveDetail"></button>
            </div>
            <div class="modal-body">
              <div class="row">
                <div class="col-sm-4"><strong>Mã NV:</strong></div>
                <div class="col-sm-8">{{ selectedLeave.EmployeeID || 'N/A' }}</div>
              </div>
              <div class="row mt-2">
                <div class="col-sm-4"><strong>Ngày nghỉ:</strong></div>
                <div class="col-sm-8">{{ formatDate(selectedLeave.LeaveDate) }}</div>
              </div>
              <div class="row mt-2">
                <div class="col-sm-4"><strong>Số ngày:</strong></div>
                <div class="col-sm-8">{{ formatQuantity(selectedLeave.Quantity) }}</div>
              </div>
              <div class="row mt-2">
                <div class="col-sm-4"><strong>Loại phép:</strong></div>
                <div class="col-sm-8">
                  <span class="badge bg-info text-dark">{{ selectedLeave.LeaveTypeID || 'N/A' }}</span>
                </div>
              </div>
              <div class="row mt-2">
                <div class="col-sm-4"><strong>Tên loại phép:</strong></div>
                <div class="col-sm-8">{{ selectedLeave.LeaveTypeNameU || 'N/A' }}</div>
              </div>
              <div class="row mt-2">
                <div class="col-sm-4"><strong>Năm:</strong></div>
                <div class="col-sm-8">{{ selectedLeave.TranYear || 'N/A' }}</div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeLeaveDetail">Đóng</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Legend -->
      <div v-if="currentYearData.length > 0 && !loading" class="mt-3">
        <h6 class="text-muted mb-2">
          <i class="bi bi-info-circle me-2"></i>Chú thích
        </h6>
        <div class="d-flex flex-wrap gap-2">
          <div class="d-flex align-items-center">
            <div class="legend-item annual-leave me-1"></div>
            <small>Nghỉ phép năm</small>
          </div>
          <div class="d-flex align-items-center">
            <div class="legend-item balance-leave me-1"></div>
            <small>Nghỉ phép tồn</small>
          </div>
          <div class="d-flex align-items-center">
            <div class="legend-item personal-leave me-1"></div>
            <small>Nghỉ có tang</small>
          </div>
          <div class="d-flex align-items-center">
            <div class="legend-item other-leave me-1"></div>
            <small>Loại khác</small>
          </div>
        </div>
      </div>
      
      <!-- No Data States -->
      <div v-else-if="!loading && !error && hasAttemptedFetch && leaveLetter.length === 0" class="text-center py-5">
        <i class="bi bi-inbox display-1 text-muted mb-3"></i>
        <h5 class="text-muted">Không có dữ liệu nghỉ phép</h5>
        <p class="text-muted small">Chưa có thông tin nghỉ phép nào được ghi nhận</p>
      </div>

      <div v-else-if="!loading && !error && leaveLetter.length > 0 && currentYearData.length === 0" class="text-center py-5">
        <i class="bi bi-calendar-x display-1 text-muted mb-3"></i>
        <h5 class="text-muted">Không có dữ liệu cho năm {{ selectedYear }}</h5>
        <p class="text-muted">Hãy chọn năm khác để xem dữ liệu nghỉ phép</p>
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

// Calendar states
const selectedYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth())
const currentYear = ref(new Date().getFullYear())
const selectedLeave = ref(null)
const remain = ref('')
const PPN_count = ref('')

// Calendar constants
const monthNames = [
  'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
  'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
]

const dayNames = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']

// Computed userId từ store
const computedUserId = computed(() => {
  if (!userInfo.value.samAccount || typeof userInfo.value.samAccount !== 'string') {
    return ''
  }

  return userInfo.value.samAccount.length > 1 
    ? "0" + userInfo.value.samAccount.substring(1) 
    : userInfo.value.samAccount
})

// Get available years from data
const availableYears = computed(() => {
  const years = new Set()
  leaveLetter.value.forEach(item => {
    let year = item.TranYear
    if (!year && item.LeaveDate) {
      year = new Date(item.LeaveDate).getFullYear()
    }
    if (year && !isNaN(year)) {
      years.add(year)
    }
  })
  return Array.from(years).sort((a, b) => b - a)
})

// Get data for selected year
const currentYearData = computed(() => {
  return leaveLetter.value.filter(item => {
    let year = item.TranYear
    if (!year && item.LeaveDate) {
      year = new Date(item.LeaveDate).getFullYear()
    }
    return year === selectedYear.value
  })
})

// Calendar days computation
const calendarDays = computed(() => {
  const days = []
  const firstDay = new Date(currentYear.value, currentMonth.value, 1)
  const lastDay = new Date(currentYear.value, currentMonth.value + 1, 0)
  const startDate = new Date(firstDay)
  
  // Start from the beginning of the week
  startDate.setDate(startDate.getDate() - startDate.getDay())
  
  // Generate 42 days (6 weeks)
  for (let i = 0; i < 42; i++) {
    const date = new Date(startDate)
    date.setDate(startDate.getDate() + i)
    
    const isCurrentMonth = date.getMonth() === currentMonth.value
    const isToday = date.toDateString() === new Date().toDateString()
    const isWeekend = date.getDay() === 0
    
    // Get leaves for this date
    const leaves = currentYearData.value.filter(leave => {
      if (!leave.LeaveDate) return false
      const leaveDate = new Date(leave.LeaveDate)
      return leaveDate.toDateString() === date.toDateString()
    })
    
    days.push({
      date: date.getDate(),
      fullDate: new Date(date),
      isCurrentMonth,
      isToday,
      isWeekend,
      leaves
    })
  }
  
  return days
})

// Year statistics
const yearStats = computed(() => {
  const data = currentYearData.value
  const totalLeaves = data.length

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

const totalRecords = computed(() => currentYearData.value.length)

// Calendar navigation
const previousMonth = () => {
  if (currentMonth.value === 0) {
    currentMonth.value = 11
    currentYear.value--
  } else {
    currentMonth.value--
  }
}

const nextMonth = () => {
  if (currentMonth.value === 11) {
    currentMonth.value = 0
    currentYear.value++
  } else {
    currentMonth.value++
  }
}

// Leave detail modal
const showLeaveDetail = (leave) => {
  selectedLeave.value = leave
}

const closeLeaveDetail = () => {
  selectedLeave.value = null
}

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

const formatQuantity = (quantity) => {
  if (!quantity) return '0'
  const num = parseFloat(quantity)
  if (isNaN(num)) return '0'
  
  if (num === 0.0625) return '30 phút (nửa giờ)'
  if (num === 0.5) return '0.5 ngày (4 giờ)'
  if (num === 1) return '1 ngày (8 giờ)'
  
  return num < 1 ? `${(num * 8).toFixed(1)}h` : `${num.toFixed(1)}n`
}

const getLeaveTypeClass = (LeaveTypeNameU) => {
  if (!LeaveTypeNameU) return 'other-leave'
  
  const type = LeaveTypeNameU.toLowerCase()
  if (type.includes('phép năm') ) return 'annual-leave'
  if (type.includes('tồn phép đầu năm') ) return 'balance-leave'
  if (type.includes('tang') ) return 'personal-leave'
  
  return 'other-leave'
}

// Watchers
watch(selectedYear, (newYear) => {
  currentYear.value = newYear
})

watch(availableYears, (newYears) => {
  if (newYears.length > 0 && !newYears.includes(selectedYear.value)) {
    selectedYear.value = newYears[0]
  }
}, { immediate: true })

// API functions
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

    if (data.success && Array.isArray(data.records)) {
      leaveLetter.value = data.records
      console.log(`✅ Đã load ${data.count} bản ghi nghỉ phép`)
      remain.value = leaveLetter.value[0]?.remain || '0'
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
  totalRecords
})
</script>

<style scoped>
.calendar-grid {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.calendar-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: #343a40;
  color: white;
}

.day-header {
  padding: 12px 8px;
  text-align: center;
  font-weight: 600;
  font-size: 0.9rem;
}

.calendar-body {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background: #e9ecef;
}

.calendar-day {
  background: white;
  min-height: 100px;
  padding: 8px;
  position: relative;
  cursor: pointer;
  transition: all 0.2s ease;
}

.calendar-day:hover {
  background: #f8f9fa;
}

.calendar-day.other-month {
  background: #f8f9fa;
  color: #6c757d;
}

.calendar-day.today {
  background: #e3f2fd;
  border: 2px solid #2196f3;
}

.calendar-day.weekend {
  background: #fff3e0;
}

.calendar-day.has-leave {
  background: #f0f8ff;
}

.day-number {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 4px;
}

.leave-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.leave-item {
  background: #007bff;
  color: white;
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.leave-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.leave-item.annual-leave {
  background: #28a745;
}

.leave-item.balance-leave {
  background: #dc3545;
}

.leave-item.personal-leave {
  background: #ffc107;
  color: #212529;
}

.leave-item.other-leave {
  background: #6c757d;
}

.leave-type {
  font-weight: 600;
}

.leave-duration {
  font-size: 0.6rem;
  opacity: 0.9;
}

.legend-item {
  width: 16px;
  height: 16px;
  border-radius: 3px;
  display: inline-block;
}

.legend-item.annual-leave {
  background: #28a745;
}

.legend-item.balance-leave {
  background: #dc3545;
}

.legend-item.personal-leave {
  background: #ffc107;
}

.legend-item.other-leave {
  background: #6c757d;
}

.spinner-border {
  width: 1.5rem;
  height: 1.5rem;
}

.display-1 {
  font-size: 4rem;
  opacity: 0.3;
}

.bg-light {
  transition: all 0.2s ease-in-out;
}

.bg-light:hover {
  background-color: #f8f9fa !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.modal.show {
  display: block !important;
}

.modal-backdrop {
  background: rgba(0, 0, 0, 0.5);
}

@media (max-width: 768px) {
  .calendar-day {
    min-height: 80px;
    padding: 6px;
  }
  
  .day-header {
    padding: 8px 4px;
    font-size: 0.8rem;
  }
  
  .leave-item {
    font-size: 0.6rem;
    padding: 1px 3px;
  }
  
  .day-number {
    font-size: 0.8rem;
  }
}

@media (max-width: 576px) {
  .calendar-day {
    min-height: 60px;
    padding: 4px;
  }
  
  .leave-item {
    font-size: 0.55rem;
  }
  
  .leave-duration {
    display: none;
  }
}
</style>