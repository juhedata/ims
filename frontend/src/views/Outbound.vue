<script setup>
import { nextTick, onMounted, ref, computed } from 'vue'
import { Delete, View, Promotion, Select, Close, Edit, QuestionFilled, OfficeBuilding } from '@element-plus/icons-vue'
import OutboundDetail from '@/views/OutboundDetail.vue'
import {
  listOutboundOrders, createOutboundOrder, updateOutboundOrder, getOutboundOrder,
  submitOutboundOrder, approveOutboundOrder, cancelOutboundOrder, deleteOutboundOrder,
} from '@/api/outbound'
import { listAvailableItems } from '@/api/inventory'
import { listPartners } from '@/api/partner'
import { listCustomers } from '@/api/customer'
import { listSkus, listCategories } from '@/api/product'
import {
  OUTBOUND_TYPE_MAP, OPERATION_STATUS_MAP, PARTNER_TYPE_MAP,
  STOCK_CONDITION_MAP, statusTagType, selectableOutboundTypeEntries, selectableStockConditionEntries,
} from '@/constants/enums'
import { dateTimeColumnFormatter } from '@/utils/datetime'

const drawerVisible = ref(false)
const drawerOrderNo = ref('')

const loading = ref(false)
const orders = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(15)
const query = ref({
  order_no: '',
  item_sn: '',
  operation_status: '',
  outbound_type: '',
  partner_id: null,
  sku_id: null,
  dateRange: [],
})

const dialogVisible = ref(false)
const editingOrderId = ref(null)
const availableItems = ref([])
const itemsLoading = ref(false)
const itemsTotal = ref(0)
const itemsPage = ref(1)
const itemsPageSize = ref(20)
const MAX_SN_KEYWORDS = 100
const itemQuery = ref({ category_id: null, sku_id: null, stock_condition: '', keyword: '' })

function countKeywordTokens(keyword) {
  if (!keyword?.trim()) return 0
  const seen = new Set()
  let count = 0
  for (const line of keyword.split(/\r?\n/)) {
    const token = line.trim()
    if (!token || seen.has(token)) continue
    seen.add(token)
    count++
  }
  return count
}
const skuList = ref([])
const categoryList = ref([])
const itemTableRef = ref(null)
const partnerList = ref([])
const customerList = ref([])
const allPartners = ref([])
const selectedIds = ref([])

const form = ref({ outbound_type: 'SOLD', partner_id: null, customer_name: '', remark: '' })

const dialogTitle = computed(() => (editingOrderId.value ? '编辑出库单' : '新增出库单'))

onMounted(() => { loadData(); loadPartners(); loadCustomers(); loadSkus(); loadCategories() })

const filteredSkuList = computed(() => {
  if (!itemQuery.value.category_id) return skuList.value
  return skuList.value.filter(s => s.category_id === itemQuery.value.category_id)
})

async function loadCategories() {
  const res = await listCategories()
  categoryList.value = res.data
}

async function loadSkus() {
  const res = await listSkus({ page: 1, page_size: 500 })
  skuList.value = res.data.items
}

async function loadPartners() {
  const res = await listPartners({ page: 1, page_size: 500 })
  allPartners.value = res.data.items
  partnerList.value = res.data.items.filter(p => p.status === 1)
}

async function loadCustomers() {
  const res = await listCustomers({ page: 1, page_size: 500 })
  customerList.value = res.data.items
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (query.value.order_no) params.order_no = query.value.order_no
    if (query.value.item_sn?.trim()) params.item_sn = query.value.item_sn.trim()
    if (query.value.operation_status) params.operation_status = query.value.operation_status
    if (query.value.outbound_type) params.outbound_type = query.value.outbound_type
    if (query.value.partner_id) params.partner_id = query.value.partner_id
    if (query.value.sku_id) params.sku_id = query.value.sku_id
    if (query.value.dateRange?.length === 2) {
      params.start_time = `${query.value.dateRange[0]} 00:00:00`
      params.end_time = `${query.value.dateRange[1]} 23:59:59`
    }
    const res = await listOutboundOrders(params)
    orders.value = res.data.items
    total.value = res.data.total
  } finally { loading.value = false }
}

function searchOrders() {
  page.value = 1
  loadData()
}

function resetQuery() {
  query.value = {
    order_no: '',
    item_sn: '',
    operation_status: '',
    outbound_type: '',
    partner_id: null,
    sku_id: null,
    dateRange: [],
  }
  searchOrders()
}

function handlePageChange(p) {
  page.value = p
  loadData()
}

async function loadAvailableItems() {
  itemsLoading.value = true
  try {
    const params = {
      page: itemsPage.value,
      page_size: itemsPageSize.value,
      sku_id: itemQuery.value.sku_id || undefined,
      category_id: itemQuery.value.category_id || undefined,
      stock_condition: itemQuery.value.stock_condition || undefined,
      keyword: itemQuery.value.keyword || undefined,
    }
    if (editingOrderId.value) {
      params.outbound_order_id = editingOrderId.value
    }
    const res = await listAvailableItems(params)
    availableItems.value = res.data.items
    itemsTotal.value = res.data.total
    await restoreItemSelection()
  } finally { itemsLoading.value = false }
}

async function restoreItemSelection() {
  await nextTick()
  if (!itemTableRef.value || !selectedIds.value.length) return
  availableItems.value.forEach(row => {
    if (selectedIds.value.includes(row.id)) {
      itemTableRef.value.toggleRowSelection(row, true)
    }
  })
}

async function openCreate() {
  editingOrderId.value = null
  form.value = { outbound_type: 'SOLD', partner_id: null, customer_name: '', remark: '' }
  selectedIds.value = []
  itemQuery.value = { category_id: null, sku_id: null, stock_condition: '', keyword: '' }
  itemsPage.value = 1
  dialogVisible.value = true
  await loadAvailableItems()
  await nextTick()
  itemTableRef.value?.clearSelection()
}

async function openEdit(row) {
  editingOrderId.value = row.id
  selectedIds.value = []
  itemQuery.value = { category_id: null, sku_id: null, stock_condition: '', keyword: '' }
  itemsPage.value = 1
  dialogVisible.value = true
  try {
    const res = await getOutboundOrder(row.id)
    const order = res.data
    form.value = {
      outbound_type: order.outbound_type,
      partner_id: order.partner_id,
      customer_name: order.customer_name || '',
      remark: order.remark || '',
    }
    selectedIds.value = (order.items || []).map(i => i.item_id)
    await loadAvailableItems()
    await nextTick()
    itemTableRef.value?.clearSelection()
    await restoreItemSelection()
  } catch {
    dialogVisible.value = false
    editingOrderId.value = null
  }
}

function onCategoryChange() {
  if (itemQuery.value.sku_id && !filteredSkuList.value.some(s => s.id === itemQuery.value.sku_id)) {
    itemQuery.value.sku_id = null
  }
}

function searchAvailableItems() {
  const tokenCount = countKeywordTokens(itemQuery.value.keyword)
  if (tokenCount > MAX_SN_KEYWORDS) {
    ElMessage.warning(`最多支持同时查询 ${MAX_SN_KEYWORDS} 个 SN`)
    return
  }
  itemsPage.value = 1
  loadAvailableItems()
}

function resetItemQuery() {
  itemQuery.value = { category_id: null, sku_id: null, stock_condition: '', keyword: '' }
  searchAvailableItems()
}

function handleItemsPageChange(page) {
  itemsPage.value = page
  loadAvailableItems()
}

function handleSelectionChange(rows) {
  selectedIds.value = rows.map(r => r.id)
}

async function handleSave() {
  if (!form.value.partner_id) {
    ElMessage.warning('请选择关联单位')
    return
  }
  if (!form.value.customer_name?.trim()) {
    ElMessage.warning('请填写客户名称')
    return
  }
  if (!selectedIds.value.length) {
    ElMessage.warning('请勾选出库商品')
    return
  }
  const payload = { ...form.value, item_ids: selectedIds.value }
  if (editingOrderId.value) {
    await updateOutboundOrder(editingOrderId.value, payload)
    ElMessage.success('出库单已更新')
  } else {
    await createOutboundOrder(payload)
    ElMessage.success('出库单创建成功')
  }
  dialogVisible.value = false
  editingOrderId.value = null
  loadCustomers()
  loadData()
}

function showDetail(row) {
  drawerOrderNo.value = row.order_no
  drawerVisible.value = true
}

function onDetailDeleted() {
  drawerVisible.value = false
  loadData()
}

async function handleAction(action, row) {
  const map = {
    submit: [submitOutboundOrder, '确认提交审核？'],
    approve: [approveOutboundOrder, '确认通过该出库单？'],
    cancel: [cancelOutboundOrder, '确认取消？'],
    delete: [deleteOutboundOrder, '确认删除？'],
  }
  await ElMessageBox.confirm(map[action][1], '提示', { type: 'warning' })
  await map[action][0](row.id)
  ElMessage.success('操作成功')
  loadData()
}

function canSubmit(row) { return row.operation_status === 'INITIATED' && !row.submitted_at }
function canEdit(row) { return row.operation_status === 'INITIATED' && !row.submitted_at }
function canApprove(row) { return row.operation_status === 'INITIATED' && row.submitted_at }
function canCancel(row) { return row.operation_status === 'INITIATED' && row.submitted_at }
function canDelete(row) { return row.operation_status === 'INITIATED' && !row.submitted_at }
</script>

<template>
  <el-card shadow="never">
    <el-form :inline="true" class="list-search" @submit.prevent="searchOrders">
      <el-form-item label="出库单号">
        <el-input v-model="query.order_no" clearable placeholder="单号模糊搜索" style="width:160px" />
      </el-form-item>
      <el-form-item label="商品 SN">
        <el-input v-model="query.item_sn" clearable placeholder="SN 模糊搜索" style="width:160px" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="query.operation_status" clearable placeholder="全部" style="width:130px">
          <el-option v-for="(label, key) in OPERATION_STATUS_MAP" :key="key" :label="label" :value="key" />
        </el-select>
      </el-form-item>
      <el-form-item label="出库类型">
        <el-select v-model="query.outbound_type" clearable placeholder="全部" style="width:120px">
          <el-option v-for="[key, label] in selectableOutboundTypeEntries()" :key="key" :label="label" :value="key" />
        </el-select>
      </el-form-item>
      <el-form-item label="关联单位">
        <el-select v-model="query.partner_id" clearable filterable placeholder="全部" style="width:160px">
          <el-option v-for="p in allPartners" :key="p.id" :label="`${p.partner_group_name} - ${p.name}`" :value="p.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="商品 SKU">
        <el-select v-model="query.sku_id" clearable filterable placeholder="全部" style="width:180px">
          <el-option v-for="s in skuList" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="创建时间">
        <el-date-picker
          v-model="query.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width:260px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="searchOrders">查询</el-button>
        <el-button @click="resetQuery">重置</el-button>
        <el-button type="primary" plain @click="openCreate">新增出库</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="orders" v-loading="loading" stripe>
      <el-table-column label="出库单号" min-width="150">
        <template #default="{ row }">
          <el-button type="primary" link @click="showDetail(row)">{{ row.order_no }}</el-button>
        </template>
      </el-table-column>
      <el-table-column label="出库类型" min-width="100">
        <template #default="{ row }">{{ OUTBOUND_TYPE_MAP[row.outbound_type] }}</template>
      </el-table-column>
      <el-table-column label="关联单位" min-width="140" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="partner-name-cell">
            {{ row.partner_name || '—' }}
            <el-tooltip v-if="row.partner_group_name" :content="row.partner_group_name" placement="top">
              <el-icon class="partner-group-icon"><OfficeBuilding /></el-icon>
            </el-tooltip>
          </span>
        </template>
      </el-table-column>
      <el-table-column label="关联客户" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ row.customer_name || '—' }}</template>
      </el-table-column>
      <el-table-column prop="total_qty" label="数量" min-width="70" align="center" />
      <el-table-column label="状态" min-width="90">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.operation_status)" size="small">{{ OPERATION_STATUS_MAP[row.operation_status] }}</el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="created_at" min-width="170" label="创建时间" :formatter="dateTimeColumnFormatter" />
      <el-table-column label="操作" min-width="168" align="center" fixed="right">
        <template #default="{ row }">
          <div class="row-actions">
            <el-tooltip content="详情" placement="top">
              <el-button type="primary" plain size="small" :icon="View" circle @click="showDetail(row)" />
            </el-tooltip>
            <el-tooltip v-if="canEdit(row)" content="编辑" placement="top">
              <el-button type="primary" plain size="small" :icon="Edit" circle @click="openEdit(row)" />
            </el-tooltip>
            <el-tooltip v-if="canSubmit(row)" content="提交审核" placement="top">
              <el-button type="warning" plain size="small" :icon="Promotion" circle @click="handleAction('submit', row)" />
            </el-tooltip>
            <el-tooltip v-if="canApprove(row)" content="确认通过" placement="top">
              <el-button type="primary" size="small" :icon="Select" circle @click="handleAction('approve', row)" />
            </el-tooltip>
            <el-tooltip v-if="canCancel(row)" content="取消" placement="top">
              <el-button type="info" plain size="small" :icon="Close" circle @click="handleAction('cancel', row)" />
            </el-tooltip>
            <el-tooltip v-if="canDelete(row)" content="删除" placement="top">
              <el-button type="danger" plain size="small" :icon="Delete" circle @click="handleAction('delete', row)" />
            </el-tooltip>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > 0"
      class="list-pagination"
      background
      layout="total, prev, pager, next"
      :total="total"
      :page-size="pageSize"
      :current-page="page"
      @current-change="handlePageChange"
    />
  </el-card>

  <!-- 新建/编辑出库 -->
  <el-drawer v-model="dialogVisible" :title="dialogTitle" size="60%" destroy-on-close>
    <div class="form-drawer-body">
    <el-form label-width="90px">
      <el-form-item label="出库类型" required>
        <el-select v-model="form.outbound_type">
          <el-option v-for="[key, label] in selectableOutboundTypeEntries()" :key="key" :label="label" :value="key" />
        </el-select>
      </el-form-item>
      <el-form-item label="关联单位" required>
        <el-select v-model="form.partner_id" filterable placeholder="选择往来单位" style="width:100%">
          <el-option
            v-for="p in partnerList"
            :key="p.id"
            :label="`${p.partner_group_name} - ${p.name}（${PARTNER_TYPE_MAP[p.partner_type]}）`"
            :value="p.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="选择客户" required>
        <el-select
          v-model="form.customer_name"
          filterable
          allow-create
          default-first-option
          placeholder="选择或输入客户名称"
          style="width:100%"
        >
          <el-option v-for="c in customerList" :key="c.id" :label="c.name" :value="c.name" />
        </el-select>
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="如有特殊备注请填写，如：淘宝店铺单号、重点客户等"/>
      </el-form-item>
    </el-form>

    <el-divider content-position="left">勾选可出库商品（在库状态）</el-divider>
    <el-form :inline="true" class="item-search" @submit.prevent="searchAvailableItems">
      <el-form-item class="sn-search-item">
        <template #label>
          <span class="sn-label-with-tip">
            SN号
            <el-tooltip content="支持同时检索多个SN号，一行一个。最大支持100个" placement="top">
              <el-icon class="sn-help-icon"><QuestionFilled /></el-icon>
            </el-tooltip>
          </span>
        </template>
        <el-input
          v-model="itemQuery.keyword"
          type="textarea"
          :rows="1"
          clearable
          placeholder="请输入检索的SN号"
        />
      </el-form-item>
      <el-form-item label="商品分类">
        <el-select
          v-model="itemQuery.category_id"
          clearable
          filterable
          placeholder="全部"
          style="width:140px"
          @change="onCategoryChange"
        >
          <el-option v-for="c in categoryList" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="商品 SKU">
        <el-select v-model="itemQuery.sku_id" clearable filterable placeholder="全部" style="width:180px">
          <el-option v-for="s in filteredSkuList" :key="s.id" :label="`${s.name}`" :value="s.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="库存属性">
        <el-select v-model="itemQuery.stock_condition" clearable placeholder="全部" style="width:130px">
          <el-option v-for="[key, label] in selectableStockConditionEntries()" :key="key" :label="label" :value="key" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="searchAvailableItems">查询</el-button>
        <el-button @click="resetItemQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <p v-if="selectedIds.length" class="selected-hint">已勾选 {{ selectedIds.length }} 件（跨页保留）</p>

    <el-table
      ref="itemTableRef"
      :data="availableItems"
      v-loading="itemsLoading"
      stripe border
      row-key="id"
      max-height="360"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="50" :reserve-selection="true" />
      <el-table-column prop="item_sn" label="Item SN" min-width="160" />
      <el-table-column prop="sku_name" label="商品名称" min-width="160" />
      <el-table-column label="属性" width="110">
        <template #default="{ row }">{{ STOCK_CONDITION_MAP[row.stock_condition] || row.stock_condition }}</template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="itemsTotal > 0"
      class="items-pagination"
      background
      layout="total, prev, pager, next"
      :total="itemsTotal"
      :page-size="itemsPageSize"
      :current-page="itemsPage"
      @current-change="handleItemsPageChange"
    />

    </div>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSave">保存（暂存）</el-button>
    </template>
  </el-drawer>

  <el-drawer
    v-model="drawerVisible"
    :title="drawerOrderNo"
    size="60%"
    destroy-on-close
  >
    <OutboundDetail
      v-if="drawerOrderNo"
      :order-id="drawerOrderNo"
      :is-panel="true"
      @deleted="onDetailDeleted"
    />
  </el-drawer>

</template>

<style scoped>
.form-drawer-body { padding-bottom: 8px; }
.list-search { margin-bottom: 4px; }
.list-search :deep(.el-form-item) { margin-bottom: 12px; }
.list-pagination { margin-top: 16px; justify-content: flex-end; }
.item-search { margin-bottom: 8px; }
.item-search :deep(.el-form-item) { margin-bottom: 8px; }
.sn-search-item { align-items: flex-start; }
.sn-search-item :deep(.el-form-item__label) { padding-top: 6px; }
.sn-label-with-tip { display: inline-flex; align-items: center; gap: 4px; }
.sn-help-icon { font-size: 14px; color: #909399; cursor: help; }
.sn-help-icon:hover { color: #409eff; }
.partner-name-cell { display: inline-flex; align-items: center; gap: 4px; }
.partner-group-icon { font-size: 14px; color: #909399; cursor: help; flex-shrink: 0; }
.partner-group-icon:hover { color: #409eff; }
.selected-hint { margin: 0 0 8px; font-size: 13px; color: var(--el-color-primary); }
.items-pagination { margin-top: 12px; justify-content: flex-end; }
.row-actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 2px;
  align-items: center;
  justify-content: center;
}
.row-actions :deep(.el-tooltip__trigger) {
  display: inline-flex;
}
.row-actions .el-button {
  margin: 0;
}
</style>
