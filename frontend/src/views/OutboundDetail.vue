<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import JsBarcode from 'jsbarcode'
import { ArrowLeft } from '@element-plus/icons-vue'
import {
  getOutboundOrder, submitOutboundOrder, approveOutboundOrder,
  cancelOutboundOrder, deleteOutboundOrder,
} from '@/api/outbound'
import { listPartners } from '@/api/partner'
import {
  OUTBOUND_TYPE_MAP, OPERATION_STATUS_MAP, STOCK_CONDITION_MAP,
  statusTagType,
} from '@/constants/enums'
import { formatDateTime } from '@/utils/datetime'

const props = defineProps({
  /** 面板模式：由父组件传入单号或 ID，不从路由读取 */
  orderId: { type: String, default: null },
  /** true 时隐藏返回按钮，适合嵌入 drawer/dialog */
  isPanel: { type: Boolean, default: false },
})
const emit = defineEmits(['deleted'])

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const detail = ref(null)
const allPartners = ref([])

const resolvedId = () => props.orderId ?? route.params.id

function partnerName(partnerId) {
  return allPartners.value.find(p => p.id === partnerId)?.name || '-'
}

async function loadDetail() {
  loading.value = true
  try {
    const res = await getOutboundOrder(resolvedId())
    detail.value = res.data
  } finally {
    loading.value = false
  }
}

async function loadPartners() {
  const res = await listPartners({ page: 1, page_size: 500 })
  allPartners.value = res.data.items
}

onMounted(() => {
  loadDetail()
  loadPartners()
})

watch(() => props.orderId, (val) => { if (val) loadDetail() })

function canSubmit(row) { return row.operation_status === 'INITIATED' && !row.submitted_at }
function canApprove(row) { return row.operation_status === 'INITIATED' && row.submitted_at }
function canCancel(row) { return row.operation_status === 'INITIATED' && row.submitted_at }
function canDelete(row) { return row.operation_status === 'INITIATED' && !row.submitted_at }

function printDetail() {
  const d = detail.value
  if (!d) return

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  JsBarcode(svg, d.order_no, { format: 'CODE128', width: 1.5, height: 40, displayValue: true, fontSize: 11, margin: 4 })
  const barcodeSvg = svg.outerHTML

  const descRows = [
    [['单位组', d.partner_group_name || '-'], ['关联单位', partnerName(d.partner_id)]],
    [['出库类型', OUTBOUND_TYPE_MAP[d.outbound_type] || d.outbound_type], ['状态', OPERATION_STATUS_MAP[d.operation_status] || d.operation_status]],
    [['关联客户', d.customer_name || '-'], ['数量', d.total_qty]],
    [['创建时间', formatDateTime(d.created_at) || '-'],['更新时间', formatDateTime(d.updated_at) || '-']],
    [['备注', d.remark || '-'], ['', '']],
  ]

  const descHtml = descRows.map(pairs => {
    const cells = pairs.map(([label, val]) => `<td class="label">${label}</td><td>${val}</td>`).join('')
    return `<tr>${cells}</tr>`
  }).join('')

  const itemsHtml = (d.items || []).map(item => `
    <tr><td>${item.item_sn}</td><td>${item.sku_name || '-'}</td><td style="text-align:center">${item.sku_unit || '-'}</td><td style="text-align:center">1</td></tr>
  `).join('')

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>出库单 ${d.order_no}</title>
  <style>
    body { font-family: Arial, sans-serif; font-size: 13px; padding: 24px; color: #333; }
    .header { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
    .header h2 { margin: 0; font-size: 22px; }
    .barcode { flex-shrink: 0; }
    table.desc { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
    table.desc td { border: 0.2px solid #333; padding: 6px 10px; }
    table.desc td.label { background: #f5f5f5; font-weight: bold; width: 100px; white-space: nowrap; }
    table.items { border-collapse: collapse; width: 100%; }
    table.items th, table.items td { border: 0.2px solid #333; padding: 5px 10px; text-align: left; }
    table.items th { background: #f5f5f5; }
    h3 { font-size: 14px; margin: 0 0 8px; }
    .footer-sign { margin-top: 40px; text-align: right; line-height: 2.2; }
    @media print { body { padding: 12px; } }
  </style></head><body>
  <div class="header">
    <h2>出库单：${d.order_no}</h2>
    <div class="barcode">${barcodeSvg}</div>
  </div>
  <table class="desc">${descHtml}</table>
  <h3>出库商品明细</h3>
  <table class="items">
    <thead><tr><th>序列号</th><th>商品名称</th><th style="text-align:center;width:60px">单位</th><th style="text-align:center;width:60px">数量</th></tr></thead>
    <tbody>${itemsHtml}</tbody>
  </table>
  <div class="footer-sign">
    <div>签字：________________</div>
    <div>日期：______ 年 ______ 月 ______ 日</div>
  </div>
  <script>window.onload=function(){window.print();}<\/script>
  </body></html>`

  const win = window.open('', '_blank')
  win.document.write(html)
  win.document.close()
}

async function handleAction(action) {
  const actions = {
    submit: { fn: submitOutboundOrder, msg: '确认提交审核？' },
    approve: { fn: approveOutboundOrder, msg: '确认通过该出库单？' },
    cancel: { fn: cancelOutboundOrder, msg: '确认取消？' },
    delete: { fn: deleteOutboundOrder, msg: '确认删除？' },
  }
  await ElMessageBox.confirm(actions[action].msg, '提示', { type: 'warning' })
  await actions[action].fn(detail.value.id)
  ElMessage.success('操作成功')
  if (action === 'delete') {
    if (props.isPanel) emit('deleted')
    else router.push('/outbound')
  } else {
    loadDetail()
  }
}
</script>

<template>
  <div v-loading="loading" class="detail-page">
    <div class="detail-header">
      <el-button v-if="!isPanel" :icon="ArrowLeft" circle @click="router.back()" title="返回列表" />
      <span class="detail-title">出库单详情</span>
      <div class="detail-actions" v-if="detail">
        <el-button type="primary" plain size="small" @click="printDetail">🖨 打印</el-button>
        <el-button v-if="canSubmit(detail)" type="warning" size="small" plain @click="handleAction('submit')">提交审核</el-button>
        <el-button v-if="canApprove(detail)" type="primary" size="small" @click="handleAction('approve')">确认通过</el-button>
        <el-button v-if="canCancel(detail)" type="info" size="small" plain @click="handleAction('cancel')">取消</el-button>
        <el-button v-if="canDelete(detail)" type="danger" size="small" plain @click="handleAction('delete')">删除</el-button>
      </div>
    </div>

    <el-card v-if="detail" shadow="never" class="detail-card">
      <el-descriptions title="基本信息" :column="2" border>
        <el-descriptions-item label="出库单号">{{ detail.order_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType(detail.operation_status)" size="small">
            {{ OPERATION_STATUS_MAP[detail.operation_status] }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="出库类型">{{ OUTBOUND_TYPE_MAP[detail.outbound_type] }}</el-descriptions-item>
        <el-descriptions-item label="总数量">{{ detail.total_qty }}</el-descriptions-item>
        <el-descriptions-item label="单位组">{{ detail.partner_group_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="关联单位">{{ detail.partner_name || partnerName(detail.partner_id) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(detail.created_at) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDateTime(detail.updated_at) || '-' }}</el-descriptions-item>
        <el-descriptions-item label="关联客户" :span="2">{{ detail.customer_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ detail.remark || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="items-section">
        <div class="items-title">出库商品明细</div>
        <el-table :data="detail.items" stripe border size="normal">
          <el-table-column type="index" label="#" width="55" align="center" />
          <el-table-column prop="item_sn" label="序列号" min-width="180" />
          <el-table-column prop="sku_name" label="商品名称" min-width="180" />
          <el-table-column prop="sku_unit" label="单位" width="70" align="center" />
          <el-table-column label="数量" width="70" align="center">
            <template #default>1</template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.detail-page {
  padding: 0;
}
.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.detail-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}
.detail-actions {
  display: flex;
  gap: 8px;
}
.detail-card {
  margin-bottom: 16px;
}
.items-section {
  margin-top: 24px;
}
.items-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  border-left: 3px solid var(--el-color-primary);
  padding-left: 8px;
}
</style>
