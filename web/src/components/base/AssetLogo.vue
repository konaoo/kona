<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  name?: string
  code?: string
  logoUrl?: string | null
  market?: string
  assetType?: string
}>()

const imageError = ref(false)
const retryCount = ref(0)

// 第一级：判断是否为基金。基金统一显示专用图标，不走 Logo 逻辑。
const isFund = computed(() => props.assetType === 'fund' || props.market === 'fund')

// 提取域名用于备选源
const domain = computed(() => {
  if (!props.logoUrl) return ''
  try {
    const url = new URL(props.logoUrl)
    if (url.hostname === 'logo.clearbit.com') {
      return url.pathname.replace('/', '')
    }
    return url.hostname
  } catch (e) {
    return props.logoUrl.replace('https://logo.clearbit.com/', '')
  }
})

// 定义备选来源列表
const sources = computed(() => {
  if (isFund.value || !domain.value) return []
  
  const list = []
  if (props.logoUrl) list.push(props.logoUrl) // 1. 原始源 (通常是 Clearbit)
  
  // 2. Google Favicon (全球通用，但在国内不稳定)
  list.push(`https://www.google.com/s2/favicons?domain=${domain.value}&sz=128`)
  
  // 3. Icon Horse (备选)
  list.push(`https://icon.horse/icon/${domain.value}`)
  
  // 4. DuckDuckGo (通用备选)
  list.push(`https://icons.duckduckgo.com/ip3/${domain.value}.ico`)

  // 5. iowen.cn (国内环境高可用备选)
  list.push(`https://api.iowen.cn/favicon/${domain.value}.png`)
  
  return list
})

// 当前尝试的 URL
const currentUrl = computed(() => {
  if (retryCount.value < sources.value.length) {
    return sources.value[retryCount.value]
  }
  return null
})

// 第二级：提取占位字符（股票名称首字母或代码前两位）
const placeholder = computed(() => {
  if (!props.name) return props.code?.substring(0, 2).toUpperCase() || '?'
  const firstChar = props.name.trim().charAt(0)
  return firstChar.toUpperCase()
})

// 根据市场类型定义不同的占位图背景色
const bgClass = computed(() => {
  // 如果是基金，始终显示基金背景色
  if (isFund.value) return 'bg-fund'
  
  // 关键修复：只有在图片加载失败（imageError = true），或没有图片尝试加载时，才显示市场背景色进行占位
  if (imageError.value || !currentUrl.value) {
    switch (props.market?.toLowerCase()) {
      case 'us': return 'bg-us'
      case 'hk': return 'bg-hk'
      case 'a': return 'bg-a'
      default: return 'bg-default'
    }
  }
  
  // 图片加载成功时，使用纯白色或透明背景，不再使用蓝色背景干扰视觉
  return 'bg-white'
})

function handleImageError() {
  if (retryCount.value < sources.value.length - 1) {
    // 还没试完所有源，继续下一个
    retryCount.value++
  } else {
    // 全部失败，进入最终兜底
    imageError.value = true
  }
}
</script>

<template>
  <div class="asset-logo" :class="[bgClass]">
    <template v-if="isFund">
      <svg viewBox="0 0 24 24" fill="none" class="fund-icon">
        <path d="M12 2L4 7v10l8 5 8-5V7l-8-5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M12 22V12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M12 12l8-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M12 12L4 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </template>

    <template v-else>
      <img 
        v-if="currentUrl && !imageError" 
        :key="currentUrl"
        :src="currentUrl" 
        :alt="name"
        class="real-logo"
        @error="handleImageError"
      />
      <span v-else class="placeholder-text">{{ placeholder }}</span>
    </template>
  </div>
</template>

<style scoped>
.asset-logo {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  font-weight: 700;
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.real-logo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.placeholder-text {
  font-size: 1.2em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.fund-icon {
  width: 60%;
  height: 60%;
  opacity: 0.9;
}

/* 市场背景色 */
.bg-fund { background: linear-gradient(135deg, #6366f1, #4f46e5); border-color: rgba(99, 102, 241, 0.3); }
.bg-us { background: linear-gradient(135deg, #3b82f6, #2563eb); border-color: rgba(59, 130, 246, 0.3); }
.bg-hk { background: linear-gradient(135deg, #f59e0b, #d97706); border-color: rgba(245, 158, 11, 0.3); }
.bg-a { background: linear-gradient(135deg, #ef4444, #dc2626); border-color: rgba(239, 68, 68, 0.3); }
.bg-default { background: linear-gradient(135deg, #6b7280, #4b5563); }
.bg-white { background: #fff; border-color: rgba(0,0,0,0.05); }

.asset-logo:hover {
  transform: scale(1.05);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
</style>
