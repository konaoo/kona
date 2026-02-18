<template>
  <LegacyAppShell>
    <template #fab>
      <button class="legacy-fab-btn" @click="togglePrivacy">{{ isPrivacyMode ? '🙈' : '👁️' }}</button>
      <button class="legacy-fab-btn" @click="saveAsImage">📸</button>
    </template>

    <div id="capture-area">
      <section class="legacy-section">
        <div class="assets-header">
          <div class="total-assets-section">
            <div class="total-mv-label">总资产 (CNY)</div>
            <div class="main-mv">{{ masked(formatCny(totalAssets)) }}</div>
          </div>
          <div class="asset-breakdown">
            <article class="asset-card">
              <div class="asset-card-label">现金资产</div>
              <div class="asset-card-value cash">{{ masked(formatCny(cashTotal)) }}</div>
            </article>
            <article class="asset-card">
              <div class="asset-card-label">投资资产</div>
              <div class="asset-card-value invest">{{ masked(formatCny(investTotal.mv)) }}</div>
            </article>
            <article class="asset-card">
              <div class="asset-card-label">其他资产</div>
              <div class="asset-card-value other">{{ masked(formatCny(otherTotal)) }}</div>
            </article>
          </div>
        </div>
      </section>

      <section class="legacy-section">
        <div class="section-header">
          <div class="section-title">投资资产</div>
          <RouterLink to="/app/invest" class="goto-link">查看详情 →</RouterLink>
        </div>

        <div class="invest-header">
          <div class="invest-total">
            <div class="invest-total-label">持有总市值 (CNY)</div>
            <div class="invest-total-value">{{ masked(formatCny(investTotal.mv)) }}</div>
          </div>
          <div class="pnl-stats">
            <article class="pnl-stat-item">
              <div class="pnl-label">今日盈亏</div>
              <div class="pnl-value" :class="valueClass(investTotal.dayPnl)">
                {{ masked(formatSignedCny(investTotal.dayPnl)) }}
              </div>
              <div class="pnl-rate" :class="valueClass(investTotal.dayRate)">{{ formatPct(investTotal.dayRate) }}</div>
            </article>
            <article class="pnl-stat-item">
              <div class="pnl-label">持仓盈亏</div>
              <div class="pnl-value" :class="valueClass(investTotal.floatPnl)">
                {{ masked(formatSignedCny(investTotal.floatPnl)) }}
              </div>
              <div class="pnl-rate" :class="valueClass(investTotal.floatRate)">{{ formatPct(investTotal.floatRate) }}</div>
            </article>
            <article class="pnl-stat-item">
              <div class="pnl-label">累计盈亏</div>
              <div class="pnl-value" :class="valueClass(investTotal.totalPnl)">
                {{ masked(formatSignedCny(investTotal.totalPnl)) }}
              </div>
              <div class="pnl-rate" :class="valueClass(investTotal.totalRate)">{{ formatPct(investTotal.totalRate) }}</div>
            </article>
          </div>
        </div>

        <div class="category-grid">
          <article v-for="market in marketCards" :key="market.key" class="category-card">
            <div class="category-header">
              <span class="category-icon">{{ market.icon }}</span>
              <span class="category-name">{{ market.name }}</span>
            </div>
            <div class="category-mv" :class="market.key">{{ masked(formatCny(market.mv)) }}</div>
            <div class="category-pnl">
              <div class="category-pnl-row">
                <span class="category-pnl-label">今日盈亏</span>
                <span class="category-pnl-value" :class="valueClass(market.dayPnl)">
                  {{ masked(formatSignedCny(market.dayPnl)) }} ({{ formatPct(market.dayRate) }})
                </span>
              </div>
              <div class="category-pnl-row">
                <span class="category-pnl-label">持仓盈亏</span>
                <span class="category-pnl-value" :class="valueClass(market.floatPnl)">
                  {{ masked(formatSignedCny(market.floatPnl)) }} ({{ formatPct(market.floatRate) }})
                </span>
              </div>
              <div class="category-pnl-row">
                <span class="category-pnl-label">累计盈亏</span>
                <span class="category-pnl-value" :class="valueClass(market.totalPnl)">
                  {{ masked(formatSignedCny(market.totalPnl)) }} ({{ formatPct(market.totalRate) }})
                </span>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="legacy-section">
        <div class="section-header">
          <div class="section-title">现金资产</div>
          <button class="legacy-btn-primary section-add-btn" @click="openModal('cash')">+ 添加</button>
        </div>
        <div class="invest-total-label">现金总额 (CNY)</div>
        <div class="invest-total-value cash">{{ masked(formatCny(cashTotal)) }}</div>
        <div class="asset-card-grid">
          <article v-for="item in cashAssets" :key="`cash-${item.id}`" class="asset-card-item">
            <div class="asset-card-item-header">
              <div class="asset-card-item-name">{{ item.name }}</div>
              <div class="row-actions">
                <button class="action-btn" @click="openModal('cash', item)">编辑</button>
                <button class="action-btn danger" @click="removeAsset('cash', item.id)">删除</button>
              </div>
            </div>
            <div class="asset-card-item-value cash">{{ masked(formatCny(toCny(item.amount, item.curr))) }}</div>
          </article>
          <div v-if="!cashAssets.length" class="empty-state">暂无现金资产</div>
        </div>
      </section>

      <section class="legacy-section">
        <div class="section-header">
          <div class="section-title">其他资产</div>
          <button class="legacy-btn-primary section-add-btn" @click="openModal('other')">+ 添加</button>
        </div>
        <div class="invest-total-label">其他资产总额 (CNY)</div>
        <div class="invest-total-value other">{{ masked(formatCny(otherTotal)) }}</div>
        <div class="asset-card-grid">
          <article v-for="item in otherAssets" :key="`other-${item.id}`" class="asset-card-item">
            <div class="asset-card-item-header">
              <div class="asset-card-item-name">{{ item.name }}</div>
              <div class="row-actions">
                <button class="action-btn" @click="openModal('other', item)">编辑</button>
                <button class="action-btn danger" @click="removeAsset('other', item.id)">删除</button>
              </div>
            </div>
            <div class="asset-card-item-value other">{{ masked(formatCny(toCny(item.amount, item.curr))) }}</div>
          </article>
          <div v-if="!otherAssets.length" class="empty-state">暂无其他资产</div>
        </div>
      </section>

      <section class="legacy-section">
        <div class="section-header">
          <div class="section-title">我的负债</div>
          <button class="legacy-btn-primary section-add-btn" @click="openModal('liability')">+ 添加</button>
        </div>
        <div class="invest-total-label">负债总额 (CNY)</div>
        <div class="invest-total-value liability">{{ masked(formatCny(liabilityTotal)) }}</div>
        <div class="asset-card-grid">
          <article v-for="item in liabilities" :key="`liability-${item.id}`" class="asset-card-item">
            <div class="asset-card-item-header">
              <div class="asset-card-item-name">{{ item.name }}</div>
              <div class="row-actions">
                <button class="action-btn" @click="openModal('liability', item)">编辑</button>
                <button class="action-btn danger" @click="removeAsset('liability', item.id)">删除</button>
              </div>
            </div>
            <div class="asset-card-item-value liability">{{ masked(formatCny(toCny(item.amount, item.curr))) }}</div>
          </article>
          <div v-if="!liabilities.length" class="empty-state">暂无负债记录</div>
        </div>
      </section>
    </div>

    <div v-if="modalVisible" class="overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ modalMode === 'add' ? '添加资产' : '编辑资产' }}</h3>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <form @submit.prevent="submitModal">
          <div class="input-group">
            <label class="input-label">资产名称</label>
            <input v-model.trim="form.name" class="modal-input" required />
          </div>
          <div class="input-group">
            <label class="input-label">金额 (CNY)</label>
            <input v-model.number="form.amount" class="modal-input" type="number" min="0.01" step="0.01" required />
          </div>
          <button class="btn-primary full" type="submit">{{ modalMode === 'add' ? '确认保存' : '保存修改' }}</button>
        </form>
      </div>
    </div>
  </LegacyAppShell>
</template>

<script setup lang="ts">
import html2canvas from 'html2canvas'
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import LegacyAppShell from '../../layouts/LegacyAppShell.vue'
import { api } from '../../shared/http'
import { toNumber } from '../../shared/format'
import { useKonaStore } from '../../shared/store'

type AssetType = 'cash' | 'other' | 'liability'
type SimpleAsset = { id: number; name: string; amount: number; curr?: string }

const store = useKonaStore()
const rows = computed(() => store.rows.value)
const rates = computed(() => store.state.rates)

const cashAssets = ref<SimpleAsset[]>([])
const otherAssets = ref<SimpleAsset[]>([])
const liabilities = ref<SimpleAsset[]>([])
const isPrivacyMode = ref(localStorage.getItem('privacy_mode') === 'true')

const modalVisible = ref(false)
const modalType = ref<AssetType>('cash')
const modalMode = ref<'add' | 'edit'>('add')
const form = reactive<{ id: number | null; name: string; amount: number; curr: string }>({
  id: null,
  name: '',
  amount: 0,
  curr: 'CNY',
})

const marketMeta = {
  a: { name: 'A股', icon: '🇨🇳' },
  us: { name: '美股', icon: '🇺🇸' },
  hk: { name: '港股', icon: '🇭🇰' },
  fund: { name: '基金', icon: '📊' },
} as const

function rateToCny(curr?: string): number {
  const c = String(curr || 'CNY').toUpperCase()
  return toNumber(rates.value[c], 1) || 1
}

function toCny(amount: unknown, curr?: string): number {
  return toNumber(amount) * rateToCny(curr)
}

function formatCny(value: number): string {
  return `¥ ${Math.round(value).toLocaleString('zh-CN')}`
}

function formatSignedCny(value: number): string {
  const sign = value >= 0 ? '+' : '-'
  return `${sign}¥ ${Math.abs(Math.round(value)).toLocaleString('zh-CN')}`
}

function formatPct(value: number): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
}

function valueClass(value: number): 'up' | 'down' {
  return value >= 0 ? 'up' : 'down'
}

function masked(text: string): string {
  return isPrivacyMode.value ? '****' : text
}

const investTotal = computed(() => {
  let mv = 0
  let cost = 0
  let dayPnl = 0
  let floatPnl = 0
  let totalPnl = 0
  for (const row of rows.value) {
    const rate = rateToCny(row.curr)
    const rowMv = toNumber(row.value) * rate
    const rowCost = toNumber(row.costPrice) * toNumber(row.qty) * rate
    mv += rowMv
    cost += rowCost
    dayPnl += toNumber(row.dayPnl) * rate
    floatPnl += (toNumber(row.value) - toNumber(row.costPrice) * toNumber(row.qty)) * rate
    totalPnl += toNumber(row.totalPnl) * rate
  }
  return {
    mv,
    cost,
    dayPnl,
    floatPnl,
    totalPnl,
    dayRate: mv - dayPnl > 0 ? (dayPnl / (mv - dayPnl)) * 100 : 0,
    floatRate: cost > 0 ? (floatPnl / cost) * 100 : 0,
    totalRate: cost > 0 ? (totalPnl / cost) * 100 : 0,
  }
})

const marketCards = computed(() => {
  const marketStats = {
    a: { mv: 0, cost: 0, dayPnl: 0, floatPnl: 0, totalPnl: 0 },
    us: { mv: 0, cost: 0, dayPnl: 0, floatPnl: 0, totalPnl: 0 },
    hk: { mv: 0, cost: 0, dayPnl: 0, floatPnl: 0, totalPnl: 0 },
    fund: { mv: 0, cost: 0, dayPnl: 0, floatPnl: 0, totalPnl: 0 },
  }

  for (const row of rows.value) {
    const key = String(row.market || 'a') as keyof typeof marketStats
    const stats = marketStats[key]
    const rate = rateToCny(row.curr)
    const mv = toNumber(row.value) * rate
    const cost = toNumber(row.costPrice) * toNumber(row.qty) * rate
    stats.mv += mv
    stats.cost += cost
    stats.dayPnl += toNumber(row.dayPnl) * rate
    stats.floatPnl += (toNumber(row.value) - toNumber(row.costPrice) * toNumber(row.qty)) * rate
    stats.totalPnl += toNumber(row.totalPnl) * rate
  }

  return (Object.keys(marketMeta) as Array<keyof typeof marketMeta>).map((key) => {
    const stats = marketStats[key]
    return {
      key,
      name: marketMeta[key].name,
      icon: marketMeta[key].icon,
      ...stats,
      dayRate: stats.mv - stats.dayPnl > 0 ? (stats.dayPnl / (stats.mv - stats.dayPnl)) * 100 : 0,
      floatRate: stats.cost > 0 ? (stats.floatPnl / stats.cost) * 100 : 0,
      totalRate: stats.cost > 0 ? (stats.totalPnl / stats.cost) * 100 : 0,
    }
  })
})

const cashTotal = computed(() => cashAssets.value.reduce((sum, item) => sum + toCny(item.amount, item.curr), 0))
const otherTotal = computed(() => otherAssets.value.reduce((sum, item) => sum + toCny(item.amount, item.curr), 0))
const liabilityTotal = computed(() => liabilities.value.reduce((sum, item) => sum + toCny(item.amount, item.curr), 0))
const totalAssets = computed(() => investTotal.value.mv + cashTotal.value + otherTotal.value - liabilityTotal.value)

async function loadLists() {
  const [cash, other, debt] = await Promise.all([
    api.get<SimpleAsset[]>('/api/cash_assets'),
    api.get<SimpleAsset[]>('/api/other_assets'),
    api.get<SimpleAsset[]>('/api/liabilities'),
  ])
  cashAssets.value = Array.isArray(cash) ? cash : []
  otherAssets.value = Array.isArray(other) ? other : []
  liabilities.value = Array.isArray(debt) ? debt : []
}

async function refresh() {
  await Promise.all([store.refreshAll(), loadLists()])
}

function togglePrivacy() {
  isPrivacyMode.value = !isPrivacyMode.value
  localStorage.setItem('privacy_mode', String(isPrivacyMode.value))
}

async function saveAsImage() {
  const target = document.getElementById('capture-area')
  if (!target) return
  const canvas = await html2canvas(target, { backgroundColor: '#0a0e27', scale: 2, useCORS: true })
  const link = document.createElement('a')
  link.download = `kaka-assets-${Date.now()}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}

function openModal(type: AssetType, item?: SimpleAsset) {
  modalType.value = type
  modalMode.value = item ? 'edit' : 'add'
  form.id = item?.id ?? null
  form.name = item?.name ?? ''
  form.amount = toNumber(item?.amount, 0)
  form.curr = item?.curr || 'CNY'
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
}

async function submitModal() {
  const payload = { id: form.id, name: form.name, amount: form.amount, curr: form.curr }
  const map = {
    cash: {
      add: '/api/cash_assets/add',
      update: '/api/cash_assets/update',
    },
    other: {
      add: '/api/other_assets/add',
      update: '/api/other_assets/update',
    },
    liability: {
      add: '/api/liabilities/add',
      update: '/api/liabilities/update',
    },
  } as const
  const route = modalMode.value === 'add' ? map[modalType.value].add : map[modalType.value].update
  await api.post(route, payload)
  closeModal()
  await refresh()
}

async function removeAsset(type: AssetType, id: number) {
  const ok = confirm('确认删除该资产？')
  if (!ok) return
  const map = {
    cash: '/api/cash_assets/delete',
    other: '/api/other_assets/delete',
    liability: '/api/liabilities/delete',
  } as const
  await api.post(map[type], { id })
  await refresh()
}

onMounted(refresh)
</script>

<style scoped>
.assets-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 28px;
}

.total-assets-section {
  display: flex;
  flex-direction: column;
}

.total-mv-label {
  font-size: 14px;
  color: var(--legacy-text-secondary);
  margin-bottom: 14px;
}

.main-mv {
  font-size: 52px;
  font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  user-select: none;
}

.asset-breakdown {
  display: flex;
  gap: 14px;
}

.asset-card {
  background: var(--legacy-bg-tertiary);
  border: 2px solid var(--legacy-border);
  border-radius: var(--legacy-radius-sm);
  padding: 14px 16px;
  min-width: 170px;
}

.asset-card-label {
  font-size: 13px;
  color: var(--legacy-text-secondary);
  margin-bottom: 8px;
}

.asset-card-value {
  font-size: 24px;
  font-weight: 800;
}

.asset-card-value.cash { color: var(--legacy-green); }
.asset-card-value.invest { color: var(--legacy-blue); }
.asset-card-value.other { color: var(--legacy-orange); }

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--legacy-border);
}

.section-title {
  font-size: 30px;
  font-weight: 700;
  margin: 0;
}

.goto-link {
  color: var(--legacy-text-secondary);
  text-decoration: none;
  font-size: 13px;
}

.section-add-btn {
  min-width: 88px;
  height: 36px;
  border-radius: 999px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 700;
  background: linear-gradient(135deg, #4d7dff 0%, #6b6cff 100%);
  box-shadow: 0 8px 20px rgba(77, 125, 255, 0.32);
}

.section-add-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(77, 125, 255, 0.4);
}

.invest-header {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}

.invest-total-label {
  color: var(--legacy-text-secondary);
  margin-bottom: 8px;
}

.invest-total-value {
  font-size: 40px;
  font-weight: 700;
}

.invest-total-value.cash { color: var(--legacy-green); }
.invest-total-value.other { color: var(--legacy-orange); }
.invest-total-value.liability { color: var(--legacy-red); }

.pnl-stats {
  display: flex;
  gap: 12px;
}

.pnl-stat-item {
  background: var(--legacy-bg-tertiary);
  border: 2px solid var(--legacy-border);
  border-radius: var(--legacy-radius-sm);
  padding: 14px 16px;
  min-width: 160px;
}

.pnl-label {
  font-size: 12px;
  color: var(--legacy-text-secondary);
  margin-bottom: 8px;
}

.pnl-value {
  font-size: 18px;
  font-weight: 700;
}

.pnl-rate {
  margin-top: 4px;
  font-size: 13px;
}

.up { color: var(--legacy-red); }
.down { color: var(--legacy-green); }

.category-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.category-card {
  background: var(--legacy-bg-tertiary);
  border: 2px solid var(--legacy-border);
  border-radius: var(--legacy-radius-sm);
  padding: 14px 16px;
}

.category-header {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
}

.category-name {
  font-size: 20px;
  font-weight: 700;
}

.category-mv {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}

.category-mv.a { color: var(--legacy-blue); }
.category-mv.us { color: var(--legacy-purple); }
.category-mv.hk { color: var(--legacy-orange); }
.category-mv.fund { color: var(--legacy-green); }

.category-pnl-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 6px;
  font-size: 14px;
}

.category-pnl-label {
  color: var(--legacy-text-secondary);
}

.asset-card-grid {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.asset-card-item {
  background: var(--legacy-bg-tertiary);
  border: 2px solid var(--legacy-border);
  border-radius: 12px;
  padding: 14px;
  min-height: 108px;
  position: relative;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.asset-card-item:hover {
  background: rgba(255, 255, 255, 0.09);
  border-color: rgba(255, 255, 255, 0.2);
}

.asset-card-item-header {
  display: block;
  min-height: 22px;
}

.asset-card-item-name {
  color: var(--legacy-text-secondary);
  font-size: 14px;
  padding-right: 88px;
}

.asset-card-item-value {
  margin-top: 14px;
  font-size: 24px;
  font-weight: 700;
}

.asset-card-item-value.cash { color: var(--legacy-green); }
.asset-card-item-value.other { color: var(--legacy-orange); }
.asset-card-item-value.liability { color: var(--legacy-red); }

.row-actions {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 4px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
}

.asset-card-item:hover .row-actions {
  opacity: 1;
  pointer-events: auto;
}

.action-btn {
  height: 26px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.9);
  color: var(--legacy-text-secondary);
  font-size: 12px;
  padding: 0 8px;
  cursor: pointer;
}

.action-btn:hover { color: #fff; }
.action-btn.danger:hover { color: #ff9c9d; }

.empty-state {
  padding: 24px;
  color: var(--legacy-text-secondary);
}

.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  z-index: 6000;
}

.modal {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #1e293b;
  border-radius: 20px;
  padding: 28px;
  width: 420px;
  border: 1px solid var(--legacy-border);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.close-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 0;
  cursor: pointer;
  background: var(--legacy-bg-tertiary);
  color: #fff;
  font-size: 24px;
}

.input-group { margin-bottom: 16px; }
.input-label {
  display: block;
  margin-bottom: 8px;
  color: var(--legacy-text-secondary);
  font-size: 13px;
}
.modal-input {
  width: 100%;
  background: #0f172a;
  border: 1px solid var(--legacy-border);
  border-radius: 12px;
  color: #fff;
  padding: 12px;
}
.btn-primary.full {
  width: 100%;
  border: 0;
  border-radius: 12px;
  height: 44px;
  cursor: pointer;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: #fff;
  font-weight: 700;
}

@media (max-width: 1400px) {
  .asset-card-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }

  .category-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .assets-header,
  .invest-header {
    flex-direction: column;
  }

  .asset-breakdown,
  .pnl-stats {
    flex-wrap: wrap;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .main-mv { font-size: 38px; }
  .section-title { font-size: 30px; }
  .asset-card-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .category-grid { grid-template-columns: 1fr; }
  .modal { width: 90%; padding: 20px; }
}

@media (hover: none) {
  .row-actions {
    opacity: 1;
    pointer-events: auto;
  }
}
</style>
