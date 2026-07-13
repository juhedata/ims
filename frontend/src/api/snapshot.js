import request from '@/utils/request'

export function listSnapshotDates(params) {
  return request.get('/api/v1/snapshots/dates', { params })
}

export function listDailyLedger(params) {
  return request.get('/api/v1/snapshots/daily-ledger', { params })
}

export function getDailyLedgerBreakdown(snapshotDate, dimension, skuId) {
  const params = { dimension }
  if (skuId != null) params.sku_id = skuId
  return request.get(`/api/v1/snapshots/daily-ledger/${snapshotDate}/breakdown`, {
    params,
  })
}

export function exportDailyLedger(params) {
  return request.get('/api/v1/snapshots/daily-ledger/export', { params, responseType: 'blob' })
}

export function listLedgerSummary(params) {
  return request.get('/api/v1/snapshots/ledger-summary', { params })
}

export function getLedgerSummaryBreakdown(skuId, params) {
  return request.get(`/api/v1/snapshots/ledger-summary/${skuId}/breakdown`, { params })
}

export function exportLedgerSummary(params) {
  return request.get('/api/v1/snapshots/ledger-summary/export', { params, responseType: 'blob' })
}

export function listSnapshotItems(params) {
  return request.get('/api/v1/snapshots/items', { params })
}

export function exportSnapshotItems(params) {
  return request.get('/api/v1/snapshots/items/export', { params, responseType: 'blob' })
}

export function triggerDailySnapshot() {
  return request.post('/api/v1/snapshots/trigger')
}
