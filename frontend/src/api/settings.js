import request from '@/utils/request'

/** 公开：获取品牌配置 */
export function getBranding() {
  return request.get('/api/v1/settings/branding')
}

/** 管理员：更新项目名称与副标题 */
export function updateBranding(data) {
  return request.put('/api/v1/settings/branding', data)
}

/** 管理员：上传 Logo */
export function uploadLogo(file) {
  const form = new FormData()
  form.append('file', file)
  return request.post('/api/v1/settings/branding/logo', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/** 管理员：清除 Logo */
export function clearLogo() {
  return request.delete('/api/v1/settings/branding/logo')
}
