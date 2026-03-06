/**
 * Auth Store - 用户认证和授权
 */

import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/shared/http'
import {
  clearAuth,
  persistAuth,
  persistUser,
  readAccessToken,
  readRefreshToken,
  readStoredUser,
} from '@/shared/auth'
import type { User } from './types'

export const useAuthStore = defineStore('auth', () => {
  // ───────────────────────────────────────────────────────────────
  // State
  // ───────────────────────────────────────────────────────────────

  const bootstrapped = ref(false)
  const loading = ref(false)
  const token = ref(readAccessToken() || '')
  const refreshToken = ref(readRefreshToken() || '')
  const user = ref<User | null>(readStoredUser<User>() || null)
  const authError = ref('')

  // ───────────────────────────────────────────────────────────────
  // Computed
  // ───────────────────────────────────────────────────────────────

  const isAuthenticated = computed(() => Boolean(token.value))
  const isAdmin = computed(() => Boolean(user.value && Number(user.value.is_admin || 0) === 1))
  const userId = computed(() => String(user.value?.id || '').trim() || 'guest')

  // ───────────────────────────────────────────────────────────────
  // Actions
  // ───────────────────────────────────────────────────────────────

  /**
   * Bootstrap - 初始化认证状态
   */
  async function bootstrap() {
    if (bootstrapped.value) return
    bootstrapped.value = true

    if (!token.value || !refreshToken.value) return

    let timeoutId: ReturnType<typeof setTimeout> | null = null
    try {
      const timeoutPromise = new Promise<never>((_, reject) => {
        timeoutId = setTimeout(
          () => reject(new Error('AUTH_BOOTSTRAP_TIMEOUT')),
          2500
        )
      })

      const me = await Promise.race([
        api.get<User>('/api/auth/me', true),
        timeoutPromise
      ]) as User

      if (timeoutId) clearTimeout(timeoutId)

      user.value = me
      persistUser(me)
    } catch {
      if (timeoutId) clearTimeout(timeoutId)
      clearAuthState()
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
    const newRefreshToken = String(payload.refresh_token || '')

    if (!accessToken || !newRefreshToken) {
      throw new Error('登录返回缺少 token')
    }

    token.value = accessToken
    refreshToken.value = newRefreshToken
    user.value = (payload.user || null) as User | null

    persistAuth(accessToken, newRefreshToken, user.value)
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
    const newRefreshToken = String(payload.refresh_token || '')

    if (!accessToken || !newRefreshToken) {
      throw new Error('注册返回缺少 token')
    }

    token.value = accessToken
    refreshToken.value = newRefreshToken
    user.value = (payload.user || null) as User | null

    persistAuth(accessToken, newRefreshToken, user.value)
  }

  /**
   * Logout - 用户登出
   */
  async function logout() {
    try {
      await api.post('/api/auth/logout', { refresh_token: refreshToken.value }, true)
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
