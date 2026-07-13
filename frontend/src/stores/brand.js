import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getBranding } from '@/api/settings'

const DEFAULT_NAME = 'IMS'
const DEFAULT_SUBTITLE = '一物一码库存管理系统'

export const useBrandStore = defineStore('brand', () => {
  const appName = ref(DEFAULT_NAME)
  const appSubtitle = ref(DEFAULT_SUBTITLE)
  const logoUrl = ref(null)
  const loaded = ref(false)

  function applyDocumentTitle() {
    document.title = appName.value || DEFAULT_NAME
  }

  function apply(data) {
    if (!data) return
    appName.value = data.app_name || DEFAULT_NAME
    appSubtitle.value = data.app_subtitle || DEFAULT_SUBTITLE
    logoUrl.value = data.logo_url || null
    applyDocumentTitle()
  }

  async function fetchBranding() {
    try {
      const res = await getBranding()
      apply(res.data)
    } catch {
      appName.value = DEFAULT_NAME
      appSubtitle.value = DEFAULT_SUBTITLE
      logoUrl.value = null
      applyDocumentTitle()
    } finally {
      loaded.value = true
    }
  }

  return { appName, appSubtitle, logoUrl, loaded, apply, fetchBranding }
})
