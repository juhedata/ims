import request from '@/utils/request'

export function listCustomers(params) {
  return request.get('/api/v1/customers', { params })
}
