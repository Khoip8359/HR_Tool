<template>
  <div class="manager-list-container">
    <!-- Header -->
    <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center mb-3">
      <h5 class="card-title mb-0">
        <i class="bi bi-people-fill me-2"></i>
        Quản lý nhân viên ({{ subordinatesCount }})
      </h5>
      <div class="d-flex gap-2">
        <button 
          @click="refreshData" 
          :disabled="loading"
          class="btn btn-light btn-sm"
        >
          <i class="bi bi-arrow-clockwise me-1"></i>
          {{ loading ? 'Đang tải...' : 'Làm mới' }}
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="d-flex justify-content-center align-items-center py-5">
      <div class="spinner-border text-primary me-3" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <span class="text-muted">Đang tải danh sách nhân viên...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="alert alert-danger" role="alert">
      <i class="bi bi-exclamation-triangle-fill me-2"></i>
      {{ error }}
      <button @click="refreshData" class="btn btn-outline-danger btn-sm ms-3">
        Thử lại
      </button>
    </div>

    <!-- Content -->
    <div v-else-if="subordinates.length > 0" class="row">
      <!-- Filters -->
      <div class="col-12 mb-3">
        <div class="card">
          <div class="card-body">
            <div class="row g-3">
              <div class="col-md-4">
                <label class="form-label">Tìm kiếm</label>
                <input 
                  v-model="searchTerm" 
                  type="text" 
                  class="form-control" 
                  placeholder="Tìm theo tên, email, phòng ban..."
                >
              </div>
              <div class="col-md-3">
                <label class="form-label">Phòng ban</label>
                <select v-model="selectedDepartment" class="form-select">
                  <option value="">Tất cả phòng ban</option>
                  <option v-for="dept in departments" :key="dept" :value="dept">
                    {{ dept }}
                  </option>
                </select>
              </div>
              <div class="col-md-3">
                <label class="form-label">Sắp xếp</label>
                <select v-model="sortBy" class="form-select">
                  <option value="displayName">Theo tên</option>
                  <option value="department">Theo phòng ban</option>
                  <option value="title">Theo chức vụ</option>
                </select>
              </div>
              <div class="col-md-2">
                <label class="form-label">Hiển thị</label>
                <select v-model="itemsPerPage" class="form-select">
                  <option value="10">10</option>
                  <option value="25">25</option>
                  <option value="50">50</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Employee Cards -->
      <div class="col-12">
        <div class="row g-3">
          <div 
            v-for="employee in paginatedEmployees" 
            :key="employee.sam_account"
            class="col-lg-4 col-md-6"
          >
            <div class="card h-100 employee-card" @click="selectEmployee(employee)">
              <div class="card-body">
                <div class="d-flex align-items-center mb-3">
                  <div class="avatar-circle me-3">
                    {{ getInitials(employee.display_name) }}
                  </div>
                  <div class="flex-grow-1">
                    <h6 class="card-title mb-1">{{ employee.display_name }}</h6>
                    <small class="text-muted">{{ employee.sam_account }}</small>
                  </div>
                  <div class="dropdown">
                    <button 
                      class="btn btn-sm btn-outline-secondary"
                      @click.stop="toggleDropdown(employee.sam_account)"
                    >
                      <i class="bi bi-three-dots"></i>
                    </button>
                    <ul 
                      v-if="activeDropdown === employee.sam_account"
                      class="dropdown-menu dropdown-menu-end"
                    >
                      <li><a class="dropdown-item" href="#" @click.stop="viewProfile(employee)">
                        <i class="bi bi-person me-2"></i>Xem hồ sơ
                      </a></li>
                      <li><a class="dropdown-item" href="#" @click.stop="viewLeaveHistory(employee)">
                        <i class="bi bi-calendar-check me-2"></i>Lịch sử nghỉ phép
                      </a></li>
                      <li><hr class="dropdown-divider"></li>
                      <li><a class="dropdown-item text-danger" href="#" @click.stop="contactEmployee(employee)">
                        <i class="bi bi-envelope me-2"></i>Liên hệ
                      </a></li>
                    </ul>
                  </div>
                </div>
                
                <div class="employee-info">
                  <p class="mb-1">
                    <i class="bi bi-building me-2 text-muted"></i>
                    <strong>Phòng ban:</strong> {{ employee.department || 'N/A' }}
                  </p>
                  <p class="mb-1">
                    <i class="bi bi-briefcase me-2 text-muted"></i>
                    <strong>Chức vụ:</strong> {{ employee.title || 'N/A' }}
                  </p>
                  <p class="mb-1">
                    <i class="bi bi-envelope me-2 text-muted"></i>
                    <strong>Email:</strong> 
                    <a :href="`mailto:${employee.mail}`" class="text-decoration-none">
                      {{ employee.mail || 'N/A' }}
                    </a>
                  </p>
                  <p class="mb-0" v-if="employee.phone">
                    <i class="bi bi-telephone me-2 text-muted"></i>
                    <strong>Điện thoại:</strong> 
                    <a :href="`tel:${employee.phone}`" class="text-decoration-none">
                      {{ employee.phone }}
                    </a>
                  </p>
                </div>
              </div>
              
              <div class="card-footer bg-light">
                <div class="d-flex justify-content-between align-items-center">
                  <small class="text-muted">
                    <i class="bi bi-calendar-event me-1"></i>
                    Cập nhật: {{ formatDate(employee.last_updated) }}
                  </small>
                  <span 
                    class="badge"
                    :class="getStatusClass(employee.status)"
                  >
                    {{ getStatusText(employee.status) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div class="col-12 mt-4">
        <nav v-if="totalPages > 1">
          <ul class="pagination justify-content-center">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" href="#" @click.prevent="currentPage = 1">
                <i class="bi bi-chevron-double-left"></i>
              </a>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" href="#" @click.prevent="currentPage--">
                <i class="bi bi-chevron-left"></i>
              </a>
            </li>
            
            <li 
              v-for="page in visiblePages" 
              :key="page"
              class="page-item"
              :class="{ active: page === currentPage }"
            >
              <a class="page-link" href="#" @click.prevent="currentPage = page">
                {{ page }}
              </a>
            </li>
            
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <a class="page-link" href="#" @click.prevent="currentPage++">
                <i class="bi bi-chevron-right"></i>
              </a>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <a class="page-link" href="#" @click.prevent="currentPage = totalPages">
                <i class="bi bi-chevron-double-right"></i>
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-5">
      <i class="bi bi-people display-1 text-muted mb-3"></i>
      <h5 class="text-muted">Không có nhân viên nào</h5>
      <p class="text-muted">Bạn chưa có nhân viên nào dưới quyền quản lý</p>
    </div>

    <!-- Summary Stats -->
    <div v-if="subordinates.length > 0" class="row mt-4">
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <h6 class="card-title">Thống kê tổng quan</h6>
            <div class="row g-3">
              <div class="col-md-3">
                <div class="text-center">
                  <div class="h4 text-primary">{{ subordinatesCount }}</div>
                  <small class="text-muted">Tổng nhân viên</small>
                </div>
              </div>
              <div class="col-md-3">
                <div class="text-center">
                  <div class="h4 text-success">{{ activeEmployeesCount }}</div>
                  <small class="text-muted">Đang làm việc</small>
                </div>
              </div>
              <div class="col-md-3">
                <div class="text-center">
                  <div class="h4 text-warning">{{ onLeaveCount }}</div>
                  <small class="text-muted">Đang nghỉ phép</small>
                </div>
              </div>
              <div class="col-md-3">
                <div class="text-center">
                  <div class="h4 text-info">{{ departments.length }}</div>
                  <small class="text-muted">Phòng ban</small>
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

const emit = defineEmits(['employee-selected'])

const userStore = useUserStore()

// Reactive data
const subordinates = ref([])
const loading = ref(false)
const error = ref('')
const searchTerm = ref('')
const selectedDepartment = ref('')
const sortBy = ref('displayName')
const itemsPerPage = ref(10)
const currentPage = ref(1)
const activeDropdown = ref(null)

// Computed properties
const subordinatesCount = computed(() => subordinates.value.length)

const filteredEmployees = computed(() => {
  let filtered = subordinates.value

  // Filter by search term
  if (searchTerm.value) {
    const term = searchTerm.value.toLowerCase()
    filtered = filtered.filter(emp => 
      emp.display_name?.toLowerCase().includes(term) ||
      emp.mail?.toLowerCase().includes(term) ||
      emp.department?.toLowerCase().includes(term) ||
      emp.sam_account?.toLowerCase().includes(term)
    )
  }

  // Filter by department
  if (selectedDepartment.value) {
    filtered = filtered.filter(emp => emp.department === selectedDepartment.value)
  }

  return filtered
})

const sortedEmployees = computed(() => {
  const sorted = [...filteredEmployees.value]
  
  switch (sortBy.value) {
    case 'displayName':
      return sorted.sort((a, b) => a.display_name?.localeCompare(b.display_name))
    case 'department':
      return sorted.sort((a, b) => a.department?.localeCompare(b.department))
    case 'title':
      return sorted.sort((a, b) => a.title?.localeCompare(b.title))
    default:
      return sorted
  }
})

const totalPages = computed(() => Math.ceil(sortedEmployees.value.length / itemsPerPage.value))

const paginatedEmployees = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return sortedEmployees.value.slice(start, end)
})

const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

const departments = computed(() => {
  const depts = new Set()
  subordinates.value.forEach(emp => {
    if (emp.department) depts.add(emp.department)
  })
  return Array.from(depts).sort()
})

const activeEmployeesCount = computed(() => 
  subordinates.value.filter(emp => emp.status === 'active').length
)

const onLeaveCount = computed(() => 
  subordinates.value.filter(emp => emp.status === 'on_leave').length
)

// Methods
const fetchSubordinates = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const response = await apiService.getSubordinates(userStore.tokens.accessToken)
    
    if (response.success && Array.isArray(response.data)) {
      subordinates.value = response.data
      console.log(`✅ Loaded ${response.data.length} subordinates`)
    } else {
      throw new Error('Invalid response format')
    }
  } catch (err) {
    console.error('❌ Error fetching subordinates:', err)
    error.value = err.message || 'Không thể tải danh sách nhân viên'
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchSubordinates()
}

const selectEmployee = (employee) => {
  emit('employee-selected', employee)
}

const toggleDropdown = (employeeId) => {
  activeDropdown.value = activeDropdown.value === employeeId ? null : employeeId
}

const getInitials = (name) => {
  if (!name) return '?'
  return name.split(' ')
    .map(word => word.charAt(0))
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

const getStatusClass = (status) => {
  switch (status) {
    case 'active': return 'bg-success'
    case 'on_leave': return 'bg-warning'
    case 'inactive': return 'bg-secondary'
    default: return 'bg-info'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'active': return 'Đang làm việc'
    case 'on_leave': return 'Nghỉ phép'
    case 'inactive': return 'Không hoạt động'
    default: return 'Không xác định'
  }
}

const viewProfile = (employee) => {
  console.log('View profile:', employee)
  // Implement profile view
}

const viewLeaveHistory = (employee) => {
  console.log('View leave history:', employee)
  // Implement leave history view
}

const contactEmployee = (employee) => {
  if (employee.mail) {
    window.open(`mailto:${employee.mail}`, '_blank')
  }
}

// Watchers
watch(currentPage, () => {
  activeDropdown.value = null
})

watch([searchTerm, selectedDepartment, sortBy], () => {
  currentPage.value = 1
})

// Lifecycle
onMounted(() => {
  fetchSubordinates()
})

// Expose methods
defineExpose({
  refreshData,
  fetchSubordinates
})
</script>

<style scoped>
.manager-list-container {
  min-height: 400px;
}

.employee-card {
  transition: all 0.2s ease-in-out;
  cursor: pointer;
}

.employee-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.avatar-circle {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1rem;
  flex-shrink: 0;
}

.employee-info p {
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.dropdown-menu {
  min-width: 200px;
}

.pagination .page-link {
  color: #007bff;
}

.pagination .page-item.active .page-link {
  background-color: #007bff;
  border-color: #007bff;
}

.display-1 {
  font-size: 4rem;
  opacity: 0.3;
}
</style>