import request from '@/utils/request'

export function listAuditLogs(params) {
  return request.get('/api/v1/audit-logs', { params })
}
