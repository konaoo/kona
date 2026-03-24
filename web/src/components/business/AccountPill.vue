<script setup lang="ts">
/**
 * AccountPill - 账户选择器组件
 * 用于切换不同账户/账户组
 */

import { computed } from 'vue'
import type { User } from '@/types'

export interface AccountPillProps {
  /** 用户信息 */
  user: User
  /** 账户余额 */
  balance?: number
  /** 币种 */
  currency?: string
  /** 是否显示余额 */
  showBalance?: boolean
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 是否可点击 */
  clickable?: boolean
}

const props = withDefaults(defineProps<AccountPillProps>(), {
  balance: 0,
  currency: 'CNY',
  showBalance: true,
  size: 'md',
  clickable: true
})

const emit = defineEmits<{
  click: []
}>()

const pillClass = computed(() => {
  return [
    'account-pill',
    `account-pill-${props.size}`,
    {
      'account-pill-clickable': props.clickable
    }
  ]
})

const displayName = computed(() => {
  return props.user.nickname || props.user.username
})

const formattedBalance = computed(() => {
  const currencySymbol = props.currency === 'CNY' ? '¥' : props.currency === 'HKD' ? '$' : 'US$'
  return `${currencySymbol}${props.balance.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
})

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<template>
  <div :class="pillClass" @click="handleClick">
    <div class="account-pill-avatar">
      <span class="avatar-text">{{ displayName.charAt(0).toUpperCase() }}</span>
    </div>

    <div class="account-pill-info">
      <div class="account-pill-name">{{ displayName }}</div>
      <div v-if="showBalance" class="account-pill-balance mono">
        {{ formattedBalance }}
      </div>
    </div>

    <div v-if="clickable" class="account-pill-arrow">
      ▼
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   ACCOUNT PILL - 账户选择器样式
   ═══════════════════════════════════════════════════════════════ */

.account-pill {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  transition: all var(--duration-base) var(--easing-default);
}

.account-pill-clickable {
  cursor: pointer;
  user-select: none;
}

.account-pill-clickable:hover {
  background: var(--s2);
  border-color: var(--border-hover);
}

.account-pill-clickable:active {
  transform: scale(0.98);
}

/* ───────────────────────────────────────────────────────────────
   AVATAR - 头像
   ─────────────────────────────────────────────────────────────── */

.account-pill-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--blue), var(--green));
  flex-shrink: 0;
}

.avatar-text {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: white;
  line-height: 1;
}

/* ───────────────────────────────────────────────────────────────
   INFO - 信息区
   ─────────────────────────────────────────────────────────────── */

.account-pill-info {
  flex: 1;
  min-width: 0;
}

.account-pill-name {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
}

.account-pill-balance {
  font-size: var(--font-size-sm);
  color: var(--sub);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ───────────────────────────────────────────────────────────────
   ARROW - 箭头
   ─────────────────────────────────────────────────────────────── */

.account-pill-arrow {
  font-size: 10px;
  color: var(--muted);
  flex-shrink: 0;
  transition: transform var(--duration-base) var(--easing-default);
}

.account-pill-clickable:hover .account-pill-arrow {
  transform: translateY(2px);
}

/* ───────────────────────────────────────────────────────────────
   SIZE VARIANTS - 尺寸变体
   ─────────────────────────────────────────────────────────────── */

.account-pill-sm .account-pill-avatar {
  width: 28px;
  height: 28px;
}

.account-pill-sm .avatar-text {
  font-size: var(--font-size-sm);
}

.account-pill-sm .account-pill-name {
  font-size: var(--font-size-sm);
}

.account-pill-sm .account-pill-balance {
  font-size: var(--font-size-xs);
}

.account-pill-lg .account-pill-avatar {
  width: 44px;
  height: 44px;
}

.account-pill-lg .avatar-text {
  font-size: var(--font-size-lg);
}

.account-pill-lg .account-pill-name {
  font-size: var(--font-size-md);
}

.account-pill-lg .account-pill-balance {
  font-size: var(--font-size-base);
}
</style>
