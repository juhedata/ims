import {
  OUTBOUND_TYPE_MAP,
  OUTBOUND_TYPE_ORDER,
  RETURN_CONDITION_ORDER,
  STOCK_CONDITION_MAP,
} from '@/constants/enums'

/** 其他入库：各类退回（含借用归还） */
export const OTHER_INBOUND_TYPE_CODES = [...RETURN_CONDITION_ORDER, 'RETURNED_FROM_BORROW']

/** 其他出库：除售出/准售出/赠送外的出库类型 */
export const OTHER_OUTBOUND_TYPE_CODES = ['SCRAPPED', 'RND', 'SAMPLE', 'TRIAL', 'REPAIR', 'DEPT_PROCUREMENT', 'BORROWED']

/** 流水明细：入库类型行（对应 inventory_sku_daily_ledger 入库列） */
export const LEDGER_INBOUND_DETAIL_ITEMS = [
  { code: 'NEW', label: STOCK_CONDITION_MAP.NEW },
  ...OTHER_INBOUND_TYPE_CODES.map((code) => ({
    code,
    label: STOCK_CONDITION_MAP[code] || code,
  })),
]

/** 流水明细：出库类型行（对应 inventory_sku_daily_ledger 出库列） */
export const LEDGER_OUTBOUND_DETAIL_ITEMS = [
  ...OUTBOUND_TYPE_ORDER.map((code) => ({
    code,
    label: OUTBOUND_TYPE_MAP[code] || code,
  })),
  { code: 'BORROWED', label: OUTBOUND_TYPE_MAP.BORROWED },
]

export const OTHER_INBOUND_TOOLTIP = `其他入库包含：${OTHER_INBOUND_TYPE_CODES.map((code) => STOCK_CONDITION_MAP[code] || code).join('、')}`

export const OTHER_OUTBOUND_TOOLTIP = `其他出库包含：${OTHER_OUTBOUND_TYPE_CODES.map((code) => OUTBOUND_TYPE_MAP[code] || code).join('、')}`

export function buildLedgerInboundDetailRows(typeMap) {
  return LEDGER_INBOUND_DETAIL_ITEMS.map(({ code, label }) => ({
    label,
    qty: typeMap?.[code] || 0,
  }))
}

export function buildLedgerOutboundDetailRows(typeMap) {
  return LEDGER_OUTBOUND_DETAIL_ITEMS.map(({ code, label }) => ({
    label,
    qty: typeMap?.[code] || 0,
  }))
}

export function sumTypeQty(typeMap, codes) {
  return codes.reduce((sum, code) => sum + (typeMap?.[code] || 0), 0)
}

export function ledgerInboundNormalQty(typeMap) {
  return typeMap?.NEW || 0
}

export function ledgerInboundOtherQty(typeMap) {
  return sumTypeQty(typeMap, OTHER_INBOUND_TYPE_CODES)
}

export function ledgerOutboundSoldQty(typeMap) {
  return typeMap?.SOLD || 0
}

export function ledgerOutboundSoldOfflineQty(typeMap) {
  return typeMap?.SOLD_OFFLINE || 0
}

export function ledgerOutboundPresoldQty(typeMap) {
  return typeMap?.PRESOLD || 0
}

export function ledgerOutboundGiftedQty(typeMap) {
  return typeMap?.GIFTED || 0
}

export function ledgerOutboundOtherQty(typeMap) {
  return sumTypeQty(typeMap, OTHER_OUTBOUND_TYPE_CODES)
}

/** 其他入库 hover 分项（仅数量 > 0） */
export function otherInboundBreakdownLines(typeMap) {
  return OTHER_INBOUND_TYPE_CODES.map((code) => ({
    label: STOCK_CONDITION_MAP[code] || code,
    qty: typeMap?.[code] || 0,
  })).filter((item) => item.qty > 0)
}

/** 其他出库 hover 分项（仅数量 > 0） */
export function otherOutboundBreakdownLines(typeMap) {
  return OTHER_OUTBOUND_TYPE_CODES.map((code) => ({
    label: OUTBOUND_TYPE_MAP[code] || code,
    qty: typeMap?.[code] || 0,
  })).filter((item) => item.qty > 0)
}
