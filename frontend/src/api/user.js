import request from '@/utils/request'

export function listUsers(params) {
  return request.get('/api/v1/users', { params })
}

export function createUser(data) {
  return request.post('/api/v1/users', data)
}

export function updateUser(id, data) {
  return request.put(`/api/v1/users/${id}`, data)
}

export function toggleUserStatus(id) {
  return request.patch(`/api/v1/users/${id}/status`)
}

export function deleteUser(id) {
  return request.delete(`/api/v1/users/${id}`)
}

export function changePassword(data) {
  return request.post('/api/v1/users/change-password', data)
}
