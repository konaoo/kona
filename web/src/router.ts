import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import PortalPage from './pages/portal/PortalPage.vue'
import AppLoginPage from './pages/app/AppLoginPage.vue'
import AppHomePage from './pages/app/AppHomePage.vue'
import AppInvestPage from './pages/app/AppInvestPage.vue'
import AppAnalysisPage from './pages/app/AppAnalysisPage.vue'
import AppNewsPage from './pages/app/AppNewsPage.vue'
import AppMePage from './pages/app/AppMePage.vue'
import AppAssetDetailPage from './pages/app/AppAssetDetailPage.vue'
import AdminLoginPage from './pages/admin/AdminLoginPage.vue'
import AdminOverviewPage from './pages/admin/AdminOverviewPage.vue'
import AdminUsersPage from './pages/admin/AdminUsersPage.vue'
import AdminInvitesPage from './pages/admin/AdminInvitesPage.vue'
import AdminApisPage from './pages/admin/AdminApisPage.vue'
import AdminConfigPage from './pages/admin/AdminConfigPage.vue'
import { useKonaStore } from './shared/store'

const routes: RouteRecordRaw[] = [
  { path: '/', component: PortalPage },
  { path: '/app', redirect: '/app/home' },
  { path: '/app/login', component: AppLoginPage },
  { path: '/app/register', component: AppLoginPage },
  { path: '/app/home', component: AppHomePage, meta: { requiresAuth: true } },
  { path: '/app/invest', component: AppInvestPage, meta: { requiresAuth: true } },
  { path: '/app/analysis', component: AppAnalysisPage, meta: { requiresAuth: true } },
  { path: '/app/news', component: AppNewsPage, meta: { requiresAuth: true } },
  { path: '/app/me', component: AppMePage, meta: { requiresAuth: true } },
  { path: '/app/profile', redirect: '/app/me' },
  { path: '/app/asset/:code', component: AppAssetDetailPage, meta: { requiresAuth: true } },

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
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const store = useKonaStore()
  await store.bootstrap()

  if ((to.path === '/app/login' || to.path === '/app/register') && store.isAuthenticated.value) {
    return '/app/home'
  }
  if (to.path === '/admin/login' && store.isAuthenticated.value && store.isAdmin.value) {
    return '/admin/overview'
  }
  if (to.meta.requiresAuth && !store.isAuthenticated.value) {
    return to.path.startsWith('/admin') ? '/admin/login' : '/app/login'
  }
  if (to.meta.requiresAdmin && !store.isAdmin.value) {
    return '/app/home'
  }
  return true
})
