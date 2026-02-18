<template>
  <div class="shell">
    <aside class="side panel">
      <div class="brand">ADMIN</div>
      <RouterLink v-for="item in nav" :key="item.path" :to="item.path" class="nav-item" active-class="active">
        {{ item.label }}
      </RouterLink>
      <button class="btn" @click="goApp">去业务端</button>
      <button class="btn danger" @click="onLogout">退出</button>
    </aside>
    <main class="content">
      <header class="top panel">
        <div>
          <div class="title">{{ title }}</div>
          <div class="subtitle">{{ subtitle }}</div>
        </div>
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
  { path: '/admin/config', label: '配置' },
  { path: '/admin/invites', label: '邀请码' },
  { path: '/admin/data', label: '数据' },
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
.shell {
  display: grid;
  grid-template-columns: 230px minmax(0, 1fr);
  min-height: 100vh;
}

.side {
  margin: 16px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.brand {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 1px;
  margin-bottom: 12px;
}

.nav-item {
  border: 1px solid transparent;
  color: var(--muted);
  padding: 10px 12px;
  border-radius: 10px;
}

.nav-item.active {
  border-color: #36578f;
  color: var(--text);
  background: #15253f;
}

.content {
  padding: 16px 16px 24px 0;
}

.top {
  margin-bottom: 16px;
  padding: 16px 20px;
}

.title {
  font-size: 22px;
  font-weight: 800;
}

.subtitle {
  color: var(--muted);
  font-size: 13px;
}

@media (max-width: 900px) {
  .shell {
    grid-template-columns: 1fr;
  }

  .side {
    margin: 10px;
  }

  .content {
    padding: 10px;
  }
}
</style>
