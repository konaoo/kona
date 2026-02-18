<template>
  <AppShell title="快讯" subtitle="市场新闻流">
    <section class="panel" style="padding: 16px">
      <div class="head">
        <h3>最新快讯</h3>
        <button class="btn" @click="loadNews">刷新</button>
      </div>

      <article class="news-item" v-for="(item, idx) in items" :key="idx">
        <h4>{{ item.title || item.headline || '市场快讯' }}</h4>
        <p>{{ item.content || item.summary || item.text || JSON.stringify(item) }}</p>
        <small>{{ item.time || item.datetime || item.date || '-' }}</small>
      </article>
    </section>
  </AppShell>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppShell from '../../layouts/AppShell.vue'
import { api } from '../../shared/http'

const items = ref<Record<string, unknown>[]>([])

async function loadNews() {
  const payload = await api.get<{ items?: Record<string, unknown>[] }>('/api/news/latest?page=1&page_size=50', true)
  items.value = payload.items || []
}

onMounted(loadNews)
</script>

<style scoped>
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.news-item {
  padding: 12px 0;
  border-bottom: 1px solid rgba(98, 126, 172, 0.2);
}

.news-item h4 {
  margin: 0 0 6px;
}

.news-item p {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
}

.news-item small {
  display: block;
  margin-top: 6px;
  color: #7f8ea7;
}
</style>
