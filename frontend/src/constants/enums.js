export const STOCK_STATUS_MAP = {
  IN_STOCK: '在库',
  SOLD: '售出-线上',
  SOLD_OFFLINE: '售出-线下',
  PRESOLD: '准售出',
  BORROWED: '已借用',
  GIFTED: '赠送',
  SCRAPPED: '损毁',
  RND: '研发',
  SAMPLE: '样机',
  TRIAL: '试用',
  REPAIR: '维修',
  DEPT_PROCUREMENT: '部门采购',
}

/** 非采购入库类型（退货）展示顺序 */
export const RETURN_CONDITION_ORDER = [
  'RETURNED_FROM_SALE',
  'RETURNED_FROM_SOLD_OFFLINE',
  'RETURNED_FROM_PRESOLD',
  'RETURNED_FROM_GIFT',
  'RETURNED_FROM_SCRAPPED',
  'RETURNED_FROM_RND',
  'RETURNED_FROM_SAMPLE',
  'RETURNED_FROM_TRIAL',
  'RETURNED_FROM_REPAIR',
  'RETURNED_FROM_DEPT_PROCUREMENT',
]

export const STOCK_CONDITION_MAP = {
  NEW: '正常',
  RETURNED_FROM_SALE: '线上售出退回',
  RETURNED_FROM_SOLD_OFFLINE: '线下售出退回',
  RETURNED_FROM_PRESOLD: '准售出退回',
  RETURNED_FROM_BORROW: '借用归还',
  RETURNED_FROM_GIFT: '赠送退回',
  RETURNED_FROM_SCRAPPED: '损毁退回',
  RETURNED_FROM_RND: '研发退回',
  RETURNED_FROM_SAMPLE: '样机退回',
  RETURNED_FROM_TRIAL: '试用退回',
  RETURNED_FROM_REPAIR: '维修退回',
  RETURNED_FROM_DEPT_PROCUREMENT: '部门采购退回',
}

/** 出库类型展示顺序 */
export const OUTBOUND_TYPE_ORDER = [
  'SOLD',
  'SOLD_OFFLINE',
  'PRESOLD',
  'GIFTED',
  'SCRAPPED',
  'RND',
  'SAMPLE',
  'TRIAL',
  'REPAIR',
  'DEPT_PROCUREMENT',
]

export const OUTBOUND_TYPE_MAP = {
  SOLD: '售出-线上',
  SOLD_OFFLINE: '售出-线下',
  PRESOLD: '准售出',
  GIFTED: '赠送',
  SCRAPPED: '损毁',
  RND: '研发',
  SAMPLE: '样机',
  TRIAL: '试用',
  REPAIR: '维修',
  DEPT_PROCUREMENT: '部门采购',
  BORROWED: '借用',
  OFFLINE_SOLD: '售出-线下', // 历史 code，仅用于旧单展示
}

/** 已从出库选项中移除的历史 code（展示仍用 OUTBOUND_TYPE_MAP） */
export const LEGACY_OUTBOUND_TYPE_CODES = ['OFFLINE_SOLD']

/** 前端筛选项/表单项中隐藏（已有数据展示不受影响） */
export const HIDDEN_SELECT_STOCK_CONDITIONS = ['RETURNED_FROM_BORROW']
export const HIDDEN_SELECT_OUTBOUND_TYPES = ['BORROWED']

/** 在库商品的库存属性筛选项顺序（含正常 + 各类退回） */
export const IN_STOCK_CONDITION_ORDER = [
  'NEW',
  ...RETURN_CONDITION_ORDER,
]

export function selectableStockConditionEntries() {
  return IN_STOCK_CONDITION_ORDER
    .filter((k) => !HIDDEN_SELECT_STOCK_CONDITIONS.includes(k))
    .map((k) => [k, STOCK_CONDITION_MAP[k]])
}

export function selectableOutboundTypeEntries() {
  return OUTBOUND_TYPE_ORDER
    .filter((k) => !HIDDEN_SELECT_OUTBOUND_TYPES.includes(k) && !LEGACY_OUTBOUND_TYPE_CODES.includes(k))
    .map((k) => [k, OUTBOUND_TYPE_MAP[k]])
}

export function selectableReturnConditionEntries(conditions = STOCK_CONDITION_MAP) {
  return RETURN_CONDITION_ORDER
    .filter((k) => !HIDDEN_SELECT_STOCK_CONDITIONS.includes(k) && conditions[k])
    .map((k) => [k, conditions[k]])
}

/** 入库类型 → 可关联的出库类型 code */
export const RETURN_TO_OUTBOUND = {
  RETURNED_FROM_SALE: ['SOLD'],
  RETURNED_FROM_SOLD_OFFLINE: ['SOLD_OFFLINE', 'OFFLINE_SOLD'],
  RETURNED_FROM_PRESOLD: ['PRESOLD'],
  RETURNED_FROM_GIFT: ['GIFTED'],
  RETURNED_FROM_SCRAPPED: ['SCRAPPED'],
  RETURNED_FROM_RND: ['RND'],
  RETURNED_FROM_SAMPLE: ['SAMPLE'],
  RETURNED_FROM_TRIAL: ['TRIAL'],
  RETURNED_FROM_REPAIR: ['REPAIR'],
  RETURNED_FROM_DEPT_PROCUREMENT: ['DEPT_PROCUREMENT'],
  RETURNED_FROM_BORROW: ['BORROWED'],
}

export function stockConditionName(code) {
  return STOCK_CONDITION_MAP[code] || code || ''
}

export function filterOutboundsByReturnCondition(outbounds, stockCondition) {
  if (!stockCondition) return []
  const allowed = RETURN_TO_OUTBOUND[stockCondition]
  if (!allowed) return outbounds
  return outbounds.filter((o) => allowed.includes(o.outbound_type))
}

/** 出库类型 → 其他入库库存属性 */
export const OUTBOUND_TO_RETURN_CONDITION = {
  SOLD: 'RETURNED_FROM_SALE',
  SOLD_OFFLINE: 'RETURNED_FROM_SOLD_OFFLINE',
  OFFLINE_SOLD: 'RETURNED_FROM_SOLD_OFFLINE',
  PRESOLD: 'RETURNED_FROM_PRESOLD',
  BORROWED: 'RETURNED_FROM_BORROW',
  GIFTED: 'RETURNED_FROM_GIFT',
  SCRAPPED: 'RETURNED_FROM_SCRAPPED',
  RND: 'RETURNED_FROM_RND',
  SAMPLE: 'RETURNED_FROM_SAMPLE',
  TRIAL: 'RETURNED_FROM_TRIAL',
  REPAIR: 'RETURNED_FROM_REPAIR',
  DEPT_PROCUREMENT: 'RETURNED_FROM_DEPT_PROCUREMENT',
}

/** 根据出库单类型推断其他入库的库存属性 */
export function stockConditionFromOutboundType(outboundType) {
  return OUTBOUND_TO_RETURN_CONDITION[outboundType] || null
}

export function outboundOptionLabel(order) {
  const typeLabel = OUTBOUND_TYPE_MAP[order.outbound_type] || order.outbound_type
  return `${order.order_no}（${typeLabel}，共${order.total_qty}件）`
}

export function stockConditionLabel(stock_status_code, stock_condition_code) {
  if (stock_status_code === 'IN_STOCK') {
    return { stock_status_name: '在库', stock_condition_name: STOCK_CONDITION_MAP[stock_condition_code] || (stock_condition_code || '在库'), class_type:'IN' }
  }
  const outLabel = STOCK_STATUS_MAP[stock_status_code]
  if (outLabel) {
    return { stock_status_name: '出库', stock_condition_name: outLabel, class_type:'OUT' }
  }
  return { stock_status_name: stock_status_code || '', stock_condition_name: stock_condition_code || '' , class_type:'UN' }
}

export const OPERATION_STATUS_MAP = {
  INITIATED: '已发起',
  PICKING: '出库处理中',
  CHECKING: '入库处理中',
  COMPLETED: '已完成',
  CANCELLED: '已取消',
  FAILED: '失败',
}

export const INBOUND_MODE_MAP = {
  PROCUREMENT: '采购入库',
  NON_PROCUREMENT: '其他入库',
}

export function inboundModeLabel(mode_code, condition_code) {
  if (mode_code === 'PROCUREMENT') {
    return stockConditionName(condition_code) || '正常'
  }
  if (mode_code === 'NON_PROCUREMENT') {
    return stockConditionName(condition_code)
  }
  return stockConditionName(condition_code) || (mode_code || '')
}

export const PARTNER_TYPE_MAP = {
  0: '供应商 & 客户',
  1: '客户',
  2: '供应商',
}

export function eventTypeLabel(event_type) {
  if (event_type === 'INBOUND') {
    return {'event_type_name': '入库', 'event_type_class': 'IN'}
  } else if (event_type === 'OUTBOUND') {
    return {'event_type_name': '出库', 'event_type_class': 'OUT'}
  } else if (event_type === 'STATUS_CHANGE') {
    return {'event_type_name': '库存状态变更', 'event_type_class': 'STATUS'}
  }
  return {'event_type_name': event_type || '', 'event_type_class': 'UN'}
}

export function statusTagType(status) {
  const map = {
    INITIATED: 'warning',
    PICKING: 'warning',
    CHECKING: 'warning',
    COMPLETED: 'success',
    CANCELLED: 'info',
    FAILED: 'danger',
    IN_STOCK: 'success',
    SOLD: '',
    PRESOLD: 'warning',
    SOLD_OFFLINE: 'success',
    BORROWED: 'warning',
    GIFTED: 'info',
    SCRAPPED: 'danger',
    RND: 'info',
    SAMPLE: 'info',
    TRIAL: 'warning',
    REPAIR: 'warning',
    DEPT_PROCUREMENT: 'info',

    IN: 'success',
    OUT: 'warning',
    UN: 'info',

    STATUS: 'info',
  }
  return map[status] || ''
}

export const SNNO_IMPORT_MODE_MAP = {
  MANUAL: '人工录入',
  AUTO: '系统生成',
  BOTH: '两者皆可',
}

export const USER_ROLE_MAP = {
  ADMIN: '管理员',
  STAFF: '普通员工',
}

export const AUDIT_ACTION_MAP = {
  LOGIN: '登录',
  LOGOUT: '登出',
  CREATE: '新增',
  UPDATE: '修改',
  DELETE: '删除',
  SUBMIT: '提交审核',
  APPROVE: '审核通过',
  CANCEL: '取消',
  TOGGLE: '切换状态',
  EXPORT: '导出',
  SEED: '初始化',
  CHANGE_PASSWORD: '修改密码',
}

export const AUDIT_MODULE_MAP = {
  auth: '认证',
  user: '员工账号',
  settings: '系统设置',
  product: '商品SKU',
  partner: '往来单位',
  inbound: '入库',
  outbound: '出库',
  inventory: '库存',
}
