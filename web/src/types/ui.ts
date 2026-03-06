/* ═══════════════════════════════════════════════════════════════
   UI TYPES - UI 组件类型定义
   ═══════════════════════════════════════════════════════════════ */

import type { MarketCode, Currency } from './index'

/**
 * 按钮 Props
 */
export type ButtonProps = {
  type?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  icon?: string
  block?: boolean
}

/**
 * 输入框 Props
 */
export type InputProps = {
  modelValue: string | number
  type?: 'text' | 'number' | 'password' | 'email'
  placeholder?: string
  disabled?: boolean
  error?: string
  icon?: string
  suffix?: string
  maxlength?: number
}

/**
 * 选择框 Props
 */
export type SelectProps = {
  modelValue: string | number
  options: SelectOption[]
  placeholder?: string
  disabled?: boolean
  error?: string
}

/**
 * 选择框选项
 */
export type SelectOption = {
  label: string
  value: string | number
  disabled?: boolean
}

/**
 * 模态框 Props
 */
export type ModalProps = {
  show: boolean
  title?: string
  subtitle?: string
  width?: string
  closable?: boolean
  maskClosable?: boolean
}

/**
 * Tab Props
 */
export type TabProps = {
  modelValue: string | number
  options: TabOption[]
  type?: 'line' | 'card'
}

/**
 * Tab 选项
 */
export type TabOption = {
  label: string
  value: string | number
  icon?: string
  disabled?: boolean
  badge?: number | string
}

/**
 * 进度条 Props
 */
export type ProgressProps = {
  percent: number
  type?: 'line' | 'circle'
  size?: 'sm' | 'md' | 'lg'
  showInfo?: boolean
}

/**
 * 徽章 Props
 */
export type BadgeProps = {
  text?: string | number
  type?: 'up' | 'down' | 'neutral' | 'success' | 'warning' | 'danger'
  dot?: boolean
}

/**
 * 标签 Props
 */
export type TagProps = {
  text: string
  type?: 'hk' | 'us' | 'a' | 'fund'
  size?: 'sm' | 'md'
  closable?: boolean
}

/**
 * 卡片 Props
 */
export type CardProps = {
  title?: string
  subtitle?: string
  extra?: string
  padding?: string
  hoverable?: boolean
}

/**
 * 表格列定义
 */
export type TableColumn = {
  key: string
  title: string
  width?: string | number
  align?: 'left' | 'center' | 'right'
  sortable?: boolean
  render?: (row: unknown) => string
}

/**
 * 表格 Props
 */
export type TableProps = {
  columns: TableColumn[]
  data: unknown[]
  loading?: boolean
  bordered?: boolean
  size?: 'sm' | 'md' | 'lg'
}

/**
 * 下拉菜单项
 */
export type MenuItem = {
  key: string
  label: string
  icon?: string
  disabled?: boolean
  divided?: boolean
  children?: MenuItem[]
}

/**
 * 日历单元格
 */
export type CalendarCell = {
  date: number
  month: number
  year: number
  is_today: boolean
  is_current_month: boolean
  pnl?: number
  events?: string[]
}

/**
 * 新闻卡片 Props
 */
export type NewsCardProps = {
  id: string
  category: string
  category_label: string
  source: string
  title: string
  summary: string
  symbol?: string
  impact_text: string
  impact: 'up' | 'down' | 'neu'
  important: boolean
  published_at: string
}

/**
 * 排行榜项
 */
export type RankingCardProps = {
  rank: number
  code: string
  name: string
  pnl: string
  rate: string
  medal?: 'gold' | 'silver' | 'bronze'
}

/**
 * 持仓卡片 Props
 */
export type PositionCardProps = {
  code: string
  name: string
  market: MarketCode
  qty: number
  price: number
  value: number
  pnl: number
  rate: number
  progress: number
}

/**
 * 资产类型标签
 */
export type AssetTypeTag = {
  type: 'stock' | 'fund' | 'bond'
  market: MarketCode
  label: string
  color: string
  background: string
}

/**
 * 账户卡片 Props
 */
export type AccountCardProps = {
  id: string
  name: string
  type: 'cash' | 'other' | 'debt'
  currency: Currency
  amount: number
  emoji?: string
  color?: string
}

/**
 * 期间统计卡片 Props
 */
export type PeriodCardProps = {
  label: string
  value: string
  rate: string
  selected?: boolean
}

/**
 * 工具栏按钮 Props
 */
export type ToolbarButtonProps = {
  icon: string
  label?: string
  title?: string
  active?: boolean
  disabled?: boolean
}

/**
 * 通知类型
 */
export type NotificationType = 'success' | 'warning' | 'error' | 'info'

/**
 * 通知 Props
 */
export type NotificationProps = {
  type: NotificationType
  title?: string
  message: string
  duration?: number
  closable?: boolean
}

/**
 * 加载状态 Props
 */
export type LoadingProps = {
  loading: boolean
  delay?: number
  tip?: string
  fullscreen?: boolean
}

/**
 * 空状态 Props
 */
export type EmptyStateProps = {
  image?: string
  description?: string
  actionText?: string
}
