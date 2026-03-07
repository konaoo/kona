<template>
  <AppShell title="市场快讯">
    <div class="news-page-layout">
      <!-- Feed Column Only -->
      <div class="news-feed-column">
        <div class="news-filter-bar">
          <button 
            v-for="cat in categories" 
            :key="cat.key"
            class="news-filter-btn" 
            :class="{ active: currentCategory === cat.key }"
            @click="setCategory(cat.key)"
          >
            {{ cat.label }}
          </button>
          
          <button 
            class="news-filter-btn important" 
            :class="{ active: importantOnly }"
            @click="toggleImportantOnly"
            style="margin-left:auto"
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            仅看重要
          </button>
        </div>

        <div class="news-feed-list">
          <article 
            v-for="item in processedItems" 
            :key="item.id" 
            class="news-card"
            :class="{ important: item.important }"
          >
            <div class="news-card-header">
              <span class="news-cat" :class="getCategoryClass(item.category)">{{ item.categoryLabel }}</span>
              <span class="news-time">{{ item.time }}</span>
            </div>
            <h3 class="news-title">{{ item.title }}</h3>
            <p class="news-summary" v-if="item.summary">{{ item.summary }}</p>
            <div class="news-footer" v-if="item.relatedAssets?.length">
              <div class="news-tags">
                <span v-for="asset in item.relatedAssets" :key="asset" class="tag">{{ asset }}</span>
              </div>
            </div>
          </article>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, onUnmounted } from 'vue'
import AppShell from '../../layouts/AppShell.vue'
import { api } from '../../shared/http'
import { readPageCache, writePageCache } from '../../shared/pageCache'
import { useKonaStore } from '../../stores/composables'

type NewsItem = {
  id: string
  time: string
  title: string
  summary: string
  category: string
  categoryLabel: string
  important: boolean
  show: boolean
  relatedAssets?: string[]
}

type NewsCachePayload = {
  items: NewsItem[]
  lastId: string
}

const CACHE_DOMAIN = 'news'
const CACHE_KEY = 'timeline'
const CACHE_TTL_MS = 1000 * 60 * 20
const NEWS_PAGE_SIZE = 50
const NEWS_POLL_INTERVAL_MS = 5000

const store = useKonaStore()
const rawItems = ref<NewsItem[]>([])
const lastId = ref('')
const importantOnly = ref(false)
const currentCategory = ref('all')
const lastSyncTime = ref('刚刚')

const categories = [
  { key: 'all', label: '全部' },
  { key: 'macro', label: '宏观' },
  { key: 'company', label: '公司' },
  { key: 'trade', label: '交易' },
  { key: 'policy', label: '政策' },
]

const processedItems = computed(() => {
  let filtered = rawItems.value
  if (importantOnly.value) {
    filtered = filtered.filter(item => item.important)
  }
  if (currentCategory.value !== 'all') {
    filtered = filtered.filter(item => item.category === currentCategory.value)
  }
  return filtered
})

let timer: number | null = null

function cacheUserId(): string {
  return String(store.state.user?.id || 'guest')
}

function persistCache() {
  writePageCache<NewsCachePayload>(
    CACHE_DOMAIN,
    CACHE_KEY,
    cacheUserId(),
    {
      items: rawItems.value.map((item) => ({ ...item, show: true })),
      lastId: lastId.value,
    },
    CACHE_TTL_MS,
  )
}

function restoreCache() {
  const cached = readPageCache<NewsCachePayload>(
    CACHE_DOMAIN,
    CACHE_KEY,
    cacheUserId(),
    CACHE_TTL_MS,
  )
  if (!cached?.items?.length) return
  rawItems.value = cached.items.map((item) => ({ ...item, show: true }))
  lastId.value = String(cached.lastId || cached.items[0]?.id || '')
}

function toggleImportantOnly() {
  importantOnly.value = !importantOnly.value
}

function setCategory(key: string) {
  currentCategory.value = key
}

function normalizeNews(raw: Record<string, unknown>): NewsItem {
  const content = String(raw.content || raw.summary || raw.text || raw.title || '市场快讯')
  const title = String(raw.title || content.slice(0, 30) + (content.length > 30 ? '...' : ''))
  
  const cats = ['macro', 'company', 'trade', 'policy']
  const cat = String(raw.category || cats[Math.floor(Math.random() * cats.length)])
  
  return {
    id: String(raw.id || `${raw.time || ''}-${content}`),
    time: String(raw.time || '-').split(' ')[1] || String(raw.time || '-'),
    title: title,
    summary: content,
    category: cat,
    categoryLabel: categories.find(c => c.key === cat)?.label || '资讯',
    important: Boolean(raw.important || raw.level === 'high'),
    show: false,
    relatedAssets: []
  }
}

async function fetchNews() {
  try {
    const payload = await api.get<{ items?: Record<string, unknown>[] }>(
      `/api/news/latest?page=1&page_size=${NEWS_PAGE_SIZE}`,
    )
    const list = (payload.items || []).map(normalizeNews)

    if (!list.length) return
    if (!lastId.value) {
      rawItems.value = [...list]
      lastId.value = list[0]?.id || ''
      persistCache()
      return
    }

    const newItems: NewsItem[] = []
    for (const item of list) {
      if (item.id === lastId.value) break
      newItems.push(item)
    }
    if (!newItems.length) return

    lastId.value = newItems[0]?.id || lastId.value
    rawItems.value = [...newItems, ...rawItems.value].slice(0, 100)
    persistCache()
    lastSyncTime.value = '刚刚'
  } catch {
    // keep showing cached timeline
  }
}

function getCategoryClass(cat: string) {
  return cat
}

onMounted(async () => {
  restoreCache()
  await fetchNews()
  timer = window.setInterval(fetchNews, NEWS_POLL_INTERVAL_MS)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<style scoped>
.news-page-layout {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 10px 40px;
}

.news-filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.news-filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.04);
  font-size: 12px;
  font-weight: 600;
  color: var(--sub);
  cursor: pointer;
  transition: all .14s;
}

.news-filter-btn:hover {
  background: rgba(255, 255, 255, 0.07);
  color: var(--text);
}

.news-filter-btn.active {
  background: rgba(91, 141, 239, 0.14);
  border-color: rgba(91, 141, 239, 0.28);
  color: var(--blue);
}

.news-filter-btn.important.active {
  background: rgba(212, 175, 100, 0.12);
  border-color: rgba(212, 175, 100, 0.28);
  color: var(--gold);
}

.news-feed-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.news-card {
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px;
  cursor: pointer;
  transition: background .15s;
}

.news-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: var(--border-b);
}

.news-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.news-cat {
  font-family: var(--font-family-mono);
  font-size: 9px;
  font-weight: 600;
  letter-spacing: .06em;
  padding: 2px 7px;
  border-radius: 4px;
}

.news-cat.macro { color: #a78bfa; background: rgba(167, 139, 250, 0.12); }
.news-cat.company { color: var(--blue); background: rgba(91, 141, 239, 0.12); }
.news-cat.trade { color: var(--green); background: rgba(62, 207, 130, 0.11); }
.news-cat.policy { color: var(--gold); background: rgba(212, 175, 100, 0.11); }

.news-time {
  font-size: 11px;
  color: var(--muted);
}

.news-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.45;
  margin-bottom: 6px;
}

.news-summary {
  font-size: 12px;
  color: var(--sub);
  line-height: 1.6;
}

.news-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}

.news-stats-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.news-stats-column .card {
  margin-bottom: 0;
}

.holding-list-mini {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.holding-row.mini {
  padding: 10px 12px;
}

.holding-row.mini .h-icon {
  width: 30px;
  height: 30px;
  font-size: 8px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 700;
}
.h-icon.blue { background: rgba(91, 141, 239, 0.14); color: #739bf0; }
.h-icon.orange { background: rgba(224, 107, 58, 0.12); color: #e06b3a; }

.holding-row.mini .h-name { font-size: 12px; }
.holding-row.mini .h-code { font-size: 11px; margin-top: 2px; }

.empty-state {
  padding: 40px 0;
  text-align: center;
  color: var(--muted);
  font-size: 13px;
}

.empty-state.mini {
  padding: 20px 0;
  font-size: 11px;
}

.gold { color: var(--gold); }
.up { color: var(--red); }
.dn { color: var(--green); }
.muted { color: var(--muted); }

@media (max-width: 900px) {
  .news-page-layout {
    grid-template-columns: 1fr;
  }
}
</style>
