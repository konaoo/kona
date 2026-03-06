# 组件库使用指南

本文档介绍咔咔记账 Web 组件库的所有组件及使用方法。

---

## 📦 安装与导入

### 全局注册（可选）

```typescript
// main.ts
import { createApp } from 'vue'
import App from './App.vue'
import * as Components from './components'

const app = createApp(App)

// 全局注册所有组件
Object.entries(Components).forEach(([name, component]) => {
  if (name !== 'default' && typeof component !== 'function') {
    app.component(name, component)
  }
})
```

### 按需导入（推荐）

```vue
<script setup lang="ts">
import { Button, Input, Modal } from '@/components'
</script>
```

---

## 🎨 基础组件

### 1. Button - 按钮

基础交互组件，支持多种样式和状态。

```vue
<template>
  <!-- 基础用法 -->
  <Button type="primary">主要按钮</Button>
  <Button type="secondary">次要按钮</Button>
  <Button type="ghost">幽灵按钮</Button>
  <Button type="danger">危险按钮</Button>

  <!-- 不同尺寸 -->
  <Button size="sm">小按钮</Button>
  <Button size="md">中按钮</Button>
  <Button size="lg">大按钮</Button>

  <!-- 状态 -->
  <Button disabled>禁用按钮</Button>
  <Button loading>加载中...</Button>

  <!-- 特效 -->
  <Button hover-lift>悬停提升</Button>
  <Button pulse>脉冲动画</Button>

  <!-- 事件 -->
  <Button @click="handleClick">点击事件</Button>
</template>

<script setup lang="ts">
import { Button } from '@/components'

const handleClick = (e: MouseEvent) => {
  console.log('Button clicked', e)
}
</script>
```

### 2. Input - 输入框

基础表单组件。

```vue
<template>
  <!-- 基础用法 -->
  <Input v-model="value" placeholder="请输入内容" />

  <!-- 带清除按钮 -->
  <Input v-model="value" clearable placeholder="可清除" />

  <!-- 带前后图标 -->
  <Input v-model="value" prefix-icon="🔍" placeholder="搜索" />
  <Input v-model="value" suffix-icon="📅" placeholder="日期" />

  <!-- 错误状态 -->
  <Input v-model="value" error :error-text="'输入有误'" />

  <!-- 数字输入 -->
  <Input v-model="num" type="number" :min="0" :max="100" />

  <!-- 事件 -->
  <Input
    v-model="value"
    @focus="handleFocus"
    @blur="handleBlur"
    @enter="handleEnter"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Input } from '@/components'

const value = ref('')
const num = ref(0)
</script>
```

### 3. Select - 选择器

下拉选择组件。

```vue
<template>
  <Select
    v-model="selected"
    :options="options"
    placeholder="请选择"
    clearable
    filterable
    @change="handleChange"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Select, type SelectOption } from '@/components'

const selected = ref('')

const options: SelectOption[] = [
  { value: '1', label: '选项1' },
  { value: '2', label: '选项2' },
  { value: '3', label: '选项3' }
]

const handleChange = (value: string | number) => {
  console.log('Selected:', value)
}
</script>
```

### 4. Modal - 模态框

弹窗对话框组件。

```vue
<template>
  <Button @click="show = true">打开模态框</Button>

  <Modal
    v-model:show="show"
    title="标题"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <p>这是模态框内容</p>
  </Modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Modal, Button } from '@/components'

const show = ref(false)

const handleOk = () => {
  console.log('确认')
  show.value = false
}

const handleCancel = () => {
  console.log('取消')
  show.value = false
}
</script>
```

### 5. Tabs - 标签页

组织和切换内容。

```vue
<template>
  <Tabs :tabs="tabs" default-key="home" @change="handleChange">
    <template #home>首页内容</template>
    <template #profile>个人资料</template>
  </Tabs>
</template>

<script setup lang="ts">
import { Tabs, type Tab } from '@/components'

const tabs: Tab[] = [
  { key: 'home', label: '首页' },
  { key: 'profile', label: '资料' }
]

const handleChange = (key: string) => {
  console.log('Tab changed:', key)
}
</script>
```

### 6. Badge - 徽章

用于显示状态标识。

```vue
<template>
  <!-- 自动判断涨跌 -->
  <Badge :value="1.23" />

  <!-- 手动指定类型 -->
  <Badge type="up" text="+5.0%" />
  <Badge type="down" text="-3.2%" />
  <Badge type="neutral" text="0.0%" />
</template>
```

### 7. Tag - 标签

用于显示分类标识。

```vue
<template>
  <Tag type="hk">港股</Tag>
  <Tag type="us">美股</Tag>
  <Tag type="a">A股</Tag>
  <Tag type="fund">基金</Tag>
</template>
```

### 8. Card - 卡片

容器组件。

```vue
<template>
  <Card border hoverable padding="md">
    <h3>卡片标题</h3>
    <p>卡片内容</p>
  </Card>
</template>
```

### 9. Progress - 进度条

显示进度。

```vue
<template>
  <!-- 线性进度条 -->
  <Progress :percent="60" />

  <!-- 圆形进度条 -->
  <Progress type="circle" :percent="75" />

  <!-- 不同颜色 -->
  <Progress :percent="80" color-type="success" />
  <Progress :percent="90" color-type="warning" />
  <Progress :percent="30" color-type="danger" />
</template>
```

### 10. Table - 表格

展示结构化数据。

```vue
<template>
  <Table
    :columns="columns"
    :data="data"
    stripe
    hover
    @row-click="handleRowClick"
  >
    <template #cell-name="{ row, value }">
      <strong>{{ value }}</strong>
    </template>
  </Table>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Table, type TableColumn } from '@/components'

const columns: TableColumn[] = [
  { key: 'name', title: '名称', width: 200 },
  { key: 'value', title: '数值', align: 'right' }
]

const data = ref([
  { id: 1, name: '项目A', value: 100 },
  { id: 2, name: '项目B', value: 200 }
])
</script>
```

---

## 💼 业务组件

### 11. PositionCard - 持仓卡片

```vue
<template>
  <PositionCard
    :position="positionData"
    :clickable="true"
    @click="handleClick"
  />
</template>

<script setup lang="ts">
import { PositionCard } from '@/components'
import type { PositionRow } from '@/types'

const positionData: PositionRow = {
  code: '00700.HK',
  name: '腾讯控股',
  market: 'hk',
  qty: 1000,
  cost_price: 300,
  // ... 其他字段
}
</script>
```

### 12. MarketTag - 市场标签

```vue
<template>
  <MarketTag market="hk" :show-icon="true" :full-name="true" />
  <!-- 显示: 🇭🇰 港股 -->
</template>
```

### 13. AccountPill - 账户选择器

```vue
<template>
  <AccountPill
    :user="userData"
    :balance="123456.78"
    currency="CNY"
    @click="handleClick"
  />
</template>
```

### 14. Calendar - 日历

```vue
<template>
  <Calendar
    v-model="selectedDate"
    :highlighted-dates="highlightedDates"
    @select="handleDateSelect"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Calendar } from '@/components'

const selectedDate = ref(new Date())
const highlightedDates = ref([new Date(), new Date('2026-03-10')])
</script>
```

### 15. NewsCard - 新闻卡片

```vue
<template>
  <NewsCard
    title="新闻标题"
    summary="新闻摘要..."
    source="财经快讯"
    :time="new Date()"
    :show-image="false"
  />
</template>
```

### 16. RankingCard - 排行榜

```vue
<template>
  <RankingCard
    title="涨幅榜"
    type="gain"
    :items="rankingData"
    :limit="5"
    @item-click="handleItemClick"
  />
</template>
```

### 17. PnLBar - 盈亏进度条

```vue
<template>
  <PnLBar
    :value="1234.56"
    :total="10000"
    :show-value="true"
    :show-percent="true"
  />
</template>
```

### 18. AssetSummary - 资产摘要

```vue
<template>
  <AssetSummary
    :total-asset="123456.78"
    :day-pnl="1234.56"
    :day-pnl-rate="1.23"
    :total-pnl="12345.67"
    :total-pnl-rate="10.5"
    currency="CNY"
    layout="horizontal"
  />
</template>
```

### 19. IconButton - 图标按钮

```vue
<template>
  <IconButton
    icon="🔍"
    tooltip="搜索"
    @click="handleClick"
  />

  <IconButton
    icon="❌"
    type="danger"
    size="sm"
    @click="handleDelete"
  />
</template>
```

---

## 🎯 完整示例：持仓列表

```vue
<template>
  <div class="position-list">
    <AssetSummary
      :total-asset="totalAsset"
      :day-pnl="dayPnL"
      :day-pnl-rate="dayPnLRate"
      :total-pnl="totalPnL"
      :total-pnl-rate="totalPnLRate"
    />

    <Table
      :columns="columns"
      :data="positions"
      :loading="loading"
      @row-click="handleRowClick"
    >
      <template #cell-market="{ row, value }">
        <MarketTag :market="value" size="sm" />
      </template>

      <template #cell-day_pnl="{ row, value }">
        <Badge :value="value" />
      </template>
    </Table>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Table, AssetSummary, MarketTag, Badge, type TableColumn } from '@/components'
import type { PositionRow } from '@/types'

const loading = ref(false)
const positions = ref<PositionRow[]>([])

const columns: TableColumn[] = [
  { key: 'name', title: '名称', width: 200 },
  { key: 'market', title: '市场', width: 100, align: 'center' },
  { key: 'value', title: '持有金额', align: 'right' },
  { key: 'day_pnl', title: '当日盈亏', align: 'right' }
]

const totalAsset = computed(() =>
  positions.value.reduce((sum, p) => sum + p.value, 0)
)

const dayPnL = computed(() =>
  positions.value.reduce((sum, p) => sum + p.day_pnl, 0)
)
</script>
```

---

## 📝 类型定义

所有组件都导出了完整的 TypeScript 类型定义：

```typescript
import type {
  ButtonProps,
  InputProps,
  SelectOption,
  TableColumn,
  ModalProps,
  PositionCardProps,
  // ... 更多类型
} from '@/components'
```

---

## 🔧 自定义样式

组件使用了 CSS 变量，可以通过覆盖变量来自定义样式：

```css
/* 在你的组件或全局样式中 */
.custom-button {
  --btn-primary-bg: #custom-color;
  --btn-primary-hover: #custom-hover-color;
}
```

---

## 📚 更多资源

- 查看源码：`src/components/base/` 和 `src/components/business/`
- 设计系统：`src/styles/tokens.css`
- 类型定义：`src/types/`
