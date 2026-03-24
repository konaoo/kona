<script setup lang="ts">
/**
 * Calendar - 日历组件
 * 用于选择日期、显示月度数据
 */

import { computed, ref, watch } from 'vue'
import dayjs from 'dayjs'

export interface CalendarProps {
  /** 当前日期（v-model） */
  modelValue?: Date
  /** 最小日期 */
  minDate?: Date
  /** 最大日期 */
  maxDate?: Date
  /** 是否显示周数 */
  showWeekNumber?: boolean
  /** 是否可选择 */
  selectable?: boolean
  /** 高亮日期 */
  highlightedDates?: Date[]
  /** 禁用日期 */
  disabledDates?: Date[]
  /** 每周的第一天（0-6，0为周日） */
  firstDayOfWeek?: number
}

const props = withDefaults(defineProps<CalendarProps>(), {
  modelValue: () => new Date(),
  minDate: undefined,
  maxDate: undefined,
  showWeekNumber: false,
  selectable: true,
  highlightedDates: () => [],
  disabledDates: () => [],
  firstDayOfWeek: 0
})

const emit = defineEmits<{
  'update:modelValue': [date: Date]
  select: [date: Date]
  monthChange: [date: Date]
}>()

const currentDate = ref(props.modelValue)

const weekDays = computed(() => {
  const days = ['日', '一', '二', '三', '四', '五', '六']
  const start = props.firstDayOfWeek
  return [...days.slice(start), ...days.slice(0, start)]
})

const calendarDays = computed(() => {
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()

  // 获取月份第一天和最后一天
  const firstDay = new Date(year, month, 1)
  // 计算日历网格的起始日期
  const startDay = new Date(firstDay)
  const diff = (firstDay.getDay() - props.firstDayOfWeek + 7) % 7
  startDay.setDate(startDay.getDate() - diff)

  // 生成42天（6周）
  const days: Array<{
    date: Date
    isCurrentMonth: boolean
    isToday: boolean
    isSelected: boolean
    isHighlighted: boolean
    isDisabled: boolean
  }> = []

  for (let i = 0; i < 42; i++) {
    const date = new Date(startDay)
    date.setDate(date.getDate() + i)

    const isCurrentMonth = date.getMonth() === month
    const isToday = dayjs().isSame(date, 'day')
    const isSelected = Boolean(props.modelValue && dayjs(props.modelValue).isSame(date, 'day'))
    const isHighlighted = props.highlightedDates.some(d => dayjs(d).isSame(date, 'day'))
    const isDisabled = Boolean(
      props.disabledDates.some(d => dayjs(d).isSame(date, 'day')) ||
      (props.minDate && dayjs(date).isBefore(props.minDate, 'day')) ||
      (props.maxDate && dayjs(date).isAfter(props.maxDate, 'day'))
    )

    days.push({
      date,
      isCurrentMonth,
      isToday,
      isSelected,
      isHighlighted,
      isDisabled
    })
  }

  return days
})

const weeks = computed(() => {
  const weekCount = Math.ceil(calendarDays.value.length / 7)
  return Array.from({ length: weekCount }, (_, i) => {
    const start = i * 7
    return calendarDays.value.slice(start, start + 7)
  })
})

const currentMonthText = computed(() => {
  return currentDate.value.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' })
})

const prevMonth = () => {
  const newDate = new Date(currentDate.value)
  newDate.setMonth(newDate.getMonth() - 1)
  currentDate.value = newDate
  emit('monthChange', newDate)
}

const nextMonth = () => {
  const newDate = new Date(currentDate.value)
  newDate.setMonth(newDate.getMonth() + 1)
  currentDate.value = newDate
  emit('monthChange', newDate)
}

const handleDateClick = (day: typeof calendarDays.value[0]) => {
  if (props.selectable && !day.isDisabled) {
    emit('update:modelValue', day.date)
    emit('select', day.date)
  }
}

const getWeekNumber = (days: typeof calendarDays.value): number => {
  const firstDay = days[0]?.date
  if (!firstDay) return 0
  const startOfYear = new Date(firstDay.getFullYear(), 0, 1)
  const diffDays = Math.floor((firstDay.getTime() - startOfYear.getTime()) / 86400000)
  return Math.floor((diffDays + startOfYear.getDay()) / 7) + 1
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    currentDate.value = newVal
  }
})
</script>

<template>
  <div class="calendar">
    <!-- 头部：月份切换 -->
    <div class="calendar-header">
      <button class="calendar-nav" @click="prevMonth" :disabled="!selectable">
        ‹
      </button>
      <div class="calendar-month">{{ currentMonthText }}</div>
      <button class="calendar-nav" @click="nextMonth" :disabled="!selectable">
        ›
      </button>
    </div>

    <!-- 星期标题 -->
    <div class="calendar-weekdays">
      <div v-if="showWeekNumber" class="calendar-weekday">周</div>
      <div v-for="day in weekDays" :key="day" class="calendar-weekday">
        {{ day }}
      </div>
    </div>

    <!-- 日历网格 -->
    <div class="calendar-weeks">
      <div v-for="(week, index) in weeks" :key="index" class="calendar-week">
        <div v-if="showWeekNumber" class="calendar-week-number">
          {{ getWeekNumber(week) }}
        </div>
        <div
          v-for="day in week"
          :key="day.date.toISOString()"
          :class="[
            'calendar-day',
            {
              'calendar-day-current': day.isCurrentMonth,
              'calendar-day-today': day.isToday,
              'calendar-day-selected': day.isSelected,
              'calendar-day-highlighted': day.isHighlighted,
              'calendar-day-disabled': day.isDisabled
            }
          ]"
          @click="handleDateClick(day)"
        >
          {{ day.date.getDate() }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   CALENDAR COMPONENT - 日历组件样式
   ═══════════════════════════════════════════════════════════════ */

.calendar {
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

/* ───────────────────────────────────────────────────────────────
   HEADER - 头部
   ─────────────────────────────────────────────────────────────── */

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.calendar-nav {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: 18px;
  color: var(--text);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--duration-base) var(--easing-default);
}

.calendar-nav:hover:not(:disabled) {
  background: var(--s2);
}

.calendar-nav:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.calendar-month {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text);
}

/* ───────────────────────────────────────────────────────────────
   WEEKDAYS - 星期标题
   ─────────────────────────────────────────────────────────────── */

.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: var(--space-1);
  margin-bottom: var(--space-2);
}

.calendar-weekday {
  text-align: center;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--muted);
  padding: var(--space-2);
}

/* ───────────────────────────────────────────────────────────────
   WEEKS - 周和日期
   ─────────────────────────────────────────────────────────────── */

.calendar-weeks {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.calendar-week {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: var(--space-1);
}

.calendar-week-number {
  text-align: center;
  font-size: var(--font-size-xs);
  color: var(--muted);
  padding: var(--space-2);
  font-weight: var(--font-weight-medium);
}

.calendar-day {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  color: var(--muted);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--duration-base) var(--easing-default);
  user-select: none;
}

.calendar-day-current {
  color: var(--text);
}

.calendar-day-today {
  background: var(--s2);
  color: var(--blue);
  font-weight: var(--font-weight-semibold);
}

.calendar-day-selected {
  background: var(--blue);
  color: white;
  font-weight: var(--font-weight-semibold);
}

.calendar-day-highlighted {
  background: rgba(91, 141, 239, 0.2);
  color: var(--blue);
}

.calendar-day-disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.calendar-day:not(.calendar-day-disabled):hover {
  background: var(--s2);
}
</style>
