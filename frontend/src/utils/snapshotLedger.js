import {
  ledgerInboundNormalQty,
  ledgerInboundOtherQty,
  ledgerOutboundSoldQty,
  ledgerOutboundSoldOfflineQty,
  ledgerOutboundPresoldQty,
  ledgerOutboundGiftedQty,
  ledgerOutboundOtherQty,
} from '@/utils/ledgerDisplay'

export const LEDGER_QTY_LABELS = new Set([
  '期初在库', '期末在库', '理论期末',
  '正常', '其他入库',
  '售出-线上', '售出-线下', '准售出', '赠送', '其他出库',
])

export function formatDateInput(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function getYesterday() {
  const d = new Date()
  d.setDate(d.getDate() - 1)
  d.setHours(0, 0, 0, 0)
  return d
}

export function isSnapshotDateDisabled(date) {
  const yesterday = getYesterday()
  const day = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  return day.getTime() > yesterday.getTime()
}

export function initDefaultDateRange(target) {
  if (target.value.dateRange?.length === 2) return
  const end = getYesterday()
  const start = new Date(end)
  start.setDate(end.getDate() - 6)
  target.value.dateRange = [formatDateInput(start), formatDateInput(end)]
}

export function formatAmount(value) {
  if (value == null || value === '') return '-'
  return `¥${Number(value).toFixed(2)}`
}

export function ledgerQtyValue(row, label) {
  switch (label) {
    case '期初在库': return row.opening_in_stock_qty
    case '期末在库': return row.closing_in_stock_qty
    case '理论期末': return row.expected_closing_qty
    case '正常': return ledgerInboundNormalQty(row.inbound_by_type)
    case '其他入库': return ledgerInboundOtherQty(row.inbound_by_type)
    case '售出-线上': return ledgerOutboundSoldQty(row.outbound_by_type)
    case '售出-线下': return ledgerOutboundSoldOfflineQty(row.outbound_by_type)
    case '准售出': return ledgerOutboundPresoldQty(row.outbound_by_type)
    case '赠送': return ledgerOutboundGiftedQty(row.outbound_by_type)
    case '其他出库': return ledgerOutboundOtherQty(row.outbound_by_type)
    default: return null
  }
}

export function ledgerQtyCellClass({ row, column }) {
  if (!LEDGER_QTY_LABELS.has(column.label)) return ''
  return ledgerQtyValue(row, column.label) === 0 ? 'qty-zero' : ''
}
