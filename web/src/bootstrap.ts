import { createApp } from 'vue'
import { createPinia } from 'pinia'
import type { Router } from 'vue-router'
import App from './App.vue'

type BootMode = 'app' | 'admin' | 'portal'

const BOOT_CLASS_MAP: Record<BootMode, string> = {
  app: 'app-boot',
  admin: 'admin-boot',
  portal: 'portal-boot',
}

export const bootApp = (router: Router, mode: BootMode) => {
  const pinia = createPinia()
  const app = createApp(App)
  app.use(pinia)
  app.use(router)
  app.mount('#app')

  const root = document.documentElement
  Object.values(BOOT_CLASS_MAP).forEach((cls) => root.classList.remove(cls))
  root.classList.add(BOOT_CLASS_MAP[mode])
}
