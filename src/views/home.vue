<template>
  <div class="container-fluid py-4">
    <!-- User Information Component -->
    <UserInfo ref="userInfoRef" />
    
    <div class="row g-2">
      <div class="col-auto">
        <RouterLink to="/home/list" class="btn btn-outline-primary btn-sm">
          <i class="bi bi-list me-1"></i> List
        </RouterLink>
      </div>
      <div class="col-auto">
        <RouterLink to="/home/calendar" class="btn btn-outline-success btn-sm">
          <i class="bi bi-calendar-event me-1"></i> Calendar
        </RouterLink>
      </div>
    </div>
    
    <hr>
    <!-- Leave Data Component -->
    <RouterView></RouterView>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import UserInfo from '@/components/UserInfo.vue'

const router = useRouter()
const userStore = useUserStore()
const { authInfo, userInfo } = userStore

const userInfoRef = ref(null)
const leaveDataRef = ref(null)

// Redirect nếu không có user thông tin
onMounted(() => {
  const hasAuth = authInfo?.username
  const hasUser = userInfo?.username
})

// Computed userId để truyền cho LeaveData component
const userId = computed(() => {
  const username = userInfo?.username || authInfo?.username

  if (!username || typeof username !== 'string') {
    return ''
  }

  return username.length > 1 ? username.substring(1) : username
})

// Expose methods để có thể gọi từ bên ngoài nếu cần
defineExpose({
  refreshUserInfo: () => userInfoRef.value?.fetchEmployee?.(),
  refreshLeaveData: () => leaveDataRef.value?.fetchLeaveData?.(),
  userInfoRef,
  leaveDataRef
})
</script>

<style scoped>
/* Custom styles nếu cần */
</style>