import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useSessionCoordinatorStore } from './stores/sessionCoordinator'

const routes: RouteRecordRaw[] = [
  { path: '/', component: () => import('./views/Landing.vue') },
  { path: '/app', redirect: '/app/home' },
  { path: '/app/login', component: () => import('./pages/app/AppLoginPage.vue') },
  { path: '/app/register', component: () => import('./pages/app/AppLoginPage.vue') },
  { path: '/app/home', component: () => import('./pages/app/AppHomePage.vue'), meta: { requiresAuth: true } },
  { path: '/app/invest', component: () => import('./pages/app/AppInvestPage.vue'), meta: { requiresAuth: true } },
  { path: '/app/analysis', component: () => import('./pages/app/AppAnalysisPage.vue'), meta: { requiresAuth: true } },
  { path: '/app/news', component: () => import('./pages/app/AppNewsPage.vue'), meta: { requiresAuth: true } },
  { path: '/app/me', component: () => import('./pages/app/AppMePage.vue'), meta: { requiresAuth: true } },
  { path: '/app/profile', redirect: '/app/me' },
  { path: '/app/asset/:code', component: () => import('./pages/app/AppAssetDetailPage.vue'), meta: { requiresAuth: true } },

]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const sessionCoordinatorStore = useSessionCoordinatorStore()
  await sessionCoordinatorStore.bootstrap()

  if (
    (to.path === '/app/login' || to.path === '/app/register') &&
    sessionCoordinatorStore.isAuthenticated
  ) {
    return '/app/home'
  }
  if (to.meta.requiresAuth && !sessionCoordinatorStore.isAuthenticated) {
    return '/app/login'
  }
  return true
})

router.afterEach(() => {
  document.title = '咔咔记账 - 投资记录工具'
})
