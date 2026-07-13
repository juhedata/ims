import request from '@/utils/request'

export function getPendingAudit() {
  return request.get('/api/v1/dashboard/pending-audit')
}

export function getStockSummary() {
  return request.get('/api/v1/dashboard/stock-summary')
}

export function getPartnerSummary(params) {
  return request.get('/api/v1/dashboard/partner-summary', {
    params,
    paramsSerializer: { indexes: null },
  })
}
