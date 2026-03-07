<template>
  <div class="shell">
    <aside class="side panel">
      <div class="brand-wrap">
        <div class="brand-mark" aria-hidden="true">K</div>
        <div>
          <p class="brand-kicker">GLOBAL ASSET DESK</p>
          <div class="brand">咔咔记账 Web</div>
        </div>
      </div>

      <nav class="nav-list" aria-label="主导航">
        <RouterLink v-for="item in nav" :key="item.path" :to="item.path" class="nav-item" active-class="active">
          <span class="dot" aria-hidden="true"></span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <button class="btn danger logout-btn" @click="onLogout">退出登录</button>
    </aside>

    <main class="content">
      <header class="top panel">
        <div class="head-copy">
          <p class="head-kicker">WORKSPACE</p>
          <div class="title">{{ title }}</div>
          <div class="subtitle">{{ subtitle }}</div>
        </div>
        <div class="user-chip">
          <span class="status-dot" aria-hidden="true"></span>
          <span>{{ username }}</span>
        </div>
      </header>
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useKonaStore } from '../stores/composables'

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
  grid-template-columns: 258px minmax(0, 1fr);
  min-height: 100vh;
  gap: 14px;
  padding: 14px;
}

.side {
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: calc(100vh - 28px);
  position: sticky;
  top: 14px;
}

.brand-wrap {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 6px 4px 12px;
  border-bottom: 1px solid rgba(109, 136, 181, 0.25);
}

.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #18315d, #2155a5);
  color: #d6e8ff;
  font-weight: 800;
  box-shadow: 0 10px 24px rgba(12, 33, 67, 0.35);
}

.brand-kicker {
  margin: 0;
  color: var(--muted);
  font-size: 10px;
  letter-spacing: 0.12em;
}

.brand {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.nav-list {
  display: grid;
  gap: 6px;
  margin-top: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid transparent;
  color: var(--muted);
  padding: 11px 12px;
  border-radius: 12px;
  transition: all var(--motion-fast);
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgba(165, 193, 243, 0.34);
}

.nav-item.active {
  border-color: #36578f;
  color: var(--text);
  background: linear-gradient(120deg, rgba(48, 73, 117, 0.44), rgba(30, 50, 86, 0.44));
}

.nav-item.active .dot {
  background: #8bb5ff;
  box-shadow: 0 0 0 4px rgba(126, 173, 255, 0.14);
}

.nav-item:hover {
  border-color: rgba(89, 120, 173, 0.55);
  color: #dce9ff;
}

.logout-btn {
  margin-top: auto;
}

.content {
  min-width: 0;
  padding: 0 0 24px;
}

.top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  padding: 16px 20px;
}

.head-kicker {
  margin: 0;
  font-size: 10px;
  letter-spacing: 0.12em;
  color: var(--muted);
}

.title {
  margin-top: 4px;
  font-size: 24px;
  font-weight: 780;
  letter-spacing: -0.02em;
}

.subtitle {
  margin-top: 4px;
  color: var(--muted);
  font-size: 12px;
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid var(--line-soft);
  background: rgba(13, 24, 42, 0.86);
  color: var(--text-soft);
  font-size: 13px;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: #60d5af;
  box-shadow: 0 0 0 5px rgba(75, 189, 152, 0.14);
}


@media (max-width: 900px) {
  .shell {
    grid-template-columns: 1fr;
    padding: 10px;
    gap: 10px;
  }

  .side {
    min-height: auto;
    position: static;
    padding: 14px;
  }

  .content {
    padding: 0;
  }

  .nav-list {
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 8px;
  }

  .nav-item {
    justify-content: center;
    padding: 10px 8px;
  }

  .nav-item .dot {
    display: none;
  }

  .logout-btn {
    margin-top: 2px;
    width: 100%;
  }

  .top {
    padding: 14px;
  }

  .title {
    font-size: 22px;
  }

  .user-chip {
    padding: 8px 12px;
    font-size: 12px;
  }
}

@media (max-width: 640px) {
  .nav-list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .top {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>
