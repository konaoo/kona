import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'
import './styles/tokens.css'
import './styles/legacy.css'
import './styles/admin-console.css'

createApp(App).use(router).mount('#app')
