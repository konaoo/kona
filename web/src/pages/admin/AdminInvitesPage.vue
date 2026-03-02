<template>
  <LegacyAdminShell title="邀请码管理" subtitle="未使用/已使用查询">
    <AdminCard class="tool-card">
      <div class="toolbar">
        <input class="input" v-model.number="count" type="number" min="1" max="50" placeholder="生成数量" />
        <AdminButton variant="primary" @click="generate">生成邀请码</AdminButton>
        <AdminButton variant="ghost" @click="load({ force: true })">刷新列表</AdminButton>
      </div>
      <p v-if="message" :class="ok ? 'up' : 'down'">{{ message }}</p>
    </AdminCard>

    <AdminCard class="list-card">
      <div class="tabs">
        <button class="tab-btn" :class="{ active: inviteStatus === 'active' }" @click="switchTab('active')">未使用</button>
        <button class="tab-btn" :class="{ active: inviteStatus === 'used' }" @click="switchTab('used')">已使用</button>
      </div>

      <AdminTable>
        <thead v-if="inviteStatus === 'active'">
          <tr>
            <th>创建时间</th>
            <th>邀请码</th>
            <th>状态</th>
          </tr>
        </thead>
        <thead v-else>
          <tr>
            <th>邀请码</th>
            <th>用户名</th>
            <th>使用时间</th>
          </tr>
        </thead>
        <tbody v-if="inviteStatus === 'active'">
          <tr v-for="item in invites.items || []" :key="item.code">
            <td>{{ formatDateOnly(item.created_at) }}</td>
            <td>{{ item.code }}</td>
            <td>{{ statusLabel(item.status) }}</td>
          </tr>
          <tr v-if="!(invites.items || []).length">
            <td colspan="3" class="empty">暂无邀请码</td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr v-for="item in invites.items || []" :key="item.code">
            <td>{{ item.code }}</td>
            <td>{{ item.used_by_username || '-' }}</td>
            <td>{{ shortDateTime(item.used_at) }}</td>
          </tr>
          <tr v-if="!(invites.items || []).length">
            <td colspan="3" class="empty">暂无已使用邀请码</td>
          </tr>
        </tbody>
      </AdminTable>

      <div class="pager-wrap">
        <div class="pager">
          <span class="pager-total">共{{ totalRows }}条</span>
          <select v-model.number="pageSize" class="pager-select">
            <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}条/页</option>
          </select>
          <AdminButton size="sm" variant="ghost" :disabled="currentPage <= 1" @click="prevPage">上一页</AdminButton>
          <span class="pager-page">第 {{ currentPage }} / {{ totalPages }} 页</span>
          <AdminButton size="sm" variant="ghost" :disabled="currentPage >= totalPages" @click="nextPage">下一页</AdminButton>
        </div>
      </div>
    </AdminCard>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
import AdminCard from '../../components/admin/ui/AdminCard.vue'
import AdminButton from '../../components/admin/ui/AdminButton.vue'
import AdminTable from '../../components/admin/ui/AdminTable.vue'
import { api } from '../../shared/http'
import { shortDateTime } from '../../shared/format'

const invites = reactive<Record<string, any>>({ items: [], total: 0 })
const count = ref(5)
const message = ref('')
const ok = ref(true)
const inviteStatus = ref<'active' | 'used'>('active')
const pageSize = ref(10)
const pageSizeOptions = [10, 20, 50, 100]
const currentPage = ref(1)
let lastRequestKey = ''
let inflightKey = ''

const totalRows = computed(() => Number(invites.total || 0))
const totalPages = computed(() => {
  const total = totalRows.value
  return total > 0 ? Math.ceil(total / pageSize.value) : 1
})

function flash(msg: string, success: boolean) {
  message.value = msg
  ok.value = success
}

function statusLabel(status: unknown): string {
  const value = String(status || '').toLowerCase()
  if (value === 'active') return '未使用'
  if (value === 'used') return '已使用'
  if (value === 'revoked') return '已撤销'
  return value || '-'
}

function formatDateOnly(value: unknown): string {
  const raw = String(value || '').trim()
  if (!raw) return '-'
  if (raw.length >= 10) return raw.slice(0, 10)
  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) return raw
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

async function load(options: { force?: boolean } = {}) {
  const status = inviteStatus.value
  const limit = pageSize.value
  const offset = (currentPage.value - 1) * pageSize.value
  const force = Boolean(options.force)
  const key = `${status}|${limit}|${offset}|${force ? '1' : '0'}`
  if (!force && (key === lastRequestKey || key === inflightKey)) return
  inflightKey = key
  try {
    const params = new URLSearchParams({
      status,
      limit: String(limit),
      offset: String(offset),
    })
    if (force) params.set('force', '1')
    Object.assign(invites, await api.get(`/api/admin/invites?${params.toString()}`))
    if (!force) lastRequestKey = key
  } finally {
    if (inflightKey === key) inflightKey = ''
  }
}

function switchTab(next: 'active' | 'used') {
  if (inviteStatus.value === next) return
  inviteStatus.value = next
}

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function prevPage() {
  goToPage(currentPage.value - 1)
}

function nextPage() {
  goToPage(currentPage.value + 1)
}

async function generate() {
  try {
    await api.post('/api/admin/invites/generate', { count: count.value })
    flash('生成成功', true)
    currentPage.value = 1
    await load({ force: true })
  } catch (e) {
    flash(e instanceof Error ? e.message : '生成失败', false)
  }
}

watch([inviteStatus, pageSize], async () => {
  if (currentPage.value !== 1) {
    currentPage.value = 1
    return
  }
  await load()
})

watch(currentPage, async () => {
  await load()
})

onMounted(() => {
  void load()
})
</script>

<style scoped>
.tool-card {
  padding: 16px;
  margin-bottom: 16px;
}

.list-card {
  padding: 16px;
}

.toolbar {
  display: flex;
  gap: 8px;
}

.tabs {
  margin-bottom: 12px;
  display: flex;
  gap: 8px;
  width: fit-content;
  padding: 4px;
  border: 1px solid #d8e6f4;
  border-radius: 10px;
  background: #f4f9ff;
}

.tab-btn {
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: #36567d;
  padding: 8px 16px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  background: #e8f2ff;
}

.tab-btn.active {
  background: #1f8ea5;
  border-color: #1f8ea5;
  color: #fff;
}

.pager-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.pager {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid #d9e5f2;
  border-radius: 10px;
  background: #f7fbff;
  max-width: 100%;
  overflow-x: auto;
}

.pager-total,
.pager-page {
  color: #3f6086;
  font-weight: 600;
  white-space: nowrap;
  word-break: keep-all;
  line-height: 1.2;
  flex: 0 0 auto;
}

.pager-select {
  width: 120px !important;
  max-width: 120px;
  min-width: 110px;
  height: 36px;
  border: 1px solid #c7d7ea;
  border-radius: 8px;
  background: #fff;
  color: #35557d;
  padding: 0 10px;
  flex: 0 0 auto;
}

.empty {
  text-align: center;
  color: #55708f;
  font-weight: 600;
}

.up {
  color: var(--success);
}

.down {
  color: var(--danger);
}

@media (max-width: 900px) {
  .toolbar {
    flex-direction: column;
  }

  .pager-wrap {
    justify-content: flex-start;
  }

  .pager {
    flex-wrap: wrap;
  }
}
</style>
