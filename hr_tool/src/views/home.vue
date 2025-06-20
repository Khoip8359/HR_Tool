<template>
  <div class="container-fluid py-4">
    <!-- User Information Component -->
    <UserInfo ref="userInfoRef" />
    
    <hr>
    <!-- Leave Data Component -->
    <RouterView></RouterView>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import UserInfo from '@/components/UserInfo.vue'

const router = useRouter()
const userStore = useUserStore()
const { userInfo, isLoggedIn } = userStore

const userInfoRef = ref(null)
const leaveDataRef = ref(null)

// Define checkAuth function first
const checkAuth = () => {
  console.log('Checking auth:', { 
    isLoggedIn, 
    username: userInfo?.username,
    accessToken: userStore.tokens?.accessToken ? 'exists' : 'missing'
  })
}

// Check authentication on mount with delay
onMounted(async () => {
  // Wait a bit for store to initialize
  await new Promise(resolve => setTimeout(resolve, 100))
  checkAuth()
})

// Watch for changes in auth state - watch the isLoggedIn getter
watch(() => isLoggedIn, (newValue) => {
  console.log('Auth state changed:', newValue)
  checkAuth()
})

// Computed userId để truyền cho LeaveData component
const userId = computed(() => {
  const username = userInfo?.username

  if (!username || typeof username !== 'string') {
    return ''
  }

  return username.length > 1 ? username.substring(1) : username
})

defineExpose({
  refreshUserInfo: () => userInfoRef.value?.fetchEmployee?.(),
  refreshLeaveData: () => leaveDataRef.value?.fetchLeaveData?.(),
  userInfoRef,
  leaveDataRef
})
</script>

<style scoped>
/* Add any component-specific styles here */
</style>