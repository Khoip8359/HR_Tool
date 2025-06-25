<template>
  <div class="manager-calendar-container">
    <!-- Header -->
    <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center mb-3">
      <h5 class="card-title mb-0">
        <i class="bi bi-calendar3 me-2"></i>
        Lịch nghỉ phép nhân viên
      </h5>
      <div class="d-flex gap-2">
        <button 
          @click="previousMonth" 
          class="btn btn-light btn-sm"
        >
          <i class="bi bi-chevron-left"></i>
        </button>
        <button 
          @click="goToToday" 
          class="btn btn-light btn-sm"
        >
          Hôm nay
        </button>
        <button 
          @click="nextMonth" 
          class="btn btn-light btn-sm"
        >
          <i class="bi bi-chevron-right"></i>
        </button>
      </div>
    </div>

    <!-- Calendar Controls -->
    <div class="row mb-3">
      <div class="col-md-6">
        <div class="d-flex align-items-center gap-3">
          <h4 class="mb-0">{{ currentMonthName }} {{ currentYear }}</h4>
          <div class="btn-group btn-group-sm">
            <button 
              @click="viewMode = 'month'"
              class="btn"
              :class="viewMode === 'month' ? 'btn-primary' : 'btn-outline-primary'"
            >
              Tháng
            </button>
            <button 
              @click="viewMode = 'week'"
              class="btn"
              :class="viewMode === 'week' ? 'btn-primary' : 'btn-outline-primary'"
            >
              Tuần
            </button>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="d-flex justify-content-end gap-2">
          <select v-model="selectedEmployee" class="form-select form-select-sm" style="width: auto;">
            <option value="">Tất cả nhân viên</option>
            <option v-for="emp in employees" :key="emp.sam_account" :value="emp.sam_account">
              {{ emp.display_name }}
            </option>
          </select>
          <button 
            @click="refreshData" 
            :disabled="loading"
            class="btn btn-outline-primary btn-sm"
          >
            <i class="bi bi-arrow-clockwise"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="d-flex justify-content-center align-items-center py-5">
      <div class="spinner-border text-primary me-3" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <span class="text-muted">Đang tải dữ liệu lịch...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="alert alert-danger" role="alert">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>
      {{ error }}
      <button @click="refreshData" class="btn btn-outline-danger btn-sm ms-3">
        Thử lại
      </button>
    </div>

    <!-- Calendar View -->
    <div v-else class="calendar-wrapper">
      <!-- Month View -->
      <div v-if="viewMode === 'month'" class="month-view">
        <!-- Calendar Header -->
        <div class="calendar-header">
          <div 
            v-for="dayName in dayNames" 
            :key="dayName"
            class="day-header"
          >
            {{ dayName }}
          </div>
        </div>

        <!-- Calendar Body -->
        <div class="calendar-body">
          <div 
            v-for="day in calendarDays" 
            :key="day.date"
            class="calendar-day"
            :class="{
              'other-month': !day.isCurrentMonth,
              'today': day.isToday,
              'has-events': day.events.length > 0
            }"
            @click="selectDay(day)"
          >
            <div class="day-number">{{ day.dayNumber }}</div>
            <div class="day-events">
              <div 
                v-for="event in day.events.slice(0, 3)" 
                :key="event.id"
                class="event-indicator"
                :class="getEventClass(event.type)"
                :title="`${event.employeeName}: ${event.reason}`"
              >
                <small>{{ event.employeeName }}</small>
              </div>
              <div v-if="day.events.length > 3" class="more-events">
                +{{ day.events.length - 3 }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Week View -->
      <div v-else class="week-view">
        <div class="week-header">
          <div class="time-column">Thời gian</div>
          <div 
            v-for="day in weekDays" 
            :key="day.date"
            class="day-column"
            :class="{ 'today': day.isToday }"
          >
            <div class="day-name">{{ day.dayName }}</div>
            <div class="day-date">{{ day.dayNumber }}/{{ day.month }}</div>
          </div>
        </div>
        
        <div class="week-body">
          <div 
            v-for="hour in workingHours" 
            :key="hour"
            class="time-slot"
          >
            <div class="time-label">{{ formatHour(hour) }}</div>
            <div 
              v-for="day in weekDays" 
              :key="day.date"
              class="time-cell"
            >
              <div 
                v-for="event in getEventsForTimeSlot(day.date, hour)"
                :key="event.id"
                class="week-event"
                :class="getEventClass(event.type)"
                :style="getEventStyle(event)"
              >
                <small>{{ event.employeeName }}</small>
                <small class="event-reason">{{ event.reason }}</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Event Details Modal -->
    <div 
      v-if="selectedEvent"
      class="modal fade show d-block"
      style="background-color: rgba(0,0,0,0.5);"
      @click="closeEventModal"
    >
      <div class="modal-dialog" @click.stop>
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="bi bi-calendar-event me-2"></i>
              Chi tiết nghỉ phép
            </h5>
            <button type="button" class="btn-close" @click="closeEventModal"></button>
          </div>
          <div class="modal-body">
            <div class="row">
              <div class="col-md-6">
                <p><strong>Nhân viên:</strong> {{ selectedEvent.employeeName }}</p>
                <p><strong>Loại phép:</strong> {{ selectedEvent.reason }}</p>
                <p><strong>Ngày bắt đầu:</strong> {{ formatDate(selectedEvent.startDate) }}</p>
                <p><strong>Ngày kết thúc:</strong> {{ formatDate(selectedEvent.endDate) }}</p>
              </div>
              <div class="col-md-6">
                <p><strong>Thời gian:</strong> {{ selectedEvent.duration }}</p>
                <p><strong>Trạng thái:</strong> 
                  <span :class="getStatusBadgeClass(selectedEvent.status)">
                    {{ getStatusText(selectedEvent.status) }}
                  </span>
                </p>
                <p><strong>Ghi chú:</strong> {{ selectedEvent.note || 'Không có' }}</p>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeEventModal">
              Đóng
            </button>
            <button type="button" class="btn btn-primary" @click="approveLeave(selectedEvent)">
              Phê duyệt
            </button>
            <button type="button" class="btn btn-danger" @click="rejectLeave(selectedEvent)">
              Từ chối
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Statistics -->
    <div class="row mt-4">
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <h6 class="card-title">Thống kê tháng {{ currentMonthName }}</h6>
            <div class="row g-3">
              <div class="col-md-3">
                <div class="text-center">
                  <div class="h4 text-primary">{{ monthlyStats.totalLeaves }}</div>
                  <small class="text-muted">Tổng đơn nghỉ phép</small>
                </div>
              </div>
              <div class="col-md-3">
                <div class="text-center">
                  <div class="h4 text-success">{{ monthlyStats.approvedLeaves }}</div>
                  <small class="text-muted">Đã phê duyệt</small>
                </div>
              </div>
              <div class="col-md-3">
                <div class="text-center">
                  <div class="h4 text-warning">{{ monthlyStats.pendingLeaves }}</div>
                  <small class="text-muted">Chờ phê duyệt</small>
                </div>
              </div>
              <div class="col-md-3">
                <div class="text-center">
                  <div class="h4 text-danger">{{ monthlyStats.rejectedLeaves }}</div>
                  <small class="text-muted">Đã từ chối</small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { formatDate } from '@/utils/userUtils'
import apiService from '@/services/api'

const props = defineProps({
  selectedEmployee: {
    type: Object,
    default: null
  }
})

const userStore = useUserStore()

// Reactive data
const loading = ref(false)
const error = ref('')
const viewMode = ref('month')
const currentDate = ref(new Date())
const selectedEmployee = ref('')
const employees = ref([])
const leaveEvents = ref([])
const selectedEvent = ref(null)

// Calendar constants
const dayNames = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
const workingHours = Array.from({length: 9}, (_, i) => i + 8) // 8:00 - 16:00

// Computed properties
const currentYear = computed(() => currentDate.value.getFullYear())
const currentMonth = computed(() => currentDate.value.getMonth())
const currentMonthName = computed(() => {
  const months = [
    'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
    'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
  ]
  return months[currentMonth.value]
})

const calendarDays = computed(() => {
  const days = []
  const firstDay = new Date(currentYear.value, currentMonth.value, 1)
  const lastDay = new Date(currentYear.value, currentMonth.value + 1, 0)
  const startDate = new Date(firstDay)
  startDate.setDate(startDate.getDate() - firstDay.getDay())
  
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  
  for (let i = 0; i < 42; i++) {
    const date = new Date(startDate)
    date.setDate(startDate.getDate() + i)
    
    const dayEvents = getEventsForDate(date)
    
    days.push({
      date: date.toISOString().split('T')[0],
      dayNumber: date.getDate(),
      isCurrentMonth: date.getMonth() === currentMonth.value,
      isToday: date.getTime() === today.getTime(),
      events: dayEvents
    })
  }
  
  return days
})

const weekDays = computed(() => {
  const days = []
  const today = new Date()
  const currentWeekStart = new Date(today)
  currentWeekStart.setDate(today.getDate() - today.getDay())
  
  for (let i = 0; i < 7; i++) {
    const date = new Date(currentWeekStart)
    date.setDate(currentWeekStart.getDate() + i)
    
    days.push({
      date: date.toISOString().split('T')[0],
      dayName: dayNames[date.getDay()],
      dayNumber: date.getDate(),
      month: date.getMonth() + 1,
      isToday: date.getTime() === today.getTime()
    })
  }
  
  return days
})

const monthlyStats = computed(() => {
  const stats = {
    totalLeaves: 0,
    approvedLeaves: 0,
    pendingLeaves: 0,
    rejectedLeaves: 0
  }
  
  leaveEvents.value.forEach(event => {
    if (new Date(event.startDate).getMonth() === currentMonth.value) {
      stats.totalLeaves++
      switch (event.status) {
        case 'approved':
          stats.approvedLeaves++
          break
        case 'pending':
          stats.pendingLeaves++
          break
        case 'rejected':
          stats.rejectedLeaves++
          break
      }
    }
  })
  
  return stats
})

// Methods
const fetchEmployees = async () => {
  try {
    const response = await apiService.getSubordinates(userStore.tokens.accessToken)
    if (response.success && Array.isArray(response.data)) {
      employees.value = response.data
    }
  } catch (err) {
    console.error('Error fetching employees:', err)
  }
}

const fetchLeaveEvents = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // Fetch leave data for all subordinates
    const events = []
    
    for (const employee of employees.value) {
      try {
        const response = await apiService.getLeaveAttendance(
          employee.sam_account, 
          userStore.tokens.accessToken
        )
        
        if (response.success && Array.isArray(response.records)) {
          response.records.forEach(record => {
            events.push({
              id: `${employee.sam_account}-${record.LeaveDate}`,
              employeeName: employee.display_name,
              employeeId: employee.sam_account,
              startDate: record.LeaveDate,
              endDate: record.LeaveDate,
              reason: record.LeaveTypeNameU,
              type: record.LeaveTypeID,
              status: 'approved', // Default status
              duration: record.Quantity,
              note: record.Note || ''
            })
          })
        }
      } catch (err) {
        console.warn(`Error fetching leave data for ${employee.display_name}:`, err)
      }
    }
    
    leaveEvents.value = events
    console.log(`✅ Loaded ${events.length} leave events`)
    
  } catch (err) {
    console.error('❌ Error fetching leave events:', err)
    error.value = err.message || 'Không thể tải dữ liệu nghỉ phép'
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchEmployees()
  fetchLeaveEvents()
}

const getEventsForDate = (date) => {
  const dateStr = date.toISOString().split('T')[0]
  return leaveEvents.value.filter(event => {
    if (selectedEmployee.value && event.employeeId !== selectedEmployee.value) {
      return false
    }
    return event.startDate === dateStr
  })
}

const getEventsForTimeSlot = (date, hour) => {
  return getEventsForDate(new Date(date)).filter(event => {
    // Simple time filtering - can be enhanced
    return true
  })
}

const getEventClass = (type) => {
  switch (type) {
    case 'ANNUAL': return 'event-annual'
    case 'SICK': return 'event-sick'
    case 'PERSONAL': return 'event-personal'
    default: return 'event-other'
  }
}

const getEventStyle = (event) => {
  // Calculate position and width for week view
  return {
    backgroundColor: getEventColor(event.type)
  }
}

const getEventColor = (type) => {
  switch (type) {
    case 'ANNUAL': return '#28a745'
    case 'SICK': return '#dc3545'
    case 'PERSONAL': return '#ffc107'
    default: return '#6c757d'
  }
}

const getStatusBadgeClass = (status) => {
  switch (status) {
    case 'approved': return 'badge bg-success'
    case 'pending': return 'badge bg-warning'
    case 'rejected': return 'badge bg-danger'
    default: return 'badge bg-secondary'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'approved': return 'Đã phê duyệt'
    case 'pending': return 'Chờ phê duyệt'
    case 'rejected': return 'Đã từ chối'
    default: return 'Không xác định'
  }
}

const formatHour = (hour) => {
  return `${hour}:00`
}

const selectDay = (day) => {
  if (day.events.length > 0) {
    selectedEvent.value = day.events[0]
  }
}

const closeEventModal = () => {
  selectedEvent.value = null
}

const approveLeave = (event) => {
  console.log('Approve leave:', event)
  // Implement approval logic
  closeEventModal()
}

const rejectLeave = (event) => {
  console.log('Reject leave:', event)
  // Implement rejection logic
  closeEventModal()
}

const previousMonth = () => {
  currentDate.value = new Date(currentYear.value, currentMonth.value - 1, 1)
}

const nextMonth = () => {
  currentDate.value = new Date(currentYear.value, currentMonth.value + 1, 1)
}

const goToToday = () => {
  currentDate.value = new Date()
}

// Watchers
watch(selectedEmployee, () => {
  // Refresh calendar when employee filter changes
})

// Lifecycle
onMounted(() => {
  fetchEmployees()
  fetchLeaveEvents()
})

// Expose methods
defineExpose({
  refreshData
})
</script>

<style scoped>
.manager-calendar-container {
  min-height: 600px;
}

.calendar-wrapper {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

/* Month View Styles */
.month-view {
  display: flex;
  flex-direction: column;
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
  min-height: 100px;
  background: white;
  padding: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.calendar-day:hover {
  background-color: #f8f9fa;
}

.calendar-day.other-month {
  background-color: #f8f9fa;
  color: #6c757d;
}

.calendar-day.today {
  background-color: #e3f2fd;
  border: 2px solid #2196f3;
}

.calendar-day.has-events {
  background-color: #fff3cd;
}

.day-number {
  font-weight: 600;
  margin-bottom: 4px;
}

.day-events {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.event-indicator {
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 0.7rem;
  color: white;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-annual {
  background-color: #28a745;
}

.event-sick {
  background-color: #dc3545;
}

.event-personal {
  background-color: #ffc107;
  color: #212529;
}

.event-other {
  background-color: #6c757d;
}

.more-events {
  font-size: 0.7rem;
  color: #6c757d;
  text-align: center;
}

/* Week View Styles */
.week-view {
  display: flex;
  flex-direction: column;
}

.week-header {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  background: #343a40;
  color: white;
}

.time-column {
  padding: 12px;
  text-align: center;
  font-weight: 600;
}

.day-column {
  padding: 12px;
  text-align: center;
  border-left: 1px solid #495057;
}

.day-column.today {
  background-color: #2196f3;
}

.day-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.day-date {
  font-size: 0.8rem;
  opacity: 0.8;
}

.week-body {
  display: flex;
  flex-direction: column;
}

.time-slot {
  display: grid;
  grid-template-columns: 80px repeat(7, 1fr);
  border-bottom: 1px solid #e9ecef;
  min-height: 60px;
}

.time-label {
  padding: 8px;
  text-align: center;
  font-size: 0.8rem;
  color: #6c757d;
  background: #f8f9fa;
  border-right: 1px solid #e9ecef;
}

.time-cell {
  padding: 4px;
  border-right: 1px solid #e9ecef;
  position: relative;
}

.week-event {
  padding: 4px 6px;
  border-radius: 3px;
  font-size: 0.7rem;
  color: white;
  margin-bottom: 2px;
  overflow: hidden;
}

.event-reason {
  display: block;
  font-size: 0.6rem;
  opacity: 0.8;
}

/* Modal Styles */
.modal {
  z-index: 1050;
}

/* Responsive */
@media (max-width: 768px) {
  .calendar-day {
    min-height: 80px;
    padding: 4px;
  }
  
  .day-events {
    display: none;
  }
  
  .week-view {
    display: none;
  }
}
</style>