<template>
  <div class="login-container">
    <h2>🔐 AD Login Authentication</h2>

    <div class="form-group">
      <label for="username">Tên đăng nhập - Username</label>
      <input
        id="username"
        v-model="username"
        type="text"
        placeholder="Nhập mã nhân viên - user id"
      />
    </div>

    <div class="form-group">
      <label for="password">Mật khẩu - Password</label>
      <input
        id="password"
        v-model="password"
        type="password"
        placeholder="Nhập mật khẩu - password"
      />
    </div>

    <button @click="handleLogin">Đăng nhập - Login</button>

    <div
      v-if="responseMessage"
      :class="['response-box', isSuccess ? 'success' : 'error']"
    >
      <pre>{{ responseMessage }}</pre>
    </div>
  </div>
</template>

<script setup>
import { useUserStore } from '@/stores/user'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const username = ref('')
const password = ref('')
const responseMessage = ref('')
const isSuccess = ref(false)
const router = useRouter()
const userStore = useUserStore()

const handleLogin = async () => {
  if (!username.value || !password.value) {
    alert('Please enter both username and password')
    return
  }

  responseMessage.value = ''
  isSuccess.value = false

  try {
    const response = await fetch('http://192.168.1.70:5001/api/auth', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    })

    const responseData = await response.json()
    console.log('API raw response:', responseData)

    if (response.ok && responseData.success) {
      isSuccess.value = true

      // ✅ Kiểm tra chắc chắn có data trước khi gọi store
      if (responseData.data) {
        userStore.setUserData(responseData)
        router.push('/home')
      } else {
        responseMessage.value = '❌ Login succeeded but no data returned.'
      }
    } else {
      isSuccess.value = false
      responseMessage.value = `❌ Login Failed\nMessage: ${responseData.message || 'Unknown error'}\nError: ${responseData.error_code || 'N/A'}`
    }
  } catch (err) {
    isSuccess.value = false
    responseMessage.value = `❌ API Request Failed\nError: ${err.message}`
  }
}
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 60px auto;
  background: #fff;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
h2 {
  text-align: center;
  margin-bottom: 24px;
}
.form-group {
  margin-bottom: 16px;
}
label {
  display: block;
  margin-bottom: 4px;
}
input {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
}
button {
  width: 100%;
  padding: 10px;
  background: #007bff;
  color: white;
  font-weight: bold;
  border: none;
  cursor: pointer;
}
button:hover {
  background: #0056b3;
}
.response-box {
  margin-top: 20px;
  padding: 12px;
  white-space: pre-wrap;
  border-left: 5px solid;
  background: #f9f9f9;
}
.success {
  border-left-color: #28a745;
}
.error {
  border-left-color: #dc3545;
}
</style>