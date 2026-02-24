<template>
  <div class="legacy-shell legacy-page" :data-theme="theme">
    <aside class="legacy-sidebar">
      <div class="legacy-logo">
        <span>⚡</span>
        <span>咔咔记账</span>
      </div>
      <div class="legacy-nav-links">
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
      </div>

      <div class="legacy-sidebar-profile">
        <button class="legacy-profile-btn" type="button" @click="goMe">
          <img v-if="avatarSrc" :src="avatarSrc" alt="头像" class="legacy-profile-avatar" />
          <span v-else class="legacy-profile-avatar legacy-profile-fallback">{{ userInitial }}</span>
          <span class="legacy-profile-name">{{ displayName }}</span>
        </button>
        <button
          class="legacy-logout-icon-btn"
          type="button"
          aria-label="退出登录"
          title="退出登录"
          @click="logout"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-7.5A2.25 2.25 0 0 0 3.75 5.25v13.5A2.25 2.25 0 0 0 6 21h7.5a2.25 2.25 0 0 0 2.25-2.25V15" />
            <path d="M18 12H9m0 0 3-3m-3 3 3 3" />
          </svg>
        </button>
      </div>
    </aside>

    <div class="legacy-main-content">
      <div class="legacy-fab-group" v-if="$slots.fab">
        <slot name="fab" />
      </div>
      <slot />
    </div>

    <nav class="legacy-mobile-nav">
      <RouterLink
        v-for="item in mobileNav"
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
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useRouter } from 'vue-router'
import { useKonaStore } from '../shared/store'
import { useWebTheme } from '../shared/webTheme'

const nav = [
  { path: '/app/home', label: '我的资产', shortLabel: '资产', icon: '💰' },
  { path: '/app/invest', label: '我的投资', shortLabel: '投资', icon: '💼' },
  { path: '/app/analysis', label: '资产分析', shortLabel: '分析', icon: '📊' },
  { path: '/app/news', label: '市场分析', shortLabel: '快讯', icon: '⚡' },
]

const mobileNav = [...nav, { path: '/app/me', label: '设置', shortLabel: '设置', icon: '⚙️' }]

const router = useRouter()
const store = useKonaStore()
const { theme } = useWebTheme()

const displayName = computed(() => {
  const user = store.state.user || {}
  return String(user.nickname || user.username || '用户')
})

const avatarSrc = computed(() => {
  const user = store.state.user || {}
  const avatar = String(user.avatar || '').trim()
  return avatar || ''
})

const userInitial = computed(() => {
  const chars = [...displayName.value]
  return chars.length ? chars[0] : 'U'
})

function goMe() {
  void router.push('/app/me')
}

async function logout() {
  await store.logout()
  await router.replace('/app/login')
}
</script>

<style scoped>
.legacy-nav-links {
  display: flex;
  flex-direction: column;
}

.legacy-sidebar-profile {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--legacy-border-soft);
  display: flex;
  align-items: center;
  gap: 8px;
}

.legacy-profile-btn {
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 4px;
  cursor: pointer;
  color: var(--legacy-text-primary);
}

.legacy-profile-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--legacy-border-soft);
  background: var(--legacy-surface-strong);
}

.legacy-profile-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
  color: var(--legacy-text-primary);
}

.legacy-profile-name {
  color: var(--legacy-text-primary);
  font-size: 14px;
  font-weight: 700;
  max-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.legacy-logout-icon-btn {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  border: 1px solid var(--legacy-danger-border);
  background: var(--legacy-danger-bg);
  color: var(--legacy-danger-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  cursor: pointer;
}

.legacy-logout-icon-btn:hover {
  background: var(--legacy-danger-bg-hover);
}

.legacy-logout-icon-btn svg {
  width: 18px;
  height: 18px;
  stroke: currentColor;
  stroke-width: 1.8;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}

@media (max-width: 768px) {
  .legacy-sidebar-profile {
    display: none;
  }
}
</style>
