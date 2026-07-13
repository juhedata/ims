<script setup>
import { onMounted, ref } from 'vue'
import { listUsers, createUser, toggleUserStatus, deleteUser } from '@/api/user'
import { listAuditLogs } from '@/api/audit'
import { updateBranding, uploadLogo, clearLogo } from '@/api/settings'
import { useBrandStore } from '@/stores/brand'
import { USER_ROLE_MAP, AUDIT_ACTION_MAP, AUDIT_MODULE_MAP } from '@/constants/enums'
import { dateTimeColumnFormatter } from '@/utils/datetime'

const brand = useBrandStore()
const activeTab = ref('branding')
const users = ref([])
const loading = ref(false)

const userDialog = ref(false)
const userForm = ref({ username: '', password: '', nickname: '', email: '', phone: '', role: 'STAFF' })

// 品牌配置
const brandingForm = ref({ app_name: '', app_subtitle: '' })
const brandingSaving = ref(false)
const logoUploading = ref(false)

// 审计日志
const auditLoading = ref(false)
const auditLogs = ref([])
const auditTotal = ref(0)
const auditPage = ref(1)
const auditPageSize = ref(15)
const auditQuery = ref({
  operator_keyword: '',
  module: '',
  action: '',
  keyword: '',
  dateRange: [],
})
const detailVisible = ref(false)
const detailRow = ref(null)

onMounted(async () => {
  await brand.fetchBranding()
  syncBrandingForm()
})

function syncBrandingForm() {
  brandingForm.value = {
    app_name: brand.appName,
    app_subtitle: brand.appSubtitle,
  }
}

async function saveBranding() {
  if (!brandingForm.value.app_name?.trim()) {
    ElMessage.warning('项目名称不能为空')
    return
  }
  if (!brandingForm.value.app_subtitle?.trim()) {
    ElMessage.warning('登录页副标题不能为空')
    return
  }
  brandingSaving.value = true
  try {
    const res = await updateBranding({
      app_name: brandingForm.value.app_name.trim(),
      app_subtitle: brandingForm.value.app_subtitle.trim(),
    })
    brand.apply(res.data)
    syncBrandingForm()
    ElMessage.success('品牌配置已保存')
  } finally {
    brandingSaving.value = false
  }
}

async function handleLogoUpload({ file }) {
  logoUploading.value = true
  try {
    const res = await uploadLogo(file)
    brand.apply(res.data)
    ElMessage.success('Logo 上传成功')
  } finally {
    logoUploading.value = false
  }
  return false
}

async function handleClearLogo() {
  await ElMessageBox.confirm('确认清除当前 Logo？清除后将显示项目名称文字。', '提示', { type: 'warning' })
  const res = await clearLogo()
  brand.apply(res.data)
  ElMessage.success('Logo 已清除')
}

async function loadUsers() {
  loading.value = true
  try {
    const res = await listUsers({ page: 1, page_size: 100 })
    users.value = res.data.items
  } finally { loading.value = false }
}

async function loadAuditLogs() {
  auditLoading.value = true
  try {
    const params = {
      page: auditPage.value,
      page_size: auditPageSize.value,
      operator_keyword: auditQuery.value.operator_keyword || undefined,
      module: auditQuery.value.module || undefined,
      action: auditQuery.value.action || undefined,
      keyword: auditQuery.value.keyword || undefined,
    }
    if (auditQuery.value.dateRange?.length === 2) {
      params.start_time = auditQuery.value.dateRange[0]
      params.end_time = auditQuery.value.dateRange[1]
    }
    const res = await listAuditLogs(params)
    auditLogs.value = res.data.items
    auditTotal.value = res.data.total
  } finally { auditLoading.value = false }
}

function handleAuditSearch() {
  auditPage.value = 1
  loadAuditLogs()
}

function handleAuditReset() {
  auditQuery.value = { operator_keyword: '', module: '', action: '', keyword: '', dateRange: [] }
  handleAuditSearch()
}

function handleAuditPageChange(p) {
  auditPage.value = p
  loadAuditLogs()
}

function openDetail(row) {
  detailRow.value = row
  detailVisible.value = true
}

function formatJson(jsonStr) {
  if (!jsonStr) return '—'
  try {
    return JSON.stringify(JSON.parse(jsonStr), null, 2)
  } catch {
    return jsonStr
  }
}

function onTabChange(name) {
  if (name === 'user' && users.value.length === 0) {
    loadUsers()
  }
  if (name === 'audit' && auditLogs.value.length === 0) {
    loadAuditLogs()
  }
}

function openUserDialog() {
  userForm.value = { username: '', password: '', nickname: '', email: '', phone: '', role: 'STAFF' }
  userDialog.value = true
}

async function saveUser() {
  if (!userForm.value.username?.trim()) {
    ElMessage.warning('账号不能为空')
    return
  }
  if (!userForm.value.password?.trim()) {
    ElMessage.warning('密码不能为空')
    return
  }
  if (!userForm.value.nickname?.trim()) {
    ElMessage.warning('昵称不能为空')
    return
  }
  await createUser(userForm.value)
  ElMessage.success('用户创建成功')
  userDialog.value = false
  loadUsers()
}

async function handleToggleUser(row) {
  await toggleUserStatus(row.id)
  ElMessage.success('状态已更新')
  loadUsers()
}

async function handleDeleteUser(row) {
  await ElMessageBox.confirm('确认删除该用户？', '提示', { type: 'warning' })
  await deleteUser(row.id)
  ElMessage.success('删除成功')
  loadUsers()
}
</script>

<template>
  <el-card shadow="never" style="position: relative;">
    <el-button v-if="activeTab === 'user'" type="primary" style="position: absolute; right: 20px; top: 12px; z-index: 1000;" @click="openUserDialog()">新增员工</el-button>
    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="品牌配置" name="branding">
        <el-form label-width="120px" style="max-width: 560px; margin-top: 12px">
          <el-form-item label="项目名称" required>
            <el-input v-model="brandingForm.app_name" maxlength="100" show-word-limit placeholder="如 IMS" />
          </el-form-item>
          <el-form-item label="登录页副标题" required>
            <el-input v-model="brandingForm.app_subtitle" maxlength="200" show-word-limit placeholder="如 一物一码库存管理系统" />
          </el-form-item>
          <el-form-item label="项目 Logo">
            <div class="logo-upload-row">
              <div class="logo-preview">
                <img v-if="brand.logoUrl" :src="brand.logoUrl" alt="logo" />
                <span v-else class="logo-preview-text">{{ brandingForm.app_name || 'IMS' }}</span>
              </div>
              <div class="logo-actions">
                <el-upload
                  :show-file-list="false"
                  accept="image/png,image/jpeg,image/webp,image/svg+xml,image/x-icon,.ico"
                  :http-request="handleLogoUpload"
                >
                  <el-button type="primary" :loading="logoUploading">上传 Logo</el-button>
                </el-upload>
                <el-button v-if="brand.logoUrl" @click="handleClearLogo">清除</el-button>
                <p class="logo-hint">支持 PNG / JPG / WEBP / SVG / ICO，不超过 2MB。未上传时侧栏与登录页显示项目名称。</p>
              </div>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="brandingSaving" @click="saveBranding">保存文案</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="员工账号" name="user">
        <el-table :data="users" v-loading="loading" style="margin-top:12px">
          <el-table-column prop="id" label="ID" />
          <el-table-column prop="username" label="账号" />
          <el-table-column prop="nickname" label="昵称" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="phone" label="手机" />
          <el-table-column label="角色">
            <template #default="{ row }">
              {{ USER_ROLE_MAP[row.role] || row.role }}
            </template>
          </el-table-column>
          <el-table-column label="状态">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">{{ row.status === 1 ? '正常' : '禁用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right">
            <template #default="{ row }">
              <el-button type="warning" link @click="handleToggleUser(row)">{{ row.status === 1 ? '禁用' : '启用' }}</el-button>
              <el-button type="danger" link @click="handleDeleteUser(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="审计日志" name="audit">
        <el-form class="list-search" inline @submit.prevent="handleAuditSearch">
          <el-form-item label="操作人">
            <el-input v-model="auditQuery.operator_keyword" clearable placeholder="账号/昵称" style="width:140px" />
          </el-form-item>
          <el-form-item label="模块">
            <el-select v-model="auditQuery.module" clearable placeholder="全部" style="width:120px">
              <el-option v-for="(label, key) in AUDIT_MODULE_MAP" :key="key" :label="label" :value="key" />
            </el-select>
          </el-form-item>
          <el-form-item label="操作">
            <el-select v-model="auditQuery.action" clearable placeholder="全部" style="width:120px">
              <el-option v-for="(label, key) in AUDIT_ACTION_MAP" :key="key" :label="label" :value="key" />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词">
            <el-input v-model="auditQuery.keyword" clearable placeholder="摘要/单号/资源" style="width:160px" />
          </el-form-item>
          <el-form-item label="时间">
            <el-date-picker
              v-model="auditQuery.dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始"
              end-placeholder="结束"
              value-format="YYYY-MM-DD HH:mm:ss"
              style="width:360px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" native-type="submit">查询</el-button>
            <el-button @click="handleAuditReset">重置</el-button>
          </el-form-item>
        </el-form>

        <el-table :data="auditLogs" v-loading="auditLoading" stripe>
          <el-table-column prop="created_at" label="操作时间" width="170" :formatter="dateTimeColumnFormatter" />
          <el-table-column prop="operator_name" label="操作人" width="140" />
          <el-table-column label="模块" width="100">
            <template #default="{ row }">{{ AUDIT_MODULE_MAP[row.module] || row.module }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ AUDIT_ACTION_MAP[row.action] || row.action }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="summary" label="操作摘要" min-width="240" show-overflow-tooltip />
          <el-table-column prop="resource_name" label="关联资源" width="160" show-overflow-tooltip />
          <el-table-column prop="ip_address" label="IP" width="130" />
          <el-table-column label="详情" width="70" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="openDetail(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          class="list-pagination"
          layout="total, prev, pager, next"
          :total="auditTotal"
          :page-size="auditPageSize"
          :current-page="auditPage"
          @current-change="handleAuditPageChange"
        />
      </el-tab-pane>
    </el-tabs>
  </el-card>

  <el-dialog v-model="userDialog" title="新增员工">
    <el-form label-width="80px">
      <el-form-item label="账号" required ><el-input v-model="userForm.username" placeholder="请输入账号"/></el-form-item>
      <el-form-item label="密码" required ><el-input v-model="userForm.password" type="password" show-password placeholder="请输入密码"/></el-form-item>
      <el-form-item label="昵称" required><el-input v-model="userForm.nickname" placeholder="请输入昵称"/></el-form-item>
      <el-form-item label="邮箱"><el-input v-model="userForm.email" /></el-form-item>
      <el-form-item label="手机"><el-input v-model="userForm.phone" /></el-form-item>
      <el-form-item label="角色">
        <el-select v-model="userForm.role" style="width:100%">
          <el-option label="普通员工" value="STAFF" />
          <el-option label="管理员" value="ADMIN" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="userDialog = false">取消</el-button>
      <el-button type="primary" @click="saveUser">保存</el-button>
    </template>
  </el-dialog>

  <el-drawer v-model="detailVisible" title="审计日志详情" size="60%">
    <template v-if="detailRow">
      <el-descriptions :column="2" border size="small" style="margin-bottom:16px">
        <el-descriptions-item label="操作时间">{{ dateTimeColumnFormatter(null, null, detailRow.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="操作人">{{ detailRow.operator_name }}</el-descriptions-item>
        <el-descriptions-item label="模块">{{ AUDIT_MODULE_MAP[detailRow.module] || detailRow.module }}</el-descriptions-item>
        <el-descriptions-item label="操作">{{ AUDIT_ACTION_MAP[detailRow.action] || detailRow.action }}</el-descriptions-item>
        <el-descriptions-item label="资源类型">{{ detailRow.resource_type || '—' }}</el-descriptions-item>
        <el-descriptions-item label="资源标识">{{ detailRow.resource_id || '—' }}</el-descriptions-item>
        <el-descriptions-item label="资源名称" :span="2">{{ detailRow.resource_name || '—' }}</el-descriptions-item>
        <el-descriptions-item label="IP 地址">{{ detailRow.ip_address || '—' }}</el-descriptions-item>
        <el-descriptions-item label="操作摘要" :span="2">{{ detailRow.summary }}</el-descriptions-item>
      </el-descriptions>
      <div v-if="detailRow.before_data" style="margin-bottom:12px">
        <div style="font-weight:600;margin-bottom:6px">变更前</div>
        <pre class="audit-json">{{ formatJson(detailRow.before_data) }}</pre>
      </div>
      <div v-if="detailRow.after_data">
        <div style="font-weight:600;margin-bottom:6px">变更后</div>
        <pre class="audit-json">{{ formatJson(detailRow.after_data) }}</pre>
      </div>
    </template>
  </el-drawer>
</template>

<style scoped>
.toolbar { margin-bottom: 4px; }
.list-search { margin-bottom: 4px; }
.list-search :deep(.el-form-item) { margin-bottom: 12px; }
.list-pagination { margin-top: 16px; justify-content: flex-end; }
.audit-json {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 12px;
  font-size: 12px;
  line-height: 1.5;
  max-height: 280px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}
.logo-upload-row {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.logo-preview {
  width: 160px;
  height: 64px;
  border: 1px dashed #dcdfe6;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1d2b3a;
  overflow: hidden;
  flex-shrink: 0;
}
.logo-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.logo-preview-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  padding: 0 8px;
  text-align: center;
}
.logo-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.logo-hint {
  width: 100%;
  margin: 4px 0 0;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}
</style>
