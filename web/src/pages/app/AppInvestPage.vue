<template>
  <AppShell title="投资" subtitle="持仓、交易与实时价格">
    <section class="panel section">
      <div class="section-head">
        <h3 class="section-title">快捷交易</h3>
        <span class="text-muted">所有操作提交后会自动刷新持仓</span>
      </div>
      <div class="actions-grid">
        <form class="action panel" @submit.prevent="addAsset">
          <h4 class="form-title">新增持仓</h4>
          <input class="input" v-model.trim="addForm.code" placeholder="代码，如 sh600000 / hk00700 / AAPL" />
          <input class="input" v-model.trim="addForm.name" placeholder="名称" />
          <input class="input" v-model.number="addForm.qty" type="number" step="0.0001" placeholder="数量" />
          <input class="input" v-model.number="addForm.price" type="number" step="0.0001" placeholder="成本价" />
          <input class="input" v-model.trim="addForm.curr" placeholder="币种 CNY/HKD/USD" />
          <button class="btn primary" type="submit">提交</button>
        </form>

        <form class="action panel" @submit.prevent="buyAsset">
          <h4>买入</h4>
          <input class="input" v-model.trim="buyForm.code" placeholder="代码" />
          <input class="input" v-model.number="buyForm.qty" type="number" step="0.0001" placeholder="数量" />
          <input class="input" v-model.number="buyForm.price" type="number" step="0.0001" placeholder="价格" />
          <button class="btn primary" type="submit">买入</button>
        </form>

        <form class="action panel" @submit.prevent="sellAsset">
          <h4>卖出</h4>
          <input class="input" v-model.trim="sellForm.code" placeholder="代码" />
          <input class="input" v-model.number="sellForm.qty" type="number" step="0.0001" placeholder="数量" />
          <input class="input" v-model.number="sellForm.price" type="number" step="0.0001" placeholder="价格" />
          <button class="btn primary" type="submit">卖出</button>
        </form>
      </div>
      <p v-if="message" class="feedback" :class="ok ? 'value-up' : 'value-down'">{{ message }}</p>
    </section>

    <section class="panel section">
      <div class="table-head">
        <h3 class="section-title">全部持仓</h3>
        <button class="btn" @click="refresh">刷新行情</button>
      </div>
      <table class="table">
        <thead>
          <tr>
            <th>代码</th>
            <th>名称</th>
            <th>市场</th>
            <th>数量</th>
            <th>现价/成本</th>
            <th>当日盈亏</th>
            <th>累计盈亏</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.code">
            <td><RouterLink :to="`/app/asset/${row.code}`">{{ row.code }}</RouterLink></td>
            <td>{{ row.name }}</td>
            <td>{{ row.market }}</td>
            <td>{{ row.qty }}</td>
            <td>{{ money(row.currentPrice, row.curr || 'CNY') }} / {{ money(row.costPrice, row.curr || 'CNY') }}</td>
            <td :class="row.dayPnl >= 0 ? 'value-up' : 'value-down'">{{ money(row.dayPnl, row.curr || 'CNY') }} ({{ pct(row.dayPnlRate) }})</td>
            <td :class="row.totalPnl >= 0 ? 'value-up' : 'value-down'">{{ money(row.totalPnl, row.curr || 'CNY') }} ({{ pct(row.totalPnlRate) }})</td>
          </tr>
        </tbody>
      </table>
    </section>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppShell from '../../layouts/AppShell.vue'
import { api } from '../../shared/http'
import { money, pct } from '../../shared/format'
import { useKonaStore } from '../../shared/store'

const store = useKonaStore()

const rows = computed(() => store.rows.value)
const message = ref('')
const ok = ref(true)

const addForm = reactive({ code: '', name: '', qty: 0, price: 0, curr: 'CNY' })
const buyForm = reactive({ code: '', qty: 0, price: 0 })
const sellForm = reactive({ code: '', qty: 0, price: 0 })

async function refresh() {
  await store.refreshAll()
}

function flash(msg: string, success: boolean) {
  message.value = msg
  ok.value = success
}

async function addAsset() {
  try {
    await api.post('/api/portfolio/add', addForm)
    flash('新增成功', true)
    await refresh()
  } catch (e) {
    flash(e instanceof Error ? e.message : '新增失败', false)
  }
}

async function buyAsset() {
  try {
    await api.post('/api/portfolio/buy', buyForm)
    flash('买入成功', true)
    await refresh()
  } catch (e) {
    flash(e instanceof Error ? e.message : '买入失败', false)
  }
}

async function sellAsset() {
  try {
    await api.post('/api/portfolio/sell', sellForm)
    flash('卖出成功', true)
    await refresh()
  } catch (e) {
    flash(e instanceof Error ? e.message : '卖出失败', false)
  }
}

onMounted(refresh)
</script>

<style scoped>
.section {
  padding: 16px;
  margin-bottom: 14px;
}

.actions-grid {
  margin-top: 10px;
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.action {
  padding: 14px;
  display: grid;
  gap: 9px;
  border-radius: 14px;
  border-color: rgba(84, 117, 170, 0.28);
}

.form-title {
  margin: 0 0 2px;
  font-size: 15px;
  font-weight: 680;
}

.feedback {
  margin: 12px 0 0;
  border-radius: 10px;
  border: 1px solid rgba(85, 117, 170, 0.32);
  background: rgba(11, 20, 37, 0.5);
  padding: 8px 12px;
  width: fit-content;
}

.table-head {
  margin-bottom: 8px;
}

.table td a {
  color: #a9cbff;
  font-weight: 600;
}

@media (max-width: 1100px) {
  .actions-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .section {
    padding: 14px;
  }
}
</style>
