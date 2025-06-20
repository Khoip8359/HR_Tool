<template>
  <div class="container mt-4">
    <div class="card shadow rounded-4 p-4">
      <h4 class="mb-4 text-primary">Đơn xin nghỉ phép</h4>

      <div class="mb-3">
        <label class="form-label fw-semibold">User ID</label>
        <input type="text" class="form-control" :value="computedUserId" readonly/>
      </div>

      <div class="mb-3">
        <label class="form-label fw-semibold">Họ tên</label>
        <input type="text" class="form-control" :value="userName" readonly/>
      </div>

      <div class="mb-3">
        <label class="form-label fw-semibold">Lý do xin nghỉ</label>
        <div class="position-relative">
          <input 
            type="text" 
            class="form-control" 
            v-model="leaveTypeSearch" 
            @input="filterLeaveTypes"
            @focus="showLeaveTypeDropdown = true"
            @blur="handleLeaveTypeBlur"
            :placeholder="selectedLeaveTypeName || '-- Chọn hoặc tìm kiếm lý do xin nghỉ --'"
            autocomplete="off"
          />
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="position-absolute" style="right: 10px; top: 50%; transform: translateY(-50%); pointer-events: none;">
            <polyline points="6,9 12,15 18,9"></polyline>
          </svg>
          
          <!-- Dropdown danh sách -->
          <div 
            v-if="showLeaveTypeDropdown && filteredLeaveTypes.length > 0"
            class="position-absolute w-100 bg-white border rounded shadow-sm mt-1"
            style="z-index: 1000; max-height: 200px; overflow-y: auto;"
          >
            <div 
              v-for="type in filteredLeaveTypes" 
              :key="type.LeaveTypeID"
              class="p-2 border-bottom cursor-pointer hover-bg-light"
              @mousedown="selectLeaveType(type)"
              style="cursor: pointer;"
              @mouseover="$event.target.style.backgroundColor = '#f8f9fa'"
              @mouseout="$event.target.style.backgroundColor = 'white'"
            >
              {{ type.LeaveTypeNameU }}
            </div>
          </div>
        </div>
      </div>

      <!-- Phần chọn ngày giờ được cải tiến -->
      <div class="row mb-3">
        <div class="col-md-6">
          <label class="form-label fw-semibold">Nghỉ từ</label>
          <div class="row g-2">
            <div class="col-7">
              <input 
                type="date" 
                class="form-control" 
                v-model="fromDate"
                :min="today"
              />
            </div>
            <div class="col-5">
              <div class="position-relative">
                <input 
                  type="text" 
                  class="form-control" 
                  :value="fromTime || 'Chọn giờ'"
                  readonly
                  @click="openTimePicker('from')"
                  style="cursor: pointer;"
                />
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="position-absolute" style="right: 10px; top: 50%; transform: translateY(-50%); pointer-events: none;">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12,6 12,12 16,14"></polyline>
                </svg>
              </div>
            </div>
          </div>
        </div>
        
        <div class="col-md-6">
          <label class="form-label fw-semibold">Đến</label>
          <div class="row g-2">
            <div class="col-7">
              <input 
                type="date" 
                class="form-control" 
                v-model="toDate"
                :min="fromDate || today"
              />
            </div>
            <div class="col-5">
              <div class="position-relative">
                <input 
                  type="text" 
                  class="form-control" 
                  :value="toTime || 'Chọn giờ'"
                  readonly
                  @click="openTimePicker('to')"
                  style="cursor: pointer;"
                />
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="position-absolute" style="right: 10px; top: 50%; transform: translateY(-50%); pointer-events: none;">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12,6 12,12 16,14"></polyline>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Các nút quick select -->
      <div class="mb-3">
        <label class="form-label fw-semibold">Chọn nhanh:</label>
        <div class="btn-group-sm d-flex flex-wrap gap-1" role="group">
          <button type="button" class="btn btn-outline-primary btn-sm" @click="setQuickTime('morning')">
            Sáng (7:30-12:00)
          </button>
          <button type="button" class="btn btn-outline-primary btn-sm" @click="setQuickTime('afternoon')">
            Chiều (11:30-17:00)
          </button>
          <button type="button" class="btn btn-outline-primary btn-sm" @click="setQuickTime('fullday')">
            Cả ngày (7:30-17:00)
          </button>
          <button type="button" class="btn btn-outline-secondary btn-sm" @click="clearDateTime">
            Xóa
          </button>
        </div>
      </div>

      <div class="mb-3">
        <label class="form-label fw-semibold">Thời gian nghỉ</label>
        <input 
          type="text" 
          class="form-control" 
          :value="leaveDuration" 
          readonly
          :class="{'text-danger': leaveDuration.toString().includes('không hợp lệ')}"
        />
      </div>

      <div class="mb-3">
        <label class="form-label fw-semibold">Ghi chú thêm</label>
        <textarea class="form-control" v-model="note" rows="3"></textarea>
      </div>

      <div class="text-end">
        <button class="btn btn-success px-4" :disabled="!isFormValid">
          Gửi đơn
        </button>
      </div>
    </div>

    <!-- Time Picker Modal -->
    <div 
      v-if="showTimePicker" 
      class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center"
      style="background-color: rgba(0,0,0,0.5); z-index: 1050;"
      @click="closeTimePicker"
    >
      <div class="bg-white rounded-3 shadow-lg p-4" style="min-width: 380px;" @click.stop>
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="mb-0">Chọn thời gian</h5>
          <button type="button" class="btn-close" @click="closeTimePicker"></button>
        </div>

        <div class="row g-3 mb-3">
          <div class="col-6">
            <label class="form-label fw-semibold">Giờ</label>
            <select class="form-select form-select-lg" v-model="tempHour" @change="updateDirectInput">
              <option v-for="hour in hours" :key="hour" :value="hour">
                {{ hour.toString().padStart(2, '0') }}
              </option>
            </select>
          </div>
          <div class="col-6">
            <label class="form-label fw-semibold">Phút</label>
            <select class="form-select form-select-lg" v-model="tempMinute" @change="updateDirectInput">
              <option v-for="minute in minutes" :key="minute" :value="minute">
                {{ minute.toString().padStart(2, '0') }}
              </option>
            </select>
          </div>
        </div>
        
        <!-- Quick time buttons -->
        <div class="mb-3">
          <label class="form-label fw-semibold">Thời gian thông dụng:</label>
          <div class="d-flex flex-wrap gap-1">
            <button 
              v-for="quickTime in quickTimes" 
              :key="quickTime.label"
              type="button" 
              class="btn btn-outline-primary btn-sm"
              @click="setQuickTimeInPicker(quickTime.hour, quickTime.minute)"
            >
              {{ quickTime.label }}
            </button>
          </div>
        </div>
        
        <div class="d-flex gap-2 justify-content-end">
          <button type="button" class="btn btn-secondary" @click="closeTimePicker">
            Hủy
          </button>
          <button type="button" class="btn btn-primary" @click="confirmTime" :disabled="!!timeInputError">
            Xác nhận
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useUserStore } from '@/stores/user';
import { storeToRefs } from 'pinia';

const userStore = useUserStore()
const {userInfo} = storeToRefs(userStore)
const leaveType = ref([])

// Leave type search variables
const selectedLeaveType = ref('')
const selectedLeaveTypeName = ref('')
const leaveTypeSearch = ref('')
const showLeaveTypeDropdown = ref(false)
const filteredLeaveTypes = ref([])

const fromDate = ref('')
const fromTime = ref('')
const toDate = ref('')
const toTime = ref('')
const leaveDuration = ref('')
const note = ref('')

// Time picker variables
const showTimePicker = ref(false)
const currentTimeField = ref('') // 'from' hoặc 'to'
const tempHour = ref(7)
const tempMinute = ref(30)
const directTimeInput = ref('')
const timeInputError = ref('')

// Hours and minutes for picker
const hours = ref(Array.from({length: 24}, (_, i) => i))
const minutes = ref([0, 15, 30, 45])

// Quick time options
const quickTimes = ref([
  { label: '7:30', hour: 7, minute: 30 },
  { label: '8:00', hour: 8, minute: 0 },
  { label: '12:00', hour: 12, minute: 0 },
  { label: '13:30', hour: 13, minute: 30 },
  { label: '17:00', hour: 17, minute: 0 }
])

// Leave type functions
const filterLeaveTypes = () => {
  const search = leaveTypeSearch.value.toLowerCase()
  filteredLeaveTypes.value = leaveType.value.filter(type => 
    type.LeaveTypeNameU.toLowerCase().includes(search)
  )
}

const selectLeaveType = (type) => {
  selectedLeaveType.value = type.LeaveTypeID
  selectedLeaveTypeName.value = type.LeaveTypeNameU
  leaveTypeSearch.value = ''
  showLeaveTypeDropdown.value = false
}

const handleLeaveTypeBlur = () => {
  // Delay to allow click on dropdown items
  setTimeout(() => {
    showLeaveTypeDropdown.value = false
    if (!selectedLeaveType.value) {
      leaveTypeSearch.value = ''
    }
  }, 200)
}
const updateDirectInput = () => {
  directTimeInput.value = `${tempHour.value.toString().padStart(2, '0')}:${tempMinute.value.toString().padStart(2, '0')}`
  timeInputError.value = ''
}

// Ngày hôm nay cho min date
const today = computed(() => {
  return new Date().toISOString().split('T')[0]
})

// Tạo datetime string từ date và time
const leaveDateFrom = computed(() => {
  if (!fromDate.value || !fromTime.value) return ''
  return `${fromDate.value}T${fromTime.value}`
})

const leaveDateTo = computed(() => {
  if (!toDate.value || !toTime.value) return ''
  return `${toDate.value}T${toTime.value}`
})

// Validate form
const isFormValid = computed(() => {
  return selectedLeaveType.value && 
         fromDate.value && fromTime.value && 
         toDate.value && toTime.value &&
         leaveDuration.value &&
         !leaveDuration.value.toString().includes('không hợp lệ')
})

const userName = computed(() =>{
  if(!userInfo.value.displayName){
    return ''
  }
  return userInfo.value.displayName
})

const computedUserId = computed(() => {
  if (!userInfo.value.samAccount || typeof userInfo.value.samAccount !== 'string') {
    return ''
  }

  return userInfo.value.samAccount.length > 1 
    ? "0" + userInfo.value.samAccount.substring(1) 
    : userInfo.value.samAccount
})

// Các hàm quick select
const setQuickTime = (type) => {
  const today = new Date().toISOString().split('T')[0]
  
  if (!fromDate.value) {
    fromDate.value = today
  }
  if (!toDate.value) {
    toDate.value = fromDate.value
  }
  
  switch(type) {
    case 'morning':
      fromTime.value = '07:30'
      toTime.value = '12:00'
      break
    case 'afternoon':
      fromTime.value = '11:30'
      toTime.value = '17:00'
      break
    case 'fullday':
      fromTime.value = '07:30'
      toTime.value = '17:00'
      break
  }
}

const clearDateTime = () => {
  fromDate.value = ''
  fromTime.value = ''
  toDate.value = ''
  toTime.value = ''
}

// Time picker functions
const openTimePicker = (field) => {
  currentTimeField.value = field
  
  // Set current time if exists
  const currentTime = field === 'from' ? fromTime.value : toTime.value
  if (currentTime) {
    const [hour, minute] = currentTime.split(':').map(Number)
    tempHour.value = hour
    tempMinute.value = minute
  } else {
    tempHour.value = 7
    tempMinute.value = 30
  }
  
  updateDirectInput()
  showTimePicker.value = true
}

const closeTimePicker = () => {
  showTimePicker.value = false
  currentTimeField.value = ''
  directTimeInput.value = ''
  timeInputError.value = ''
}

const setQuickTimeInPicker = (hour, minute) => {
  tempHour.value = hour
  tempMinute.value = minute
  updateDirectInput()
}

const confirmTime = () => {
  if (timeInputError.value) return
  
  const timeString = `${tempHour.value.toString().padStart(2, '0')}:${tempMinute.value.toString().padStart(2, '0')}`
  
  if (currentTimeField.value === 'from') {
    fromTime.value = timeString
  } else {
    toTime.value = timeString
  }
  
  closeTimePicker()
}

const fetchLeaveType = async () => {
  try {
    leaveType.value = []
    
    const res = await fetch('http://192.168.1.70:5002/leave/type', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': userStore.getAuthHeader()
      }
    })

    if (!res.ok) {
      const msg = `HTTP ${res.status}: Không tìm thấy dữ liệu hoặc lỗi máy chủ.`
      console.error('❌ Fetch error:', msg)
      throw new Error(msg)
    }

    const data = await res.json()
    leaveType.value = data.data
    filteredLeaveTypes.value = data.data
    
  } catch (error) {
    console.log("Lỗi" + error)
  }
}

// Watch để tính toán thời gian nghỉ
watch([leaveDateFrom, leaveDateTo], ([from, to]) => {
  if (!from || !to) {
    leaveDuration.value = ''
    return
  }

  const start = new Date(from)
  const end = new Date(to)

  if (end <= start) {
    leaveDuration.value = 'Thời gian không hợp lệ'
    return
  }

  const WORK_MORNING_START = 7.5
  const WORK_MORNING_END = 11.5
  const WORK_AFTERNOON_START = 13
  const WORK_AFTERNOON_END = 17

  let totalHours = 0

  const loopDate = new Date(start)
  loopDate.setHours(0, 0, 0, 0)

  while (loopDate < end) {
    const weekday = loopDate.getDay()

    const cloneDate = (h) => {
      const d = new Date(loopDate)
      const hour = Math.floor(h)
      const minute = Math.round((h - hour) * 60)
      d.setHours(hour, minute, 0, 0)
      return d
    }

    const morningStart = cloneDate(WORK_MORNING_START)
    const morningEnd = cloneDate(WORK_MORNING_END)
    const afternoonStart = cloneDate(WORK_AFTERNOON_START)
    const afternoonEnd = cloneDate(WORK_AFTERNOON_END)

    const calcOverlap = (aStart, aEnd, bStart, bEnd) =>
      Math.max(0, (Math.min(aEnd, bEnd) - Math.max(aStart, bStart)) / (1000 * 60 * 60))

    if (weekday === 0) {
      // Chủ nhật - không tính
    } else if (weekday === 6) {
      // Thứ 7 - chỉ tính buổi sáng
      totalHours += calcOverlap(start, end, morningStart, morningEnd)
    } else {
      // Thứ 2-6 - tính cả sáng và chiều
      totalHours += calcOverlap(start, end, morningStart, morningEnd)
      totalHours += calcOverlap(start, end, afternoonStart, afternoonEnd)
    }

    loopDate.setDate(loopDate.getDate() + 1)
  }

  leaveDuration.value = `${totalHours.toFixed(2)} giờ`
})

onMounted(() => {
  fetchLeaveType()
})
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}

.hover-bg-light:hover {
  background-color: #f8f9fa !important;
}
</style>