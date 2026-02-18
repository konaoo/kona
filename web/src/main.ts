import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'
import './styles/tokens.css'
import './styles/legacy.css'

document.documentElement.classList.add('density-compact')

createApp(App).use(router).mount('#app')
