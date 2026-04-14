/**
 * 组件库入口文件
 * 统一导出所有组件
 */

// ───────────────────────────────────────────────────────────────
// BASE COMPONENTS - 基础组件
// ───────────────────────────────────────────────────────────────

export { default as Button } from './base/Button.vue'
export { default as Input } from './base/Input.vue'
export { default as Select } from './base/Select.vue'
export { default as Modal } from './base/Modal.vue'
export { default as Tabs } from './base/Tabs.vue'
export { default as Badge } from './base/Badge.vue'
export { default as Tag } from './base/Tag.vue'
export { default as Card } from './base/Card.vue'
export { default as Progress } from './base/Progress.vue'
export { default as Table } from './base/Table.vue'
export { default as FormItem } from './base/FormItem.vue'

// ───────────────────────────────────────────────────────────────
// BUSINESS COMPONENTS - 业务组件
// ───────────────────────────────────────────────────────────────

export { default as PositionCard } from './business/PositionCard.vue'
export { default as MarketTag } from './business/MarketTag.vue'
export { default as AccountPill } from './business/AccountPill.vue'
export { default as Calendar } from './business/Calendar.vue'
export { default as NewsCard } from './business/NewsCard.vue'
export { default as RankingCard } from './business/RankingCard.vue'
export { default as PnLBar } from './business/PnLBar.vue'
export { default as AssetSummary } from './business/AssetSummary.vue'
export { default as IconButton } from './business/IconButton.vue'
export { default as InvestTradeModal } from './business/InvestTradeModal.vue'
export { default as LedgerManageModal } from './business/LedgerManageModal.vue'

// ───────────────────────────────────────────────────────────────
// TYPE EXPORTS - 类型导出
// ───────────────────────────────────────────────────────────────

export type { ButtonProps } from './base/Button.vue'
export type { InputProps } from './base/Input.vue'
export type { SelectProps, SelectOption } from './base/Select.vue'
export type { ModalProps } from './base/Modal.vue'
export type { TabsProps, Tab } from './base/Tabs.vue'
export type { BadgeProps } from './base/Badge.vue'
export type { TagProps } from './base/Tag.vue'
export type { CardProps } from './base/Card.vue'
export type { ProgressProps } from './base/Progress.vue'
export type { TableColumn, TableProps } from './base/Table.vue'
export type { FormItemProps } from './base/FormItem.vue'

export type { PositionCardProps } from './business/PositionCard.vue'
export type { MarketTagProps } from './business/MarketTag.vue'
export type { AccountPillProps } from './business/AccountPill.vue'
export type { CalendarProps } from './business/Calendar.vue'
export type { NewsCardProps } from './business/NewsCard.vue'
export type { RankingCardProps, RankingItem } from './business/RankingCard.vue'
export type { PnLBarProps } from './business/PnLBar.vue'
export type { AssetSummaryProps } from './business/AssetSummary.vue'
export type { IconButtonProps } from './business/IconButton.vue'
