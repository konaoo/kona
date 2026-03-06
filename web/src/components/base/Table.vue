<script setup lang="ts">
/**
 * Table - 表格组件
 * 用于展示结构化数据
 */

import { computed, ref } from 'vue'

export interface TableColumn {
  /** 列键值 */
  key: string
  /** 列标题 */
  title: string
  /** 列宽度 */
  width?: string | number
  /** 对齐方式 */
  align?: 'left' | 'center' | 'right'
  /** 是否可排序 */
  sortable?: boolean
  /** 自定义渲染函数 */
  render?: (value: unknown, row: Record<string, unknown>) => unknown
}

export interface TableProps {
  /** 表格列定义 */
  columns: TableColumn[]
  /** 表格数据 */
  data: Record<string, unknown>[]
  /** 表格尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 是否显示边框 */
  border?: boolean
  /** 是否斑马纹 */
  stripe?: boolean
  /** 是否悬停高亮 */
  hover?: boolean
  /** 是否显示表头 */
  showHeader?: boolean
  /** 空状态文字 */
  emptyText?: string
  /** 行键值字段 */
  rowKey?: string
  /** 是否可点击行 */
  clickable?: boolean
  /** 加载状态 */
  loading?: boolean
}

const props = withDefaults(defineProps<TableProps>(), {
  size: 'md',
  border: false,
  stripe: true,
  hover: true,
  showHeader: true,
  emptyText: '暂无数据',
  rowKey: 'id',
  clickable: false,
  loading: false
})

const emit = defineEmits<{
  rowClick: [row: Record<string, unknown>, index: number]
  sortChange: [column: TableColumn, order: 'asc' | 'desc' | null]
}>()

const sortColumn = ref<TableColumn>()
const sortOrder = ref<'asc' | 'desc' | null>(null)

const tableClass = computed(() => {
  return [
    'table',
    `table-${props.size}`,
    {
      'table-border': props.border,
      'table-stripe': props.stripe,
      'table-hover': props.hover
    }
  ]
})

const alignedClass = (align?: string) => {
  return align ? `table-cell-${align}` : ''
}

const handleSort = (column: TableColumn) => {
  if (!column.sortable) return

  if (sortColumn.value?.key === column.key) {
    // 切换排序顺序：asc -> desc -> null
    if (sortOrder.value === 'asc') {
      sortOrder.value = 'desc'
    } else if (sortOrder.value === 'desc') {
      sortOrder.value = null
      sortColumn.value = undefined
    } else {
      sortOrder.value = 'asc'
    }
  } else {
    sortColumn.value = column
    sortOrder.value = 'asc'
  }

  emit('sortChange', column, sortOrder.value)
}

const getSortIcon = (column: TableColumn) => {
  if (sortColumn.value?.key !== column.key || !sortOrder.value) {
    return '⇅'
  }
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

const handleRowClick = (row: Record<string, unknown>, index: number) => {
  if (props.clickable) {
    emit('rowClick', row, index)
  }
}

const getCellValue = (column: TableColumn, row: Record<string, unknown>) => {
  const value = row[column.key]

  if (column.render) {
    return column.render(value, row)
  }

  return value
}
</script>

<template>
  <div class="table-wrapper">
    <table :class="tableClass">
      <thead v-if="showHeader">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            :class="['table-th', alignedClass(column.align), { 'table-th-sortable': column.sortable }]"
            :style="{ width: typeof column.width === 'number' ? `${column.width}px` : column.width }"
            @click="handleSort(column)"
          >
            <span class="table-th-content">
              {{ column.title }}
              <span v-if="column.sortable" class="table-sort-icon">{{ getSortIcon(column) }}</span>
            </span>
          </th>
        </tr>
      </thead>

      <tbody>
        <tr v-if="loading">
          <td :colspan="columns.length" class="table-loading">
            <div class="loading-spinner"></div>
            <div>加载中...</div>
          </td>
        </tr>

        <tr v-else-if="data.length === 0">
          <td :colspan="columns.length" class="table-empty">
            {{ emptyText }}
          </td>
        </tr>

        <tr
          v-else
          v-for="(row, index) in data"
          :key="(row[rowKey] as string) || index"
          :class="{ 'table-row-clickable': clickable }"
          @click="handleRowClick(row, index)"
        >
          <td
            v-for="column in columns"
            :key="column.key"
            :class="['table-td', alignedClass(column.align)]"
          >
            <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
              {{ getCellValue(column, row) }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   TABLE COMPONENT - 表格组件样式
   ═══════════════════════════════════════════════════════════════ */

.table-wrapper {
  width: 100%;
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: var(--bg);
}

/* ───────────────────────────────────────────────────────────────
   HEADER - 表头
   ─────────────────────────────────────────────────────────────── */

.table-th {
  padding: var(--space-3) var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--sub);
  text-align: left;
  border-bottom: 1px solid var(--border);
  background: var(--s1);
  user-select: none;
}

.table-th-content {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.table-th-sortable {
  cursor: pointer;
  transition: color var(--duration-base) var(--easing-default);
}

.table-th-sortable:hover {
  color: var(--text);
}

.table-sort-icon {
  font-size: var(--font-size-xs);
  color: var(--muted);
}

/* ───────────────────────────────────────────────────────────────
   BODY - 表格内容
   ─────────────────────────────────────────────────────────────── */

.table-td {
  padding: var(--space-3) var(--space-4);
  font-size: var(--font-size-base);
  color: var(--text);
  border-bottom: 1px solid var(--border);
  transition: background var(--duration-base) var(--easing-default);
}

.table-row-clickable {
  cursor: pointer;
}

/* ───────────────────────────────────────────────────────────────
   ALIGNMENT - 对齐方式
   ─────────────────────────────────────────────────────────────── */

.table-cell-left {
  text-align: left;
}

.table-cell-center {
  text-align: center;
}

.table-cell-right {
  text-align: right;
}

/* ───────────────────────────────────────────────────────────────
   BORDER - 边框
   ─────────────────────────────────────────────────────────────── */

.table-border .table-td {
  border-right: 1px solid var(--border);
}

.table-border .table-th {
  border-right: 1px solid var(--border);
}

/* ───────────────────────────────────────────────────────────────
   STRIPE - 斑马纹
   ─────────────────────────────────────────────────────────────── */

.table-stripe tbody tr:nth-child(even) {
  background: var(--s1);
}

/* ───────────────────────────────────────────────────────────────
   HOVER - 悬停效果
   ─────────────────────────────────────────────────────────────── */

.table-hover tbody tr:hover:not(.table-row-clickable) {
  background: var(--s1);
}

.table-hover tbody tr.table-row-clickable:hover {
  background: var(--s2);
  box-shadow: var(--shadow-sm);
}

/* ───────────────────────────────────────────────────────────────
   SIZE VARIANTS - 尺寸变体
   ─────────────────────────────────────────────────────────────── */

.table-sm .table-th,
.table-sm .table-td {
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-sm);
}

.table-lg .table-th,
.table-lg .table-td {
  padding: var(--space-4) var(--space-5);
  font-size: var(--font-size-md);
}

/* ───────────────────────────────────────────────────────────────
   STATES - 状态
   ─────────────────────────────────────────────────────────────── */

.table-loading,
.table-empty {
  text-align: center !important;
  color: var(--muted);
  padding: var(--space-8) var(--space-4);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  margin: 0 auto var(--space-3);
  border: 3px solid var(--border);
  border-top-color: var(--blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
