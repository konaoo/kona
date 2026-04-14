/**
 * Session Coordinator Store - 统一管理 Web 端会话恢复和认证入口
 */

import { computed } from 'vue'
import { defineStore } from 'pinia'
import { useAuthStore } from './auth'
import { useRefreshCoordinatorStore } from './refreshCoordinator'
import { useLedgerScopeStore } from './ledgerScope'

export const useSessionCoordinatorStore = defineStore('sessionCoordinator', () => {
  const authStore = useAuthStore()
  const refreshCoordinatorStore = useRefreshCoordinatorStore()
  const bootstrapped = computed(() => authStore.bootstrapped)
  const isAuthenticated = computed(() => authStore.isAuthenticated)
  const isAdmin = computed(() => authStore.isAdmin)
  const authError = computed(() => authStore.authError)
  const user = computed(() => authStore.user)
  const lastBootstrapResult = computed(() => authStore.lastBootstrapResult)

  async function bootstrap() {
    const result = await authStore.bootstrap()
    refreshCoordinatorStore.ensureHydrated()
    if (authStore.isAuthenticated) {
      const ledgerStore = useLedgerScopeStore()
      void ledgerStore.loadLedgers()
    }
    return result
  }

  async function login(username: string, password: string) {
    await authStore.login(username, password)
    refreshCoordinatorStore.ensureHydrated()
    const ledgerStore = useLedgerScopeStore()
    void ledgerStore.loadLedgers()
  }

  async function register(username: string, password: string, inviteCode: string) {
    await authStore.register(username, password, inviteCode)
    refreshCoordinatorStore.ensureHydrated()
  }

  async function logout() {
    await authStore.logout()
    refreshCoordinatorStore.ensureHydrated()
  }

  return {
    bootstrapped,
    isAuthenticated,
    isAdmin,
    authError,
    user,
    lastBootstrapResult,
    bootstrap,
    login,
    register,
    logout,
  }
})
