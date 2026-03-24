<template>
  <div class="container admin-overview">
    <AdminConsoleNav />

    <!-- Main Content -->
    <div class="main-content">
      <div class="header">
        <div class="header-title">
          <h1>{{ greeting }}，{{ store.state.user?.username }}</h1>
        </div>
        <div class="header-actions">
          <button class="add-btn" @click="load(true)">
            <span>+</span>
            <span>刷新数据</span>
          </button>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card revenue">
          <div class="stat-header">
            <span class="stat-label">今日新增用户</span>
            <div class="avatars">
              <div class="avatar" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);"></div>
              <div class="avatar" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);"></div>
              <div class="avatar-count">+{{ overview.dashboard?.new_users_avatar_count || 0 }}</div>
            </div>
          </div>
          <div class="stat-value">{{ overview.dashboard?.new_users_today || 0 }}</div>
          <div class="chart-mini">
            <div
              v-for="(item, i) in overview.dashboard?.new_user_bars || []"
              :key="`new-${item.date}-${i}`"
              class="chart-bar"
              :style="{ height: item.height, background: item.is_latest ? '#000' : '#FFB84D' }"
            ></div>
          </div>
          <div class="percentage">
            <span>⚫</span>
            <span>{{ overview.dashboard?.new_user_trend_text || '近7天新增走势' }}</span>
          </div>
        </div>

        <div class="stat-card expenses">
          <div class="stat-header">
            <span class="stat-label">今日活跃用户</span>
            <button class="icon-btn" style="background: rgba(0,0,0,0.05);">+</button>
          </div>
          <div class="stat-value">{{ overview.dashboard?.active_users_today || 0 }}</div>
          <div class="chart-mini">
            <div
              v-for="(item, i) in overview.dashboard?.active_user_bars || []"
              :key="`active-${item.date}-${i}`"
              class="chart-bar"
              :style="{ height: item.height, background: item.is_latest ? '#FF8B94' : '#000' }"
            ></div>
          </div>
          <div class="percentage">
            <span>⚫</span>
            <span>{{ overview.dashboard?.active_user_trend_text || '近7天活跃走势' }}</span>
          </div>
        </div>

        <div class="stat-card tax">
          <div class="tax-illustration">
            <svg width="100" height="100" viewBox="0 0 100 100">
              <path d="M20,80 Q30,20 50,50 T80,80" stroke="#8BC34A" stroke-width="3" fill="none"/>
              <circle cx="80" cy="80" r="8" fill="#000"/>
              <path d="M80,80 L85,70 L90,80 L95,65" stroke="#000" stroke-width="2" fill="none"/>
            </svg>
          </div>
          <div class="stat-label">系统总计</div>
          <div style="font-size: 20px; font-weight: 700; margin: 12px 0;">累计注册用户</div>
          <div style="font-size: 32px; font-weight: 800; color: #000; margin-bottom: 4px;">{{ overview.dashboard?.total_users || 0 }}</div>
          <div style="font-size: 13px; color: #666;">
            截止当前系统累计<br>
            <strong>入驻用户总数</strong>
          </div>
        </div>
      </div>

      <!-- User Statistics Table -->
      <div class="user-stats-section">
        <h2 class="section-title">用户增长与留存</h2>
        
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>新增用户</th>
                <th>活跃用户</th>
                <th>新增次留</th>
                <th>新增3留</th>
                <th>新增7留</th>
                <th>新增14留</th>
                <th>活跃次留</th>
                <th>活跃3留</th>
                <th>活跃7留</th>
                <th>活跃14留</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in pagedRows" :key="item.date">
                <td>{{ formatDateDisplay(item.date) }}</td>
                <td>{{ item.new_users ?? 0 }}</td>
                <td>{{ item.active_users ?? 0 }}</td>
                <td><span class="retention-rate" :class="getRetentionClass(item.retention_1d)">{{ formatRate(item.retention_1d) }}</span></td>
                <td><span class="retention-rate" :class="getRetentionClass(item.retention_3d)">{{ formatRate(item.retention_3d) }}</span></td>
                <td><span class="retention-rate" :class="getRetentionClass(item.retention_7d)">{{ formatRate(item.retention_7d) }}</span></td>
                <td><span class="retention-rate" :class="getRetentionClass(item.retention_14d)">{{ formatRate(item.retention_14d) }}</span></td>
                <td><span class="retention-rate" :class="getRetentionClass(item.active_retention_1d)">{{ formatRate(item.active_retention_1d) }}</span></td>
                <td><span class="retention-rate" :class="getRetentionClass(item.active_retention_3d)">{{ formatRate(item.active_retention_3d) }}</span></td>
                <td><span class="retention-rate" :class="getRetentionClass(item.active_retention_7d)">{{ formatRate(item.active_retention_7d) }}</span></td>
                <td><span class="retention-rate" :class="getRetentionClass(item.active_retention_14d)">{{ formatRate(item.active_retention_14d) }}</span></td>
              </tr>
              <tr v-if="!retentionRows.length">
                <td colspan="11" style="text-align: center; color: #999; padding: 40px;">暂无统计数据</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="table-footer">
          <div class="page-size-selector">
            <label>每页显示：</label>
            <select v-model.number="pageSize">
              <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}条/页</option>
            </select>
          </div>
          
          <div class="pagination-info">
            显示 <span>{{ startIndex + 1 }}</span>-<span>{{ endIndex }}</span> 
            共 <span>{{ totalRows }}</span> 条
          </div>

          <div class="pagination-controls">
            <button class="page-btn" @click="currentPage = 1" :disabled="currentPage === 1">«</button>
            <button class="page-btn" @click="currentPage--" :disabled="currentPage === 1">‹</button>
            
            <div class="page-numbers">
              <button 
                v-for="p in visiblePages" 
                :key="p" 
                class="page-btn" 
                :class="{ active: p === currentPage }"
                @click="currentPage = p"
              >{{ p }}</button>
            </div>

            <button class="page-btn" @click="currentPage++" :disabled="currentPage === totalPages">›</button>
            <button class="page-btn" @click="currentPage = totalPages" :disabled="currentPage === totalPages">»</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../../shared/http'
import AdminConsoleNav from '../../components/admin/AdminConsoleNav.vue'
import { useKonaStore } from '../../stores/composables'

const store = useKonaStore()

const overview = reactive<Record<string, any>>({
  dashboard: {},
  retention_rows: [],
})

const pageSize = ref(10)
const pageSizeOptions = [10, 30, 50, 100]
const currentPage = ref(1)

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 9) return '早上好'
  if (hour >= 9 && hour < 12) return '上午好'
  if (hour >= 12 && hour < 13) return '中午好'
  if (hour >= 13 && hour < 18) return '下午好'
  return '晚上好'
})

const retentionRows = computed(() => (overview.retention_rows || []) as Array<Record<string, any>>)
const totalRows = computed(() => retentionRows.value.length)
const totalPages = computed(() => Math.ceil(totalRows.value / pageSize.value) || 1)
const startIndex = computed(() => (currentPage.value - 1) * pageSize.value)
const endIndex = computed(() => Math.min(startIndex.value + pageSize.value, totalRows.value))
const pagedRows = computed(() => retentionRows.value.slice(startIndex.value, endIndex.value))

const visiblePages = computed(() => {
  const pages: number[] = []
  let start = Math.max(1, currentPage.value - 2)
  let end = Math.min(totalPages.value, start + 4)
  if (end - start < 4) start = Math.max(1, end - 4)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})


async function load(force = false) {
  const suffix = force ? '?force=1' : ''
  try {
    const payload = await api.get<Record<string, any>>(`/api/admin/overview${suffix}`)
    overview.dashboard = payload?.dashboard || {}
    overview.retention_rows = payload?.retention_rows || []
    currentPage.value = 1
  } catch (e) {
    console.error('Failed to load overview data', e)
  }
}

function formatRate(value: unknown): string {
  if (value === null || value === undefined || value === '') return '-'
  const num = Number(value)
  if (!Number.isFinite(num)) return '-'
  return `${(num * 100).toFixed(1)}%`
}

function formatDateDisplay(dateStr: string): string {
  if (!dateStr || !dateStr.includes('-')) return dateStr
  const parts = dateStr.split('-')
  if (parts.length >= 3) {
    const month = parseInt(parts[1] ?? '0', 10)
    const day = parseInt(parts[2] ?? '0', 10)
    return `${month}月${day}日`
  }
  return dateStr
}

function getRetentionClass(rate: any) {
  if (rate === null || rate === undefined) return ''
  const percent = Number(rate) * 100
  if (percent >= 50) return 'high'
  if (percent >= 30) return 'medium'
  return 'low'
}

watch(pageSize, () => {
  currentPage.value = 1
})

onMounted(() => {
  void load()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.container {
  width: 100vw;
  height: 100vh;
  background: white;
  overflow: hidden;
  display: flex;
  font-family: 'Inter', sans-serif;
  color: #333;
}

/* Sidebar */
.sidebar {
  width: 260px;
  background: white;
  padding: 30px 0 0 0; /* 移除左右和底部 padding 以便于底部栏完全铺满 */
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  height: 100vh;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 800;
  font-size: 19px;
  margin-bottom: 35px;
  padding: 0 24px;
  color: #000;
  letter-spacing: -0.5px;
}

.logo-icon {
  width: 34px;
  height: 34px;
  background: #000;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 18px;
  margin: 0 12px 6px 12px;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: #666;
  font-weight: 600;
  text-decoration: none;
  font-size: 14.5px;
}

.nav-item:hover {
  background: #f8f9fa;
  color: #000;
}

.nav-item.active {
  background: #000;
  color: white;
}

.user-profile {
  margin-top: auto;
  padding: 24px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fdfdfd;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  flex-shrink: 0;
  object-fit: cover;
}

.user-avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: 800;
}

.user-details {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
}

.user-details h4 {
  font-size: 16px;
  font-weight: 800;
  margin: 0;
  padding: 0;
  color: #000;
  line-height: 1;
}

.user-details p {
  font-size: 12px;
  color: #999;
  font-weight: 500;
  margin: 4px 0 0 0;
  padding: 0;
  line-height: 1;
  text-align: left;
}

.user-actions {
  display: flex;
  align-items: center;
}

.logout-btn {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid #e2e2e2;
  background: transparent;
  color: #888;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.logout-btn svg {
  width: 17px;
  height: 17px;
}

.logout-btn:hover {
  background: #2d2d2d;
  color: #fff;
  border-color: #444;
  transform: translateX(2px);
}

/* Main Content */
.main-content {
  flex: 1;
  padding: 40px 50px;
  overflow-y: auto;
  height: 100vh;
  background: #fafafa;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 35px;
}

.header-title h1 {
  font-size: 32px;
  font-weight: 800;
  margin-bottom: 6px;
  color: #000;
  letter-spacing: -0.8px;
}

.header-title p {
  color: #888;
  font-size: 15px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.search-btn, .notification-btn {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-size: 18px;
}

.search-btn:hover, .notification-btn:hover {
  background: white;
  border-color: #000;
  transform: translateY(-2px);
}

.add-btn {
  padding: 0 22px;
  height: 46px;
  background: #000;
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14.5px;
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

/* Stats Cards */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 35px;
}

.stat-card {
  padding: 26px;
  border-radius: 22px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  border: 1px solid transparent;
}

.stat-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
}

.stat-card.revenue {
  background: linear-gradient(135deg, #FFF5E6 0%, #FFECD1 100%);
}

.stat-card.expenses {
  background: linear-gradient(135deg, #FFEBEB 0%, #FFDADA 100%);
}

.stat-card.tax {
  background: linear-gradient(135deg, #EBFCEB 0%, #DAFADA 100%);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.stat-label {
  font-size: 13.5px;
  color: #777;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 36px;
  font-weight: 800;
  margin-bottom: 20px;
  color: #000;
  letter-spacing: -1px;
}

.chart-mini {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 55px;
}

.chart-bar {
  flex: 1;
  border-radius: 4px;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.chart-bar:hover {
  filter: brightness(0.9);
  transform: scaleY(1.05);
}

.percentage {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  font-weight: 700;
  margin-top: 15px;
  color: #333;
}

.avatars {
  display: flex;
  margin-left: 12px;
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid white;
  margin-left: -10px;
}

.avatar-count {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #000;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  margin-left: -10px;
  border: 2px solid white;
}

.tax-illustration {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  width: 90px;
  height: 90px;
  opacity: 0.9;
}

/* Table Section */
.user-stats-section {
  margin-bottom: 40px;
}

.section-title {
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 22px;
  color: #000;
}

.table-container {
  background: white;
  border: 1px solid #edeef1;
  border-radius: 18px;
  overflow: hidden;
  margin-bottom: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: #fbfbfc;
}

.data-table th {
  padding: 16px 22px;
  text-align: center;
  font-weight: 700;
  font-size: 13px;
  color: #888;
  border-bottom: 1px solid #f0f0f2;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-table tbody tr {
  transition: all 0.2s;
  border-bottom: 1px solid #f8f8fb;
}

.data-table tbody tr:hover {
  background: #fcfcfd;
}

.data-table td {
  padding: 18px 22px;
  font-size: 14px;
  color: #444;
  font-weight: 500;
  text-align: center;
}

.data-table td:first-child {
  font-weight: 700;
  color: #000;
}

.retention-rate {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 12.5px;
}

.retention-rate.high {
  background: #ecfdf5;
  color: #10b981;
}

.retention-rate.medium {
  background: #fffbeb;
  color: #f59e0b;
}

.retention-rate.low {
  background: #fef2f2;
  color: #ef4444;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13.5px;
  color: #777;
  font-weight: 600;
}

.page-size-selector select {
  padding: 9px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: white;
  cursor: pointer;
  font-size: 13.5px;
  font-weight: 600;
  transition: all 0.2s;
  outline: none;
}

.page-size-selector select:hover {
  border-color: #000;
}

.pagination-info {
  font-size: 13.5px;
  color: #777;
  font-weight: 600;
}

.pagination-info span {
  font-weight: 800;
  color: #000;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-numbers {
  display: flex;
  gap: 6px;
}

.page-btn {
  min-width: 38px;
  height: 38px;
  padding: 0 10px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.page-btn:hover:not(:disabled) {
  background: white;
  border-color: #000;
  transform: translateY(-1px);
}

.page-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.page-btn.active {
  background: #000;
  color: white;
  border-color: #000;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 900px) {
  .sidebar {
    display: none;
  }
  .main-content {
    padding: 30px 20px calc(112px + env(safe-area-inset-bottom));
  }
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
