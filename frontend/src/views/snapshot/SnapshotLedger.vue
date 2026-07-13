<script setup>
import { computed, onMounted, ref } from 'vue'
import { listDailyLedger, exportDailyLedger } from '@/api/snapshot'
import { listSkus } from '@/api/product'
import {
  ledgerInboundNormalQty,
  ledgerInboundOtherQty,
  ledgerOutboundSoldQty,
  ledgerOutboundSoldOfflineQty,
  ledgerOutboundPresoldQty,
  ledgerOutboundGiftedQty,
  ledgerOutboundOtherQty,
  OTHER_INBOUND_TOOLTIP,
  OTHER_OUTBOUND_TOOLTIP,
  buildLedgerInboundDetailRows,
  buildLedgerOutboundDetailRows,
  otherInboundBreakdownLines,
  otherOutboundBreakdownLines,
} from '@/utils/ledgerDisplay'
import { formatAmount, initDefaultDateRange, isSnapshotDateDisabled, ledgerQtyCellClass } from '@/utils/snapshotLedger'
import { Download, QuestionFilled, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const ledgerLoading = ref(false)
const ledgerExportLoading = ref(false)
const ledgerQuery = ref({ dateRange: [], sku_id: null })
const ledgerItems = ref([])
const skuList = ref([])

const ledgerDetailVisible = ref(false)
const ledgerDetailRow = ref(null)

const ledgerDetailTitle = computed(() => {
  const row = ledgerDetailRow.value
  if (!row) return 'SKU 日流水明细'
  return `SKU 日流水明细 · ${row.snapshot_date} · ${row.sku_name}`
})

const ledgerInboundDetailRows = computed(() => (
  ledgerDetailRow.value
    ? buildLedgerInboundDetailRows(ledgerDetailRow.value.inbound_by_type)
    : []
))

const ledgerOutboundDetailRows = computed(() => (
  ledgerDetailRow.value
    ? buildLedgerOutboundDetailRows(ledgerDetailRow.value.outbound_by_type)
    : []
))

onMounted(async () => {
  initDefaultDateRange(ledgerQuery)
  await loadSkus()
  loadLedger()
})

async function loadSkus() {
  const res = await listSkus({ page: 1, page_size: 500 })
  skuList.value = res.data.items
}

function buildLedgerParams() {
  const params = {
    date_from: ledgerQuery.value.dateRange[0],
    date_to: ledgerQuery.value.dateRange[1],
  }
  if (ledgerQuery.value.sku_id) params.sku_id = ledgerQuery.value.sku_id
  return params
}

async function loadLedger() {
  if (ledgerQuery.value.dateRange?.length !== 2) {
    ledgerItems.value = []
    return
  }
  ledgerLoading.value = true
  try {
    const res = await listDailyLedger(buildLedgerParams())
    ledgerItems.value = res.data
  } finally {
    ledgerLoading.value = false
  }
}

function handleLedgerSearch() {
  loadLedger()
}

async function handleLedgerExport() {
  if (ledgerQuery.value.dateRange?.length !== 2) {
    ElMessage.warning('请先选择日期区间')
    return
  }
  ledgerExportLoading.value = true
  try {
    const params = buildLedgerParams()
    const blob = await exportDailyLedger(params)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `库存日流水_${params.date_from}_${params.date_to}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } finally {
    ledgerExportLoading.value = false
  }
}

function openLedgerDetail(row) {
  ledgerDetailRow.value = row
  ledgerDetailVisible.value = true
}
</script>

<template>
<el-form :inline="true" class="list-search" @submit.prevent="handleLedgerSearch">
  <el-form-item label="日期区间">
    <el-date-picker
      v-model="ledgerQuery.dateRange"
      type="daterange"
      range-separator="至"
      start-placeholder="开始日期"
      end-placeholder="结束日期"
      value-format="YYYY-MM-DD"
      :disabled-date="isSnapshotDateDisabled"
      style="width:260px"
    />
  </el-form-item>
  <el-form-item label="商品 SKU">
    <el-select v-model="ledgerQuery.sku_id" clearable filterable placeholder="全部" style="width:180px">
      <el-option v-for="s in skuList" :key="s.id" :label="s.name" :value="s.id" />
    </el-select>
  </el-form-item>
  <el-form-item>
    <el-button type="primary" @click="handleLedgerSearch">查询</el-button>
    <el-button
      type="success"
      :icon="Download"
      :loading="ledgerExportLoading"
      :disabled="ledgerQuery.dateRange?.length !== 2"
      @click="handleLedgerExport"
    >
      导出流水
    </el-button>
  </el-form-item>
</el-form>

<p class="hint">期初在库 = 上一日期末在库；期末在库口径为在库且操作已完成。当日入库分为正常/其他入库，当日出库分为售出-线上、售出-线下、准售出、赠送、其他出库。</p>

<el-table
  :data="ledgerItems"
  v-loading="ledgerLoading"
  stripe
  class="ledger-type-table"
  :cell-class-name="ledgerQtyCellClass"
>
  <el-table-column prop="snapshot_date" label="日期" min-width="120" fixed="left" />
  <el-table-column prop="sku_name" label="SKU" min-width="160" show-overflow-tooltip fixed="left" />
  <el-table-column label="期初在库" min-width="100" align="center">
    <template #default="{ row }">{{ row.opening_in_stock_qty ?? '—' }}</template>
  </el-table-column>
  <el-table-column label="当日入库" align="center">
    <el-table-column label="正常" min-width="88" align="center">
      <template #default="{ row }">{{ ledgerInboundNormalQty(row.inbound_by_type) }}</template>
    </el-table-column>
    <el-table-column label="其他入库" min-width="110" align="center">
      <template #header>
        <span class="col-header-with-tip">
          其他入库
          <el-tooltip :content="OTHER_INBOUND_TOOLTIP" placement="top">
            <el-icon class="col-help-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </span>
      </template>
      <template #default="{ row }">
        <el-tooltip placement="top" popper-class="ledger-qty-tooltip">
          <template #content>
            <template v-if="otherInboundBreakdownLines(row.inbound_by_type).length">
              <div
                v-for="item in otherInboundBreakdownLines(row.inbound_by_type)"
                :key="item.label"
                class="qty-breakdown-line"
              >
                {{ item.label }}：{{ item.qty }}
              </div>
            </template>
            <span v-else>暂无分项</span>
          </template>
          <span
            class="qty-hover-cell"
            :class="{ 'has-detail': otherInboundBreakdownLines(row.inbound_by_type).length }"
          >
            {{ ledgerInboundOtherQty(row.inbound_by_type) }}
          </span>
        </el-tooltip>
      </template>
    </el-table-column>
  </el-table-column>
  <el-table-column label="当日出库" align="center">
    <el-table-column label="售出-线上" min-width="96" align="center">
      <template #default="{ row }">{{ ledgerOutboundSoldQty(row.outbound_by_type) }}</template>
    </el-table-column>
    <el-table-column label="售出-线下" min-width="96" align="center">
      <template #default="{ row }">{{ ledgerOutboundSoldOfflineQty(row.outbound_by_type) }}</template>
    </el-table-column>
    <el-table-column label="准售出" min-width="88" align="center">
      <template #default="{ row }">{{ ledgerOutboundPresoldQty(row.outbound_by_type) }}</template>
    </el-table-column>
    <el-table-column label="赠送" min-width="72" align="center">
      <template #default="{ row }">{{ ledgerOutboundGiftedQty(row.outbound_by_type) }}</template>
    </el-table-column>
    <el-table-column label="其他出库" min-width="110" align="center">
      <template #header>
        <span class="col-header-with-tip">
          其他出库
          <el-tooltip :content="OTHER_OUTBOUND_TOOLTIP" placement="top">
            <el-icon class="col-help-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </span>
      </template>
      <template #default="{ row }">
        <el-tooltip placement="top" popper-class="ledger-qty-tooltip">
          <template #content>
            <template v-if="otherOutboundBreakdownLines(row.outbound_by_type).length">
              <div
                v-for="item in otherOutboundBreakdownLines(row.outbound_by_type)"
                :key="item.label"
                class="qty-breakdown-line"
              >
                {{ item.label }}：{{ item.qty }}
              </div>
            </template>
            <span v-else>暂无分项</span>
          </template>
          <span
            class="qty-hover-cell"
            :class="{ 'has-detail': otherOutboundBreakdownLines(row.outbound_by_type).length }"
          >
            {{ ledgerOutboundOtherQty(row.outbound_by_type) }}
          </span>
        </el-tooltip>
      </template>
    </el-table-column>
  </el-table-column>
  <el-table-column prop="closing_in_stock_qty" label="期末在库" min-width="100" align="center" />
  <el-table-column label="期末资产金额" min-width="130" align="right">
    <template #default="{ row }">{{ formatAmount(row.closing_asset_amount) }}</template>
  </el-table-column>
  <el-table-column label="操作" min-width="70" fixed="right" align="center">
    <template #default="{ row }">
      <el-tooltip content="查看明细" placement="top">
        <el-button type="primary" link :icon="View" @click="openLedgerDetail(row)" />
      </el-tooltip>
    </template>
  </el-table-column>
</el-table>

  <el-drawer
    v-model="ledgerDetailVisible"
    :title="ledgerDetailTitle"
    size="60%"
    destroy-on-close
  >
    <template v-if="ledgerDetailRow">
      <el-descriptions :column="2" border size="small" class="ledger-detail-summary">
        <el-descriptions-item label="业务日期">{{ ledgerDetailRow.snapshot_date }}</el-descriptions-item>
        <el-descriptions-item label="SKU">{{ ledgerDetailRow.sku_name }}</el-descriptions-item>
        <el-descriptions-item label="期初在库">{{ ledgerDetailRow.opening_in_stock_qty ?? '—' }}</el-descriptions-item>
        <el-descriptions-item label="期末在库">{{ ledgerDetailRow.closing_in_stock_qty }}</el-descriptions-item>
        <el-descriptions-item label="当日入库合计">{{ ledgerDetailRow.inbound_qty }}</el-descriptions-item>
        <el-descriptions-item label="当日出库合计">{{ ledgerDetailRow.outbound_qty }}</el-descriptions-item>
        <el-descriptions-item label="期末资产金额" :span="2">
          {{ formatAmount(ledgerDetailRow.closing_asset_amount) }}
        </el-descriptions-item>
      </el-descriptions>

      <p class="ledger-detail-section-title">入库明细</p>
      <el-table :data="ledgerInboundDetailRows" stripe border size="small" empty-text="暂无数据">
        <el-table-column prop="label" label="入库类型" min-width="180" />
        <el-table-column prop="qty" label="数量" width="100" align="center" />
      </el-table>

      <p class="ledger-detail-section-title">出库明细</p>
      <el-table :data="ledgerOutboundDetailRows" stripe border size="small" empty-text="暂无数据">
        <el-table-column prop="label" label="出库类型" min-width="180" />
        <el-table-column prop="qty" label="数量" width="100" align="center" />
      </el-table>
    </template>
  </el-drawer>
</template>

<style scoped>
.list-search { margin-bottom: 4px; }
.list-search :deep(.el-form-item) { margin-bottom: 12px; }
.hint { font-size: 13px; color: #909399; margin: 0 0 12px; }
.ledger-type-table { width: 100%; }
.ledger-type-table :deep(.el-table__body-wrapper) { overflow-x: auto; }
.col-header-with-tip { display: inline-flex; align-items: center; justify-content: center; gap: 4px; }
.col-help-icon { font-size: 14px; color: #909399; cursor: help; vertical-align: middle; }
.col-help-icon:hover { color: #409eff; }
.qty-hover-cell { display: inline-block; min-width: 1em; }
.qty-hover-cell.has-detail { cursor: help; border-bottom: 1px dashed #909399; }
.ledger-detail-summary { margin-bottom: 16px; }
.ledger-detail-section-title { margin: 16px 0 8px; font-size: 13px; font-weight: 600; color: #606266; }
.ledger-detail-section-title:first-of-type { margin-top: 0; }
:deep(.qty-zero) { color: #c0c4cc; }
</style>
