<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="brand">
        <div class="brand-title">管理后台</div>
      </div>

      <div class="nav-group">
        <div class="nav-group-title">管理菜单</div>
        <nav class="nav">
          <RouterLink v-for="item in nav" :key="item.path" :to="item.path" active-class="active">
            <AdminIcon :name="item.icon" :size="16" />
            {{ item.label }}
          </RouterLink>
        </nav>
      </div>

      <div class="sidebar-profile">
        <div class="sidebar-avatar" />
        <div class="sidebar-user">
          <p class="sidebar-user-name">{{ store.state.user?.username || '管理员' }}</p>
          <p class="sidebar-user-role">Admin</p>
        </div>
      </div>

      <div class="side-actions">
        <AdminButton variant="ghost" block @click="goApp">去业务端</AdminButton>
        <AdminButton variant="danger" block @click="onLogout">退出登录</AdminButton>
      </div>
    </aside>

    <main class="admin-main">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { useKonaStore } from '../shared/store'
import AdminButton from '../components/admin/ui/AdminButton.vue'
import AdminIcon from '../components/admin/ui/AdminIcon.vue'

defineProps<{ title: string; subtitle?: string }>()

const router = useRouter()
const store = useKonaStore()

const nav = [
  { path: '/admin/overview', label: '数据概览', icon: 'dashboard' },
  { path: '/admin/users', label: '用户管理', icon: 'users' },
  { path: '/admin/invites', label: '邀请码管理', icon: 'invite' },
  { path: '/admin/config', label: '运营配置', icon: 'ops' },
  { path: '/admin/apis', label: '接口管理', icon: 'api' },
]

async function onLogout() {
  await store.logout()
  await router.push('/admin/login')
}

async function goApp() {
  await router.push('/app/home')
}
</script>

<style scoped>
.admin-layout {
  --admin-font-scale: var(--density-font-scale, 1);
  --admin-space-scale: var(--density-space-scale, 1);
  --admin-control-scale: var(--density-control-scale, 1);
  display: grid;
  grid-template-columns: calc(252px * var(--admin-space-scale)) 1fr;
  min-height: 100vh;
}

.admin-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: calc(20px * var(--admin-space-scale)) calc(14px * var(--admin-space-scale));
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.brand {
  margin: 2px calc(10px * var(--admin-space-scale)) calc(16px * var(--admin-space-scale));
}

.brand-title {
  font-size: calc(28px * var(--admin-font-scale));
  font-weight: 900;
  letter-spacing: 0.02em;
}

.nav-group-title {
  margin: 0 calc(10px * var(--admin-space-scale)) calc(8px * var(--admin-space-scale));
  font-size: calc(11px * var(--admin-font-scale));
  font-weight: 700;
  text-transform: uppercase;
}

.nav a {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: calc(6px * var(--admin-space-scale));
  padding: calc(12px * var(--admin-space-scale)) calc(12px * var(--admin-space-scale));
  text-decoration: none;
  border-radius: 14px;
  font-size: calc(18px * var(--admin-font-scale));
  font-weight: 700;
  transition: all .16s ease;
}

.side-actions {
  display: grid;
  gap: calc(8px * var(--admin-space-scale));
  padding: calc(8px * var(--admin-space-scale));
}

.admin-main {
  min-width: 0;
  padding: calc(14px * var(--admin-space-scale)) clamp(14px, 2vw, 28px) calc(24px * var(--admin-space-scale));
}

.admin-main :deep(.panel) {
  border-radius: 18px;
}

.admin-main :deep(.up) {
  color: #059669;
}

.admin-main :deep(.down) {
  color: #dc2626;
}

@media (max-width: 900px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }

  .admin-sidebar {
    position: static;
    height: auto;
  }

  .admin-main {
    padding-top: 12px;
  }
}
</style>
