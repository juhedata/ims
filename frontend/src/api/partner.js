import request from '@/utils/request'

export function listGroups() {
  return request.get('/api/v1/partners/groups')
}

export function createGroup(data) {
  return request.post('/api/v1/partners/groups', data)
}

export function updateGroup(id, data) {
  return request.put(`/api/v1/partners/groups/${id}`, data)
}

export function deleteGroup(id) {
  return request.delete(`/api/v1/partners/groups/${id}`)
}

export function listPartners(params) {
  return request.get('/api/v1/partners', { params })
}

export function createPartner(data) {
  return request.post('/api/v1/partners', data)
}

export function updatePartner(id, data) {
  return request.put(`/api/v1/partners/${id}`, data)
}

export function deletePartner(id) {
  return request.delete(`/api/v1/partners/${id}`)
}
