<template>
  <div class="admin-layout">
    <aside class="admin-sidebar">
      <div class="brand">
        <div class="brand-title">管理后台</div>
        <div class="brand-sub">Operations Console</div>
      </div>

      <div class="nav-group">
        <div class="nav-group-title">管理菜单</div>
        <nav class="nav">
          <RouterLink v-for="item in nav" :key="item.path" :to="item.path" active-class="active">
            {{ item.label }}
          </RouterLink>
        </nav>
      </div>

      <div class="side-actions">
        <button class="btn-secondary" @click="goApp">去业务端</button>
        <button class="btn-danger" @click="onLogout">退出登录</button>
      </div>
    </aside>

    <main class="admin-main">
      <header class="topbar">
        <div class="topbar-title">{{ title }}<span v-if="subtitle"> · {{ subtitle }}</span></div>
      </header>
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { useKonaStore } from '../shared/store'

defineProps<{ title: string; subtitle?: string }>()

const router = useRouter()
const store = useKonaStore()

const nav = [
  { path: '/admin/overview', label: '概览' },
  { path: '/admin/users', label: '用户' },
  { path: '/admin/invites', label: '邀请码' },
  { path: '/admin/apis', label: '接口策略' },
  { path: '/admin/audit', label: '审计' },
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
  grid-template-columns: calc(244px * var(--admin-space-scale)) 1fr;
  min-height: 100vh;
  background:
    radial-gradient(920px 420px at 8% 6%, rgba(10, 143, 152, 0.08), transparent 64%),
    radial-gradient(880px 380px at 95% 94%, rgba(245, 158, 11, 0.08), transparent 62%),
    linear-gradient(160deg, #f2f6fb 0%, #f7fafd 48%, #fcfdff 100%);
}

.admin-sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  background: linear-gradient(180deg, #0a2c42 0%, #0a2439 100%);
  color: #d9ebff;
  border-right: 1px solid #1d3d56;
  padding: calc(18px * var(--admin-space-scale)) calc(12px * var(--admin-space-scale));
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.brand {
  margin: 2px calc(10px * var(--admin-space-scale)) calc(14px * var(--admin-space-scale));
}

.brand-title {
  font-size: calc(18px * var(--admin-font-scale));
  font-weight: 800;
  letter-spacing: 0.5px;
}

.brand-sub {
  margin-top: 4px;
  color: #97b8d6;
  font-size: calc(11px * var(--admin-font-scale));
}

.nav-group-title {
  margin: 0 calc(10px * var(--admin-space-scale)) calc(6px * var(--admin-space-scale));
  color: #7ba2c5;
  font-size: calc(10px * var(--admin-font-scale));
  letter-spacing: 0.8px;
  text-transform: uppercase;
}

.nav a {
  display: block;
  margin-bottom: calc(5px * var(--admin-space-scale));
  padding: calc(9px * var(--admin-space-scale)) calc(11px * var(--admin-space-scale));
  color: #d6e9ff;
  text-decoration: none;
  border-radius: 10px;
  font-size: calc(13px * var(--admin-font-scale));
  transition: background .2s ease;
}

.nav a:hover {
  background: rgba(130, 187, 228, 0.16);
}

.nav a.active {
  background: linear-gradient(120deg, rgba(10, 143, 152, 0.36), rgba(18, 95, 118, 0.48));
  border: 1px solid rgba(132, 215, 223, 0.34);
  font-weight: 700;
}

.side-actions {
  margin-top: auto;
  display: grid;
  gap: calc(7px * var(--admin-space-scale));
  padding: calc(8px * var(--admin-space-scale));
}

.btn-secondary,
.btn-danger {
  border: 0;
  border-radius: 10px;
  padding: calc(8px * var(--admin-control-scale)) calc(12px * var(--admin-control-scale));
  font-size: calc(13px * var(--admin-font-scale));
  font-weight: 600;
  cursor: pointer;
}

.btn-secondary {
  background: #e8eff7;
  color: #1f3f58;
  border: 1px solid #c8d6e7;
}

.btn-danger {
  color: #fff;
  background: linear-gradient(120deg, #b42318, #d92d20);
}

.admin-main {
  min-width: 0;
  padding: calc(16px * var(--admin-space-scale)) clamp(12px, 1.8vw, 22px) calc(20px * var(--admin-space-scale));
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  margin-bottom: calc(12px * var(--admin-space-scale));
  padding: calc(9px * var(--admin-space-scale)) calc(12px * var(--admin-space-scale));
  border: 1px solid #d7e1ee;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.84);
  backdrop-filter: blur(8px);
  box-shadow: 0 8px 22px rgba(16, 36, 62, 0.04);
}

.topbar-title {
  font-size: calc(13px * var(--admin-font-scale));
  color: #55708f;
}

.admin-main :deep(.panel) {
  border: 1px solid #d7e1ee;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: 0 12px 36px rgba(16, 36, 62, 0.08);
}

.admin-main :deep(.btn) {
  border: 0;
  border-radius: 9px;
  padding: calc(8px * var(--admin-control-scale)) calc(12px * var(--admin-control-scale));
  font-size: calc(13px * var(--admin-font-scale));
  font-weight: 600;
  cursor: pointer;
  color: #fff;
  background: linear-gradient(120deg, #0f5f73, #0a8f98);
  box-shadow: none;
}

.admin-main :deep(.btn:hover) {
  filter: brightness(1.04);
  transform: none;
}

.admin-main :deep(.btn.primary) {
  background: linear-gradient(120deg, #0f5f73, #0a8f98);
  color: #fff;
}

.admin-main :deep(.btn.danger) {
  background: linear-gradient(120deg, #b42318, #d92d20);
  color: #fff;
}

.admin-main :deep(.input),
.admin-main :deep(select),
.admin-main :deep(textarea) {
  border: 1px solid #cfd9e7;
  border-radius: 9px;
  padding: calc(8px * var(--admin-control-scale)) calc(10px * var(--admin-control-scale));
  font-size: calc(13px * var(--admin-font-scale));
  color: #10243e;
  background: #fff;
}

.admin-main :deep(.input:focus),
.admin-main :deep(select:focus),
.admin-main :deep(textarea:focus) {
  outline: none;
  border-color: #6ea5d4;
  box-shadow: 0 0 0 3px rgba(69, 141, 198, 0.16);
}

.admin-main :deep(.table th) {
  color: #55708f;
  font-size: calc(11px * var(--admin-font-scale));
  letter-spacing: 0.02em;
  text-transform: none;
  background: #f8fbff;
}

.admin-main :deep(.table td) {
  color: #10243e;
  font-size: calc(13px * var(--admin-font-scale));
}

.admin-main :deep(.table tbody tr:hover) {
  background: #f8fbff;
}

.admin-main :deep(.up) {
  color: #067647;
}

.admin-main :deep(.down) {
  color: #b42318;
}

@media (max-width: 900px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }

  .admin-sidebar {
    position: static;
    height: auto;
  }
}
</style>
