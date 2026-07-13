import request from '@/utils/request'

export function listItems(params) {
  return request.get('/api/v1/inventory/items', { params })
}

export function exportItems(params) {
  return request.get('/api/v1/inventory/items/export', { params, responseType: 'blob' })
}

export function listAvailableItems(params) {
  return request.get('/api/v1/inventory/items/available', { params })
}

export function getItemHistory(itemSn) {
  return request.get(`/api/v1/inventory/items/${itemSn}/history`)
}

export function completeOfflineSale(itemSn) {
  return request.post(`/api/v1/inventory/items/${itemSn}/complete-offline-sale`)
}
