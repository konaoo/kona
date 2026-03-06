# Pinia Stores 使用指南

本文档介绍咔咔记账 Web Pinia 状态管理的使用方法。

---

## 📦 安装

Pinia 已在第二阶段添加到依赖中。如果未安装，运行：

```bash
npm install pinia
```

---

## 🎯 快速开始

### 1. 基础使用（向后兼容）

如果你之前使用 `useKonaStore()`，无需修改代码，只需更新导入路径：

```vue
<script setup lang="ts">
// 原来的导入
// import { useKonaStore } from '@/shared/store'

// 新的导入（只需改这一行）
import { useKonaStore } from '@/stores/composables'

const {
  state,
  rows,
  summary,
  isAuthenticated,
  refreshAll
} = useKonaStore()

// 使用方式与之前完全相同
onMounted(() => {
  refreshAll()
})
</script>
```

### 2. 模块化使用（推荐）

使用组合式 API 直接访问特定领域：

```vue
<script setup lang="ts">
import { useAuth, usePortfolio } from '@/stores/composables'

// 认证
const { user, isAuthenticated, login, logout } = useAuth()

// 投资组合
const { rows, summary, loadPortfolio } = usePortfolio()

// 使用
onMounted(async () => {
  if (isAuthenticated.value) {
    await loadPortfolio()
  }
})
</script>
```

### 3. 直接使用 Store（高级）

直接访问 Pinia store 实例：

```vue
<script setup lang="ts">
import { useAuthStore } from '@/stores'
import { usePortfolioStore } from '@/stores'

const authStore = useAuthStore()
const portfolioStore = usePortfolioStore()

// 直接访问 store 的状态和方法
console.log(authStore.user)
console.log(portfolioStore.summary.totalValue)

// 调用 actions
await portfolioStore.loadPortfolio()
</script>
```

---

## 📚 Stores 详解

### Auth Store - 认证管理

```typescript
import { useAuthStore } from '@/stores'

const authStore = useAuthStore()

// 状态
authStore.token          // 访问令牌
authStore.refreshToken   // 刷新令牌
authStore.user           // 用户信息
authStore.isAuthenticated // 是否已登录（computed）
authStore.isAdmin        // 是否管理员（computed）

// 方法
await authStore.bootstrap()           // 初始化认证
await authStore.login(username, password)      // 登录
await authStore.register(username, password, code)  // 注册
await authStore.logout()                        // 登出
authStore.clearAuthState()                     // 清除认证状态
```

**使用示例**：

```vue
<script setup lang="ts">
import { useAuth } from '@/stores/composables'

const { user, isAuthenticated, login, logout } = useAuth()

const handleLogin = async () => {
  try {
    await login('myusername', 'mypassword')
    console.log('登录成功', user.value)
  } catch (error) {
    console.error('登录失败', error)
  }
}
</script>

<template>
  <div v-if="isAuthenticated">
    <p>欢迎，{{ user?.nickname || user?.username }}</p>
    <button @click="logout">登出</button>
  </div>
  <div v-else>
    <button @click="handleLogin">登录</button>
  </div>
</template>
```

---

### Portfolio Store - 投资组合管理

```typescript
import { usePortfolioStore } from '@/stores'

const portfolioStore = usePortfolioStore()

// 状态
portfolioStore.portfolio  // 原始持仓数据
portfolioStore.loading    // 加载状态

// 计算属性
portfolioStore.rows              // 计算后的持仓行（包含所有计算字段）
portfolioStore.summary           // 投资组合摘要
portfolioStore.groupedByMarket   // 按市场分组

// 方法
await portfolioStore.loadPortfolio()                  // 加载持仓
portfolioStore.updatePortfolioItem(code, updates)    // 更新持仓
portfolioStore.removePortfolioItem(code)             // 删除持仓
portfolioStore.addPortfolioItem(item)                // 添加持仓
portfolioStore.getPortfolioItem(code)                // 获取持仓
portfolioStore.clearPortfolio()                      // 清空持仓
```

**使用示例**：

```vue
<script setup lang="ts">
import { usePortfolio } from '@/stores/composables'
import { computed } from 'vue'

const { rows, summary, loadPortfolio, updatePortfolioItem } = usePortfolio()

// 计算总资产
const totalAsset = computed(() => summary.value.totalValue)

// 按加载持仓
onMounted(() => {
  loadPortfolio()
})

// 更新持仓数量
const handleUpdateQty = (code: string, newQty: number) => {
  updatePortfolioItem(code, { qty: newQty })
}
</script>

<template>
  <div>
    <h2>总资产：¥{{ totalAsset.toLocaleString() }}</h2>

    <table>
      <thead>
        <tr>
          <th>名称</th>
          <th>数量</th>
          <th>现价</th>
          <th>盈亏</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.code">
          <td>{{ row.name }}</td>
          <td>{{ row.qty }}</td>
          <td>¥{{ row.currentPrice.toFixed(2) }}</td>
          <td :class="row.totalPnl >= 0 ? 'text-up' : 'text-down'">
            ¥{{ row.totalPnl.toFixed(2) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
```

---

### Quote Store - 行情管理

```typescript
import { useQuoteStore } from '@/stores'

const quoteStore = useQuoteStore()

// 状态
quoteStore.quotes        // 行情数据
quoteStore.quotePolicy   // 行情策略
quoteStore.loading       // 加载状态

// 方法
await quoteStore.loadQuotes(codes)              // 加载行情
quoteStore.getQuote(code)                       // 获取行情
quoteStore.getQuotePrice(code)                  // 获取价格
quoteStore.getQuoteYClose(code)                 // 获取昨收价
quoteStore.getQuoteSession(code)                // 获取会话
quoteStore.startAutoRefresh()                   // 开始自动刷新
quoteStore.stopAutoRefresh()                    // 停止自动刷新
```

**使用示例**：

```vue
<script setup lang="ts">
import { useQuote } from '@/stores/composables'
import { onMounted, onUnmounted } from 'vue'

const { loadQuotes, getQuotePrice, startAutoRefresh, stopAutoRefresh } = useQuote()

const codes = ['00700.HK', 'AAPL', '600519']

onMounted(async () => {
  await loadQuotes(codes)
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

const getPrice = (code: string) => {
  return getQuotePrice(code).toFixed(2)
}
</script>

<template>
  <div>
    <div v-for="code in codes" :key="code">
      {{ code }}: ¥{{ getPrice(code) }}
    </div>
  </div>
</template>
```

---

### Market Store - 市场状态管理

```typescript
import { useMarketStore } from '@/stores'

const marketStore = useMarketStore()

// 状态
marketStore.marketStatus     // 市场状态
marketStore.allClosed        // 是否全部闭市
marketStore.rates            // 汇率
marketStore.loading          // 加载状态

// 计算属性
marketStore.hasAnyOpenMarket // 是否有开市市场

// 方法
await marketStore.loadMarketStatus()        // 加载市场状态
await marketStore.loadRates()               // 加载汇率
marketStore.getMarketStatus(market)         // 获取市场状态
marketStore.isMarketOpen(market)            // 判断是否开市
marketStore.getRate(from, to)               // 获取汇率
```

**使用示例**：

```vue
<script setup lang="ts">
import { useMarket } from '@/stores/composables'
import { onMounted } from 'vue'

const {
  marketStatus,
  hasAnyOpenMarket,
  loadMarketStatus,
  isMarketOpen
} = useMarket()

onMounted(() => {
  loadMarketStatus()
})

const getMarketText = (market: string) => {
  return isMarketOpen(market as any) ? '开市' : '闭市'
}
</script>

<template>
  <div>
    <p>市场状态：{{ hasAnyOpenMarket ? '有市场开市' : '全部闭市' }}</p>
    <ul>
      <li>A股：{{ getMarketText('a') }}</li>
      <li>港股：{{ getMarketText('hk') }}</li>
      <li>美股：{{ getMarketText('us') }}</li>
    </ul>
  </div>
</template>
```

---

### Sync Store - 数据同步管理

```typescript
import { useSyncStore } from '@/stores'

const syncStore = useSyncStore()

// 状态
syncStore.syncVersions    // 同步版本
syncStore.loading         // 加载状态

// 方法
await syncStore.loadBootstrap(include)            // Bootstrap 同步
syncStore.invalidateSyncVersion(domain)          // 使版本失效
syncStore.markPortfolioDirty()                   // 标记投资组合为脏
syncStore.markRatesDirty()                       // 标记汇率为脏
syncStore.clearStoreCache()                      // 清除缓存
syncStore.persistStoreCache(...)                 // 持久化缓存
syncStore.hydrateStoreCache(...)                 // 恢复缓存
```

---

## 🔄 完整示例：持仓列表

```vue
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuth, usePortfolio, useMarket } from '@/stores/composables'
import { Table, Badge, MarketTag, type TableColumn } from '@/components'

// 认证状态
const { isAuthenticated, user } = useAuth()

// 投资组合
const { rows, summary, loading, loadPortfolio } = usePortfolio()

// 市场状态
const { marketStatus, loadMarketStatus } = useMarket()

// 表格列定义
const columns: TableColumn[] = [
  { key: 'name', title: '名称', width: 200 },
  { key: 'market', title: '市场', width: 100 },
  { key: 'qty', title: '数量', align: 'right' },
  { key: 'value', title: '持有金额', align: 'right' },
  { key: 'dayPnl', title: '当日盈亏', align: 'right' },
  { key: 'totalPnl', title: '累计盈亏', align: 'right' },
]

// 生命周期
onMounted(async () => {
  if (isAuthenticated.value) {
    await Promise.all([
      loadPortfolio(),
      loadMarketStatus()
    ])
  }
})

// 计算属性
const totalAsset = computed(() => summary.value.totalValue)
const dayPnl = computed(() => summary.value.todayPnl)
const totalPnl = computed(() => summary.value.totalPnl)
</script>

<template>
  <div class="portfolio-page">
    <!-- 资产摘要 -->
    <div class="summary">
      <div class="summary-item">
        <span class="label">总资产</span>
        <span class="value">¥{{ totalAsset.toLocaleString() }}</span>
      </div>
      <div class="summary-item">
        <span class="label">当日盈亏</span>
        <span class="value" :class="dayPnl >= 0 ? 'text-up' : 'text-down'">
          ¥{{ dayPnl >= 0 ? '+' : '' }}{{ dayPnl.toLocaleString() }}
        </span>
      </div>
      <div class="summary-item">
        <span class="label">累计盈亏</span>
        <span class="value" :class="totalPnl >= 0 ? 'text-up' : 'text-down'">
          ¥{{ totalPnl >= 0 ? '+' : '' }}{{ totalPnl.toLocaleString() }}
        </span>
      </div>
    </div>

    <!-- 持仓列表 -->
    <Table
      :columns="columns"
      :data="rows"
      :loading="loading"
      stripe
      hover
    >
      <template #cell-market="{ row, value }">
        <MarketTag :market="value" size="sm" />
      </template>

      <template #cell-dayPnl="{ row, value }">
        <Badge :value="value" />
      </template>

      <template #cell-value="{ row, value }">
        <span class="mono">¥{{ value.toLocaleString() }}</span>
      </template>
    </Table>
  </div>
</template>
```

---

## 💡 最佳实践

### 1. 使用组合式 API

推荐使用组合式 API 而不是直接使用 store：

```typescript
// ✅ 推荐
import { useAuth, usePortfolio } from '@/stores/composables'

// ❌ 不推荐（除非需要高级功能）
import { useAuthStore, usePortfolioStore } from '@/stores'
```

### 2. 按需导入

只导入需要的功能：

```typescript
// ✅ 推荐：只导入需要的
import { useAuth } from '@/stores/composables'

// ❌ 不推荐：导入所有
import { useKonaStore } from '@/stores/composables'
```

### 3. 使用计算属性

对于复杂的派生状态，使用计算属性：

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { usePortfolio } from '@/stores/composables'

const { rows } = usePortfolio()

// ✅ 推荐：使用计算属性
const hkPositions = computed(() =>
  rows.value.filter(row => row.market === 'hk')
)

// ❌ 不推荐：在模板中直接过滤
</script>

<template>
  <!-- ✅ 使用计算属性 -->
  <div v-for="row in hkPositions" :key="row.code">
    {{ row.name }}
  </div>
</template>
```

### 4. 错误处理

始终处理异步操作的错误：

```typescript
// ✅ 推荐：处理错误
try {
  await loadPortfolio()
} catch (error) {
  console.error('加载持仓失败', error)
  // 显示错误提示
}

// ❌ 不推荐：忽略错误
await loadPortfolio()
```

---

## 🔧 调试

### Pinia DevTools

Pinia 支持官方 DevTools 扩展：

1. 安装 [Vue DevTools](https://devtools.vuejs.org/)
2. 打开浏览器开发者工具
3. 切换到 "Pinia" 标签
4. 查看所有 stores 的状态

### 查看状态

```typescript
import { useAuthStore } from '@/stores'

const authStore = useAuthStore()

// 在控制台查看
console.log('Auth Store:', authStore)
console.log('User:', authStore.user)
console.log('Is Authenticated:', authStore.isAuthenticated)
```

---

## 📚 更多资源

- [Pinia 官方文档](https://pinia.vuejs.org/)
- [Vue 3 文档](https://vuejs.org/)
- 项目类型定义：`src/stores/types.ts`
- 组件库文档：`COMPONENT-LIBRARY.md`
