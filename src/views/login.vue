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

    <div class="form-group checkbox-group">
      <input type="checkbox" id="rememberMe" v-model="rememberMe" />
      <label for="rememberMe">Ghi nhớ đăng nhập - Remember Me</label>
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
import { useAccountStore } from '@/stores/account'
import { useUserStore } from '@/stores/user'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const username = ref('')
const password = ref('')
const rememberMe = ref(false) // <-- Thêm ref mới cho "remember me"
const responseMessage = ref('')
const isSuccess = ref(false)
const router = useRouter()
const userStore = useUserStore()
const accountStore = useAccountStore()

accountStore.saveAccount(username, password, true)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    alert('Please enter both username and password')
    return
  }

  responseMessage.value = ''
  isSuccess.value = false

  try {
    const response = await fetch('http://192.168.1.70:5002/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value,
        remember_me: rememberMe.value // <-- Bao gồm giá trị "remember me"
      })
    })

    const responseData = await response.json()
    console.log('API raw response:', responseData)

    if (response.ok && responseData.success) {
      isSuccess.value = true

      // ✅ Kiểm tra chắc chắn có data trước khi gọi store
      if (responseData.data) {
        userStore.setUserData(responseData)
        if(!responseData.data.data.user.is_manager) {
          router.push('/home/list')
        }else{
          router.push('/home/manager/list')
        }
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
input[type="text"],
input[type="password"] {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.checkbox-group {
  display: flex; /* Sử dụng flexbox để căn chỉnh hộp kiểm và nhãn */
  align-items: center; /* Căn chỉnh theo chiều dọc */
  margin-bottom: 16px; /* Khoảng cách dưới cho nhóm */
}

.checkbox-group input[type="checkbox"] {
  width: auto; /* Để hộp kiểm không chiếm toàn bộ chiều rộng */
  margin-right: 8px; /* Khoảng cách giữa hộp kiểm và nhãn */
}

.checkbox-group label {
  margin-bottom: 0; /* Xóa margin dưới mặc định của nhãn trong nhóm này */
}

button {
  width: 100%;
  padding: 10px;
  background: #007bff;
  color: white;
  font-weight: bold;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s ease;
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
  border-radius: 4px;
}
.success {
  border-left-color: #28a745;
  color: #28a745;
}
.error {
  border-left-color: #dc3545;
  color: #dc3545;
}
</style>