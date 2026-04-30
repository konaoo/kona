import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useSessionCoordinatorStore } from './stores/sessionCoordinator'

const routes: RouteRecordRaw[] = [
  { path: '/admin', redirect: '/admin/overview' },
  { path: '/admin/login', component: () => import('./pages/admin/AdminLoginPage.vue') },
  { path: '/admin/overview', component: () => import('./pages/admin/AdminOverviewPage.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/users', component: () => import('./pages/admin/AdminUsersPage.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/invites', component: () => import('./pages/admin/AdminInvitesPage.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/apis', component: () => import('./pages/admin/AdminApisPage.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/config', component: () => import('./pages/admin/AdminConfigPage.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/ai', component: () => import('./pages/admin/AdminAiPage.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/data', redirect: '/admin/overview' },
]

export const router = createRouter({
  history: createWebHistory('/'),
  routes,
})

router.beforeEach(async (to) => {
  const sessionCoordinatorStore = useSessionCoordinatorStore()
  await sessionCoordinatorStore.bootstrap()

  if (
    to.path === '/admin/login' &&
    sessionCoordinatorStore.isAuthenticated &&
    sessionCoordinatorStore.isAdmin
  ) {
    return '/admin/overview'
  }
  if (to.meta.requiresAuth && !sessionCoordinatorStore.isAuthenticated) {
    return '/admin/login'
  }
  if (to.meta.requiresAdmin && !sessionCoordinatorStore.isAdmin) {
    window.location.assign('/app/home')
    return false
  }
  return true
})

router.afterEach(() => {
  document.title = '咔咔记账 - 管理后台'
})
