<template>
  <div class="portal page-wrap">
    <section class="hero-shell" aria-label="咔咔记账首页主视觉">
      <header class="hero-top">
        <div class="brand">
          <span class="brand-mark" aria-hidden="true"></span>
          <span class="brand-name">{{ portalTitle }}</span>
        </div>
        <nav class="hero-nav" aria-label="首页导航">
          <RouterLink class="nav-link" to="/app/login">网页端登录</RouterLink>
          <a
            class="nav-link"
            :class="{ disabled: !apkUrl }"
            :href="apkUrl || undefined"
            :target="apkUrl ? '_blank' : undefined"
            :rel="apkUrl ? 'noreferrer' : undefined"
            :aria-disabled="!apkUrl"
            :tabindex="apkUrl ? 0 : -1"
            @click="onApkClick"
            @keydown.enter="onApkClick"
            @keydown.space.prevent="onApkClick"
          >{{ apkUrl ? '下载 APK' : 'APK 暂未提供' }}</a>
          <RouterLink class="nav-link" to="/admin/login">管理后台</RouterLink>
        </nav>
      </header>

      <div class="hero-content">
        <div class="hero-copy">
          <p class="hero-kicker">GLOBAL ASSET DESK</p>
          <h1>咔咔记账</h1>
          <h2>一站式管理全球市场资产</h2>
          <p class="hero-desc">
            覆盖全球主流市场资产，聚焦实时可读性与操作效率，帮助你在一个工作台内完成记录、跟踪与决策。
          </p>
          <div class="hero-actions">
            <RouterLink class="btn primary" to="/app/login">进入网页端</RouterLink>
            <a
              class="btn"
              :class="{ disabled: !apkUrl }"
              :href="apkUrl || undefined"
              :target="apkUrl ? '_blank' : undefined"
              :rel="apkUrl ? 'noreferrer' : undefined"
              :aria-disabled="!apkUrl"
              :tabindex="apkUrl ? 0 : -1"
              @click="onApkClick"
              @keydown.enter="onApkClick"
              @keydown.space.prevent="onApkClick"
            >{{ apkUrl ? '下载 APK' : 'APK 暂未提供' }}</a>
          </div>
        </div>

        <div class="hero-visual" aria-hidden="true">
          <div class="orb orb-1"></div>
          <div class="orb orb-2"></div>
          <div class="orb orb-3"></div>
          <div class="star star-1">✦</div>
          <div class="star star-2">✦</div>
          <div class="star star-3">✦</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../../shared/http'

const portalTitle = ref('咔咔记账')
const apkUrl = ref('')

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
  min-height: calc(100vh - 48px);
  display: grid;
  align-items: center;
  padding-top: 12px;
  padding-bottom: 12px;
}

.hero-shell {
  position: relative;
  overflow: hidden;
  padding: 26px 30px 30px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.62);
  background:
    radial-gradient(800px 380px at 95% 20%, rgba(184, 143, 255, 0.35), rgba(184, 143, 255, 0)),
    radial-gradient(640px 280px at 8% 92%, rgba(255, 176, 130, 0.28), rgba(255, 176, 130, 0)),
    linear-gradient(112deg, #f8f6fb 0%, #f6f4ff 45%, #f5eeff 100%);
  box-shadow:
    0 40px 90px rgba(9, 20, 39, 0.38),
    inset 0 0 0 1px rgba(255, 255, 255, 0.5);
}

.hero-top {
  position: relative;
  z-index: 3;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.brand-mark {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #a1aec4;
  background:
    radial-gradient(circle at 45% 50%, #11356f 0 3px, transparent 4px),
    radial-gradient(circle at 50% 50%, rgba(17, 53, 111, 0.36) 0 10px, transparent 11px);
}

.brand-name {
  color: #0f2f63;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.hero-nav {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.nav-link {
  border: 1px solid rgba(28, 63, 117, 0.14);
  border-radius: 999px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.58);
  color: #1c3f75;
  font-size: 13px;
  transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease;
}

.nav-link:hover {
  transform: translateY(-1px);
  border-color: rgba(28, 63, 117, 0.3);
  box-shadow: 0 8px 20px rgba(36, 69, 127, 0.12);
}

.nav-link.disabled {
  opacity: 0.58;
  cursor: not-allowed;
  box-shadow: none;
}

.hero-content {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 1.08fr 0.92fr;
  gap: 22px;
  margin-top: 28px;
}

.hero-copy {
  max-width: 620px;
}

.hero-kicker {
  color: #5f6e89;
  letter-spacing: 1.3px;
  font-size: 11px;
  font-weight: 700;
  margin: 0;
}

h1 {
  margin: 10px 0 0;
  font-size: clamp(38px, 7vw, 72px);
  line-height: 1.02;
  color: #102d60;
  letter-spacing: -1.4px;
}

h2 {
  margin: 14px 0 0;
  font-size: clamp(22px, 3.6vw, 38px);
  line-height: 1.16;
  color: #173b78;
  font-weight: 600;
}

.hero-desc {
  margin: 18px 0 0;
  color: #4f627f;
  line-height: 1.72;
  font-size: 15px;
  max-width: 560px;
}

.hero-actions {
  margin-top: 26px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.hero-actions .btn {
  border-color: rgba(28, 63, 117, 0.18);
  color: #1c3f75;
  background: rgba(255, 255, 255, 0.72);
}

.hero-actions .btn.primary {
  border-color: transparent;
  color: #ffffff;
  background: linear-gradient(90deg, #183e79, #24559f);
}

.hero-actions .btn.disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.hero-visual {
  position: relative;
  min-height: 420px;
}

.orb {
  position: absolute;
  border-radius: 50%;
  border: 1.4px solid rgba(255, 255, 255, 0.75);
  pointer-events: none;
  animation: drift 12s ease-in-out infinite;
}

.orb-1 {
  width: 410px;
  height: 240px;
  top: 8px;
  right: -34px;
  transform: rotate(18deg);
}

.orb-2 {
  width: 360px;
  height: 210px;
  top: 124px;
  right: -18px;
  transform: rotate(-8deg);
  animation-delay: 1.1s;
}

.orb-3 {
  width: 280px;
  height: 180px;
  top: 246px;
  right: 8px;
  transform: rotate(10deg);
  border-style: dashed;
  animation-delay: 2.2s;
}

.star {
  position: absolute;
  color: rgba(165, 106, 210, 0.62);
  font-size: 20px;
  animation: twinkle 4.8s ease-in-out infinite;
}

.star-1 {
  top: 64px;
  right: 286px;
}

.star-2 {
  top: 188px;
  right: 62px;
  animation-delay: 1.6s;
}

.star-3 {
  top: 312px;
  right: 238px;
  animation-delay: 2.7s;
}

@keyframes drift {
  0%,
  100% {
    transform: translateY(0) rotate(10deg);
  }
  50% {
    transform: translateY(-8px) rotate(13deg);
  }
}

@keyframes twinkle {
  0%,
  100% {
    opacity: 0.3;
    transform: scale(0.95);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.04);
  }
}

@media (max-width: 1023px) {
  .hero-shell {
    padding: 20px 22px 24px;
  }

  .hero-content {
    grid-template-columns: 1fr 0.9fr;
    gap: 14px;
    margin-top: 20px;
  }

  .hero-visual {
    min-height: 360px;
  }

  .orb-1 {
    width: 310px;
    height: 190px;
    right: -18px;
  }

  .orb-2 {
    width: 278px;
    height: 170px;
    top: 112px;
    right: -8px;
  }

  .orb-3 {
    width: 224px;
    height: 142px;
    top: 218px;
    right: 10px;
  }
}

@media (max-width: 767px) {
  .portal {
    min-height: auto;
  }

  .hero-shell {
    padding: 16px 16px 20px;
  }

  .hero-top {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-nav {
    width: 100%;
    gap: 8px;
  }

  .nav-link {
    flex: 1;
    min-width: 104px;
    text-align: center;
    padding: 8px 10px;
    font-size: 12px;
  }

  .hero-content {
    grid-template-columns: 1fr;
    margin-top: 16px;
  }

  .hero-desc {
    font-size: 14px;
  }

  .hero-actions .btn {
    flex: 1;
    min-width: 132px;
    text-align: center;
  }

  .hero-visual {
    min-height: 220px;
  }

  .orb-1 {
    width: 220px;
    height: 140px;
    top: 14px;
    right: 8px;
  }

  .orb-2 {
    width: 188px;
    height: 118px;
    top: 88px;
    right: 18px;
  }

  .orb-3 {
    width: 156px;
    height: 94px;
    top: 144px;
    right: 24px;
  }

  .star-1 {
    top: 26px;
    right: 152px;
  }

  .star-2 {
    top: 118px;
    right: 46px;
  }

  .star-3 {
    top: 170px;
    right: 122px;
  }
}
</style>
