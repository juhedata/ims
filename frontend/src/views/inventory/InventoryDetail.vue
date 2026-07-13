<script setup>
import { computed, onMounted, ref } from 'vue'
import InboundDetail from '@/views/InboundDetail.vue'
import OutboundDetail from '@/views/OutboundDetail.vue'
import { listItems, getItemHistory, exportItems, completeOfflineSale } from '@/api/inventory'
import { listSkus, listCategories } from '@/api/product'
import { STOCK_STATUS_MAP, OPERATION_STATUS_MAP, statusTagType, stockConditionLabel, eventTypeLabel, selectableStockConditionEntries } from '@/constants/enums'
import { dateTimeColumnFormatter } from '@/utils/datetime'
import { Clock, Download, OfficeBuilding } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const exportLoading = ref(false)

const drawerVisible = ref(false)
const drawerOrderNo = ref('')
const drawerType = ref('')
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(15)
const query = ref({
  keyword: '',
  category_id: null,
  sku_id: null,
  stock_status: '',
  stock_condition: '',
  operation_status: '',
  last_order_no: '',
})

const skuList = ref([])
const categoryList = ref([])
const historyVisible = ref(false)
const historyList = ref([])
const historySn = ref('')

const filteredSkuList = computed(() => {
  if (!query.value.category_id) return skuList.value
  return skuList.value.filter(s => s.category_id === query.value.category_id)
})

const stockOptions = computed(() => [
  {
    value: 'IN_STOCK',
    label: STOCK_STATUS_MAP.IN_STOCK,
    children: selectableStockConditionEntries().map(([value, label]) => ({ value, label })),
  },
  {
    value: 'OUT',
    label: '出库',
    children: Object.entries(STOCK_STATUS_MAP)
      .filter(([key]) => key !== 'IN_STOCK')
      .map(([value, label]) => ({ value, label })),
  },
])

const stockCascade = computed({
  get() {
    const s = query.value.stock_status
    if (!s) return []
    if (s === 'IN_STOCK') return query.value.stock_condition ? ['IN_STOCK', query.value.stock_condition] : ['IN_STOCK']
    if (s === 'OUT') return ['OUT']
    return ['OUT', s]
  },
  set(val) {
    if (!val || val.length === 0) {
      query.value.stock_status = ''
      query.value.stock_condition = ''
      return
    }
    const [level1, level2] = val
    if (level1 === 'IN_STOCK') {
      query.value.stock_status = 'IN_STOCK'
      query.value.stock_condition = level2 || ''
    } else {
      query.value.stock_status = level2 || 'OUT'
      query.value.stock_condition = ''
    }
  },
})

onMounted(() => {
  loadSkus()
  loadCategories()
  loadData()
})

async function loadSkus() {
  const res = await listSkus({ page: 1, page_size: 500 })
  skuList.value = res.data.items
}

async function loadCategories() {
  const res = await listCategories()
  categoryList.value = res.data
}

function buildFilterParams() {
  const params = {}
  if (query.value.keyword) params.keyword = query.value.keyword
  if (query.value.category_id) params.category_id = query.value.category_id
  if (query.value.sku_id) params.sku_id = query.value.sku_id
  if (query.value.stock_status) params.stock_status = query.value.stock_status
  if (query.value.stock_condition) params.stock_condition = query.value.stock_condition
  if (query.value.operation_status) params.operation_status = query.value.operation_status
  if (query.value.last_order_no) params.last_order_no = query.value.last_order_no
  return params
}

async function loadData() {
  loading.value = true
  try {
    const params = { ...buildFilterParams(), page: page.value, page_size: pageSize.value }
    const res = await listItems(params)
    items.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function handleExport() {
  exportLoading.value = true
  try {
    const blob = await exportItems(buildFilterParams())
    const d = new Date()
    const dateStr = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `IMS-实时库存-${dateStr}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } finally {
    exportLoading.value = false
  }
}

function onCategoryChange() {
  if (query.value.sku_id && !filteredSkuList.value.some(s => s.id === query.value.sku_id)) {
    query.value.sku_id = null
  }
}

function handleSearch() {
  page.value = 1
  loadData()
}

function resetQuery() {
  query.value = {
    keyword: '',
    category_id: null,
    sku_id: null,
    stock_status: '',
    stock_condition: '',
    operation_status: '',
    last_order_no: '',
  }
  handleSearch()
}

function handlePageChange(p) {
  page.value = p
  loadData()
}

function openOrderDrawer(orderNo) {
  if (!orderNo) return
  drawerOrderNo.value = orderNo
  if (orderNo.startsWith('JIN-')) drawerType.value = 'inbound'
  else if (orderNo.startsWith('JOUT-')) drawerType.value = 'outbound'
  else return
  drawerVisible.value = true
}

async function showHistory(row) {
  historySn.value = row.item_sn
  const res = await getItemHistory(row.item_sn)
  historyList.value = res.data
  historyVisible.value = true
}

async function handleCompleteOfflineSale(row) {
  try {
    await ElMessageBox.confirm(
      `确认单品 [${row.item_sn}] 线下销售已完成？状态将变为「售出-线下」。`,
      '确认线下成交',
      { type: 'warning' },
    )
    await completeOfflineSale(row.item_sn)
    ElMessage.success('已确认线下销售完成')
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.response?.data?.detail || e?.message || '操作失败')
  }
}
</script>

<template>
  <el-form :inline="true" class="list-search" @submit.prevent="handleSearch">
    <el-form-item label="SN号">
      <el-input v-model="query.keyword" clearable placeholder="商品SN号" />
    </el-form-item>
    <el-form-item label="商品分类">
      <el-select
        v-model="query.category_id"
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
      <el-select v-model="query.sku_id" clearable filterable placeholder="全部" style="width:180px">
        <el-option v-for="s in filteredSkuList" :key="s.id" :label="`${s.name}`" :value="s.id" />
      </el-select>
    </el-form-item>
    <el-form-item label="库存状态">
      <el-cascader
        v-model="stockCascade"
        :options="stockOptions"
        :props="{ checkStrictly: true, expandTrigger: 'hover' }"
        clearable
        placeholder="全部"
        style="width:150px"
      />
    </el-form-item>
    <el-form-item label="操作状态">
      <el-select v-model="query.operation_status" clearable placeholder="全部" style="width:130px">
        <el-option v-for="(label, key) in OPERATION_STATUS_MAP" :key="key" :label="label" :value="key" />
      </el-select>
    </el-form-item>
    <el-form-item label="关联单号">
      <el-input v-model="query.last_order_no" clearable placeholder="单号模糊搜索" style="width:150px" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="handleSearch">查询</el-button>
      <el-button @click="resetQuery">重置</el-button>
      <el-button type="success" :icon="Download" :loading="exportLoading" @click="handleExport">导出库存</el-button>
    </el-form-item>
  </el-form>

  <el-table :data="items" v-loading="loading" stripe>
    <el-table-column prop="item_sn" label="商品SN号" min-width="160" show-overflow-tooltip />
    <el-table-column prop="sku_name" label="商品名称" min-width="140" show-overflow-tooltip />
    <el-table-column label="采购单价" min-width="100" align="right">
      <template #default="{ row }">{{ row.unit_price != null ? `¥${Number(row.unit_price).toFixed(2)}` : '-' }}</template>
    </el-table-column>
    <el-table-column label="库存状态" min-width="100" align="center">
      <template #default="{ row }">
        <el-tag :type="statusTagType(stockConditionLabel(row.stock_status, row.stock_condition).class_type)" size="small">{{ stockConditionLabel(row.stock_status, row.stock_condition).stock_status_name }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="库存属性" min-width="100" align="center">
      <template #default="{ row }"><el-tag size="small">{{ stockConditionLabel(row.stock_status, row.stock_condition).stock_condition_name }}</el-tag></template>
    </el-table-column>
    <el-table-column label="关联单号" min-width="140" show-overflow-tooltip>
      <template #default="{ row }">
        <el-button v-if="row.last_order_no" type="primary" link @click="openOrderDrawer(row.last_order_no)">
          {{ row.last_order_no }}
        </el-button>
        <span v-else>-</span>
      </template>
    </el-table-column>
    <el-table-column label="关联单位" min-width="110" show-overflow-tooltip>
      <template #default="{ row }">
        <span v-if="row.stock_status !== 'IN_STOCK'" class="partner-name-cell">
          {{ row.partner_name || '—' }}
          <el-tooltip v-if="row.partner_group_name" :content="row.partner_group_name" placement="top">
            <el-icon class="partner-group-icon"><OfficeBuilding /></el-icon>
          </el-tooltip>
        </span>
      </template>
    </el-table-column>
    <el-table-column label="关联客户" min-width="110" show-overflow-tooltip>
      <template #default="{ row }">
        <span v-if="row.stock_status !== 'IN_STOCK' && row.last_order_no?.startsWith('JOUT-')">
          {{ row.customer_name || '—' }}
        </span>
      </template>
    </el-table-column>
    <el-table-column label="操作状态" min-width="100" align="center">
      <template #default="{ row }">
        <el-tag :type="statusTagType(row.operation_status)" size="small">{{ OPERATION_STATUS_MAP[row.operation_status] || row.operation_status }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="操作" min-width="120" fixed="right" align="center">
      <template #default="{ row }">
        <el-button
          v-if="row.stock_status === 'PRESOLD'"
          type="success"
          link
          size="small"
          @click="handleCompleteOfflineSale(row)"
        >确认成交</el-button>
        <el-tooltip content="变动轨迹" placement="top">
          <el-button type="primary" link :icon="Clock" @click="showHistory(row)" />
        </el-tooltip>
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

  <el-drawer
    v-model="drawerVisible"
    :title="drawerOrderNo"
    size="60%"
    destroy-on-close
  >
    <InboundDetail
      v-if="drawerType === 'inbound'"
      :order-id="drawerOrderNo"
      :is-panel="true"
      @deleted="drawerVisible = false"
    />
    <OutboundDetail
      v-if="drawerType === 'outbound'"
      :order-id="drawerOrderNo"
      :is-panel="true"
      @deleted="drawerVisible = false"
    />
  </el-drawer>

  <el-dialog v-model="historyVisible" :title="`变动轨迹 - ${historySn}`">
    <el-table :data="historyList" stripe border size="small">
      <el-table-column prop="event_type" label="事件">
        <template #default="{ row }">
          <el-tag :type="statusTagType(eventTypeLabel(row.event_type).event_type_class)" size="small">{{ eventTypeLabel(row.event_type).event_type_name }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="order_no" label="关联单号" width="160" />
      <el-table-column prop="partner_group_name" label="单位组" min-width="120" />
      <el-table-column prop="partner_name" label="单位名称" min-width="120" />
      <el-table-column label="库存变更" min-width="160">
        <template #default="{ row }">{{ stockConditionLabel(row.from_stock_status, row.from_stock_condition).stock_condition_name }} → {{ stockConditionLabel(row.to_stock_status, row.to_stock_condition).stock_condition_name }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="170" :formatter="dateTimeColumnFormatter" />
    </el-table>
  </el-dialog>
</template>

<style scoped>
.list-search { margin-bottom: 4px; }
.list-search :deep(.el-form-item) { margin-bottom: 12px; }
.list-pagination { margin-top: 16px; justify-content: flex-end; }
.partner-name-cell { display: inline-flex; align-items: center; gap: 4px; }
.partner-group-icon { font-size: 14px; color: #909399; cursor: help; flex-shrink: 0; }
.partner-group-icon:hover { color: #409eff; }
</style>
