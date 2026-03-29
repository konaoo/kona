<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useKonaStore } from '../stores/composables'
import html2canvas from 'html2canvas'

import { toAvatarSrc } from '../shared/avatar'
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
  return toAvatarSrc(user.avatar)
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
        <img class="s-logo-icon" src="/assets/logo.png" alt="咔咔记账 logo" />
        <div>
          <div class="s-logo-name">咔咔记账</div>
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
      <!-- Topbar: Hidden as requested by user -->
      <div v-if="false" class="topbar">
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

    <!-- Mobile Bottom Navigation (Flutter-style) -->
    <nav class="mobile-bottom-nav">
      <template v-for="item in navItems" :key="item.path">
        <div 
          class="m-nav-item" 
          :class="{ active: currentPath === item.path }"
          @click="navigate(item.path)"
        >
          <span class="m-nav-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path v-if="item.icon.includes('M')" :d="item.icon" />
              <rect v-if="item.label === '投资'" x="2" y="3" width="20" height="14" rx="2" />
              <line v-if="item.label === '投资'" x1="8" y1="21" x2="16" y2="21" />
              <line v-if="item.label === '投资'" x1="12" y1="17" x2="12" y2="21" />
            </svg>
          </span>
          <span class="m-nav-label">{{ item.label }}</span>
        </div>
      </template>
      
      <!-- Profile / Me (我的) tab for mobile -->
      <div 
        class="m-nav-item" 
        :class="{ active: isProfileActive }"
        @click="navigate('/app/me')"
      >
        <span class="m-nav-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </span>
        <span class="m-nav-label">我的</span>
      </div>
    </nav>
  </div>
</template>

<style scoped>
@import '@/styles/homepage-original.css';

.layout {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--blue) 14%, transparent), transparent 34%),
    radial-gradient(circle at bottom right, color-mix(in srgb, var(--gold) 10%, transparent), transparent 30%),
    var(--bg);
}

/* Sidebar Overrides & Extensions */
.sidebar {
  background: color-mix(in srgb, var(--s1) 96%, transparent);
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
  background: color-mix(in srgb, var(--text) 3%, transparent);
  border: 1px solid color-mix(in srgb, var(--text) 4%, transparent);
}

.profile-mini:hover {
  background: color-mix(in srgb, var(--text) 6%, transparent);
  border-color: color-mix(in srgb, var(--text) 8%, transparent);
}

.profile-mini.active {
  background: linear-gradient(180deg, color-mix(in srgb, var(--text) 8%, transparent), color-mix(in srgb, var(--blue) 8%, transparent));
  border-color: color-mix(in srgb, var(--text) 12%, transparent);
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--text) 6%, transparent);
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
  background: color-mix(in srgb, var(--bg) 88%, transparent);
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

[data-theme='light'] .sidebar {
  box-shadow: 6px 0 24px rgba(15, 23, 42, 0.04);
}

[data-theme='light'] .topbar {
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.03);
}

.page {
  height: 100vh;
  overflow-y: auto;
  padding: 24px 0; /* Vertical padding only, horiz handled by inner */
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--blue) 10%, transparent), transparent 26%),
    var(--bg);
}

/* Scrollbar styling */
.page::-webkit-scrollbar {
  width: 5px;
}
.page::-webkit-scrollbar-thumb {
  background: var(--surface-divider);
  border-radius: 10px;
}

/* ─────────────────────────────────────────────────────────
   Mobile Responsive Parity (Flutter style)
   ───────────────────────────────────────────────────────── */
.mobile-bottom-nav {
  display: none; /* hidden on desktop */
}

@media (max-width: 768px) {
  /* Hide desktop sidebar */
  .sidebar {
    display: none !important;
  }
  
  /* Show bottom navigation */
  .mobile-bottom-nav {
    display: flex;
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    height: calc(56px + env(safe-area-inset-bottom, 0px));
    padding-bottom: env(safe-area-inset-bottom, 0px);
    background: color-mix(in srgb, var(--bg) 92%, transparent);
    backdrop-filter: blur(20px);
    border-top: 1px solid var(--border);
    z-index: 50;
    justify-content: space-around;
    align-items: center;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.05);
  }
  
  .m-nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    color: var(--muted);
    flex: 1;
    cursor: pointer;
    height: 100%;
    transition: all 0.2s;
  }
  
  .m-nav-item.active {
    color: var(--blue);
  }
  
  .m-nav-item:active {
    transform: scale(0.95);
  }
  
  .m-nav-icon svg {
    width: 22px;
    height: 22px;
  }
  
  .m-nav-label {
    font-size: 10px;
    font-weight: 500;
  }

  /* Adjust Main Content Area */
  .main {
    width: 100vw;
  }
  
  .page {
    /* Full viewport, use padding to push content above bottom nav */
    height: 100vh;
    padding: 16px 0 calc(56px + 24px + env(safe-area-inset-bottom, 0px));
  }
  
  /* Topbar AppBar adjustments (Center Title) */
  .topbar {
    justify-content: center;
  }
  
  .topbar-content {
    justify-content: space-between;
    padding: 0 16px;
  }
  
  .topbar-title {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    font-size: 17px;
    font-weight: 600;
  }
  
  .container-inner {
    padding: 0 16px;
  }
}
</style>
