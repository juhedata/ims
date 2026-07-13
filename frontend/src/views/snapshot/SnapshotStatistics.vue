<script setup>
import { computed, onMounted, ref } from 'vue'
import { listLedgerSummary, exportLedgerSummary } from '@/api/snapshot'
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
  otherInboundBreakdownLines,
  otherOutboundBreakdownLines,
} from '@/utils/ledgerDisplay'
import { formatAmount, initDefaultDateRange, isSnapshotDateDisabled, ledgerQtyCellClass } from '@/utils/snapshotLedger'
import { Download, QuestionFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const summaryLoading = ref(false)
const summaryExportLoading = ref(false)
const summaryQuery = ref({ dateRange: [] })
const summaryItems = ref([])

const summaryScopeLabel = computed(() => {
  const range = summaryQuery.value.dateRange
  if (range?.length !== 2) return ''
  return `${range[0]} 至 ${range[1]}`
})

onMounted(() => {
  initDefaultDateRange(summaryQuery)
  loadSummary()
})

async function loadSummary() {
  if (summaryQuery.value.dateRange?.length !== 2) {
    summaryItems.value = []
    return
  }
  summaryLoading.value = true
  try {
    const res = await listLedgerSummary({
      date_from: summaryQuery.value.dateRange[0],
      date_to: summaryQuery.value.dateRange[1],
    })
    summaryItems.value = res.data
  } finally {
    summaryLoading.value = false
  }
}

function handleSummarySearch() {
  loadSummary()
}

async function handleSummaryExport() {
  if (summaryQuery.value.dateRange?.length !== 2) {
    ElMessage.warning('请先选择日期区间')
    return
  }
  summaryExportLoading.value = true
  try {
    const params = {
      date_from: summaryQuery.value.dateRange[0],
      date_to: summaryQuery.value.dateRange[1],
    }
    const blob = await exportLedgerSummary(params)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `库存快照汇总_${params.date_from}_${params.date_to}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } finally {
    summaryExportLoading.value = false
  }
}
</script>

<template>
<el-form :inline="true" class="list-search" @submit.prevent="handleSummarySearch">
  <el-form-item label="日期区间">
    <el-date-picker
      v-model="summaryQuery.dateRange"
      type="daterange"
      range-separator="至"
      start-placeholder="开始日期"
      end-placeholder="结束日期"
      value-format="YYYY-MM-DD"
      :disabled-date="isSnapshotDateDisabled"
      style="width:260px"
    />
  </el-form-item>
  <el-form-item>
    <el-button type="primary" @click="handleSummarySearch">查询</el-button>
    <el-button
      type="success"
      :icon="Download"
      :loading="summaryExportLoading"
      :disabled="summaryQuery.dateRange?.length !== 2"
      @click="handleSummaryExport"
    >
      导出汇总
    </el-button>
  </el-form-item>
</el-form>

<p v-if="summaryScopeLabel" class="hint">
  汇总区间：{{ summaryScopeLabel }}，按 SKU 汇总。期初 = 区间内首日该 SKU 期初；期末 = 区间内末日该 SKU 期末。入库/出库分组口径与库存流水一致。
</p>

<el-table
  :data="summaryItems"
  v-loading="summaryLoading"
  stripe
  empty-text="暂无汇总数据"
  class="ledger-type-table"
  :cell-class-name="ledgerQtyCellClass"
>
  <el-table-column prop="sku_name" label="SKU" min-width="160" show-overflow-tooltip fixed="left" />
  <el-table-column label="期初在库" min-width="100" align="center">
    <template #default="{ row }">{{ row.opening_in_stock_qty ?? '—' }}</template>
  </el-table-column>
  <el-table-column label="总入库" align="center">
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
  <el-table-column label="总出库" align="center">
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
  <el-table-column label="理论期末" min-width="100" align="center">
    <template #default="{ row }">{{ row.expected_closing_qty ?? '—' }}</template>
  </el-table-column>
  <el-table-column prop="closing_in_stock_qty" label="期末在库" min-width="100" align="center" />
  <el-table-column label="期末资产金额" min-width="130" align="right">
    <template #default="{ row }">{{ formatAmount(row.closing_asset_amount) }}</template>
  </el-table-column>
  <el-table-column label="校验结果" min-width="110" align="center">
    <template #default="{ row }">
      <el-tag v-if="row.balanced" type="success" size="small">账实一致</el-tag>
      <el-tag v-else-if="row.expected_closing_qty != null" type="danger" size="small">
        差异 {{ row.diff_qty > 0 ? '+' : '' }}{{ row.diff_qty }} 件
      </el-tag>
      <span v-else class="summary-meta">期初未知</span>
    </template>
  </el-table-column>
</el-table>
</template>

<style scoped>
.list-search { margin-bottom: 4px; }
.list-search :deep(.el-form-item) { margin-bottom: 12px; }
.hint { font-size: 13px; color: #909399; margin: 0 0 12px; }
.summary-meta { font-size: 13px; font-weight: 400; color: #909399; }
.ledger-type-table { width: 100%; }
.ledger-type-table :deep(.el-table__body-wrapper) { overflow-x: auto; }
.col-header-with-tip { display: inline-flex; align-items: center; justify-content: center; gap: 4px; }
.col-help-icon { font-size: 14px; color: #909399; cursor: help; vertical-align: middle; }
.col-help-icon:hover { color: #409eff; }
.qty-hover-cell { display: inline-block; min-width: 1em; }
.qty-hover-cell.has-detail { cursor: help; border-bottom: 1px dashed #909399; }
:deep(.qty-zero) { color: #c0c4cc; }
</style>
