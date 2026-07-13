<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useBrandStore } from '@/stores/brand'

const router = useRouter()
const auth = useAuthStore()
const brand = useBrandStore()
const loading = ref(false)
const form = ref({ username: '', password: '' })

onMounted(() => {
  if (!brand.loaded) brand.fetchBranding()
})

async function handleLogin() {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div v-if="brand.logoUrl" class="login-logo">
        <img :src="brand.logoUrl" :alt="brand.appName" />
      </div>
      <h1>{{ brand.appName }}</h1>
      <p class="subtitle">{{ brand.appSubtitle }}</p>
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" :prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" :prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleLogin">登 录</el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1d2b3a 0%, #2c5364 100%);
}
.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,.2);
}
.login-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}
.login-logo img {
  max-height: 56px;
  max-width: 220px;
  object-fit: contain;
}
h1 { text-align: center; margin: 0 0 8px; color: #1d2b3a; }
.subtitle { text-align: center; color: #909399; margin: 0 0 32px; font-size: 14px; }
</style>
