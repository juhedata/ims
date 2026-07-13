import request from '@/utils/request'

export function login(data) {
  return request.post('/api/v1/auth/login', data)
}

export function getMe() {
  return request.get('/api/v1/auth/me')
}
