<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { Delete, View, Promotion, Select, Close, Edit } from '@element-plus/icons-vue'
import InboundDetail from '@/views/InboundDetail.vue'
import {
  listInboundOrders, createInboundOrder, updateInboundOrder, getInboundOrder, submitInboundOrder,
  approveInboundOrder, cancelInboundOrder, deleteInboundOrder,
  getReturnableItems,
} from '@/api/inbound'
import { listSkus, listCategories } from '@/api/product'
import { listPartners } from '@/api/partner'
import { listOutboundOrders, getOutboundOrder } from '@/api/outbound'
import { INBOUND_MODE_MAP, STOCK_CONDITION_MAP, OPERATION_STATUS_MAP, PARTNER_TYPE_MAP, statusTagType, inboundModeLabel, selectableReturnConditionEntries, stockConditionFromOutboundType, outboundOptionLabel, stockConditionLabel } from '@/constants/enums'
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
  operation_status: '',
  inbound_mode: '',
  stock_condition: '',
  partner_id: null,
  sku_id: null,
  dateRange: [],
})

const inboundTypeOptions = computed(() => [
  {
    value: 'PROCUREMENT',
    label: INBOUND_MODE_MAP.PROCUREMENT,
    children: [{ value: 'NEW', label: STOCK_CONDITION_MAP.NEW }],
  },
  {
    value: 'NON_PROCUREMENT',
    label: INBOUND_MODE_MAP.NON_PROCUREMENT,
    children: selectableReturnConditionEntries().map(([value, label]) => ({ value, label })),
  },
])

// 级联选择映射回 inbound_mode / stock_condition
const inboundTypeCascade = computed({
  get() {
    const mode = query.value.inbound_mode
    if (!mode) return []
    return query.value.stock_condition ? [mode, query.value.stock_condition] : [mode]
  },
  set(val) {
    if (!val || val.length === 0) {
      query.value.inbound_mode = ''
      query.value.stock_condition = ''
      return
    }
    const [level1, level2] = val
    query.value.inbound_mode = level1
    query.value.stock_condition = level2 || ''
  },
})

const dialogVisible = ref(false)
const editingOrderId = ref(null)
const returnTableRef = ref(null)
const skuList = ref([])
const partnerList = ref([])
const allPartners = ref([])
const outboundOptions = ref([])
const outboundSearchLoading = ref(false)
const returnableItems = ref([])
const selectedReturnIds = ref([])
const loadingReturnable = ref(false)
const returnItemsPage = ref(1)
const returnItemsPageSize = ref(20)
const returnItemsTotal = ref(0)
const MAX_SN_KEYWORDS = 100
const returnItemQuery = ref({ category_id: null, sku_id: null, keyword: '' })
const categoryList = ref([])

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

const filteredReturnSkuList = computed(() => {
  if (!returnItemQuery.value.category_id) return skuList.value
  return skuList.value.filter(s => s.category_id === returnItemQuery.value.category_id)
})

const form = ref({
  inbound_mode: 'PROCUREMENT',
  stock_condition: 'NEW',
  partner_id: null,
  related_outbound_order_id: null,
  remark: '',
  lines: [{ sku_id: null, quantity: 1, unit_price: null, item_sns: '' }],
})

onMounted(() => { loadData(); loadSkus(); loadPartners(); loadCategories() })

const selectedOutboundOrder = computed(() =>
  outboundOptions.value.find(o => o.id === form.value.related_outbound_order_id),
)

const dialogTitle = computed(() => (editingOrderId.value ? '编辑入库单' : '新增入库单'))

async function searchOutbounds(keyword) {
  const query = keyword?.trim()
  if (!query) {
    outboundOptions.value = []
    return
  }
  outboundSearchLoading.value = true
  try {
    const res = await listOutboundOrders({
      page: 1,
      page_size: 20,
      operation_status: 'COMPLETED',
      order_no: query,
    })
    outboundOptions.value = res.data.items
  } finally {
    outboundSearchLoading.value = false
  }
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (query.value.order_no) params.order_no = query.value.order_no
    if (query.value.operation_status) params.operation_status = query.value.operation_status
    if (query.value.inbound_mode) params.inbound_mode = query.value.inbound_mode
    if (query.value.stock_condition) params.stock_condition = query.value.stock_condition
    if (query.value.partner_id) params.partner_id = query.value.partner_id
    if (query.value.sku_id) params.sku_id = query.value.sku_id
    if (query.value.dateRange?.length === 2) {
      params.start_time = `${query.value.dateRange[0]} 00:00:00`
      params.end_time = `${query.value.dateRange[1]} 23:59:59`
    }
    const res = await listInboundOrders(params)
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
    operation_status: '',
    inbound_mode: '',
    stock_condition: '',
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

async function loadCategories() {
  const res = await listCategories()
  categoryList.value = res.data
}

async function loadSkus() {
  const res = await listSkus({ page: 1, page_size: 200 })
  skuList.value = res.data.items
}

async function loadPartners() {
  const res = await listPartners({ page: 1, page_size: 500 })
  allPartners.value = res.data.items
  partnerList.value = res.data.items.filter(p => p.status === 1)
}

function onOutboundChange(outboundId) {
  if (!outboundId) {
    form.value.stock_condition = ''
    returnableItems.value = []
    selectedReturnIds.value = []
    returnItemsTotal.value = 0
    returnItemQuery.value = { category_id: null, sku_id: null, keyword: '' }
    returnItemsPage.value = 1
    return
  }
  const outbound = outboundOptions.value.find(o => o.id === outboundId)
  if (!outbound) return
  const condition = stockConditionFromOutboundType(outbound.outbound_type)
  if (!condition) {
    ElMessage.warning('无法识别该出库单类型对应的入库类型')
    form.value.related_outbound_order_id = null
    form.value.stock_condition = ''
    returnableItems.value = []
    selectedReturnIds.value = []
    returnItemsTotal.value = 0
    return
  }
  form.value.stock_condition = condition
  returnItemQuery.value = { category_id: null, sku_id: null, keyword: '' }
  returnItemsPage.value = 1
  loadReturnableItems()
}

async function restoreReturnSelection() {
  await nextTick()
  if (!returnTableRef.value || !selectedReturnIds.value.length) return
  returnableItems.value.forEach(row => {
    if (selectedReturnIds.value.includes(row.item_id)) {
      returnTableRef.value.toggleRowSelection(row, true)
    }
  })
}

async function loadReturnableItems() {
  if (!form.value.related_outbound_order_id || !form.value.stock_condition) {
    returnableItems.value = []
    selectedReturnIds.value = []
    returnItemsTotal.value = 0
    return
  }
  loadingReturnable.value = true
  const prevSelected = [...selectedReturnIds.value]
  try {
    const res = await getReturnableItems(
      form.value.related_outbound_order_id,
      form.value.stock_condition,
      {
        exclude_inbound_order_id: editingOrderId.value,
        page: returnItemsPage.value,
        page_size: returnItemsPageSize.value,
        keyword: returnItemQuery.value.keyword || undefined,
        sku_id: returnItemQuery.value.sku_id || undefined,
        category_id: returnItemQuery.value.category_id || undefined,
      },
    )
    returnableItems.value = res.data.items
    returnItemsTotal.value = res.data.total
    selectedReturnIds.value = prevSelected
    await nextTick()
    returnTableRef.value?.clearSelection()
    await restoreReturnSelection()
  } finally { loadingReturnable.value = false }
}

function onReturnCategoryChange() {
  if (returnItemQuery.value.sku_id && !filteredReturnSkuList.value.some(s => s.id === returnItemQuery.value.sku_id)) {
    returnItemQuery.value.sku_id = null
  }
}

function searchReturnableItems() {
  const tokenCount = countKeywordTokens(returnItemQuery.value.keyword)
  if (tokenCount > MAX_SN_KEYWORDS) {
    ElMessage.warning(`最多支持同时查询 ${MAX_SN_KEYWORDS} 个 SN`)
    return
  }
  returnItemsPage.value = 1
  loadReturnableItems()
}

function resetReturnItemQuery() {
  returnItemQuery.value = { category_id: null, sku_id: null, keyword: '' }
  searchReturnableItems()
}

function handleReturnItemsPageChange(page) {
  returnItemsPage.value = page
  loadReturnableItems()
}

function buildLinesFromOrder(order) {
  const items = order.items || []
  return (order.lines || []).map(line => ({
    sku_id: line.sku_id,
    quantity: line.quantity,
    unit_price: line.unit_price,
    item_sns: items.filter(i => i.line_id === line.id).map(i => i.item_sn).join('\n'),
  }))
}

function openCreate() {
  editingOrderId.value = null
  form.value = {
    inbound_mode: 'PROCUREMENT', stock_condition: 'NEW',
    partner_id: null, related_outbound_order_id: null, remark: '',
    lines: [{ sku_id: null, quantity: 1, unit_price: null, item_sns: '' }],
  }
  outboundOptions.value = []
  returnableItems.value = []
  selectedReturnIds.value = []
  returnItemsTotal.value = 0
  returnItemQuery.value = { category_id: null, sku_id: null, keyword: '' }
  returnItemsPage.value = 1
  dialogVisible.value = true
}

async function openEdit(row) {
  editingOrderId.value = row.id
  outboundOptions.value = []
  returnableItems.value = []
  selectedReturnIds.value = []
  returnItemsTotal.value = 0
  returnItemQuery.value = { category_id: null, sku_id: null, keyword: '' }
  returnItemsPage.value = 1
  dialogVisible.value = true
  try {
    const res = await getInboundOrder(row.id)
    const order = res.data
    form.value = {
      inbound_mode: order.inbound_mode,
      stock_condition: order.stock_condition,
      partner_id: order.partner_id,
      related_outbound_order_id: order.related_outbound_order_id,
      remark: order.remark || '',
      lines: order.inbound_mode === 'PROCUREMENT'
        ? buildLinesFromOrder(order)
        : [{ sku_id: null, quantity: 1, unit_price: null, item_sns: '' }],
    }
    if (order.inbound_mode === 'NON_PROCUREMENT' && order.related_outbound_order_id) {
      const obRes = await getOutboundOrder(order.related_outbound_order_id)
      outboundOptions.value = [obRes.data]
      selectedReturnIds.value = (order.items || []).map(i => i.item_id).filter(Boolean)
      await loadReturnableItems()
    }
  } catch {
    dialogVisible.value = false
    editingOrderId.value = null
  }
}

function onModeChange(mode) {
  if (editingOrderId.value) return
  returnableItems.value = []
  selectedReturnIds.value = []
  returnItemsTotal.value = 0
  returnItemQuery.value = { category_id: null, sku_id: null, keyword: '' }
  returnItemsPage.value = 1
  form.value.related_outbound_order_id = null
  outboundOptions.value = []
  if (mode === 'NON_PROCUREMENT') {
    form.value.stock_condition = ''
  } else {
    form.value.stock_condition = 'NEW'
  }
}

function addLine() {
  form.value.lines.push({ sku_id: null, quantity: 1, unit_price: null, item_sns: '' })
}

function removeLine(idx) {
  form.value.lines.splice(idx, 1)
}

function generateSns(skuId, quantity) {
  const now = new Date()
  const pad = (n, len = 2) => String(n).padStart(len, '0')
  const ts = `${String(now.getFullYear()).slice(2)}${pad(now.getMonth() + 1)}${pad(now.getDate())}${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`
  return Array.from({ length: quantity }, (_, i) => {
    const seq = String(i + 1).padStart(3, '0')
    return `${skuId}-${ts}-${seq}`
  }).join('\n')
}

function getLineSku(line) {
  return skuList.value.find(s => s.id === line.sku_id)
}

function isAutoSn(line) {
  return getLineSku(line)?.sn_mode === 'AUTO'
}

function onSkuChange(line) {
  const sku = getLineSku(line)
  if (sku?.sn_mode === 'AUTO') {
    line.item_sns = generateSns(line.sku_id, line.quantity)
  } else {
    line.item_sns = ''
  }
}

function onQuantityChange(line) {
  if (isAutoSn(line)) {
    line.item_sns = generateSns(line.sku_id, line.quantity)
  }
}

function handleReturnSelection(rows) {
  selectedReturnIds.value = rows.map(r => r.item_id)
}

function buildSavePayload() {
  if (form.value.inbound_mode === 'NON_PROCUREMENT') {
    if (!form.value.related_outbound_order_id) {
      ElMessage.warning('请选择关联出库单')
      return null
    }
    if (!form.value.stock_condition) {
      ElMessage.warning('无法匹配入库类型，请更换出库单')
      return null
    }
  } else if (!form.value.stock_condition) {
    ElMessage.warning('请选择入库类型')
    return null
  }
  if (!form.value.partner_id) {
    ElMessage.warning('请选择关联单位')
    return null
  }
  if (form.value.inbound_mode === 'PROCUREMENT') {
    for (let i = 0; i < form.value.lines.length; i++) {
      const line = form.value.lines[i]
      const label = `第 ${i + 1} 组`
      if (!line.sku_id) {
        ElMessage.warning(`${label}：请选择入库商品`)
        return null
      }
      if (line.unit_price == null || line.unit_price === '') {
        ElMessage.warning(`${label}：请填写商品单价`)
        return null
      }
      if (line.unit_price < 0 || line.unit_price > 9999999.99) {
        ElMessage.warning(`${label}：商品单价需在 0 ~ 9,999,999.99 元之间`)
        return null
      }
      const sku = getLineSku(line)
      const sns = line.item_sns ? line.item_sns.split('\n').map(s => s.trim()).filter(Boolean) : []
      if (sku?.sn_mode !== 'AUTO') {
        if (sns.length === 0) {
          ElMessage.warning(`${label}：该商品需要手动输入序列号，请填写`)
          return null
        }
        if (sns.length !== line.quantity) {
          ElMessage.warning(`${label}：填写的序列号数量（${sns.length}个）与入库数量（${line.quantity}个）不一致`)
          return null
        }
      } else if (sns.length !== line.quantity) {
        ElMessage.warning(`${label}：序列号数量（${sns.length}个）与入库数量（${line.quantity}个）不一致`)
        return null
      }
    }
  }
  const payload = {
    partner_id: form.value.partner_id,
    stock_condition: form.value.stock_condition,
    remark: form.value.remark || null,
  }
  if (form.value.inbound_mode === 'PROCUREMENT') {
    payload.lines = form.value.lines.map(l => ({
      sku_id: l.sku_id,
      quantity: l.quantity,
      unit_price: l.unit_price ?? null,
      item_sns: l.item_sns ? l.item_sns.split('\n').map(s => s.trim()).filter(Boolean) : null,
    }))
  } else {
    if (!selectedReturnIds.value.length) {
      ElMessage.warning('请勾选需要退货的商品')
      return null
    }
    payload.related_outbound_order_id = form.value.related_outbound_order_id
    payload.return_item_ids = selectedReturnIds.value
  }
  if (!editingOrderId.value) {
    payload.inbound_mode = form.value.inbound_mode
  }
  return payload
}

async function handleSave() {
  const payload = buildSavePayload()
  if (!payload) return
  if (editingOrderId.value) {
    await updateInboundOrder(editingOrderId.value, payload)
    ElMessage.success('入库单已更新')
  } else {
    await createInboundOrder(payload)
    ElMessage.success('入库单创建成功')
  }
  dialogVisible.value = false
  editingOrderId.value = null
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
  const actions = {
    submit: { fn: submitInboundOrder, msg: '确认提交审核？' },
    approve: { fn: approveInboundOrder, msg: '确认通过该入库单？' },
    cancel: { fn: cancelInboundOrder, msg: '确认取消？' },
    delete: { fn: deleteInboundOrder, msg: '确认删除？' },
  }
  await ElMessageBox.confirm(actions[action].msg, '提示', { type: 'warning' })
  await actions[action].fn(row.id)
  ElMessage.success('操作成功')
  loadData()
}

function canSubmit(row) { return row.operation_status === 'INITIATED' && !row.submitted_at }
function canEdit(row) { return row.operation_status === 'INITIATED' && !row.submitted_at }
function canApprove(row) { return row.operation_status === 'INITIATED' && row.submitted_at }
function canCancel(row) { return ['INITIATED'].includes(row.operation_status) && row.submitted_at }
function canDelete(row) { return row.operation_status === 'INITIATED' && !row.submitted_at }
</script>

<template>
  <el-card shadow="never">
    <el-form :inline="true" class="list-search" @submit.prevent="searchOrders">
      <el-form-item label="入库单号">
        <el-input v-model="query.order_no" clearable placeholder="单号模糊搜索" style="width:160px" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="query.operation_status" clearable placeholder="全部" style="width:130px">
          <el-option v-for="(label, key) in OPERATION_STATUS_MAP" :key="key" :label="label" :value="key" />
        </el-select>
      </el-form-item>
      <el-form-item label="入库类型">
        <el-cascader
          v-model="inboundTypeCascade"
          :options="inboundTypeOptions"
          :props="{ checkStrictly: true, expandTrigger: 'hover' }"
          clearable
          placeholder="全部"
          style="width:150px"
        />
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
        <el-button type="primary" plain @click="openCreate">新增入库</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="orders" v-loading="loading" stripe>
      <el-table-column label="入库单号" min-width="120">
        <template #default="{ row }">
          <el-button type="primary" link @click="showDetail(row)">{{ row.order_no }}</el-button>
        </template>
      </el-table-column>
      <!-- <el-table-column label="入库方式" width="110">
        <template #default="{ row }">{{ INBOUND_MODE_MAP[row.inbound_mode] }}</template>
      </el-table-column> -->
      <el-table-column label="入库类型" min-width="120">
        <template #default="{ row }">{{ inboundModeLabel(row.inbound_mode, row.stock_condition) }}</template>
      </el-table-column>
      <el-table-column label="单位组" min-width="120">
        <template #default="{ row }">{{ row.partner_group_name }}</template>
      </el-table-column>
      <el-table-column label="关联单位" min-width="120">
        <template #default="{ row }">{{ row.partner_name }}</template>
      </el-table-column>
      <el-table-column prop="total_qty" label="数量" min-width="70" align="center" />
      <el-table-column label="状态" min-width="90">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.operation_status)" size="small">{{ OPERATION_STATUS_MAP[row.operation_status] }}</el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="created_at" label="创建时间" min-width="120" :formatter="dateTimeColumnFormatter" />
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

  <!-- 新建/编辑入库 -->
  <el-drawer v-model="dialogVisible" :title="dialogTitle" size="60%" destroy-on-close>
    <el-form label-width="110px" class="form-drawer-body">
      <el-form-item label="入库方式">
        <el-radio-group v-model="form.inbound_mode" :disabled="!!editingOrderId" @change="onModeChange">
          <el-radio value="PROCUREMENT">采购入库</el-radio>
          <el-radio value="NON_PROCUREMENT">其他入库（退货/归还）</el-radio>
        </el-radio-group>
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
      <el-form-item v-if="form.inbound_mode === 'NON_PROCUREMENT'" label="关联出库单" required>
        <el-select
          v-model="form.related_outbound_order_id"
          filterable
          remote
          reserve-keyword
          clearable
          :remote-method="searchOutbounds"
          :loading="outboundSearchLoading"
          placeholder="输入出库单号模糊搜索"
          style="width:100%"
          @change="onOutboundChange"
        >
          <el-option
            v-for="o in outboundOptions"
            :key="o.id"
            :label="outboundOptionLabel(o)"
            :value="o.id"
          />
        </el-select>
        <p v-if="!outboundSearchLoading && outboundOptions.length === 0" class="hint">
          输入出库单号（如 JOUT-）搜索已完成的出库单
        </p>
      </el-form-item>
      <el-form-item label="入库类型" required>
        <el-select
          v-if="form.inbound_mode === 'PROCUREMENT'"
          v-model="form.stock_condition"
          placeholder="请选择入库类型"
          style="width:100%"
        >
          <el-option label="正常" value="NEW" />
        </el-select>
        <el-input
          v-else
          :model-value="form.stock_condition ? STOCK_CONDITION_MAP[form.stock_condition] : ''"
          disabled
          placeholder="选择关联出库单后自动匹配"
          style="width:100%"
        />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="2" />
      </el-form-item>

      <!-- 采购入库 -->
      <template v-if="form.inbound_mode === 'PROCUREMENT'">
        <el-divider>入库商品</el-divider>
        <div v-for="(line, idx) in form.lines" :key="idx" class="line-item">
          <el-select v-model="line.sku_id" placeholder="选择入库商品" style="width:150px" @change="onSkuChange(line)">
            <el-option v-for="s in skuList" :key="s.id" :label="`${s.name}`" :value="s.id" />
          </el-select>
          <el-input-number v-model="line.quantity" :min="1" :max="1000" style="width:120px; margin:0 8px" @change="onQuantityChange(line)" />
          <div class="price-input">
            <span class="price-symbol">¥</span>
            <el-input-number v-model="line.unit_price" :min="0" :max="9999999.99" :precision="2" :step="1" :controls="false" placeholder="99.00" />
          </div>
          <div style="flex:1; position:relative">
            <el-input
              v-model="line.item_sns"
              type="textarea"
              :rows="isAutoSn(line) ? Math.min(Math.max(2, line.quantity), 10) : 1"
              :maxrows="10"
              autosize
              :readonly="isAutoSn(line)"
              :placeholder="isAutoSn(line) ? '序列号由系统自动生成' : '请输入商品SN序列号（一行一个）'"
              :class="{ 'auto-sn-input': isAutoSn(line) }"
              style="max-height: none"
            />
            <el-tag v-if="isAutoSn(line)" size="small" type="info" class="auto-tag">自动生成</el-tag>
          </div>
          <el-button v-if="form.lines.length > 1" type="danger" link :icon="Delete" circle @click="removeLine(idx)" />
        </div>
        <el-button type="primary" link @click="addLine">+ 新增一组商品</el-button>
      </template>

      <!-- 非采购入库：勾选退货商品 -->
      <template v-if="form.inbound_mode === 'NON_PROCUREMENT' && form.related_outbound_order_id">
        <el-divider>勾选退货商品（可部分退货）</el-divider>
        <p class="hint">
          出库单共 {{ selectedOutboundOrder?.total_qty ?? '—' }} 件，可退货 {{ returnItemsTotal }} 件
        </p>
        <el-form :inline="true" class="return-item-search" @submit.prevent="searchReturnableItems">
          <el-form-item label="SN号" class="sn-search-item">
            <el-input
              v-model="returnItemQuery.keyword"
              type="textarea"
              :rows="3"
              clearable
              placeholder="每行一个 SN，最多 100 个；单行时可搜商品名称"
              style="width:360px"
            />
          </el-form-item>
          <el-form-item label="商品分类">
            <el-select
              v-model="returnItemQuery.category_id"
              clearable
              filterable
              placeholder="全部"
              style="width:140px"
              @change="onReturnCategoryChange"
            >
              <el-option v-for="c in categoryList" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="商品 SKU">
            <el-select v-model="returnItemQuery.sku_id" clearable filterable placeholder="全部" style="width:180px">
              <el-option v-for="s in filteredReturnSkuList" :key="s.id" :label="s.name" :value="s.id" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="searchReturnableItems">查询</el-button>
            <el-button @click="resetReturnItemQuery">重置</el-button>
          </el-form-item>
        </el-form>
        <el-table
          ref="returnTableRef"
          :data="returnableItems"
          v-loading="loadingReturnable"
          stripe border
          max-height="280"
          row-key="item_id"
          @selection-change="handleReturnSelection"
        >
          <el-table-column type="selection" width="50" :reserve-selection="true" />
          <el-table-column prop="item_sn" label="Item SN" min-width="160" />
          <el-table-column prop="sku_name" label="商品名称" min-width="160" />
          <el-table-column label="当前状态" width="120">
            <template #default="{ row }">
              {{ stockConditionLabel(row.stock_status, row.stock_condition).stock_condition_name }}
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-if="returnItemsTotal > 0"
          class="return-items-pagination"
          background
          layout="total, prev, pager, next"
          :total="returnItemsTotal"
          :page-size="returnItemsPageSize"
          :current-page="returnItemsPage"
          @current-change="handleReturnItemsPageChange"
        />
        <p v-if="!loadingReturnable && returnItemsTotal === 0" class="hint warn">
          该出库单没有可退货的商品（可能已全部退回）
        </p>
        <p v-if="selectedReturnIds.length" class="hint selected-hint">
          已勾选 {{ selectedReturnIds.length }} 件（跨页保留）
        </p>
      </template>
    </el-form>
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
    <InboundDetail
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
.line-item { display: flex; gap: 8px; align-items: flex-start; margin-bottom: 12px; }
.price-input { position: relative; width: 120px; }
.price-symbol { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); z-index: 1; color: #909399; font-size: 13px; pointer-events: none; }
.price-input :deep(.el-input-number) { width: 100%; }
.price-input :deep(.el-input__inner) { padding-left: 22px; text-align: left; }
.line-item :deep(textarea) { max-height: 220px; overflow-y: auto !important; resize: vertical; }
.auto-tag { position: absolute; top: 4px; right: 6px; pointer-events: none; z-index: 1; }
.auto-sn-input :deep(textarea) { background-color: #f5f7fa; color: #606266; cursor: not-allowed; font-size: 12px; line-height: 1.6; max-height: 220px; overflow-y: auto !important; resize: none; }
.hint { font-size: 13px; color: #909399; margin: 0 0 8px; }
.hint.warn { color: #e6a23c; }
.hint.selected-hint { color: var(--el-color-primary); }
.return-item-search { margin-bottom: 8px; }
.return-item-search :deep(.el-form-item) { margin-bottom: 8px; }
.sn-search-item { align-items: flex-start; }
.sn-search-item :deep(.el-form-item__label) { padding-top: 6px; }
.return-items-pagination { margin: 12px 0; justify-content: flex-end; }
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
