<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { OfficeBuilding } from '@element-plus/icons-vue'
import { getPartnerSummary, getPendingAudit, getStockSummary } from '@/api/dashboard'
import {
  partnerTotalOutbound,
  inStockDetailTooltipLines,
  qtyCellClass,
  skuRowTotal,
  skuSummaryMethod,
} from '@/utils/inventorySummary'

const router = useRouter()
const pending = ref({ inbound_pending: 0, outbound_pending: 0 })
const summary = ref([])
const partnerSummary = ref([])
const loading = ref(false)

onMounted(loadData)

async function loadData() {
  loading.value = true
  try {
    const [p, s, ps] = await Promise.all([getPendingAudit(), getStockSummary(), getPartnerSummary()])
    pending.value = p.data
    summary.value = s.data.items
    partnerSummary.value = [...ps.data.items].sort(
      (a, b) => partnerTotalOutbound(b) - partnerTotalOutbound(a),
    )
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div v-loading="loading">
    <el-row :gutter="20" class="cards">
      <el-col :span="12">
        <el-card shadow="hover" class="audit-card outbound" @click="router.push('/outbound')">
          <div class="card-num">{{ pending.outbound_pending }}</div>
          <div class="card-label">待审核出库单</div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover" class="audit-card inbound" @click="router.push('/inbound')">
          <div class="card-num">{{ pending.inbound_pending }}</div>
          <div class="card-label">待审核入库单</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" style="margin-top:20px">
      <template #header><span>实时库存统计（按 SKU）</span></template>
      <el-table
        :data="summary"
        stripe
        border
        show-summary
        :summary-method="skuSummaryMethod"
        :cell-class-name="qtyCellClass"
      >
        <el-table-column prop="sku_name" label="商品名称" min-width="150" />
        <el-table-column prop="in_stock" label="在库" align="center">
          <template #default="{ row }">
            <el-tooltip v-if="inStockDetailTooltipLines(row).length" placement="top">
              <template #content>
                <div v-for="line in inStockDetailTooltipLines(row)" :key="line.label" class="in-stock-tooltip-line">
                  {{ line.label }}：{{ line.qty }}
                </div>
              </template>
              <span class="in-stock-cell">{{ row.in_stock }}</span>
            </el-tooltip>
            <span v-else>{{ row.in_stock }}</span>
          </template>
        </el-table-column>
        <el-table-column label="不在库" align="center">
          <el-table-column prop="sold" label="售出-线上" align="center" />
          <el-table-column prop="sold_offline" label="售出-线下" align="center" />
          <el-table-column prop="presold" label="准售出" align="center" />
          <el-table-column prop="borrowed" label="借出" align="center" />
          <el-table-column prop="gifted" label="赠送" align="center" />
          <el-table-column prop="scrapped" label="损毁" align="center" />
          <el-table-column prop="rnd" label="研发" align="center" />
          <el-table-column prop="sample" label="样机" align="center" />
          <el-table-column prop="trial" label="试用" align="center" />
          <el-table-column prop="repair" label="维修" align="center" />
          <el-table-column prop="dept_procurement" label="部门采购" align="center" />
        </el-table-column>
        <el-table-column label="统计" min-width="90" align="center" fixed="right">
          <template #default="{ row }">{{ skuRowTotal(row) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never" style="margin-top:20px">
      <template #header><span>出库商品统计（按关联单位）</span></template>
      <el-table :data="partnerSummary" stripe border :cell-class-name="qtyCellClass">
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
        <el-table-column label="累计" min-width="90" align="center">
          <template #default="{ row }">{{ partnerTotalOutbound(row) }}</template>
        </el-table-column>
        <el-table-column label="售出-出库" align="center">
          <el-table-column prop="sold" label="售出-线上" align="center" />
          <el-table-column prop="sold_offline" label="售出-线下" align="center" />
          <el-table-column prop="presold" label="准售出" align="center" />
        </el-table-column>
        <el-table-column label="其他-出库" align="center">
          <el-table-column prop="borrowed" label="借出" align="center" />
          <el-table-column prop="gifted" label="赠送" align="center" />
          <el-table-column prop="scrapped" label="损毁" align="center" />
          <el-table-column prop="rnd" label="研发" align="center" />
          <el-table-column prop="sample" label="样机" align="center" />
          <el-table-column prop="trial" label="试用" align="center" />
          <el-table-column prop="repair" label="维修" align="center" />
          <el-table-column prop="dept_procurement" label="部门采购" align="center" />
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.audit-card { cursor: pointer; text-align: center; padding: 20px 0; }
.card-num { font-size: 48px; font-weight: 700; }
.card-label { font-size: 16px; color: #606266; margin-top: 8px; }
.outbound .card-num { color: #e6a23c; }
.inbound .card-num { color: #7b67ee; }
.partner-name-cell { display: inline-flex; align-items: center; gap: 4px; }
.partner-group-icon { font-size: 14px; color: #909399; cursor: help; flex-shrink: 0; }
.partner-group-icon:hover { color: #409eff; }
:deep(.qty-zero) { color: #c0c4cc; }
.in-stock-cell { cursor: help; border-bottom: 1px dashed #c0c4cc; }
:deep(.el-table__footer-wrapper td.el-table__cell .cell) {
  color: #303133;
  font-weight: 600;
}
</style>
