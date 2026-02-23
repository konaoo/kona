<template>
  <div class="legacy-shell legacy-page">
    <aside class="legacy-sidebar">
      <div class="legacy-logo">
        <span>⚡</span>
        <span>咔咔记账</span>
      </div>
      <RouterLink
        v-for="item in nav"
        :key="item.path"
        :to="item.path"
        class="legacy-menu-item"
        active-class="active"
      >
        <span>{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </RouterLink>
    </aside>

    <div class="legacy-main-content">
      <div class="legacy-fab-group" v-if="$slots.fab">
        <slot name="fab" />
      </div>
      <slot />
    </div>

    <nav class="legacy-mobile-nav">
      <RouterLink
        v-for="item in nav"
        :key="`m-${item.path}`"
        :to="item.path"
        class="legacy-mobile-nav-item"
        active-class="active"
      >
        <span>{{ item.icon }}</span>
        <span>{{ item.shortLabel }}</span>
      </RouterLink>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'

const nav = [
  { path: '/app/home', label: '我的资产', shortLabel: '资产', icon: '💰' },
  { path: '/app/invest', label: '我的投资', shortLabel: '投资', icon: '💼' },
  { path: '/app/analysis', label: '资产分析', shortLabel: '分析', icon: '📊' },
  { path: '/app/news', label: '市场分析', shortLabel: '快讯', icon: '⚡' },
  { path: '/app/me', label: '设置', shortLabel: '设置', icon: '⚙️' },
]
</script>
