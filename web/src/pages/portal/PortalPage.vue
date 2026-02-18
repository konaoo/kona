<template>
  <div class="portal page-wrap">
    <section class="hero panel">
      <div class="hero-main">
        <p class="eyebrow">KONA PORTAL</p>
        <h1>{{ portalTitle }}</h1>
        <p class="desc">
          全市场资产管理与分析工作台。Web 端与 App 端统一业务口径，提供实时价格、收益分析、休市控制与管理后台能力。
        </p>
        <div class="actions">
          <RouterLink class="btn primary" to="/app/login">网页端登录</RouterLink>
          <a
            class="btn"
            :class="{ disabled: !apkUrl }"
            :href="apkUrl || undefined"
            :target="apkUrl ? '_blank' : undefined"
            :rel="apkUrl ? 'noreferrer' : undefined"
            :aria-disabled="!apkUrl"
            @click="onApkClick"
          >{{ apkUrl ? '下载 APK' : 'APK 暂未提供' }}</a>
        </div>
      </div>
      <div class="hero-grid">
        <div class="metric panel">
          <div class="label">资产覆盖</div>
          <div class="value">A/HK/US/Fund</div>
        </div>
        <div class="metric panel">
          <div class="label">核心能力</div>
          <div class="value">实时行情 + 收益分析</div>
        </div>
        <div class="metric panel">
          <div class="label">一致性</div>
          <div class="value">Web / App 同口径</div>
        </div>
      </div>
    </section>

    <section class="features grid" style="grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: 16px">
      <article class="panel card" v-for="feature in features" :key="feature.title">
        <h3>{{ feature.title }}</h3>
        <p>{{ feature.body }}</p>
      </article>
    </section>

    <section class="faq panel" style="margin-top: 16px; padding: 20px">
      <h3>FAQ</h3>
      <div class="faq-item" v-for="item in faq" :key="item.q">
        <h4>{{ item.q }}</h4>
        <p>{{ item.a }}</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../../shared/http'

const portalTitle = ref('Kona Portfolio')
const apkUrl = ref('')

const features = [
  { title: '统一市场休市逻辑', body: 'A股、港股、美股、基金按交易日历统一判定，当日收益按开市状态计算。' },
  { title: '投资与分析双视角', body: '投资页查看实时持仓与盈亏，分析页按日/月/年维度查看收益结构与排行。' },
  { title: '管理后台闭环', body: '用户、邀请码、策略、快照与审计统一在后台管理，支持风险操作预览。' },
]

const faq = [
  { q: '网页端和 App 端口径一致吗？', a: '一致。都走同一套后端 API，并使用同样的休市与收益口径。' },
  { q: '是否支持邀请码注册？', a: '支持。登录页可直接输入邀请码完成注册。' },
  { q: '管理后台入口在哪？', a: '访问 /admin/login 后使用管理员账号登录。' },
]

onMounted(async () => {
  try {
    const payload = await api.get<{ portal_title?: string; apk_download_url?: string }>('/api/web/config', false)
    if (payload.portal_title) portalTitle.value = payload.portal_title
    if (payload.apk_download_url) apkUrl.value = payload.apk_download_url
  } catch {
    // keep fallback config
  }
})

function onApkClick(event: Event) {
  if (!apkUrl.value) {
    event.preventDefault()
  }
}
</script>

<style scoped>
.portal {
  padding-top: 24px;
  padding-bottom: 30px;
}

.hero {
  padding: 28px;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 18px;
}

.eyebrow {
  color: var(--brand-2);
  letter-spacing: 0.8px;
  font-size: 12px;
  margin: 0;
}

h1 {
  margin: 8px 0;
  font-size: clamp(34px, 5vw, 52px);
}

.desc {
  color: var(--muted);
  max-width: 640px;
  line-height: 1.65;
}

.actions {
  margin-top: 18px;
  display: flex;
  gap: 10px;
}

.actions .btn.disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.hero-grid {
  display: grid;
  gap: 12px;
}

.metric {
  padding: 14px;
}

.metric .label {
  font-size: 12px;
  color: var(--muted);
}

.metric .value {
  margin-top: 6px;
  font-size: 20px;
  font-weight: 700;
}

.card {
  padding: 18px;
}

.card h3 {
  margin: 0 0 8px;
}

.card p,
.faq p {
  margin: 0;
  color: var(--muted);
  line-height: 1.65;
}

.faq-item {
  padding: 10px 0;
  border-bottom: 1px solid rgba(98, 126, 172, 0.2);
}

.faq-item:last-child {
  border-bottom: 0;
}

@media (max-width: 900px) {
  .hero {
    grid-template-columns: 1fr;
    padding: 18px;
  }

  .features {
    grid-template-columns: 1fr !important;
  }
}
</style>
