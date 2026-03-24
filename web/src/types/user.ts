/* ═══════════════════════════════════════════════════════════════
   USER TYPES - 用户类型定义
   ═══════════════════════════════════════════════════════════════ */

import type { Currency } from './index'

/**
 * 用户偏好设置
 */
export type UserPreferences = {
  theme: 'light' | 'dark' | 'auto'
  language: 'zh-CN' | 'en-US'
  currency: Currency
  privacy_mode: boolean
  notifications_enabled: boolean
  auto_refresh_enabled: boolean
}

/**
 * 用户会话
 */
export type UserSession = {
  access_token: string
  refresh_token: string
  expires_at: number
  user: UserProfile
}

/**
 * 用户资料
 */
export type UserProfile = {
  id: string
  username: string
  nickname?: string
  email?: string
  avatar?: string
  is_admin: boolean
  is_active: boolean
  created_at: string
  build_start_at?: string
  updated_at: string
  preferences: UserPreferences
}

export type User = UserProfile

/**
 * 用户统计
 */
export type UserStats = {
  total_assets: number
  total_pnl: number
  position_count: number
  account_count: number
  days_active: number
}

/**
 * 邀请码
 */
export type InviteCode = {
  code: string
  max_uses: number
  used_count: number
  created_by: string
  created_at: string
  expires_at?: string
}

/**
 * 邀请码状态
 */
export type InviteCodeStatus = 'active' | 'expired' | 'depleted'

/**
 * 用户角色
 */
export type UserRole = 'admin' | 'user' | 'guest'

/**
 * 权限
 */
export type Permission = 'read' | 'write' | 'admin'

/**
 * 用户活动日志
 */
export type UserActivityLog = {
  id: string
  user_id: string
  action: string
  ip_address?: string
  user_agent?: string
  created_at: string
}

/**
 * 密码修改请求
 */
export type ChangePasswordRequest = {
  old_password: string
  new_password: string
  confirm_password: string
}

/**
 * 邮箱更新请求
 */
export type UpdateEmailRequest = {
  new_email: string
  password: string
}

/**
 * 用户设置更新请求
 */
export type UpdateSettingsRequest = {
  nickname?: string
  avatar?: string
  preferences?: Partial<UserPreferences>
}
