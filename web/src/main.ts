import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { router } from './router'

// Design System - 新的设计系统
import './styles/tokens.css'
import './styles/base.css'
import './styles/mixins.css'
import './styles/animations.css'

// Legacy Styles - 保留旧样式，逐步迁移
import './styles/legacy.css'
import './styles/admin-console.css'

// Pinia State Management
const pinia = createPinia()

const app = createApp(App)
app.use(pinia)
app.use(router)
app.mount('#app')
