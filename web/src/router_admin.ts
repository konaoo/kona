import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import AdminLoginPage from './pages/admin/AdminLoginPage.vue'
import AdminOverviewPage from './pages/admin/AdminOverviewPage.vue'
import AdminUsersPage from './pages/admin/AdminUsersPage.vue'
import AdminInvitesPage from './pages/admin/AdminInvitesPage.vue'
import AdminApisPage from './pages/admin/AdminApisPage.vue'
import AdminConfigPage from './pages/admin/AdminConfigPage.vue'
import { useKonaStore } from './stores/composables'

const routes: RouteRecordRaw[] = [
  { path: '/admin', redirect: '/admin/overview' },
  { path: '/admin/login', component: AdminLoginPage },
  { path: '/admin/overview', component: AdminOverviewPage, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/users', component: AdminUsersPage, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/invites', component: AdminInvitesPage, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/apis', component: AdminApisPage, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/config', component: AdminConfigPage, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/admin/data', redirect: '/admin/overview' },
]

export const router = createRouter({
  history: createWebHistory('/'),
  routes,
})

router.beforeEach(async (to) => {
  const store = useKonaStore()
  void store.bootstrap()

  if (to.path === '/admin/login' && store.isAuthenticated.value && store.isAdmin.value) {
    return '/admin/overview'
  }
  if (to.meta.requiresAuth && !store.isAuthenticated.value) {
    return '/admin/login'
  }
  if (to.meta.requiresAdmin && !store.isAdmin.value) {
    window.location.assign('/app/home')
    return false
  }
  return true
})

router.afterEach(() => {
  document.title = '咔咔记账 - 管理后台'
})
