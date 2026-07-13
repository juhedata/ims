import {
  IN_STOCK_CONDITION_ORDER,
  STOCK_CONDITION_MAP,
} from '@/constants/enums'

export const PARTNER_OUTBOUND_FIELDS = [
  'sold', 'sold_offline', 'presold', 'borrowed', 'gifted', 'scrapped',
  'rnd', 'sample', 'trial', 'repair', 'dept_procurement',
]

/** SKU 库存统计表中参与汇总的数量字段（在库 + 不在库各状态） */
export const SKU_SUMMARY_QTY_FIELDS = ['in_stock', ...PARTNER_OUTBOUND_FIELDS]

export const QTY_COLUMNS = new Set(SKU_SUMMARY_QTY_FIELDS)

export const IN_STOCK_DETAIL_COLUMNS = IN_STOCK_CONDITION_ORDER.map((code) => ({
  field: code.toLowerCase(),
  label: STOCK_CONDITION_MAP[code],
}))

export function inStockDetailTooltipLines(row) {
  const details = row.in_stock_details
  if (!details || !row.in_stock) return []
  return IN_STOCK_DETAIL_COLUMNS.map(({ field, label }) => ({
    label,
    qty: details[field] || 0,
  }))
}

export function partnerTotalOutbound(row) {
  return PARTNER_OUTBOUND_FIELDS.reduce((sum, field) => sum + (row[field] || 0), 0)
}

/** 单行 SKU 统计：在库 + 不在库各状态之和 */
export function skuRowTotal(row) {
  return SKU_SUMMARY_QTY_FIELDS.reduce((sum, field) => sum + (row[field] || 0), 0)
}

/**
 * Element Plus 表格底部汇总行：对各数量列求和，首列为「统计」。
 * @param {{ columns: Array, data: Array }} param0
 */
export function skuSummaryMethod({ columns, data }) {
  return columns.map((column, index) => {
    if (index === 0) return '统计'
    if (column.label === '统计') {
      return data.reduce((sum, row) => sum + skuRowTotal(row), 0)
    }
    // 「在库」列可能只有 label、无 property
    if (column.label === '在库' || column.property === 'in_stock') {
      return data.reduce((sum, row) => sum + (row.in_stock || 0), 0)
    }
    const prop = column.property
    if (!prop || !QTY_COLUMNS.has(prop)) return ''
    return data.reduce((sum, row) => sum + (row[prop] || 0), 0)
  })
}

export function qtyCellClass({ row, column }) {
  if (column.label === '累计') {
    return partnerTotalOutbound(row) === 0 ? 'qty-zero' : ''
  }
  if (column.label === '统计') {
    return skuRowTotal(row) === 0 ? 'qty-zero' : ''
  }
  if (column.label === '在库') {
    return (row.in_stock || 0) === 0 ? 'qty-zero' : ''
  }
  const prop = column.property
  if (!prop || !QTY_COLUMNS.has(prop)) return ''
  return (row[prop] || 0) === 0 ? 'qty-zero' : ''
}
