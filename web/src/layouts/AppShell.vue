<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useKonaStore } from '../stores/composables'
import html2canvas from 'html2canvas'

import { useWebTheme } from '../shared/webTheme'
import { usePrivacyMode } from '../shared/privacyMode'

const props = defineProps<{
  title?: string
  hideTopbar?: boolean
}>()

const router = useRouter()
const route = useRoute()
const store = useKonaStore()

const { theme, toggleTheme } = useWebTheme()
const { isPrivacyMode, togglePrivacy } = usePrivacyMode()

const currentPath = computed(() => route.path)

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

const isProfileActive = computed(() => currentPath.value === '/app/me' || currentPath.value === '/app/profile')

const navItems = [
  { path: '/app/home', label: '首页', icon: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z' },
  { path: '/app/invest', label: '投资', icon: 'M2 3h20v14H2z' },
  { path: '/app/analysis', label: '分析', icon: 'M18 20V10M12 20V4M6 20v-6' },
  { path: '/app/news', label: '快讯', icon: 'M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z' },
]

function navigate(path: string) {
  router.push(path)
}

async function saveAsImage() {
  const area = document.getElementById('capture-area') || document.body
  try {
    const canvas = await html2canvas(area, {
      backgroundColor: theme.value === 'dark' ? '#0a0b0e' : '#ffffff',
      scale: 2,
    })
    const link = document.createElement('a')
    link.download = `kaka-snapshot-${new Date().getTime()}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
  } catch (err) {
    console.error('Failed to capture:', err)
  }
}

async function handleLogout() {
  await store.logout()
  router.replace('/app/login')
}
</script>

<template>
  <div class="layout" :data-theme="theme">
    <!-- Unified Sidebar -->
    <aside class="sidebar">
      <router-link to="/app/home" class="sidebar-logo">
        <div class="s-logo-icon">
          <svg width="16" height="12" viewBox="0 0 18 14" fill="none">
            <polyline points="1,13 5,5 9,9 13,3 17,7" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div>
          <div class="s-logo-name">咔咔记账</div>
          <div class="s-logo-tag">GLOBAL ASSET DESK</div>
        </div>
      </router-link>

      <nav class="sidebar-nav">
        <template v-for="item in navItems" :key="item.path">
          <div 
            class="nav-item" 
            :class="{ active: currentPath === item.path }"
            @click="navigate(item.path)"
          >
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path v-if="item.icon.includes('M')" :d="item.icon" />
                <rect v-if="item.label === '投资'" x="2" y="3" width="20" height="14" rx="2" />
                <line v-if="item.label === '投资'" x1="8" y1="21" x2="16" y2="21" />
                <line v-if="item.label === '投资'" x1="12" y1="17" x2="12" y2="21" />
              </svg>
            </span>
            {{ item.label }}
          </div>
        </template>
      </nav>

      <!-- Sidebar Bottom: Profile & Logout -->
      <div class="sidebar-bottom">
        <div class="profile-mini" :class="{ active: isProfileActive }" @click="navigate('/app/me')">
          <img v-if="avatarSrc" :src="avatarSrc" class="mini-avatar" />
          <div v-else class="mini-avatar fallback">{{ userInitial }}</div>
          <div class="mini-info">
            <div class="mini-name">{{ displayName }}</div>
            <div class="mini-role">个人中心</div>
          </div>
          <button class="logout-btn" @click.stop="handleLogout" title="退出登录">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <main class="main">
      <!-- Topbar: Only show if not explicitly hidden -->
      <div v-if="!hideTopbar" class="topbar">
        <div class="container-inner topbar-content">
          <div class="topbar-title">{{ title || route.meta.title || '工作台' }}</div>
          <div class="topbar-actions">
            <button @click="toggleTheme" class="icon-btn" :title="theme === 'dark' ? '切换浅色模式' : '切换深色模式'">
              {{ theme === 'dark' ? '🌙' : '☀️' }}
            </button>
            <button @click="togglePrivacy" class="icon-btn" :title="isPrivacyMode ? '现实数值' : '隐私模式'">
              {{ isPrivacyMode ? '🙈' : '👁️' }}
            </button>
            <button @click="saveAsImage" class="icon-btn" title="保存截图">
              📸
            </button>
          </div>
        </div>
      </div>

      <!-- Page Content Slot -->
      <div id="capture-area" class="page active">
        <div class="container-inner">
          <slot />
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
@import '@/styles/homepage-original.css';

.layout {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

/* Sidebar Overrides & Extensions */
.sidebar {
  background: rgba(12, 13, 18, 0.98);
}

.sidebar-nav {
  user-select: none;
}

.sidebar-bottom {
  padding: 16px 12px;
  border-top: 1px solid var(--border);
}

.profile-mini {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 10px;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.profile-mini:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.08);
}

.profile-mini.active {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(91, 141, 239, 0.08));
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.mini-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid var(--border);
}

.mini-avatar.fallback {
  background: var(--s3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: var(--blue);
}

.mini-info {
  flex: 1;
  min-width: 0;
}

.mini-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mini-role {
  margin-top: 2px;
  font-size: 11px;
  color: var(--muted);
  white-space: nowrap;
}


.logout-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: rgba(240, 90, 85, 0.1);
  color: var(--red);
}

.logout-btn svg {
  width: 16px;
  height: 16px;
}

/* Page transitions/scroll fixes */
.topbar {
  height: 56px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border);
  background: rgba(10,11,14,0.8);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  align-items: center;
}

.topbar-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.container-inner {
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 0 24px;
}

.page {
  height: calc(100vh - 56px);
  overflow-y: auto;
  padding: 24px 0; /* Vertical padding only, horiz handled by inner */
}

/* Scrollbar styling */
.page::-webkit-scrollbar {
  width: 5px;
}
.page::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
}
</style>
