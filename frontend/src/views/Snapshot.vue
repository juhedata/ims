<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const TAB_ROUTES = {
  ledger: 'SnapshotLedger',
  summary: 'SnapshotStatistics',
  detail: 'SnapshotDetails',
}

const ROUTE_TO_TAB = Object.fromEntries(
  Object.entries(TAB_ROUTES).map(([tab, name]) => [name, tab]),
)

const activeTab = computed(() => ROUTE_TO_TAB[route.name] ?? 'ledger')

function onTabChange(name) {
  const target = TAB_ROUTES[name]
  if (!target || route.name === target) return
  router.push({ name: target })
}
</script>

<template>
  <el-card shadow="never">
    <el-tabs :model-value="activeTab" @tab-change="onTabChange">
      <el-tab-pane label="库存流水" name="ledger" />
      <el-tab-pane label="库存快照汇总" name="summary" />
      <el-tab-pane label="快照明细" name="detail" />
    </el-tabs>
    <router-view v-slot="{ Component }">
      <keep-alive>
        <component :is="Component" />
      </keep-alive>
    </router-view>
  </el-card>
</template>

<style>
.ledger-qty-tooltip .qty-breakdown-line { line-height: 1.6; white-space: nowrap; }
</style>
