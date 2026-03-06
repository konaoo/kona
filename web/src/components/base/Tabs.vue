<script setup lang="ts">
/**
 * Tabs - 标签页组件
 * 用于组织和切换内容
 */

import { computed, ref } from 'vue'

export interface Tab {
  key: string
  label: string
  disabled?: boolean
  icon?: string
}

export interface TabsProps {
  /** 标签页数据 */
  tabs: Tab[]
  /** 默认激活的标签 */
  defaultKey?: string
  /** 标签页位置 */
  position?: 'top' | 'left' | 'right' | 'bottom'
  /** 标签页类型 */
  type?: 'line' | 'card' | 'segment'
  /** 标签页尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 是否可关闭 */
  closable?: boolean
}

const props = withDefaults(defineProps<TabsProps>(), {
  defaultKey: '',
  position: 'top',
  type: 'line',
  size: 'md',
  closable: false
})

const emit = defineEmits<{
  change: [key: string]
  close: [key: string]
}>()

const activeKey = ref(props.defaultKey || props.tabs[0]?.key || '')

const tabsClass = computed(() => {
  return [
    'tabs',
    `tabs-${props.position}`,
    `tabs-${props.type}`,
    `tabs-${props.size}`
  ]
})

const navClass = computed(() => {
  return [
    'tabs-nav',
    `tabs-nav-${props.position}`
  ]
})

const handleTabClick = (tab: Tab) => {
  if (tab.disabled) return
  activeKey.value = tab.key
  emit('change', tab.key)
}

const handleTabClose = (e: MouseEvent, tab: Tab) => {
  e.stopPropagation()
  emit('close', tab.key)
}

const isActive = (key: string) => activeKey.value === key
</script>

<template>
  <div :class="tabsClass">
    <div :class="navClass">
      <div
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-item"
        :class="{
          'tab-active': isActive(tab.key),
          'tab-disabled': tab.disabled
        }"
        @click="handleTabClick(tab)"
      >
        <span v-if="tab.icon" class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
        <span
          v-if="closable && !tab.disabled"
          class="tab-close"
          @click="handleTabClose($event, tab)"
        >
          ×
        </span>
      </div>
    </div>

    <div class="tabs-content">
      <slot :active-key="activeKey">
        <div v-for="tab in tabs" :key="tab.key" class="tab-pane">
          <div v-if="isActive(tab.key)">
            <slot :name="tab.key">{{ tab.label }}</slot>
          </div>
        </div>
      </slot>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   TABS COMPONENT - 标签页组件样式
   ═══════════════════════════════════════════════════════════════ */

.tabs {
  display: flex;
  width: 100%;
}

/* ───────────────────────────────────────────────────────────────
   TABS NAV - 导航栏
   ─────────────────────────────────────────────────────────────── */

.tabs-nav {
  display: flex;
  flex-shrink: 0;
}

.tabs-nav-top {
  flex-direction: row;
  border-bottom: 1px solid var(--border);
}

.tabs-nav-bottom {
  flex-direction: row;
  border-top: 1px solid var(--border);
  order: 2;
}

.tabs-nav-left {
  flex-direction: column;
  border-right: 1px solid var(--border);
}

.tabs-nav-right {
  flex-direction: column;
  border-left: 1px solid var(--border);
  order: 2;
}

/* ───────────────────────────────────────────────────────────────
   TAB ITEM - 标签项
   ─────────────────────────────────────────────────────────────── */

.tab-item {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--sub);
  cursor: pointer;
  user-select: none;
  transition: all var(--duration-base) var(--easing-default);
  white-space: nowrap;
}

.tab-item:hover:not(.tab-disabled) {
  color: var(--text);
}

.tab-active {
  color: var(--text);
}

.tab-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tab-icon {
  display: inline-flex;
  align-items: center;
  font-size: var(--font-size-md);
}

.tab-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-left: var(--space-1);
  font-size: 16px;
  line-height: 1;
  border-radius: var(--radius-sm);
  transition: all var(--duration-base) var(--easing-default);
}

.tab-close:hover {
  background: var(--border);
}

/* ───────────────────────────────────────────────────────────────
   TABS TYPE LINE - 线条型
   ─────────────────────────────────────────────────────────────── */

.tabs-line .tab-item::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--blue);
  transform: scaleX(0);
  transition: transform var(--duration-base) var(--easing-default);
}

.tabs-line.tabs-nav-bottom .tab-item::after {
  bottom: auto;
  top: 0;
}

.tabs-line.tabs-nav-left .tab-item::after {
  top: 0;
  bottom: 0;
  left: auto;
  right: 0;
  width: 2px;
  height: auto;
  transform: scaleY(0);
}

.tabs-line.tabs-nav-right .tab-item::after {
  top: 0;
  bottom: 0;
  left: 0;
  right: auto;
  width: 2px;
  height: auto;
  transform: scaleY(0);
}

.tabs-line .tab-active::after {
  transform: scale(1);
}

/* ───────────────────────────────────────────────────────────────
   TABS TYPE CARD - 卡片型
   ─────────────────────────────────────────────────────────────── */

.tabs-card .tab-item {
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  margin-right: var(--space-1);
}

.tabs-card.tabs-nav-left .tab-item {
  border-radius: var(--radius-md) 0 0 var(--radius-md);
  margin-right: 0;
  margin-bottom: var(--space-1);
}

.tabs-card.tabs-nav-right .tab-item {
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  margin-left: 0;
  margin-bottom: var(--space-1);
}

.tabs-card .tab-active {
  background: var(--bg);
  border-bottom-color: var(--bg);
}

.tabs-card.tabs-nav-bottom .tab-active {
  border-bottom-color: var(--border);
  border-top-color: var(--bg);
}

.tabs-card.tabs-nav-left .tab-active {
  border-right-color: var(--bg);
}

.tabs-card.tabs-nav-right .tab-active {
  border-left-color: var(--bg);
}

/* ───────────────────────────────────────────────────────────────
   TABS TYPE SEGMENT - 分段型
   ─────────────────────────────────────────────────────────────── */

.tabs-segment {
  background: var(--s1);
  border-radius: var(--radius-md);
  padding: var(--space-1);
  gap: var(--space-1);
}

.tabs-segment .tab-item {
  border-radius: var(--radius-sm);
  padding: var(--space-1) var(--space-3);
  color: var(--sub);
}

.tabs-segment .tab-active {
  background: var(--bg);
  color: var(--text);
  box-shadow: var(--shadow-sm);
}

/* ───────────────────────────────────────────────────────────────
   TABS CONTENT - 内容区
   ─────────────────────────────────────────────────────────────── */

.tabs-content {
  flex: 1;
  overflow: auto;
}

.tab-pane {
  animation: tab-fade-in var(--duration-base) var(--easing-default);
}

@keyframes tab-fade-in {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ───────────────────────────────────────────────────────────────
   TABS SIZES - 尺寸变体
   ─────────────────────────────────────────────────────────────── */

.tabs-sm .tab-item {
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-sm);
}

.tabs-md .tab-item {
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-base);
}

.tabs-lg .tab-item {
  padding: var(--space-3) var(--space-6);
  font-size: var(--font-size-md);
}
</style>
