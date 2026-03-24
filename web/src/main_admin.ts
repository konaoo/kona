import { bootApp } from './bootstrap'
import { router } from './router_admin'

// Design System - 新的设计系统
import './styles/tokens.css'
import './styles/base.css'
import './styles/mixins.css'
import './styles/animations.css'
import './styles/shared.css'

// Legacy Styles - 保留旧样式，逐步迁移
import './styles/legacy.css'
import './styles/admin-console.css'

bootApp(router, 'admin')
