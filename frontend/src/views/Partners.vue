<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  listGroups, createGroup, updateGroup, deleteGroup,
  listPartners, createPartner, updatePartner, deletePartner,
} from '@/api/partner'
import { PARTNER_TYPE_MAP } from '@/constants/enums'
import { Edit, Delete } from '@element-plus/icons-vue'

const activeTab = ref('partner')
const groups = ref([])
const partners = ref([])
const loading = ref(false)

const partnerPage = ref(1)
const partnerPageSize = ref(15)
const partnerTotal = ref(0)

const groupPage = ref(1)
const groupPageSize = ref(15)
const pagedGroups = computed(() => {
  const start = (groupPage.value - 1) * groupPageSize.value
  return groups.value.slice(start, start + groupPageSize.value)
})

const groupDialog = ref(false)
const groupForm = ref({ id: null, name: '' })
const partnerDialog = ref(false)
const partnerForm = ref({ id: null, name: '', group_id: null, partner_type: 0, remark: '', status: 1 })

onMounted(() => { loadGroups(); loadPartners() })

async function loadGroups() {
  const res = await listGroups()
  groups.value = res.data
  const maxPage = Math.max(1, Math.ceil(groups.value.length / groupPageSize.value))
  if (groupPage.value > maxPage) groupPage.value = maxPage
}

async function loadPartners() {
  loading.value = true
  try {
    const res = await listPartners({ page: partnerPage.value, page_size: partnerPageSize.value })
    partners.value = res.data.items
    partnerTotal.value = res.data.total
  } finally { loading.value = false }
}

function handlePartnerPageChange(p) {
  partnerPage.value = p
  loadPartners()
}

function handleGroupPageChange(p) {
  groupPage.value = p
}

function openGroupDialog(row = null) {
  groupForm.value = row ? { id: row.id, name: row.name } : { id: null, name: '' }
  groupDialog.value = true
}

async function saveGroup() {
  if (!groupForm.value.name?.trim()) {
    ElMessage.warning('分组名称不能为空')
    return
  }
  if (groupForm.value.id) await updateGroup(groupForm.value.id, { name: groupForm.value.name })
  else await createGroup({ name: groupForm.value.name })
  ElMessage.success('保存成功')
  groupDialog.value = false
  loadGroups()
}

async function removeGroup(row) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await deleteGroup(row.id)
  ElMessage.success('删除成功')
  loadGroups()
}

function openPartnerDialog(row = null) {
  partnerForm.value = row
    ? { id: row.id, name: row.name, group_id: row.group_id, partner_type: row.partner_type, remark: row.remark || '', status: row.status }
    : { id: null, name: '', group_id: groups.value[0]?.id || null, partner_type: 0, remark: '', status: 1 }
  partnerDialog.value = true
}

async function savePartner() {
  if (!partnerForm.value.name?.trim()) {
    ElMessage.warning('单位名称不能为空')
    return
  }
  const { id, ...data } = partnerForm.value
  if (id) await updatePartner(id, data)
  else await createPartner(data)
  ElMessage.success('保存成功')
  partnerDialog.value = false
  loadPartners()
}

async function removePartner(row) {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  await deletePartner(row.id)
  ElMessage.success('删除成功')
  loadPartners()
}
</script>

<template>
  <el-card shadow="never" style="position: relative;">
    <el-button v-if="activeTab === 'partner'" type="primary" style="position: absolute; right: 20px; top: 12px; z-index: 1000;" @click="openPartnerDialog()">新增单位</el-button>
    <el-button v-if="activeTab === 'group'" type="primary" style="position: absolute; right: 20px; top: 12px; z-index: 1000;" @click="openGroupDialog()">新增分组</el-button>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="往来单位" name="partner">
        <el-table :data="partners" v-loading="loading" stripe style="margin-top:12px">
          <el-table-column prop="id" label="单位ID" />
          <el-table-column prop="name" label="单位名称" />
          <el-table-column label="分组">
            <template #default="{ row }">{{ groups.find(g => g.id === row.group_id)?.name || '-' }}</template>
          </el-table-column>
          <el-table-column label="单位类型">
            <template #default="{ row }">{{ PARTNER_TYPE_MAP[row.partner_type] }}</template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" show-overflow-tooltip />
          <el-table-column label="操作" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link :icon="Edit" title="编辑" @click="openPartnerDialog(row)" />
              <el-button type="danger" link :icon="Delete" title="删除" @click="removePartner(row)" />
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="partnerTotal > 0"
          class="list-pagination"
          background
          layout="total, prev, pager, next"
          :total="partnerTotal"
          :page-size="partnerPageSize"
          :current-page="partnerPage"
          @current-change="handlePartnerPageChange"
        />
      </el-tab-pane>

      <el-tab-pane label="单位分组" name="group">
        <el-table :data="pagedGroups" stripe style="margin-top:12px">
          <el-table-column prop="id" label="分组ID" width="100" />
          <el-table-column prop="name" label="分组名称" />
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button type="primary" link :icon="Edit" title="编辑" @click="openGroupDialog(row)" />
              <el-button type="danger" link :icon="Delete" title="删除" @click="removeGroup(row)" />
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="groups.length > 0"
          class="list-pagination"
          background
          layout="total, prev, pager, next"
          :total="groups.length"
          :page-size="groupPageSize"
          :current-page="groupPage"
          @current-change="handleGroupPageChange"
        />
      </el-tab-pane>
    </el-tabs>
  </el-card>

  <el-dialog v-model="groupDialog" :title="groupForm.id ? '编辑分组' : '新增分组'">
    <el-form label-width="80px">
      <el-form-item label="分组名称" required ><el-input v-model="groupForm.name" placeholder="请输入分组名称"/></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="groupDialog = false">取消</el-button>
      <el-button type="primary" @click="saveGroup">保存</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="partnerDialog" :title="partnerForm.id ? '编辑单位' : '新增单位'" >
    <el-form label-width="90px">
      <el-form-item label="单位名称" required ><el-input v-model="partnerForm.name" placeholder="请输入单位名称"/></el-form-item>
      <el-form-item label="所属分组" required >
        <el-select v-model="partnerForm.group_id" style="width:100%">
          <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="单位类型">
        <el-select v-model="partnerForm.partner_type" style="width:100%">
          <el-option v-for="(label, key) in PARTNER_TYPE_MAP" :key="key" :label="label" :value="Number(key)" />
        </el-select>
      </el-form-item>
      <el-form-item label="备注"><el-input v-model="partnerForm.remark" type="textarea" :rows="2" /></el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="partnerDialog = false">取消</el-button>
      <el-button type="primary" @click="savePartner">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.toolbar { margin-bottom: 4px; }
.list-pagination { margin-top: 16px; justify-content: flex-end; }
</style>
