<script setup lang="ts">
/**
 * 组件使用示例
 * 演示如何使用组件库中的各种组件
 */

import { ref } from 'vue'

// 导入组件
import {
  Button,
  Input,
  Select,
  Modal,
  Badge,
  Tag,
  Card,
  Table,
  AssetSummary,
  PositionCard,
  MarketTag,
  IconButton
} from '@/components'

// 导入类型
import type { SelectOption, TableColumn } from '@/components'
import type { PositionRow } from '@/types'

// ───────────────────────────────────────────────────────────────
// 状态定义
// ───────────────────────────────────────────────────────────────

const showModal = ref(false)
const inputValue = ref('')
const selectValue = ref('')
const loading = ref(false)

// Select 选项
const selectOptions: SelectOption[] = [
  { value: 'hk', label: '港股' },
  { value: 'us', label: '美股' },
  { value: 'a', label: 'A股' },
  { value: 'fund', label: '基金' }
]

// 模拟持仓数据
const mockPosition: PositionRow = {
  code: '00700.HK',
  name: '腾讯控股',
  market: 'hk',
  asset_type: 'stock',
  qty: 1000,
  costPrice: 300,
  rawCostPrice: 300,
  displayCostPrice: 320,
  currentPrice: 350,
  yclose: 345,
  value: 350000,
  cost: 320000,
  totalPnl: 30000,
  totalPnlRate: 9.375,
  dayPnl: 5000,
  dayPnlRate: 1.45,
  dayPnlDisplay: 5000,
  dayPnlRateDisplay: 1.45,
  dayPnlAggregate: 5000,
  dayPnlRateAggregate: 1.45,
  session: 'regular',
  marketOpen: true,
  marketTradingDay: true,
  marketStatusReason: 'open',
  usExtendedActive: false,
  navUpdatePending: false,
  dayPnlDisplayEnabled: true,
  dayPnlAggregateEnabled: true,
  currency: 'HKD'
}

// 表格列定义
const tableColumns: TableColumn[] = [
  { key: 'name', title: '名称', width: 200 },
  { key: 'code', title: '代码', width: 120 },
  { key: 'market', title: '市场', width: 100, align: 'center' },
  { key: 'value', title: '持有金额', align: 'right' },
  { key: 'dayPnl', title: '当日盈亏', align: 'right' }
]

// 模拟表格数据
const tableData = ref([
  {
    id: 1,
    name: '腾讯控股',
    code: '00700.HK',
    market: 'hk',
    value: 350000,
    dayPnl: 5000
  },
  {
    id: 2,
    name: '苹果公司',
    code: 'AAPL',
    market: 'us',
    value: 450000,
    dayPnl: -2000
  },
  {
    id: 3,
    name: '贵州茅台',
    code: '600519',
    market: 'a',
    value: 280000,
    dayPnl: 3000
  }
])

// ───────────────────────────────────────────────────────────────
// 事件处理
// ───────────────────────────────────────────────────────────────

const handleButtonClick = () => {
  showModal.value = true
}

const handleModalOk = () => {
  console.log('确认操作')
  showModal.value = false
}

const handleModalCancel = () => {
  console.log('取消操作')
  showModal.value = false
}

const handleSelectChange = (value: string | number) => {
  console.log('选择变更:', value)
}

const handleRowClick = (row: Record<string, unknown>, index: number) => {
  console.log('行点击:', row, index)
}

const handlePositionClick = (position: PositionRow) => {
  console.log('持仓点击:', position)
}

const handleDelete = () => {
  console.log('删除操作')
}

const handleRefresh = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 1000)
}
</script>

<template>
  <div class="component-example">
    <div style="max-width: 1200px; margin: 0 auto; padding: var(--space-6);">
      <!-- 标题 -->
      <h1 style="font-size: var(--font-size-3xl); font-weight: var(--font-weight-bold); margin-bottom: var(--space-6);">
        组件使用示例
      </h1>

      <!-- Button 示例 -->
      <Card title="Button 按钮" style="margin-bottom: var(--space-4);">
        <div style="display: flex; gap: var(--space-3); flex-wrap: wrap;">
          <Button type="primary" @click="handleButtonClick">主要按钮</Button>
          <Button type="secondary">次要按钮</Button>
          <Button type="ghost">幽灵按钮</Button>
          <Button type="danger">危险按钮</Button>
          <Button :loading="loading">加载中</Button>
          <Button @click="handleRefresh">刷新</Button>
        </div>
      </Card>

      <!-- Input 示例 -->
      <Card title="Input 输入框" style="margin-bottom: var(--space-4);">
        <div style="display: flex; gap: var(--space-3); flex-wrap: wrap;">
          <Input
            v-model="inputValue"
            placeholder="请输入内容"
            clearable
            style="width: 200px;"
          />
          <Input
            v-model="inputValue"
            type="number"
            placeholder="数字输入"
            style="width: 200px;"
          />
          <Input
            v-model="inputValue"
            prefix-icon="🔍"
            placeholder="搜索"
            style="width: 200px;"
          />
        </div>
      </Card>

      <!-- Select 示例 -->
      <Card title="Select 选择器" style="margin-bottom: var(--space-4);">
        <Select
          v-model="selectValue"
          :options="selectOptions"
          placeholder="请选择市场"
          clearable
          style="width: 200px;"
          @change="handleSelectChange"
        />
      </Card>

      <!-- Badge & Tag 示例 -->
      <Card title="Badge & Tag 徽章与标签" style="margin-bottom: var(--space-4);">
        <div style="display: flex; gap: var(--space-3); flex-wrap: wrap; align-items: center;">
          <Badge :value="1.23" />
          <Badge :value="-0.45" />
          <Badge :value="0" />
          <Badge type="primary" text="主要" />
          <Badge type="success" text="成功" />

          <div style="width: 1px; height: 20px; background: var(--border); margin: 0 var(--space-2);"></div>

          <Tag type="hk">港股</Tag>
          <Tag type="us">美股</Tag>
          <Tag type="a">A股</Tag>
          <Tag type="fund">基金</Tag>
        </div>
      </Card>

      <!-- IconButton 示例 -->
      <Card title="IconButton 图标按钮" style="margin-bottom: var(--space-4);">
        <div style="display: flex; gap: var(--space-2);">
          <IconButton icon="🔍" tooltip="搜索" />
          <IconButton icon="🔄" tooltip="刷新" @click="handleRefresh" />
          <IconButton icon="✏️" tooltip="编辑" type="secondary" />
          <IconButton icon="❌" tooltip="删除" type="danger" @click="handleDelete" />
          <IconButton icon="➕" tooltip="添加" type="primary" />
        </div>
      </Card>

      <!-- AssetSummary 示例 -->
      <Card title="AssetSummary 资产摘要" style="margin-bottom: var(--space-4);">
        <AssetSummary
          :total-asset="123456.78"
          :day-pn-l="1234.56"
          :day-pn-l-rate="1.23"
          :total-pn-l="12345.67"
          :total-pn-l-rate="10.5"
          currency="CNY"
          layout="horizontal"
        />
      </Card>

      <!-- PositionCard 示例 -->
      <Card title="PositionCard 持仓卡片" style="margin-bottom: var(--space-4);">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--space-4);">
          <PositionCard
            :position="mockPosition"
            :clickable="true"
            @click="handlePositionClick"
          />
        </div>
      </Card>

      <!-- MarketTag 示例 -->
      <Card title="MarketTag 市场标签" style="margin-bottom: var(--space-4);">
        <div style="display: flex; gap: var(--space-3); flex-wrap: wrap;">
          <MarketTag market="hk" :show-icon="true" :full-name="true" />
          <MarketTag market="us" :show-icon="true" :full-name="true" />
          <MarketTag market="a" :show-icon="true" :full-name="true" />
          <MarketTag market="fund" :show-icon="true" :full-name="true" />
        </div>
      </Card>

      <!-- Table 示例 -->
      <Card title="Table 表格" style="margin-bottom: var(--space-4);">
        <Table
          :columns="tableColumns"
          :data="tableData"
          stripe
          hover
          :clickable="true"
          @row-click="handleRowClick"
        >
          <template #cell-market="{ value }">
            <MarketTag :market="value as any" size="sm" />
          </template>

          <template #cell-dayPnl="{ value }">
            <Badge :value="value as number" />
          </template>

          <template #cell-value="{ value }">
            <span class="mono">¥{{ (value as number).toLocaleString() }}</span>
          </template>
        </Table>
      </Card>

      <!-- 组合示例：持仓列表 -->
      <Card title="组合示例：持仓列表" style="margin-bottom: var(--space-4);">
        <AssetSummary
          :total-asset="123456.78"
          :day-pn-l="1234.56"
          :day-pn-l-rate="1.23"
          :total-pn-l="12345.67"
          :total-pn-l-rate="10.5"
          layout="compact"
          style="margin-bottom: var(--space-4);"
        />

        <Table
          :columns="tableColumns"
          :data="tableData"
          stripe
          hover
        >
          <template #cell-market="{ value }">
            <MarketTag :market="value as any" size="sm" />
          </template>

          <template #cell-dayPnl="{ value }">
            <Badge :value="value as number" />
          </template>

          <template #cell-value="{ value }">
            <span class="mono">¥{{ (value as number).toLocaleString() }}</span>
          </template>
        </Table>
      </Card>

      <!-- 代码示例 -->
      <Card title="代码示例">
        <pre style="background: var(--bg); padding: var(--space-4); border-radius: var(--radius-md); overflow-x: auto; font-size: var(--font-size-sm); line-height: 1.6;"><code><span style="color: #89ddff;">&lt;script setup</span> <span style="color: #89ddff;">lang=</span><span style="color: #c3e88d;">"ts"</span><span style="color: #89ddff;">&gt;</span>
<span style="color: #89ddff;">import</span> { Button, Input, Modal } <span style="color: #89ddff;">from</span> <span style="color: #c3e88d;">'@/components'</span>

<span style="color: #89ddff;">const</span> showModal <span style="color: #89ddff;">=</span> <span style="color: #82aaff;">ref</span>(<span style="color: #f78c6c;">false</span>)
<span style="color: #89ddff;">&lt;/script&gt;</span>

<span style="color: #89ddff;">&lt;template&gt;</span>
  <span style="color: #89ddff;">&lt;Button</span> <span style="color: #f07178;">@click</span><span style="color: #89ddff;">=</span><span style="color: #c3e88d;">"showModal = true"</span><span style="color: #89ddff;">&gt;</span>打开对话框<span style="color: #89ddff;">&lt;/Button&gt;</span>

  <span style="color: #89ddff;">&lt;Modal</span> <span style="color: #f07178;">v-model:show</span><span style="color: #89ddff;">=</span><span style="color: #c3e88d;">"showModal"</span> <span style="color: #f07178;">title</span><span style="color: #89ddff;">=</span><span style="color: #c3e88d;">"提示"</span><span style="color: #89ddff;">&gt;</span>
    <span style="color: #89ddff;">&lt;Input</span> <span style="color: #f07178;">v-model</span><span style="color: #89ddff;">=</span><span style="color: #c3e88d;">"value"</span> <span style="color: #f07178;">placeholder</span><span style="color: #89ddff;">=</span><span style="color: #c3e88d;">"请输入"</span> <span style="color: #89ddff;">/&gt;</span>
  <span style="color: #89ddff;">&lt;/Modal&gt;</span>
<span style="color: #89ddff;">&lt;/template&gt;</span></code></pre>
      </Card>
    </div>

    <!-- Modal 对话框 -->
    <Modal
      v-model:show="showModal"
      title="提示"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
    >
      <p style="margin-bottom: var(--space-4);">这是一个模态框示例</p>
      <Input v-model="inputValue" placeholder="请输入内容" />
    </Modal>
  </div>
</template>

<style scoped>
.component-example {
  min-height: 100vh;
  background: var(--bg);
}

.mono {
  font-family: var(--font-family-mono);
}
</style>
