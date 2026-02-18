<template>
  <LegacyAppShell>
    <section class="legacy-section">
      <div class="head">
        <h2>资产详情 · {{ code }}</h2>
        <button class="legacy-btn-primary" @click="load">刷新</button>
      </div>
      <table class="table-legacy">
        <thead><tr><th>代码</th><th>名称</th><th>数量</th><th>现价</th><th>累计盈亏</th></tr></thead>
        <tbody>
          <tr v-if="row">
            <td>{{ row.code }}</td>
            <td>{{ row.name }}</td>
            <td>{{ row.qty }}</td>
            <td>{{ money(row.currentPrice, row.curr || 'CNY') }}</td>
            <td :class="row.totalPnl >= 0 ? 'up' : 'down'">{{ money(row.totalPnl, row.curr || 'CNY') }}</td>
          </tr>
          <tr v-else>
            <td colspan="5">未找到该资产持仓</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="legacy-section">
      <h2>相关交易</h2>
      <table class="table-legacy">
        <thead><tr><th>日期</th><th>类型</th><th>数量</th><th>价格</th><th>盈亏</th></tr></thead>
        <tbody>
          <tr v-for="item in txList" :key="item.id || `${item.date}-${item.type}-${item.qty}`">
            <td>{{ item.date || item.created_at || '-' }}</td>
            <td>{{ item.type || '-' }}</td>
            <td>{{ item.qty || '-' }}</td>
            <td>{{ item.price || '-' }}</td>
            <td>{{ item.pnl || '-' }}</td>
          </tr>
          <tr v-if="!txList.length"><td colspan="5">暂无交易记录</td></tr>
        </tbody>
      </table>
    </section>
  </LegacyAppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import LegacyAppShell from '../../layouts/LegacyAppShell.vue'
import { api } from '../../shared/http'
import { money } from '../../shared/format'
import { useKonaStore } from '../../shared/store'

const route = useRoute()
const store = useKonaStore()
const code = computed(() => String(route.params.code || '').trim())
const txList = ref<Record<string, any>[]>([])

const row = computed(() => store.rows.value.find((item) => String(item.code || '').toLowerCase() === code.value.toLowerCase()))

async function load() {
  await store.refreshAll()
  const payload = await api.get<Record<string, any>[]>('/api/transactions?days=3650')
  txList.value = (Array.isArray(payload) ? payload : []).filter((item) => String(item.code || '').toLowerCase() === code.value.toLowerCase())
}

onMounted(load)
</script>

<style scoped>
.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.up { color: var(--success); }
.down { color: var(--danger); }

h2 {
  margin: 0;
  font-size: 24px;
}

.table-legacy {
  width: 100%;
  border-collapse: collapse;
}

.table-legacy th,
.table-legacy td {
  padding: 12px;
  border-bottom: 1px solid var(--legacy-border);
  text-align: left;
}
</style>
