<template>
  <aside class="admin-sidebar">
    <div class="logo">
      <div class="logo-icon">🏠</div>
      <span>咔咔管理后台</span>
    </div>

    <nav class="admin-nav">
      <RouterLink
        v-for="item in nav"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        active-class="active"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="user-profile">
      <div class="user-info">
        <img v-if="avatarSrc" :src="avatarSrc" alt="头像" class="user-avatar" />
        <div v-else class="user-avatar user-avatar-fallback" :style="avatarStyle">{{ avatarInitial }}</div>
        <div class="user-details">
          <h4>{{ store.state.user?.username || '管理员' }}</h4>
          <p>管理员</p>
        </div>
      </div>
      <div class="user-actions">
        <button class="ghost-btn" @click="goApp">业务端</button>
        <button class="logout-btn" @click="onLogout" title="退出登录">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
        </button>
      </div>
    </div>
  </aside>

  <nav class="admin-bottom-nav">
    <RouterLink
      v-for="item in nav"
      :key="`mobile-${item.path}`"
      :to="item.path"
      class="bottom-item"
      active-class="active"
    >
      <span class="bottom-icon">{{ item.icon }}</span>
      <span class="bottom-label">{{ item.shortLabel || item.label }}</span>
    </RouterLink>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { toAvatarSrc } from '../../shared/avatar'
import { useKonaStore } from '../../stores/composables'

const router = useRouter()
const store = useKonaStore()

const nav = [
  { path: '/admin/overview', label: '数据概览', shortLabel: '概览', icon: '📊' },
  { path: '/admin/users', label: '用户管理', shortLabel: '用户', icon: '👥' },
  { path: '/admin/invites', label: '邀请码管理', shortLabel: '邀请码', icon: '🛡️' },
  { path: '/admin/config', label: '运营配置', shortLabel: '配置', icon: '⚙️' },
  { path: '/admin/apis', label: '接口管理', shortLabel: '接口', icon: '🔌' },
]

const avatarStyle = computed(() => ({
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
}))

const avatarSrc = computed(() => toAvatarSrc(store.state.user?.avatar))
const avatarInitial = computed(() => {
  const raw = String(store.state.user?.nickname || store.state.user?.username || '管').trim()
  return raw.slice(0, 1).toUpperCase()
})

async function onLogout() {
  await store.logout()
  await router.push('/admin/login')
}

async function goApp() {
  await router.push('/app/home')
}
</script>

<style scoped>
.admin-sidebar {
  width: 260px;
  background: white;
  padding: 30px 0 0;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 800;
  font-size: 19px;
  margin-bottom: 35px;
  padding: 0 24px;
  color: #000;
  letter-spacing: -0.5px;
}

.logo-icon {
  width: 34px;
  height: 34px;
  background: #000;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.admin-nav {
  display: flex;
  flex-direction: column;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 18px;
  margin: 0 12px 6px;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #666;
  font-weight: 600;
  text-decoration: none;
  font-size: 14.5px;
}

.nav-item:hover {
  background: #f8f9fa;
  color: #000;
}

.nav-item.active {
  background: #000;
  color: white;
}

.nav-icon {
  width: 20px;
  text-align: center;
}

.user-profile {
  margin-top: auto;
  padding: 24px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  background: #fdfdfd;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  flex-shrink: 0;
  object-fit: cover;
}

.user-avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: 800;
}

.user-details {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-details h4 {
  font-size: 16px;
  font-weight: 800;
  margin: 0;
  color: #000;
  line-height: 1.1;
}

.user-details p {
  font-size: 12px;
  color: #999;
  font-weight: 500;
  margin: 4px 0 0;
  line-height: 1;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.ghost-btn,
.logout-btn {
  height: 34px;
  border-radius: 10px;
  border: 1px solid #e2e2e2;
  background: transparent;
  color: #888;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.ghost-btn {
  padding: 0 12px;
  font-size: 12px;
  font-weight: 700;
}

.logout-btn {
  width: 34px;
}

.ghost-btn:hover,
.logout-btn:hover {
  background: #2d2d2d;
  color: #fff;
  border-color: #444;
}

.admin-bottom-nav {
  display: none;
}

@media (max-width: 900px) {
  .admin-sidebar {
    display: none;
  }

  .admin-bottom-nav {
    position: fixed;
    left: 10px;
    right: 10px;
    bottom: calc(10px + env(safe-area-inset-bottom));
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 8px;
    padding: 10px;
    border-radius: 20px;
    background: rgba(17, 24, 39, 0.94);
    backdrop-filter: blur(14px);
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.24);
    z-index: 60;
  }

  .bottom-item {
    min-width: 0;
    text-decoration: none;
    color: rgba(255, 255, 255, 0.68);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 8px 4px;
    border-radius: 14px;
    transition: all 0.2s ease;
  }

  .bottom-item.active {
    background: rgba(96, 165, 250, 0.18);
    color: #ffffff;
  }

  .bottom-icon {
    font-size: 16px;
    line-height: 1;
  }

  .bottom-label {
    font-size: 11px;
    font-weight: 700;
    line-height: 1;
    white-space: nowrap;
  }
}
</style>
