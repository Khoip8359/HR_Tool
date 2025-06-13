<template>
  <div class="container mt-4">
    <div class="card shadow rounded-4 p-4">
      <h4 class="mb-4 text-primary">Đơn xin nghỉ phép</h4>

      <div class="mb-3">
        <label class="form-label fw-semibold">User ID</label>
        <input type="text" class="form-control" :value="employee.EmployeeID" readonly/>
      </div>

      <div class="mb-3">
        <label class="form-label fw-semibold">Họ tên</label>
        <input type="text" class="form-control" :value="employee.EmployeeName" readonly/>
      </div>

      <div class="mb-3">
        <label class="form-label fw-semibold">Lý do xin nghỉ</label>
        <select
          class="form-select"
          v-model="selectedLeaveType"
        >
          <option value="">-- Chọn lý do xin nghỉ --</option>
          <option
            v-for="(item, index) in LeaveType"
            :key="index"
            :value="item.LeaveTypeID"
          >
            {{ item.LeaveTypeNameU }}
          </option>
        </select>
      </div>

      <div class="mb-3">
        <label class="form-label fw-semibold">Thời gian nghỉ</label>
        <input type="date" class="form-control" name="" id="">
      </div>

      <div class="mb-3">
        <label class="form-label fw-semibold">Ghi chú thêm</label>
        <textarea class="form-control" name="" id=""></textarea>
      </div>

      <div class="text-end">
        <button class="btn btn-success px-4">
          Gửi đơn
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAccountStore } from '@/stores/account';
import { useUserStore } from '@/stores/user';
import { ref, onMounted , computed} from 'vue';

const LeaveType = ref([]);
const selectedLeaveType = ref('');
const userStore = useUserStore()
const {userInfo} = userStore
const accountStore = useAccountStore()
const {username} = accountStore.loginCredentials
const employee = ref({})

const computedUserId = computed(() => {

  if (!username || typeof username !== 'string') {
    return ''
  }

  return username.length > 1 ? username.substring(1) : username
})

const fetchLeaveType = async () => {
  try {
    const res = await fetch(`http://192.168.1.70:5002/api/getLeaveType`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: Không tìm thấy dữ liệu hoặc lỗi server`);
    }
    const data = await res.json();
    LeaveType.value = data;
  } catch (err) {
    console.log(err);
  }
};

const fetchEmployee = async () =>{
  try {
    const res = await fetch(`http://192.168.1.70:5002/api/employee/${computedUserId.value}`);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: Không tìm thấy dữ liệu hoặc lỗi server`);
    }
    const data = await res.json();
    employee.value = data[0];
  } catch (err) {
    console.log(err)
  }
}

onMounted(() => {
  fetchLeaveType();
  fetchEmployee();
});
</script>
