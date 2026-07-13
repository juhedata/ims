import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './style.css'
import { formatDateTime } from './utils/datetime'
import { useBrandStore } from './stores/brand'

const app = createApp(App)

app.config.globalProperties.$formatDateTime = formatDateTime

const pinia = createPinia()
app.use(pinia)
app.use(router)

const brand = useBrandStore(pinia)
brand.fetchBranding().finally(() => {
  app.mount('#app')
})
