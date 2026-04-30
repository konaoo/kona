import { bootApp } from './bootstrap'
import { router } from './router'

// Design System - 新的设计系统
import './styles/tokens.css'
import './styles/base.css'
import './styles/mixins.css'
import './styles/animations.css'
import './styles/shared.css'

const path = window.location.pathname || '/'
const bootMode = path === '/' || path === '/index.html' ? 'portal' : 'app'

bootApp(router, bootMode)
