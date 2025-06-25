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
        <!-- Hiển thị thông báo lỗi khi vượt quá thời gian còn lại -->
        <div v-if="!isLeaveTimeValid && leaveDuration && !leaveDuration.toString().includes('không hợp lệ')" class="text-danger mt-1">
          <i class="bi bi-exclamation-triangle-fill me-1"></i>
          <span v-if="selectedLeaveType === 'PPN'">
            Thời gian nghỉ vượt quá số phép phụ nữ còn lại ({{ PPN_count }} phép = {{ (PPN_count * 0.5) }} giờ)
          </span>
          <span v-else>
            Thời gian nghỉ vượt quá số ngày phép còn lại ({{ remain }} ngày = {{ remain * 8 }} giờ)
          </span>
        </div>
      </div>

      <div class="mb-3">
        <label class="form-label fw-semibold">Ghi chú thêm</label>
        <textarea class="form-control" v-model="note" rows="3"></textarea>
      </div>

      <div class="text-end">
        <button class="btn btn-success px-4" :disabled="!canSubmit" @click="submitLeave">
          {{ !canSubmit ? 'Không thể gửi đơn' : 'Gửi đơn' }}
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

const leaveLetter = ref([])
const loading = ref(false)
const error = ref('')
const remain = ref('')
const PPN_count = ref('')

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

const submitLeave = () => {
  console.log('submitLeave called')
  
  // Double-check validation before submitting
  if (!canSubmit.value) {
    alert('Không thể gửi đơn. Vui lòng kiểm tra lại thông tin.')
    return
  }
  
  // Parse thời gian nghỉ
  const durationMatch = leaveDuration.value.match(/(\d+\.?\d*)/)
  if (!durationMatch) {
    alert('Thời gian nghỉ không hợp lệ')
    return
  }
  
  const durationHours = parseFloat(durationMatch[1])
  const durationDays = durationHours / 8
  
  // Kiểm tra lại balance
  if (selectedLeaveType.value === 'PPN') {
    const maxPPNDays = PPN_count.value * 0.0625
    if (durationDays > maxPPNDays) {
      alert(`Thời gian nghỉ vượt quá số phép phụ nữ còn lại (${PPN_count.value} phép = ${maxPPNDays} ngày)`)
      return
    }
  } else {
    const remainingDays = parseFloat(remain.value) || 0
    if (durationDays > remainingDays) {
      alert(`Thời gian nghỉ vượt quá số ngày phép còn lại (${remainingDays} ngày)`)
      return
    }
  }
  
  // Nếu tất cả validation pass, tiến hành submit
  console.log('Validation passed, proceeding with submission...')
  
  // TODO: Implement actual API call
  const leaveData = {
    employee_id: computedUserId.value,
    leave_type_id: selectedLeaveType.value,
    from_date: fromDate.value,
    from_time: fromTime.value,
    to_date: toDate.value,
    to_time: toTime.value,
    duration: durationHours,
    note: note.value
  }
  
  console.log('Leave data to submit:', leaveData)
  
  // Gọi API submit
  // submitLeaveToAPI(leaveData)
}

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
  }
}

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

// Validate leave time against remaining balance
const isLeaveTimeValid = computed(() => {
  // Kiểm tra nếu chưa có thời gian nghỉ
  if (!leaveDuration.value || leaveDuration.value.toString().includes('không hợp lệ')) {
    return false
  }

  // Parse thời gian nghỉ từ string (ví dụ: "8.00 giờ" -> 8.00)
  const durationMatch = leaveDuration.value.match(/(\d+\.?\d*)/)
  if (!durationMatch) {
    return false
  }
  
  const durationHours = parseFloat(durationMatch[1])
  const durationDays = durationHours / 8 // Chuyển giờ thành ngày

  // Kiểm tra loại phép
  if (selectedLeaveType.value === 'PPN') {
    // Phép phụ nữ: 0.5 giờ = 0.0625 ngày
    const maxPPNDays = PPN_count.value * 0.0625
    return durationDays <= maxPPNDays
  } else {
    // Phép thường: so sánh với remain (đã là số ngày)
    const remainingDays = parseFloat(remain.value) || 0
    return durationDays <= remainingDays
  }
})

// Combined validation for button
const canSubmit = computed(() => {
  return isFormValid.value && isLeaveTimeValid.value
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
  fetchLeaveData()
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