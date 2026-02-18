<template>
  <div class="shell">
    <aside class="side panel">
      <div class="brand">KONA WEB</div>
      <RouterLink v-for="item in nav" :key="item.path" :to="item.path" class="nav-item" active-class="active">
        {{ item.label }}
      </RouterLink>
      <button class="btn danger" @click="onLogout">退出登录</button>
    </aside>
    <main class="content">
      <header class="top panel">
        <div>
          <div class="title">{{ title }}</div>
          <div class="subtitle">{{ subtitle }}</div>
        </div>
        <div class="user">{{ username }}</div>
      </header>
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useKonaStore } from '../shared/store'

defineProps<{ title: string; subtitle?: string }>()

const router = useRouter()
const store = useKonaStore()

const username = computed(() => String(store.state.user?.nickname || store.state.user?.username || '用户'))

const nav = [
  { path: '/app/home', label: '首页' },
  { path: '/app/invest', label: '投资' },
  { path: '/app/analysis', label: '分析' },
  { path: '/app/news', label: '快讯' },
  { path: '/app/profile', label: '我的' },
]

async function onLogout() {
  await store.logout()
  await router.push('/app/login')
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
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.user {
  color: var(--muted);
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
