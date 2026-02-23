<template>
  <LegacyAppShell>
    <section class="legacy-section news-container">
      <div class="news-header">
        <h1 class="page-title">市场快讯</h1>
        <div class="live-status">
          <span class="live-dot"></span>
          LIVE
        </div>
      </div>

      <div class="news-timeline">
        <article
          v-for="item in items"
          :key="item.id"
          class="news-item"
          :class="{ show: item.show, important: item.important }"
        >
          <div class="news-dot"></div>
          <div class="news-time">{{ item.time }}</div>
          <div class="news-content">{{ item.content }}</div>
        </article>
        <div v-if="loading" class="loading">正在接入全球市场数据...</div>
      </div>
    </section>
  </LegacyAppShell>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import LegacyAppShell from '../../layouts/LegacyAppShell.vue'
import { api } from '../../shared/http'

type NewsItem = {
  id: string
  time: string
  content: string
  important: boolean
  show: boolean
}

const items = ref<NewsItem[]>([])
const loading = ref(true)
const lastId = ref('')
let timer: number | null = null

function normalizeNews(raw: Record<string, unknown>): NewsItem {
  return {
    id: String(raw.id || `${raw.time || ''}-${raw.content || raw.title || ''}`),
    time: String(raw.time || raw.datetime || raw.date || '-'),
    content: String(raw.content || raw.summary || raw.text || raw.title || '市场快讯'),
    important: Boolean(raw.important || raw.level === 'high'),
    show: false,
  }
}

async function fetchNews() {
  try {
    const payload = await api.get<{ items?: Record<string, unknown>[] }>('/api/news/latest?page=1&page_size=80')
    const list = (payload.items || []).map(normalizeNews)
    loading.value = false

    if (!list.length) return
    if (!lastId.value) {
      items.value = [...list].reverse().map((item) => ({ ...item, show: true })).reverse()
      lastId.value = list[0]?.id || ''
      return
    }

    const newItems: NewsItem[] = []
    for (const item of list) {
      if (item.id === lastId.value) break
      newItems.push(item)
    }
    if (!newItems.length) return

    lastId.value = newItems[0]?.id || lastId.value
    for (const item of [...newItems].reverse()) {
      items.value.unshift(item)
      requestAnimationFrame(() => {
        const target = items.value.find((n) => n.id === item.id)
        if (target) target.show = true
      })
    }
    if (items.value.length > 100) {
      items.value = items.value.slice(0, 100)
    }
  } catch {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchNews()
  timer = window.setInterval(fetchNews, 10000)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<style scoped>
.news-container {
  max-width: 860px;
  margin-inline: auto;
}

.news-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--legacy-border);
}

.page-title {
  margin: 0;
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, #fff 0%, #94a3b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.live-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--legacy-red);
  font-weight: 600;
  font-size: 14px;
  background: rgba(239, 68, 68, 0.1);
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.live-dot {
  width: 8px;
  height: 8px;
  background: var(--legacy-red);
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

.news-timeline {
  position: relative;
  padding-left: 20px;
  border-left: 2px solid var(--legacy-border);
}

.news-item {
  position: relative;
  margin-bottom: 0;
  padding-left: 20px;
  opacity: 0;
  transform: translateY(-20px);
  max-height: 0;
  overflow: hidden;
  transition: all 0.45s cubic-bezier(0.4, 0, 0.2, 1);
}

.news-item.show {
  opacity: 1;
  transform: translateY(0);
  max-height: 500px;
  margin-bottom: 18px;
  padding-top: 8px;
}

.news-dot {
  position: absolute;
  left: -27px;
  top: 14px;
  width: 12px;
  height: 12px;
  background: #334155;
  border: 2px solid var(--legacy-text-secondary);
  border-radius: 50%;
}

.news-item.important .news-dot {
  background: var(--legacy-red);
  border-color: var(--legacy-red);
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
}

.news-time {
  font-size: 14px;
  color: var(--legacy-text-secondary);
  margin-bottom: 6px;
  font-weight: 600;
}

.news-content {
  background: var(--legacy-bg-tertiary);
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid var(--legacy-border);
  line-height: 1.6;
}

.news-item:hover .news-content {
  background: var(--legacy-bg-secondary);
  border-color: rgba(59, 130, 246, 0.4);
}

.loading {
  padding: 24px 0 10px;
  color: var(--legacy-text-secondary);
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
  70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}
</style>
