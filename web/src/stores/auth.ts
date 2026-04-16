/**
 * Auth Store - 用户认证和授权
 */

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api, refreshAuthSession } from '@/shared/http'
import { finishAsyncFlow, startAsyncFlow, type AsyncFlowResult } from '@/shared/asyncFlow'
import {
  clearAuth,
  persistAuth,
  persistUser,
  readAccessToken,
  readStoredUser,
} from '@/shared/auth'
import type { User } from './types'
import { AUTH_BOOTSTRAP_TIMEOUT_MS } from './types'

export const useAuthStore = defineStore('auth', () => {
  // ───────────────────────────────────────────────────────────────
  // State
  // ───────────────────────────────────────────────────────────────

  const bootstrapped = ref(false)
  const loading = ref(false)
  const token = ref(readAccessToken() || '')
  const refreshToken = ref('')
  const user = ref<User | null>(readStoredUser<User>() || null)
  const authError = ref('')
  const lastBootstrapResult = ref<AsyncFlowResult | null>(null)

  // ───────────────────────────────────────────────────────────────
  // Computed
  // ───────────────────────────────────────────────────────────────

  const isAuthenticated = computed(() => Boolean(token.value))
  const isAdmin = computed(() => Boolean(user.value && Number(user.value.is_admin || 0) === 1))
  const userId = computed(() => String(user.value?.id || '').trim() || 'guest')

  function shouldClearAuthOnBootstrapError(error: unknown) {
    const status = Number((error as { status?: unknown })?.status || 0)
    if (error instanceof Error && error.message === 'AUTH_BOOTSTRAP_TIMEOUT') {
      return false
    }
    return status === 401 || status === 403
  }

  // ───────────────────────────────────────────────────────────────
  // Actions
  // ───────────────────────────────────────────────────────────────

  /**
   * Bootstrap - 初始化认证状态
   */
  async function bootstrap() {
    const flow = startAsyncFlow('web.auth.bootstrap')
    if (bootstrapped.value) {
      lastBootstrapResult.value = finishAsyncFlow(flow, 'skip:bootstrapped')
      return lastBootstrapResult.value
    }
    bootstrapped.value = true

    if (!token.value) {
      const restored = await refreshAuthSession()
      token.value = readAccessToken() || ''
      user.value = readStoredUser<User>() || null
      refreshToken.value = ''
      if (!restored || !token.value) {
        clearAuthState()
        lastBootstrapResult.value = finishAsyncFlow(flow, 'skip:no-session')
        return lastBootstrapResult.value
      }
    }

    let timeoutId: ReturnType<typeof setTimeout> | null = null
    try {
      const timeoutPromise = new Promise<never>((_, reject) => {
        timeoutId = setTimeout(
          () => reject(new Error('AUTH_BOOTSTRAP_TIMEOUT')),
          AUTH_BOOTSTRAP_TIMEOUT_MS
        )
      })

      const me = await Promise.race([
        api.get<User>('/api/auth/me', true),
        timeoutPromise
      ]) as User

      if (timeoutId) clearTimeout(timeoutId)

      user.value = me
      persistUser(me)
      lastBootstrapResult.value = finishAsyncFlow(flow, 'profile-loaded')
      return lastBootstrapResult.value
    } catch (error) {
      if (timeoutId) clearTimeout(timeoutId)
      if (shouldClearAuthOnBootstrapError(error)) {
        clearAuthState()
      }
      lastBootstrapResult.value = finishAsyncFlow(flow, 'failed', error)
      return lastBootstrapResult.value
    }
  }

  /**
   * Login - 用户登录
   */
  async function login(username: string, password: string) {
    authError.value = ''

    const payload = await api.post<Record<string, unknown>>('/api/auth/login', {
      username,
      password,
    }, false)

    const accessToken = String(payload.access_token || '')
    if (!accessToken) {
      throw new Error('登录返回缺少 access token')
    }

    token.value = accessToken
    refreshToken.value = ''
    user.value = (payload.user || null) as User | null

    persistAuth(accessToken, user.value)
  }

  /**
   * Register - 用户注册
   */
  async function register(username: string, password: string, inviteCode: string) {
    const payload = await api.post<Record<string, unknown>>('/api/auth/register', {
      username,
      password,
      invite_code: inviteCode,
    }, false)

    const accessToken = String(payload.access_token || '')
    if (!accessToken) {
      throw new Error('注册返回缺少 access token')
    }

    token.value = accessToken
    refreshToken.value = ''
    user.value = (payload.user || null) as User | null

    persistAuth(accessToken, user.value)
  }

  /**
   * Logout - 用户登出
   */
  async function logout() {
    try {
      await api.post('/api/auth/logout', undefined, true)
    } catch {
      // ignore logout errors
    } finally {
      clearAuthState()
    }
  }

  /**
   * ClearAuthState - 清除认证状态
   */
  function clearAuthState() {
    clearAuth()
    token.value = ''
    refreshToken.value = ''
    user.value = null
    bootstrapped.value = false
  }

  /**
   * SetAuthError - 设置认证错误
   */
  function setAuthError(error: string) {
    authError.value = error
  }

  // ───────────────────────────────────────────────────────────────
  // Return
  // ───────────────────────────────────────────────────────────────

  return {
    // State
    bootstrapped,
    loading,
    token,
    refreshToken,
    user,
    authError,
    lastBootstrapResult,

    // Computed
    isAuthenticated,
    isAdmin,
    userId,

    // Actions
    bootstrap,
    login,
    register,
    logout,
    clearAuthState,
    setAuthError,
  }
})
