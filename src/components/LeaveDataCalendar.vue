<template>
  <div class="container-fluid">
    <div class="card">
      <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
        <div class="d-flex align-items-center">
          <i class="bi bi-calendar3 me-2"></i>
          <h5 class="card-title mb-0">Lịch nghỉ phép</h5>
        </div>
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
        
        <!-- Calendar Content -->
        <div v-if="!loading && !error">
          <!-- Controls Row -->
          <div class="row mb-4">
            <div class="col-md-4">
              <div class="input-group">
                <span class="input-group-text">
                  <i class="bi bi-search"></i>
                </span>
                <input 
                  v-model="searchTerm" 
                  type="text" 
                  class="form-control" 
                  placeholder="Tìm kiếm nhân viên..."
                >
              </div>
            </div>
            
            <div class="col-md-4">
              <select 
                v-model="selectedLeaveType" 
                class="form-select"
              >
                <option value="all">Tất cả loại phép</option>
                <option v-for="type in leaveTypes" :key="type" :value="type">
                  {{ type }}
                </option>
              </select>
            </div>
            
            <div class="col-md-4">
              <RouterLink to="/home/add" class="btn btn-primary w-100">
                <i class="bi bi-plus-circle me-1"></i>Tạo đơn nghỉ phép
              </RouterLink>
            </div>
          </div>

          <!-- Calendar Navigation -->
          <div class="row mb-4 align-items-center">
            <div class="col-md-6">
              <div class="d-flex align-items-center">
                <button 
                  @click="navigateMonth(-1)"
                  class="btn btn-outline-secondary me-2"
                >
                  <
                </button>
                <h4 class="mb-0 me-2">
                  {{ monthNames[currentDate.getMonth()] }} {{ currentDate.getFullYear() }}
                </h4>
                <button 
                  @click="navigateMonth(1)"
                  class="btn btn-outline-secondary me-3"
                >
                  >
                </button>
                <button 
                  @click="goToToday"
                  class="btn btn-outline-primary"
                >
                  Tháng hiện tại
                </button>
              </div>
            </div>
          </div>

          <!-- Statistics Cards -->
          <div class="row mb-4">
            <div class="col-md-12">
              <div class="card bg-primary text-white">
                <div class="card-body text-center">
                  <h3 class="mb-0">{{ filteredLeaveData.length }}</h3>
                  <small>Tổng số đơn nghỉ phép</small>
                </div>
              </div>
            </div>
          </div>

          <!-- Calendar Grid -->
          <div class="calendar-container">
            <!-- Day Headers -->
            <div class="calendar-header">
              <div v-for="day in dayNames" :key="day" class="calendar-day-header">
                {{ day }}
              </div>
            </div>
            
            <!-- Calendar Days -->
            <div class="calendar-grid">
              <div 
                v-for="(day, index) in calendarDays" 
                :key="index"
                class="calendar-day"
                :class="{
                  'other-month': !day.isCurrentMonth,
                  'today': isToday(day.fullDate),
                  'has-events': getEventsForDate(day.fullDate).length > 0
                }"
              >
                <div class="calendar-date">{{ day.date }}</div>
                
                <!-- Events -->
                <div class="calendar-events">
                  <div 
                    v-for="event in getEventsForDate(day.fullDate).slice(0, 3)" 
                    :key="event.id"
                    class="calendar-event"
                    @click="showEventDetail(event)"
                    data-bs-toggle="tooltip"
                    :title="`${event.EmployeeName} - ${event.LeaveTypeNameU}`"
                  >
                    <div class="event-name">{{ event.EmployeeName }}</div>
                    <div class="event-type">{{ event.LeaveTypeNameU }}</div>
                  </div>
                  
                  <div 
                    v-if="getEventsForDate(day.fullDate).length > 3"
                    class="calendar-event-more"
                  >
                    +{{ getEventsForDate(day.fullDate).length - 3 }} khác
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- No Data State -->
        <div v-else-if="!loading && !error && hasAttemptedFetch && leaveLetter.length === 0" class="text-center py-5">
          <i class="bi bi-calendar-x display-1 text-muted mb-3"></i>
          <h5 class="text-muted">Không có dữ liệu nghỉ phép</h5>
          <p class="text-muted small">Chưa có thông tin nghỉ phép nào được ghi nhận</p>
        </div>
      </div>
    </div>

    <!-- Event Detail Modal -->
    <div 
      class="modal fade" 
      id="eventDetailModal" 
      tabindex="-1" 
      aria-labelledby="eventDetailModalLabel" 
      aria-hidden="true"
    >
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="eventDetailModalLabel">
              <i class="bi bi-calendar-event me-2"></i>Chi tiết nghỉ phép
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" v-if="selectedEvent">
            <div class="row mb-3">
              <div class="col-sm-4"><strong>Nhân viên:</strong></div>
              <div class="col-sm-8">{{ selectedEvent.EmployeeName }}</div>
            </div>
            <div class="row mb-3">
              <div class="col-sm-4"><strong>Mã NV:</strong></div>
              <div class="col-sm-8">{{ selectedEvent.EmployeeID }}</div>
            </div>
            <div class="row mb-3">
              <div class="col-sm-4"><strong>Phòng ban:</strong></div>
              <div class="col-sm-8">{{ selectedEvent.DepartmentNameU }}</div>
            </div>
            <div class="row mb-3">
              <div class="col-sm-4"><strong>Loại phép:</strong></div>
              <div class="col-sm-8">{{ selectedEvent.LeaveTypeNameU }}</div>
            </div>
            <div class="row mb-3">
              <div class="col-sm-4"><strong>Ngày nghỉ:</strong></div>
              <div class="col-sm-8">{{ formatDate(selectedEvent.LeaveDate) }}</div>
            </div>
            <div class="row mb-3">
              <div class="col-sm-4"><strong>Thời gian:</strong></div>
              <div class="col-sm-8">{{ selectedEvent.Quantity }}</div>
            </div>
            <div class="row mb-3" v-if="selectedEvent.Reason">
              <div class="col-sm-4"><strong>Lý do:</strong></div>
              <div class="col-sm-8">{{ selectedEvent.Reason }}</div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Đóng</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useAccountStore } from '@/stores/account'

const props = defineProps({
  userId: {
    type: String,
    default: ''
  }
})

const userStore = useUserStore()
const { authInfo, userInfo } = userStore

const leaveLetter = ref([])
const loading = ref(false)
const error = ref('')
const hasAttemptedFetch = ref(false)
const accountStore = useAccountStore()
const { username } = accountStore.loginCredentials
const employee = ref({})

// Calendar specific states
const currentDate = ref(new Date())
const selectedEvent = ref(null)
const searchTerm = ref('')
const selectedLeaveType = ref('all')

// Constants
const monthNames = [
  'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
  'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
]
const dayNames = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']

// Computed userId từ store
const computedUserId = computed(() => {
  if (!username || typeof username !== 'string') {
    return ''
  }
  return username.length > 1 ? username.substring(1) : username
})

// Get unique departments and leave types for filters
const departments = computed(() => {
  const deps = new Set()
  leaveLetter.value.forEach(item => {
    if (item.DepartmentNameU) {
      deps.add(item.DepartmentNameU)
    }
  })
  return Array.from(deps).sort()
})

const leaveTypes = computed(() => {
  const types = new Set()
  leaveLetter.value.forEach(item => {
    if (item.LeaveTypeNameU) {
      types.add(item.LeaveTypeNameU)
    }
  })
  return Array.from(types).sort()
})

// Filter leave data based on search and filters
const filteredLeaveData = computed(() => {
  return leaveLetter.value.filter(leave => {
    const matchesSearch = searchTerm.value === '' || 
      (leave.EmployeeName && leave.EmployeeName.toLowerCase().includes(searchTerm.value.toLowerCase())) ||
      (leave.EmployeeID && leave.EmployeeID.toLowerCase().includes(searchTerm.value.toLowerCase()))
    
    const matchesLeaveType = selectedLeaveType.value === 'all' || leave.LeaveTypeNameU === selectedLeaveType.value
    
    return matchesSearch  && matchesLeaveType
  })
})

const totalRecords = computed(() => filteredLeaveData.value.length)

// Generate calendar days
const calendarDays = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const firstDayWeek = firstDay.getDay()
  const daysInMonth = lastDay.getDate()
  
  const days = []
  
  // Previous month days
  const prevMonth = new Date(year, month - 1, 0)
  for (let i = firstDayWeek - 1; i >= 0; i--) {
    days.push({
      date: prevMonth.getDate() - i,
      isCurrentMonth: false,
      fullDate: new Date(year, month - 1, prevMonth.getDate() - i)
    })
  }
  
  // Current month days
  for (let day = 1; day <= daysInMonth; day++) {
    days.push({
      date: day,
      isCurrentMonth: true,
      fullDate: new Date(year, month, day)
    })
  }
  
  // Next month days
  const remainingDays = 42 - days.length
  for (let day = 1; day <= remainingDays; day++) {
    days.push({
      date: day,
      isCurrentMonth: false,
      fullDate: new Date(year, month + 1, day)
    })
  }
  
  return days
})

// Utility functions
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('vi-VN')
  } catch {
    return dateString
  }
}

const isToday = (date) => {
  const today = new Date()
  return date.toDateString() === today.toDateString()
}

const getEventsForDate = (date) => {
  const dateStr = date.toISOString().split('T')[0]
  return filteredLeaveData.value.filter(leave => {
    if (!leave.LeaveDate) return false
    const leaveDate = new Date(leave.LeaveDate).toISOString().split('T')[0]
    return leaveDate === dateStr
  })
}

// Navigation functions
const navigateMonth = (direction) => {
  const newDate = new Date(currentDate.value)
  newDate.setMonth(currentDate.value.getMonth() + direction)
  currentDate.value = newDate
}

const goToToday = () => {
  currentDate.value = new Date()
}

const showEventDetail = (event) => {
  selectedEvent.value = event
  // Use Bootstrap modal
  const modal = new bootstrap.Modal(document.getElementById('eventDetailModal'))
  modal.show()
}

// API functions
const fetchLeaveData = async () => {
  console.log('fetchLeaveData called, userId:', computedUserId.value)
  
  if (!computedUserId.value || !computedUserId.value.trim()) {
    error.value = 'Không tìm thấy mã nhân viên hợp lệ'
    hasAttemptedFetch.value = true
    return
  }

  loading.value = true
  error.value = ''
  leaveLetter.value = []

  try {
    const res = await fetch(`http://192.168.1.70:5002/api/leave/${computedUserId.value}`)
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: Không tìm thấy dữ liệu hoặc lỗi server`)
    }
    
    const data = await res.json()
    console.log('Fetched leave data:', data)
    
    leaveLetter.value = data || []
  } catch (err) {
    console.error('Fetch leave data error:', err)
    error.value = err.message
  } finally {
    loading.value = false
    hasAttemptedFetch.value = true
  }
}

const fetchEmployee = async () => {
  console.log('fetchEmployee called, computedUserId:', computedUserId.value)
  
  if (!computedUserId.value || !computedUserId.value.trim()) {
    error.value = 'Không tìm thấy mã nhân viên hợp lệ'
    return
  }

  loading.value = true
  error.value = ''
  employee.value = {}

  try {
    const res = await fetch(`http://192.168.1.70:5002/api/employee/${computedUserId.value}`)
    
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

// Watch for userId changes
watch([() => props.userId, computedUserId], ([propUserId, compUserId]) => {
  const userId = propUserId || compUserId
  console.log('userId changed:', userId)
  if (userId && userId.trim()) {
    fetchLeaveData()
    fetchEmployee()
  }
}, { immediate: true })

onMounted(() => {
  setTimeout(() => {
    if (!hasAttemptedFetch.value && computedUserId.value) {
      console.log('Fallback leave data fetch after 2 seconds')
      fetchLeaveData()
      fetchEmployee()
    }
  }, 2000)
})

// Expose methods and properties
defineExpose({
  fetchLeaveData,
  loading,
  error,
  leaveLetter,
  totalRecords,
  searchTerm,
  currentDate,
  navigateMonth,
  goToToday
})
</script>

<style scoped>
/* Calendar Styles */
.calendar-container {
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  overflow: hidden;
}

.calendar-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background-color: #343a40;
  color: white;
}

.calendar-day-header {
  padding: 1rem;
  text-align: center;
  font-weight: 600;
  border-right: 1px solid #495057;
}

.calendar-day-header:last-child {
  border-right: none;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}

.calendar-day {
  min-height: 120px;
  padding: 0.5rem;
  border-right: 1px solid #dee2e6;
  border-bottom: 1px solid #dee2e6;
  background-color: white;
  position: relative;
}

.calendar-day:nth-child(7n) {
  border-right: none;
}

.calendar-day.other-month {
  background-color: #f8f9fa;
  color: #6c757d;
}

.calendar-day.today {
  background-color: #e3f2fd;
}

.calendar-day.has-events {
  background-color: #fafafa;
}

.calendar-date {
  font-weight: 600;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.calendar-events {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.calendar-event {
  padding: 2px 4px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.75rem;
  line-height: 1.2;
  transition: all 0.2s ease;
  border-left: 3px solid #007bff;
  background-color: #e7f3ff;
  color: #0056b3;
}

.calendar-event:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  background-color: #d1ecf1;
}

.event-name {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-type {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 0.8;
}

.calendar-event-more {
  font-size: 0.7rem;
  color: #6c757d;
  text-align: center;
  padding: 2px;
  font-style: italic;
}

/* Responsive */
@media (max-width: 768px) {
  .calendar-day {
    min-height: 80px;
    padding: 0.25rem;
  }
  
  .calendar-date {
    font-size: 0.8rem;
  }
  
  .calendar-event {
    font-size: 0.7rem;
    padding: 1px 2px;
  }
  
  .calendar-day-header {
    padding: 0.5rem;
    font-size: 0.8rem;
  }
}

/* Card hover effect */
.card {
  transition: box-shadow 0.15s ease-in-out;
}

.card:hover {
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

/* Statistics cards animation */
.card.bg-primary {
  transition: transform 0.2s ease-in-out;
}

.card.bg-primary:hover {
  transform: translateY(-2px);
}
</style>