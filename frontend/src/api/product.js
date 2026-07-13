import request from '@/utils/request'

export function listCategories() {
  return request.get('/api/v1/products/categories')
}

export function createCategory(data) {
  return request.post('/api/v1/products/categories', data)
}

export function updateCategory(id, data) {
  return request.put(`/api/v1/products/categories/${id}`, data)
}

export function deleteCategory(id) {
  return request.delete(`/api/v1/products/categories/${id}`)
}

export function listSkus(params) {
  return request.get('/api/v1/products/skus', { params })
}

export function createSku(data) {
  return request.post('/api/v1/products/skus', data)
}

export function updateSku(id, data) {
  return request.put(`/api/v1/products/skus/${id}`, data)
}

export function deleteSku(id) {
  return request.delete(`/api/v1/products/skus/${id}`)
}
