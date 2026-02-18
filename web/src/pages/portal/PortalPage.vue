<template>
  <div class="portal">
    <section class="hero-shell" aria-label="咔咔记账首页主视觉">
      <div class="hero-content">
        <div class="hero-copy">
          <p class="hero-kicker">GLOBAL ASSET DESK</p>
          <h1>咔咔记账</h1>
          <h2>一站式管理全球市场资产</h2>
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

const apkUrl = ref('')

onMounted(async () => {
  try {
    const payload = await api.get<{ portal_title?: string; apk_download_url?: string }>('/api/web/config', false)
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
  min-height: 100vh;
  width: 100%;
}

.hero-shell {
  position: relative;
  overflow: hidden;
  min-height: 100vh;
  padding: 52px clamp(20px, 5vw, 64px) 42px;
  border-radius: 0;
  border: 0;
  background:
    radial-gradient(800px 380px at 95% 20%, rgba(184, 143, 255, 0.35), rgba(184, 143, 255, 0)),
    radial-gradient(640px 280px at 8% 92%, rgba(255, 176, 130, 0.28), rgba(255, 176, 130, 0)),
    linear-gradient(112deg, #f8f6fb 0%, #f6f4ff 45%, #f5eeff 100%);
}

.hero-content {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 1.08fr 0.92fr;
  gap: 22px;
  margin-top: 8px;
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

.hero-actions {
  margin-top: 34px;
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
    min-height: 100vh;
    padding: 34px 20px 24px;
  }

  .hero-content {
    grid-template-columns: 1fr 0.9fr;
    gap: 14px;
    margin-top: 6px;
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
    min-height: 100vh;
  }

  .hero-shell {
    min-height: 100vh;
    padding: 22px 16px 20px;
  }

  .hero-content {
    grid-template-columns: 1fr;
    margin-top: 0;
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
