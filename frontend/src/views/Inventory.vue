<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const TAB_ROUTES = {
  detail: 'Inventory',
  sku: 'InventorySku',
  partner: 'InventoryPartner',
}

const ROUTE_TO_TAB = Object.fromEntries(
  Object.entries(TAB_ROUTES).map(([tab, name]) => [name, tab]),
)

const activeTab = computed(() => ROUTE_TO_TAB[route.name] ?? 'detail')

function onTabChange(name) {
  const target = TAB_ROUTES[name]
  if (!target || route.name === target) return
  router.push({ name: target })
}
</script>

<template>
  <el-card shadow="never">
    <el-tabs :model-value="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="实时库存明细" name="detail" />
      <el-tab-pane label="实时库存（按SKU统计）" name="sku" />
      <el-tab-pane label="实时出库统计（按单位）" name="partner" />
    </el-tabs>
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>
  </el-card>
</template>
