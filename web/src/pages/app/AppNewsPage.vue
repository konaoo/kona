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
            <div class="news-footer">
              <span class="news-symbol">{{ item.symbolLabel }}</span>
              <span class="news-impact" :class="item.impact">{{ item.impactText }}</span>
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
  symbolLabel: string
  impact: 'up' | 'down' | 'neutral'
  impactText: string
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

const bullishKeywords = [
  '涨', '上涨', '上行', '走高', '走强', '反弹', '增长', '利好', '偏多', '回暖', '放量', '净流入', '回购', '增持', '突破', '新高', '上扬', '提振', '强势', '活跃', '加速', '扩大', '超预期', '景气', '修复', '复苏', '乐观',
]

const bearishKeywords = [
  '跌', '下跌', '下行', '走低', '走弱', '回调', '下滑', '利空', '偏空', '缩量', '净流出', '减持', '下调', '承压', '疲软', '低迷', '新低', '萎缩', '收窄', '放缓', '回落', '下挫', '失守', '不及预期', '悲观', '风险', '亏损',
]

const transitionKeywords = ['但', '不过', '然而', '同时', '落地', '超预期', '不及预期', '好于预期', '低于预期']

type NewsCategory = 'policy' | 'trade' | 'company' | 'macro'

const categoryRules: Array<{
  key: NewsCategory
  strong: string[]
  weak: string[]
}> = [
  {
    key: 'policy',
    strong: ['证监会', '央行', '发改委', '财政部', '商务部', '外交部', '国防部', '国务院', '监管', '新规', '征求意见', '政策', '关税', '制裁'],
    weak: ['财政', '货币政策', '试点', '落地', '国常会', '多部门', '办法', '意见', '条例'],
  },
  {
    key: 'trade',
    strong: ['北向资金', '南向资金', '涨停', '跌停', '收盘', '开盘', '尾盘', '盘中', '期货', 'ETF', '换手', '资金流', '净流入', '净流出'],
    weak: ['成交', '夜盘', '板块', '指数', '大盘', '沪指', '深指', '创业板', '科创50', '放量', '缩量'],
  },
  {
    key: 'company',
    strong: ['财报', '业绩', '回购', '增持', '减持', '并购', '收购', 'IPO', '上市', '预告', '分红', '营收', '净利'],
    weak: ['公司', '集团', '公告', '董事会', '股东', '管理层', '解禁', '定增', '配股'],
  },
  {
    key: 'macro',
    strong: ['GDP', 'CPI', 'PPI', '非农', '就业', '通胀', '利率', '汇率', '人民币', '美元', '原油', '黄金', '国债', '美联储'],
    weak: ['美国', '中国', '日本', '欧洲', '经济', '制造业', '消费', '社融', 'PMI'],
  },
]

const symbolPatterns: Record<string, string> = {
  '沪指': 'A:沪指',
  '深指': 'A:深指',
  '创业板': 'A:创业板',
  '科创50': 'A:科创50',
  '恒生指数': 'HK:恒指',
  '恒指': 'HK:恒指',
  '道指': 'US:道指',
  '纳指': 'US:纳指',
  '标普': 'US:标普',
  '北向资金': 'A:北向资金',
  '南向资金': 'HK:南向资金',
  '人民币': 'CNY',
  '美元': 'USD',
  '黄金': '黄金',
  '原油': '原油',
  '腾讯': 'HK:00700',
  '阿里': 'US:BABA',
  '茅台': 'A:600519',
  '比亚迪': 'A:002594',
  '宁德时代': 'A:300750',
  '特斯拉': 'US:TSLA',
  '苹果': 'US:AAPL',
  '英伟达': 'US:NVDA',
  'ETF': 'ETF',
}

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
  rawItems.value = cached.items.map((item) => ({
    ...normalizeNews(item as unknown as Record<string, unknown>),
    show: true,
  }))
  lastId.value = String(cached.lastId || cached.items[0]?.id || '')
}

function toggleImportantOnly() {
  importantOnly.value = !importantOnly.value
}

function setCategory(key: string) {
  currentCategory.value = key
}

function classifyCategory(content: string): string {
  const scores: Record<NewsCategory, number> = { macro: 0, company: 0, trade: 0, policy: 0 }

  for (const rule of categoryRules) {
    for (const keyword of rule.strong) {
      if (content.includes(keyword)) scores[rule.key] += 3
    }
    for (const keyword of rule.weak) {
      if (content.includes(keyword)) scores[rule.key] += 1
    }
  }

  if (scores.policy >= 3) return 'policy'
  if (scores.trade >= 4 && scores.trade >= scores.company) return 'trade'
  if (scores.company >= 4 && scores.company > scores.macro) return 'company'
  if (scores.macro >= 3) return 'macro'

  const ranked = (Object.entries(scores) as Array<[NewsCategory, number]>).sort((a, b) => b[1] - a[1])
  return ranked[0]?.[0] || 'macro'
}

function classifyImpact(content: string): { impact: 'up' | 'down' | 'neutral'; text: string } {
  const parts = content
    .split(/[,，。；;！!？?]/)
    .map(part => part.trim())
    .filter(Boolean)

  let bullish = 0
  let bearish = 0

  for (const part of parts) {
    let partBullish = 0
    let partBearish = 0

    for (const keyword of bullishKeywords) {
      if (part.includes(keyword)) partBullish += 1
    }
    for (const keyword of bearishKeywords) {
      if (part.includes(keyword)) partBearish += 1
    }

    const hasTransition = transitionKeywords.some(keyword => part.includes(keyword))
    const weight = hasTransition ? 1.4 : 1

    bullish += partBullish * weight
    bearish += partBearish * weight
  }

  if (Math.abs(bullish - bearish) <= 0.5) return { impact: 'neutral', text: '中性' }
  if (bullish > bearish && bullish > 0) return { impact: 'up', text: '+偏多' }
  if (bearish > bullish && bearish > 0) return { impact: 'down', text: '-偏空' }
  return { impact: 'neutral', text: '中性' }
}

function extractSymbol(content: string, category: string): string {
  for (const [keyword, symbol] of Object.entries(symbolPatterns)) {
    if (content.includes(keyword)) return symbol
  }
  const hkCode = content.match(/\b0?\d{4,5}\.HK\b/i)?.[0]
  if (hkCode) return hkCode.toUpperCase()
  const usCode = content.match(/\b[A-Z]{2,5}\b/)?.[0]
  if (usCode && ['ETF', 'GDP', 'CPI', 'PPI', 'PMI'].includes(usCode) === false) return `US:${usCode}`
  const aCode = content.match(/\b\d{6}\b/)?.[0]
  if (aCode) return aCode
  if (category === 'trade') return 'A股'
  if (category === 'policy') return '政策'
  if (category === 'company') return '公司'
  return '宏观'
}

function splitTitleContent(content: string): { title: string; summary: string } {
  const bracketIndex = content.indexOf('】')
  if (bracketIndex > 0 && bracketIndex < 30) {
    const title = content.slice(0, bracketIndex + 1).trim()
    const summary = content.slice(bracketIndex + 1).trim()
    if (summary) return { title, summary }
  }

  if (content.length > 40) {
    for (let i = 0; i < content.length && i < 40; i += 1) {
      if ('，。,；;'.includes(content[i] || '')) {
        const title = content.slice(0, i).trim()
        const summary = content.slice(i + 1).trim()
        if (title.length > 6 && summary) return { title, summary }
        break
      }
    }
  }

  return {
    title: content.length > 44 ? `${content.slice(0, 44)}...` : content,
    summary: content,
  }
}

function normalizeNews(raw: Record<string, unknown>): NewsItem {
  const content = String(raw.content || raw.summary || raw.text || raw.title || '市场快讯')
  const split = raw.title && raw.summary
    ? { title: String(raw.title || ''), summary: String(raw.summary || '') }
    : splitTitleContent(content)
  const cat = String(raw.category || classifyCategory(content))
  const impactResult = raw.impact
    ? {
        impact: String(raw.impact) as 'up' | 'down' | 'neutral',
        text: String(raw.impact_text || raw.impactText || (raw.impact === 'up' ? '+偏多' : raw.impact === 'down' ? '-偏空' : '中性')),
      }
    : classifyImpact(content)
  const symbolLabel = String(raw.symbol || extractSymbol(content, cat))
  
  return {
    id: String(raw.id || `${raw.time || ''}-${content}`),
    time: String(raw.time || '-').split(' ')[1] || String(raw.time || '-'),
    title: split.title,
    summary: split.summary,
    category: cat,
    categoryLabel: categories.find(c => c.key === cat)?.label || '资讯',
    important: Boolean(raw.important || raw.level === 'high'),
    show: false,
    symbolLabel,
    impact: impactResult.impact,
    impactText: impactResult.text,
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

    const existing = new Map(rawItems.value.map((item) => [item.id, item]))
    for (const item of list) {
      existing.set(item.id, { ...existing.get(item.id), ...item, show: true })
    }

    const newItems: NewsItem[] = []
    for (const item of list) {
      if (item.id === lastId.value) break
      newItems.push(item)
    }

    lastId.value = list[0]?.id || lastId.value
    rawItems.value = [...list, ...rawItems.value.filter((item) => !existing.has(item.id))]
      .slice(0, 100)
      .map((item) => existing.get(item.id) || item)
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
  white-space: nowrap;
}
[data-theme='light'] .news-filter-btn {
  background: rgba(15, 23, 42, 0.04);
}

.news-filter-btn:hover {
  background: rgba(255, 255, 255, 0.07);
  color: var(--text);
}
[data-theme='light'] .news-filter-btn:hover {
  background: rgba(15, 23, 42, 0.07);
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
[data-theme='light'] .news-card {
  background: linear-gradient(180deg, #ffffff, #fbfcff);
  border-color: rgba(15, 23, 42, 0.08);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
}

.news-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: var(--border-b);
}
[data-theme='light'] .news-card:hover {
  background: #ffffff;
  border-color: rgba(91, 141, 239, 0.2);
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
[data-theme='light'] .news-cat.macro { color: #7c3aed; background: rgba(124, 58, 237, 0.1); }
[data-theme='light'] .news-cat.company { color: #2563eb; background: rgba(37, 99, 235, 0.1); }
[data-theme='light'] .news-cat.trade { color: #059669; background: rgba(5, 150, 105, 0.1); }
[data-theme='light'] .news-cat.policy { color: #a16207; background: rgba(217, 119, 6, 0.1); }

.news-time {
  font-size: 11px;
  color: var(--muted);
}

.news-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.55;
  margin-bottom: 6px;
}

.news-summary {
  font-size: 12px;
  color: var(--sub);
  line-height: 1.6;
  white-space: normal;
  word-break: break-word;
}

.news-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  gap: 12px;
  min-height: 18px;
}

.news-symbol {
  font-size: 11px;
  font-family: var(--font-family-mono);
  color: var(--muted);
  letter-spacing: 0.03em;
}

.news-impact {
  font-size: 12px;
  font-weight: 700;
}

.news-impact.up {
  color: var(--red);
}

.news-impact.down {
  color: var(--green);
}

.news-impact.neutral {
  color: var(--sub);
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

@media (max-width: 640px) {
  .news-filter-btn {
    flex-shrink: 0;
  }
}
</style>
