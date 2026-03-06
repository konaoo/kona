<script setup lang="ts">
/**
 * Progress - 进度条组件
 * 用于显示进度、完成度等
 */

import { computed } from 'vue'

export interface ProgressProps {
  /** 进度百分比 (0-100) */
  percent: number
  /** 进度条类型 */
  type?: 'line' | 'circle'
  /** 进度条尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 是否显示百分比文字 */
  showText?: boolean
  /** 进度条颜色类型 */
  colorType?: 'primary' | 'success' | 'warning' | 'danger'
  /** 是否启用动画 */
  animated?: boolean
  /** 是否是条纹样式 */
  striped?: boolean
  /** 线条粗细（仅line类型） */
  strokeWidth?: number
}

const props = withDefaults(defineProps<ProgressProps>(), {
  type: 'line',
  size: 'md',
  showText: true,
  colorType: 'primary',
  animated: false,
  striped: false,
  strokeWidth: 8
})

const normalizedPercent = computed(() => {
  return Math.min(100, Math.max(0, props.percent))
})

const progressClass = computed(() => {
  return [
    'progress',
    `progress-${props.type}`,
    `progress-${props.size}`,
    `progress-${props.colorType}`,
    {
      'progress-animated': props.animated,
      'progress-striped': props.striped
    }
  ]
})

const barStyle = computed(() => {
  const baseStyle = {
    width: `${normalizedPercent.value}%`
  }

  if (props.type === 'line' && props.strokeWidth) {
    return {
      ...baseStyle,
      height: `${props.strokeWidth}px`
    }
  }

  return baseStyle
})

const circleRadius = computed(() => {
  const sizeMap = {
    sm: 32,
    md: 50,
    lg: 80
  }
  return sizeMap[props.size]
})

const circleStrokeWidth = computed(() => {
  return props.size === 'sm' ? 4 : props.size === 'md' ? 6 : 8
})

const circleCircumference = computed(() => {
  return 2 * Math.PI * (circleRadius.value - circleStrokeWidth.value / 2)
})

const circleDashOffset = computed(() => {
  return circleCircumference.value * (1 - normalizedPercent.value / 100)
})

const circleStyle = computed(() => ({
  strokeWidth: `${circleStrokeWidth.value}px`,
  strokeDasharray: `${circleCircumference.value} ${circleCircumference.value}`,
  strokeDashoffset: `${circleDashOffset.value}`
}))

const circleSize = computed(() => {
  const sizeMap = {
    sm: 40,
    md: 60,
    lg: 100
  }
  return sizeMap[props.size]
})
</script>

<template>
  <div :class="progressClass">
    <!-- 线性进度条 -->
    <template v-if="type === 'line'">
      <div class="progress-track">
        <div class="progress-bar" :style="barStyle">
          <span v-if="showText && size !== 'sm'" class="progress-text">
            {{ normalizedPercent }}%
          </span>
        </div>
      </div>
      <div v-if="showText && size === 'sm'" class="progress-text-external">
        {{ normalizedPercent }}%
      </div>
    </template>

    <!-- 圆形进度条 -->
    <template v-else-if="type === 'circle'">
      <div class="progress-circle" :style="{ width: `${circleSize}px`, height: `${circleSize}px` }">
        <svg :width="circleSize" :height="circleSize" viewBox="0 0 100 100">
          <circle
            class="progress-circle-track"
            :r="circleRadius"
            cx="50"
            cy="50"
            fill="none"
            :stroke-width="circleStrokeWidth"
          />
          <circle
            class="progress-circle-bar"
            :r="circleRadius"
            cx="50"
            cy="50"
            fill="none"
            :style="circleStyle"
            :stroke-width="circleStrokeWidth"
          />
        </svg>
        <div v-if="showText" class="progress-circle-text">
          {{ normalizedPercent }}%
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   PROGRESS COMPONENT - 进度条组件样式
   ═══════════════════════════════════════════════════════════════ */

.progress {
  display: inline-block;
  width: 100%;
}

/* ───────────────────────────────────────────────────────────────
   LINE PROGRESS - 线性进度条
   ─────────────────────────────────────────────────────────────── */

.progress-track {
  position: relative;
  width: 100%;
  background: var(--s1);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.progress-bar {
  position: relative;
  height: 100%;
  background: var(--blue);
  border-radius: var(--radius-md);
  transition: width var(--duration-slow) var(--easing-default);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: var(--space-2);
}

.progress-text {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: white;
  white-space: nowrap;
}

.progress-text-external {
  margin-top: var(--space-1);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text);
  text-align: center;
}

/* ───────────────────────────────────────────────────────────────
   CIRCLE PROGRESS - 圆形进度条
   ─────────────────────────────────────────────────────────────── */

.progress-circle {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.progress-circle-track {
  stroke: var(--s1);
}

.progress-circle-bar {
  stroke: var(--blue);
  transition: stroke-dashoffset var(--duration-slow) var(--easing-default);
  transform: rotate(-90deg);
  transform-origin: 50% 50%;
}

.progress-circle-text {
  position: absolute;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text);
}

/* ───────────────────────────────────────────────────────────────
   PROGRESS SIZES - 尺寸变体
   ─────────────────────────────────────────────────────────────── */

.progress-sm .progress-text {
  font-size: 9px;
}

.progress-md .progress-text {
  font-size: var(--font-size-xs);
}

.progress-lg .progress-text {
  font-size: var(--font-size-sm);
  padding-right: var(--space-3);
}

/* ───────────────────────────────────────────────────────────────
   PROGRESS COLOR TYPES - 颜色类型
   ─────────────────────────────────────────────────────────────── */

.progress-primary .progress-bar,
.progress-primary .progress-circle-bar {
  background: var(--blue);
  stroke: var(--blue);
}

.progress-success .progress-bar,
.progress-success .progress-circle-bar {
  background: var(--green);
  stroke: var(--green);
}

.progress-warning .progress-bar,
.progress-warning .progress-circle-bar {
  background: var(--gold);
  stroke: var(--gold);
}

.progress-danger .progress-bar,
.progress-danger .progress-circle-bar {
  background: var(--red);
  stroke: var(--red);
}

/* ───────────────────────────────────────────────────────────────
   PROGRESS EFFECTS - 特效
   ─────────────────────────────────────────────────────────────── */

.progress-striped .progress-bar {
  background-image: linear-gradient(
    45deg,
    rgba(255, 255, 255, 0.15) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255, 255, 255, 0.15) 50%,
    rgba(255, 255, 255, 0.15) 75%,
    transparent 75%,
    transparent
  );
  background-size: 1rem 1rem;
}

.progress-animated .progress-bar {
  animation: progress-stripe-animate 1s linear infinite;
}

@keyframes progress-stripe-animate {
  from {
    background-position: 1rem 0;
  }
  to {
    background-position: 0 0;
  }
}
</style>
