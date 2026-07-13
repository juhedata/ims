import request from '@/utils/request'

export function listOutboundOrders(params) {
  return request.get('/api/v1/outbound/orders', { params })
}

export function getOutboundOrder(id) {
  const params = isNaN(Number(id)) ? { lookup_by: 'order_no' } : {}
  return request.get(`/api/v1/outbound/orders/${id}`, { params })
}

export function createOutboundOrder(data) {
  return request.post('/api/v1/outbound/orders', data)
}

export function updateOutboundOrder(id, data) {
  return request.put(`/api/v1/outbound/orders/${id}`, data)
}

export function submitOutboundOrder(id) {
  return request.post(`/api/v1/outbound/orders/${id}/submit`)
}

export function approveOutboundOrder(id) {
  return request.post(`/api/v1/outbound/orders/${id}/approve`)
}

export function cancelOutboundOrder(id) {
  return request.post(`/api/v1/outbound/orders/${id}/cancel`)
}

export function deleteOutboundOrder(id) {
  return request.delete(`/api/v1/outbound/orders/${id}`)
}

export function generateOutboundNo() {
  return request.get('/api/v1/outbound/orders/generate-no')
}
