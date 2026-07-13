<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBrandStore } from '@/stores/brand'
import { changePassword } from '@/api/user'
import {
  House, Box, Download, Upload, Goods, OfficeBuilding, Setting, SwitchButton,
  Expand, Fold, Camera, List, User, Lock, ArrowDown,
} from '@element-plus/icons-vue'

const MOBILE_BREAKPOINT = 768

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const brand = useBrandStore()

const isMobile = ref(false)
const menuCollapsed = ref(false)
const passwordDialog = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref()
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const passwordRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '新密码至少 8 位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== passwordForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const allMenus = [
  { path: '/dashboard', title: '首页', icon: House },
  {
    title: '库存',
    icon: Box,
    children: [
      { path: '/inventory', title: '实时库存', icon: List },
      { path: '/snapshot', title: '历史快照', icon: Camera },
    ],
  },
  { path: '/inbound', title: '入库', icon: Download },
  { path: '/outbound', title: '出库', icon: Upload },
  { path: '/products', title: '商品SKU', icon: Goods },
  { path: '/partners', title: '往来单位', icon: OfficeBuilding },
  { path: '/settings', title: '系统设置', icon: Setting, adminOnly: true },
]

const menus = computed(() =>
  auth.isAdmin ? allMenus : allMenus.filter((m) => !m.adminOnly)
)

const activeMenu = computed(() => {
  if (route.path.startsWith('/snapshot')) return '/snapshot'
  if (route.path.startsWith('/inventory')) return '/inventory'
  return route.path
})

const asideWidth = computed(() => {
  if (isMobile.value) return '220px'
  return menuCollapsed.value ? '64px' : '220px'
})

const showSidebarBackdrop = computed(() => isMobile.value && !menuCollapsed.value)

function checkMobile() {
  const mobile = window.innerWidth < MOBILE_BREAKPOINT
  if (mobile === isMobile.value) return
  isMobile.value = mobile
  menuCollapsed.value = mobile
}

function toggleSidebar() {
  menuCollapsed.value = !menuCollapsed.value
}

function closeSidebar() {
  menuCollapsed.value = true
}

onMounted(() => {
  isMobile.value = window.innerWidth < MOBILE_BREAKPOINT
  menuCollapsed.value = isMobile.value
  auth.fetchUser()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

watch(() => route.path, () => {
  if (isMobile.value) menuCollapsed.value = true
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}

function openPasswordDialog() {
  passwordForm.value = {
    old_password: '',
    new_password: '',
    confirm_password: '',
  }
  passwordDialog.value = true
}

async function submitPasswordChange() {
  const valid = await passwordFormRef.value?.validate().catch(() => false)
  if (!valid) return

  passwordLoading.value = true
  try {
    await changePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    passwordDialog.value = false
    handleLogout()
  } finally {
    passwordLoading.value = false
  }
}
</script>

<template>
  <el-container class="layout">
    <div
      v-if="showSidebarBackdrop"
      class="sidebar-backdrop"
      @click="closeSidebar"
    />

    <el-aside
      :width="asideWidth"
      class="aside"
      :class="{
        'aside--mobile': isMobile,
        'aside--collapsed': menuCollapsed,
        'aside--desktop-collapsed': !isMobile && menuCollapsed,
      }"
    >
      <div class="logo" :class="{ 'logo--collapsed': !isMobile && menuCollapsed }">
        <img
          v-if="brand.logoUrl"
          :src="brand.logoUrl"
          :alt="brand.appName"
          class="logo-img"
        />
        <span v-else class="logo-text" :title="brand.appName">{{ brand.appName }}</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="!isMobile && menuCollapsed"
        :collapse-transition="false"
        router
        background-color="#1d2b3a"
        text-color="#bfcbd9"
        active-text-color="#7b67ee"
      >
        <template v-for="m in menus" :key="m.path || m.title">
          <el-sub-menu v-if="m.children" :index="m.title">
            <template #title>
              <el-icon><component :is="m.icon" /></el-icon>
              <span>{{ m.title }}</span>
            </template>
            <el-menu-item v-for="c in m.children" :key="c.path" :index="c.path">
              <el-icon><component :is="c.icon" /></el-icon>
              <template #title>{{ c.title }}</template>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="m.path">
            <el-icon><component :is="m.icon" /></el-icon>
            <template #title>{{ m.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container class="main-container">
      <el-header class="header">
        <div class="header-left">
          <el-button class="sidebar-toggle" text @click="toggleSidebar">
            <el-icon :size="18">
              <component :is="menuCollapsed ? Expand : Fold" />
            </el-icon>
          </el-button>
          <span class="page-title">{{ route.meta.title }}</span>
        </div>
        <el-dropdown class="header-right" trigger="click" @command="(cmd) => cmd === 'password' ? openPasswordDialog() : handleLogout()">
          <div class="user-trigger">
            <el-icon class="user-icon"><User /></el-icon>
            <span class="username">{{ auth.user?.nickname || auth.user?.username }}</span>
            <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="password">
                <el-icon><Lock /></el-icon>
                修改密码
              </el-dropdown-item>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon>
                退出
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>

    <el-dialog v-model="passwordDialog" title="修改密码" width="420px" destroy-on-close>
      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="90px">
        <el-form-item label="旧密码" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入旧密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="至少 8 位" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialog = false">取消</el-button>
        <el-button type="primary" :loading="passwordLoading" @click="submitPasswordChange">确定</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
  overflow: hidden;
}

.main-container {
  min-width: 0;
}

.aside {
  background: #1d2b3a;
  transition: width 0.25s ease, transform 0.25s ease;
  overflow: hidden;
  flex-shrink: 0;
}

.aside--mobile {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 1001;
  transform: translateX(0);
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.15);
}

.aside--mobile.aside--collapsed {
  transform: translateX(-100%);
  box-shadow: none;
}

.sidebar-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.45);
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  border-bottom: 1px solid #2d3f50;
  overflow: hidden;
  transition: padding 0.25s ease;
}

.logo--collapsed {
  width: 64px;
  padding: 0;
  justify-content: flex-start;
}

.logo-img {
  height: 22px;
  width: auto;
  max-width: 100%;
  display: block;
  transition: width 0.25s ease, object-fit 0.25s ease;
}

.logo-text {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.logo--collapsed .logo-text {
  font-size: 14px;
  max-width: 48px;
  margin-left: 8px;
}

.logo--collapsed .logo-img {
  width: 48px;
  max-width: none;
  object-fit: cover;
  object-position: left center;
  height: 24px;
  margin-left: 10px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  padding: 0 16px;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.sidebar-toggle {
  flex-shrink: 0;
  padding: 8px;
  color: #606266;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  flex-shrink: 0;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.user-trigger:hover {
  background: #f5f7fa;
}

.user-icon {
  font-size: 18px;
  color: #606266;
}

.username {
  color: #606266;
  font-size: 14px;
}

.dropdown-arrow {
  font-size: 12px;
  color: #909399;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 6px;
}

.main {
  background: #f5f7fa;
  padding: 20px;
  overflow: auto;
}

.el-menu {
  border-right: none;
}

@media (max-width: 767px) {
  .header {
    padding: 0 12px;
  }

  .page-title {
    font-size: 16px;
  }

  .username,
  .dropdown-arrow {
    display: none;
  }

  .main {
    padding: 12px;
  }
}
</style>
