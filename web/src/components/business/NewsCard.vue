<script setup lang="ts">
/**
 * NewsCard - 新闻卡片组件
 * 用于展示新闻、快讯等
 */

import { computed } from 'vue'

export interface NewsCardProps {
  /** 标题 */
  title: string
  /** 摘要 */
  summary?: string
  /** 来源 */
  source?: string
  /** 时间 */
  time?: string | Date
  /** 封面图 */
  image?: string
  /** 链接 */
  url?: string
  /** 是否显示图片 */
  showImage?: boolean
  /** 卡片尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 布局方式 */
  layout?: 'horizontal' | 'vertical'
}

const props = withDefaults(defineProps<NewsCardProps>(), {
  showImage: true,
  size: 'md',
  layout: 'horizontal'
})

const emit = defineEmits<{
  click: []
}>()

const cardClass = computed(() => {
  return [
    'news-card',
    `news-card-${props.size}`,
    `news-card-${props.layout}`,
    {
      'news-card-clickable': props.url
    }
  ]
})

const formattedTime = computed(() => {
  if (!props.time) return ''

  if (typeof props.time === 'string') {
    return props.time
  }

  const now = new Date()
  const diff = now.getTime() - props.time.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`

  return props.time.toLocaleDateString('zh-CN')
})

const handleClick = () => {
  if (props.url) {
    emit('click')
  }
}
</script>

<template>
  <article :class="cardClass" @click="handleClick">
    <div v-if="showImage && image" class="news-card-image">
      <img :src="image" :alt="title" loading="lazy" />
    </div>

    <div class="news-card-content">
      <h3 class="news-card-title">{{ title }}</h3>

      <p v-if="summary" class="news-card-summary">
        {{ summary }}
      </p>

      <div class="news-card-meta">
        <span v-if="source" class="news-card-source">{{ source }}</span>
        <span v-if="time" class="news-card-time">{{ formattedTime }}</span>
      </div>
    </div>
  </article>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   NEWS CARD - 新闻卡片样式
   ═══════════════════════════════════════════════════════════════ */

.news-card {
  display: flex;
  gap: var(--space-3);
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all var(--duration-base) var(--easing-default);
}

.news-card-clickable {
  cursor: pointer;
  user-select: none;
}

.news-card-clickable:hover {
  border-color: var(--border-hover);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

/* ───────────────────────────────────────────────────────────────
   IMAGE - 图片区域
   ─────────────────────────────────────────────────────────────── */

.news-card-image {
  flex-shrink: 0;
  width: 120px;
  height: 80px;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.news-card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--duration-base) var(--easing-default);
}

.news-card-clickable:hover .news-card-image img {
  transform: scale(1.05);
}

/* ───────────────────────────────────────────────────────────────
   CONTENT - 内容区域
   ─────────────────────────────────────────────────────────────── */

.news-card-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.news-card-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.news-card-summary {
  font-size: var(--font-size-sm);
  color: var(--sub);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.news-card-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--muted);
  margin-top: auto;
}

.news-card-source::after {
  content: '·';
  margin-left: var(--space-3);
}

/* ───────────────────────────────────────────────────────────────
   LAYOUT VARIANTS - 布局变体
   ─────────────────────────────────────────────────────────────── */

.news-card-vertical {
  flex-direction: column;
}

.news-card-vertical .news-card-image {
  width: 100%;
  height: 160px;
}

/* ───────────────────────────────────────────────────────────────
   SIZE VARIANTS - 尺寸变体
   ─────────────────────────────────────────────────────────────── */

.news-card-sm .news-card-title {
  font-size: var(--font-size-sm);
}

.news-card-sm .news-card-image {
  width: 80px;
  height: 60px;
}

.news-card-lg .news-card-title {
  font-size: var(--font-size-md);
}

.news-card-lg .news-card-image {
  width: 180px;
  height: 120px;
}
</style>
