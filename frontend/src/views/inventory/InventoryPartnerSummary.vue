<script setup>
import { onMounted, ref } from 'vue'
import { OfficeBuilding } from '@element-plus/icons-vue'
import { getPartnerSummary } from '@/api/dashboard'
import { listSkus } from '@/api/product'
import { partnerTotalOutbound, qtyCellClass } from '@/utils/inventorySummary'

const loading = ref(false)
const items = ref([])
const skuList = ref([])
const query = ref({ sku_ids: [] })

onMounted(() => {
  loadSkus()
  loadData()
})

async function loadSkus() {
  const res = await listSkus({ page: 1, page_size: 500 })
  skuList.value = res.data.items
}

async function loadData() {
  loading.value = true
  try {
    const params = {}
    if (query.value.sku_ids?.length) params.sku_ids = query.value.sku_ids
    const res = await getPartnerSummary(params)
    items.value = [...res.data.items].sort(
      (a, b) => partnerTotalOutbound(b) - partnerTotalOutbound(a),
    )
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  loadData()
}

function resetQuery() {
  query.value = { sku_ids: [] }
  loadData()
}
</script>

<template>
  <el-form :inline="true" class="list-search" @submit.prevent="handleSearch">
    <el-form-item label="选择商品SKU">
      <el-select
        v-model="query.sku_ids"
        multiple
        collapse-tags
        collapse-tags-tooltip
        clearable
        filterable
        placeholder="全部"
        style="width:280px"
      >
        <el-option v-for="s in skuList" :key="s.id" :label="`${s.name}`" :value="s.id" />
      </el-select>
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="handleSearch">查询</el-button>
      <el-button @click="resetQuery">重置</el-button>
    </el-form-item>
  </el-form>

  <el-table :data="items" v-loading="loading" stripe border class="summary-table" :cell-class-name="qtyCellClass">
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
</template>

<style scoped>
.list-search { margin-bottom: 4px; }
.list-search :deep(.el-form-item) { margin-bottom: 12px; }
.partner-name-cell { display: inline-flex; align-items: center; gap: 4px; }
.partner-group-icon { font-size: 14px; color: #909399; cursor: help; flex-shrink: 0; }
.partner-group-icon:hover { color: #409eff; }
.summary-table :deep(.qty-zero) { color: #c0c4cc; }
.summary-table :deep(.el-table__header-wrapper th.el-table__cell .cell) {
  color: #303133;
  font-weight: 500;
}
</style>
