import request from '@/utils/request'

export function listInboundOrders(params) {
  return request.get('/api/v1/inbound/orders', { params })
}

export function getInboundOrder(id) {
  const params = isNaN(Number(id)) ? { lookup_by: 'order_no' } : {}
  return request.get(`/api/v1/inbound/orders/${id}`, { params })
}

export function createInboundOrder(data) {
  return request.post('/api/v1/inbound/orders', data)
}

export function updateInboundOrder(id, data) {
  return request.put(`/api/v1/inbound/orders/${id}`, data)
}

export function submitInboundOrder(id) {
  return request.post(`/api/v1/inbound/orders/${id}/submit`)
}

export function approveInboundOrder(id) {
  return request.post(`/api/v1/inbound/orders/${id}/approve`)
}

export function cancelInboundOrder(id) {
  return request.post(`/api/v1/inbound/orders/${id}/cancel`)
}

export function deleteInboundOrder(id) {
  return request.delete(`/api/v1/inbound/orders/${id}`)
}

export function generateInboundNo() {
  return request.get('/api/v1/inbound/orders/generate-no')
}

export function validateSns(data) {
  return request.post('/api/v1/inbound/orders/validate-sns', data)
}

export function getReturnableItems(outboundOrderId, stockCondition, options = {}) {
  const params = {
    outbound_order_id: outboundOrderId,
    stock_condition: stockCondition,
    page: options.page ?? 1,
    page_size: options.page_size ?? 50,
  }
  if (options.exclude_inbound_order_id != null) {
    params.exclude_inbound_order_id = options.exclude_inbound_order_id
  }
  if (options.keyword) params.keyword = options.keyword
  if (options.sku_id) params.sku_id = options.sku_id
  if (options.category_id) params.category_id = options.category_id
  return request.get('/api/v1/inbound/orders/returnable-items', { params })
}
