<template>
  <div class="legacy-shell legacy-page">
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
          <span class="legacy-profile-meta">
            <span class="legacy-profile-name">{{ displayName }}</span>
            <span class="legacy-profile-hint">个人中心</span>
          </span>
        </button>
        <button class="legacy-logout-btn" type="button" @click="logout">退出登录</button>
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

const nav = [
  { path: '/app/home', label: '我的资产', shortLabel: '资产', icon: '💰' },
  { path: '/app/invest', label: '我的投资', shortLabel: '投资', icon: '💼' },
  { path: '/app/analysis', label: '资产分析', shortLabel: '分析', icon: '📊' },
  { path: '/app/news', label: '市场分析', shortLabel: '快讯', icon: '⚡' },
]

const mobileNav = [...nav, { path: '/app/me', label: '设置', shortLabel: '设置', icon: '⚙️' }]

const router = useRouter()
const store = useKonaStore()

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
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.legacy-profile-btn {
  width: 100%;
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
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(15, 23, 42, 0.8);
}

.legacy-profile-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
}

.legacy-profile-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
}

.legacy-profile-name {
  color: var(--legacy-text-primary);
  font-size: 14px;
  font-weight: 700;
  max-width: 140px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.legacy-profile-hint {
  color: var(--legacy-text-secondary);
  font-size: 12px;
}

.legacy-logout-btn {
  width: 100%;
  height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(248, 113, 113, 0.32);
  background: rgba(127, 29, 29, 0.18);
  color: #fda4af;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.legacy-logout-btn:hover {
  background: rgba(127, 29, 29, 0.28);
}

@media (max-width: 768px) {
  .legacy-sidebar-profile {
    display: none;
  }
}
</style>
