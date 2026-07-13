<script setup>
import { onMounted, ref } from 'vue'
import { getStockSummary } from '@/api/dashboard'
import {
  inStockDetailTooltipLines,
  qtyCellClass,
  skuRowTotal,
  skuSummaryMethod,
} from '@/utils/inventorySummary'

const loading = ref(false)
const items = ref([])

onMounted(loadData)

async function loadData() {
  loading.value = true
  try {
    const res = await getStockSummary()
    items.value = res.data.items
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-table
    :data="items"
    v-loading="loading"
    stripe
    border
    class="summary-table"
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
</template>

<style scoped>
.summary-table :deep(.qty-zero) { color: #c0c4cc; }
.in-stock-cell { cursor: help; border-bottom: 1px dashed #c0c4cc; }
.summary-table :deep(.el-table__header-wrapper th.el-table__cell .cell) {
  color: #303133;
  font-weight: 500;
}
.summary-table :deep(.el-table__footer-wrapper td.el-table__cell .cell) {
  color: #303133;
  font-weight: 600;
}
</style>
