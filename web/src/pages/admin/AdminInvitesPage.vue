<template>
  <LegacyAdminShell title="邀请码管理" subtitle="未使用/已使用查询">
    <section class="panel" style="padding: 16px; margin-bottom: 16px;">
      <div class="toolbar">
        <input class="input" v-model.number="count" type="number" min="1" max="50" placeholder="生成数量" />
        <button class="btn primary" @click="generate">生成邀请码</button>
        <button class="btn" @click="load">刷新列表</button>
      </div>
      <p v-if="message" :class="ok ? 'up' : 'down'">{{ message }}</p>
    </section>

    <section class="panel" style="padding: 16px;">
      <div class="tabs">
        <button class="tab-btn" :class="{ active: inviteStatus === 'active' }" @click="switchTab('active')">未使用</button>
        <button class="tab-btn" :class="{ active: inviteStatus === 'used' }" @click="switchTab('used')">已使用</button>
      </div>

      <table class="table">
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
            <td>{{ shortDateTime(item.created_at) }}</td>
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
      </table>

      <div class="pager-wrap">
        <div class="pager">
          <span class="pager-total">共 {{ totalRows }} 条</span>
          <select v-model.number="pageSize" class="pager-select">
            <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}条/页</option>
          </select>
          <button class="btn pager-btn" :disabled="currentPage <= 1" @click="prevPage">上一页</button>
          <span class="pager-page">第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button class="btn pager-btn" :disabled="currentPage >= totalPages" @click="nextPage">下一页</button>
        </div>
      </div>
    </section>
  </LegacyAdminShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import LegacyAdminShell from '../../layouts/LegacyAdminShell.vue'
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

async function load() {
  const status = encodeURIComponent(inviteStatus.value)
  const limit = pageSize.value
  const offset = (currentPage.value - 1) * pageSize.value
  Object.assign(invites, await api.get(`/api/admin/invites?status=${status}&limit=${limit}&offset=${offset}`))
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
    await load()
  } catch (e) {
    flash(e instanceof Error ? e.message : '生成失败', false)
  }
}

watch([inviteStatus, pageSize], async () => {
  currentPage.value = 1
  await load()
})

watch(currentPage, async () => {
  await load()
})

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
}

.tabs {
  margin-bottom: 12px;
  display: flex;
  gap: 8px;
}

.tab-btn {
  border: 1px solid #c7d7ea;
  border-radius: 8px;
  background: #fff;
  color: #36567d;
  padding: 8px 14px;
  cursor: pointer;
  font-weight: 600;
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
  gap: 10px;
}

.pager-total,
.pager-page {
  color: #3f6086;
  font-weight: 600;
}

.pager-select {
  min-width: 110px;
  height: 36px;
  border: 1px solid #c7d7ea;
  border-radius: 8px;
  background: #fff;
  color: #35557d;
  padding: 0 10px;
}

.pager-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
