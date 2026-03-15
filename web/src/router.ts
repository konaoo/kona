import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import LandingPage from './views/Landing.vue'
import AppLoginPage from './pages/app/AppLoginPage.vue'
import AppHomePage from './pages/app/AppHomePage.vue'
import AppInvestPage from './pages/app/AppInvestPage.vue'
import AppAnalysisPage from './pages/app/AppAnalysisPage.vue'
import AppNewsPage from './pages/app/AppNewsPage.vue'
import AppMePage from './pages/app/AppMePage.vue'
import AppAssetDetailPage from './pages/app/AppAssetDetailPage.vue'
import { useKonaStore } from './stores/composables'

const routes: RouteRecordRaw[] = [
  { path: '/', component: LandingPage },
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

]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const store = useKonaStore()
  void store.bootstrap()

  if ((to.path === '/app/login' || to.path === '/app/register') && store.isAuthenticated.value) {
    return '/app/home'
  }
  if (to.meta.requiresAuth && !store.isAuthenticated.value) {
    return '/app/login'
  }
  return true
})

router.afterEach(() => {
  document.title = '咔咔记账 - 投资记录工具'
})
