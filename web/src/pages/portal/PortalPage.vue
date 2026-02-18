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
          <div class="glow glow-1"></div>
          <div class="glow glow-2"></div>
          <div class="trail trail-1"></div>
          <div class="trail trail-2"></div>
          <div class="trail trail-3"></div>
          <div class="spark spark-1">✦</div>
          <div class="spark spark-2">✶</div>
          <div class="spark spark-3">✦</div>
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
  background:
    radial-gradient(1200px 560px at 112% 22%, rgba(192, 156, 255, 0.14), rgba(192, 156, 255, 0)),
    radial-gradient(900px 540px at -8% 96%, rgba(255, 190, 154, 0.16), rgba(255, 190, 154, 0)),
    linear-gradient(180deg, #f5f4fa 0%, #f3f1fa 100%);
}

.hero-shell {
  position: relative;
  overflow: hidden;
  min-height: 100vh;
  padding: 62px clamp(24px, 6vw, 86px) 48px;
  border-radius: 0;
  border: 0;
  background:
    radial-gradient(840px 420px at 94% 18%, rgba(181, 136, 255, 0.34), rgba(181, 136, 255, 0)),
    radial-gradient(640px 300px at 8% 91%, rgba(255, 184, 130, 0.26), rgba(255, 184, 130, 0)),
    linear-gradient(115deg, #fbfafd 0%, #f8f6ff 44%, #f5eeff 100%);
}

.hero-content {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 1.03fr 0.97fr;
  gap: clamp(16px, 2.8vw, 30px);
  margin-top: 14px;
  align-items: center;
}

.hero-copy {
  max-width: 650px;
}

.hero-kicker {
  color: #6b7893;
  letter-spacing: 2.6px;
  font-size: 11px;
  font-weight: 650;
  margin: 0;
  font-family: 'SF Pro Text', 'Avenir Next', 'Segoe UI', sans-serif;
  text-transform: uppercase;
}

h1 {
  margin: 16px 0 0;
  font-size: clamp(58px, 7.2vw, 92px);
  line-height: 0.94;
  color: #112f64;
  letter-spacing: -2.2px;
  font-weight: 790;
  font-family:
    'SF Pro Display',
    'PingFang SC',
    'Hiragino Sans GB',
    'Noto Sans SC',
    'Microsoft YaHei',
    sans-serif;
  text-wrap: balance;
}

h2 {
  margin: 16px 0 0;
  font-size: clamp(24px, 2.8vw, 38px);
  line-height: 1.14;
  color: #193f7f;
  font-weight: 670;
  letter-spacing: -0.5px;
  text-wrap: balance;
  font-family:
    'SF Pro Display',
    'PingFang SC',
    'Hiragino Sans GB',
    'Noto Sans SC',
    'Microsoft YaHei',
    sans-serif;
}

.hero-actions {
  margin-top: clamp(30px, 4vw, 44px);
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.hero-actions .btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 164px;
  height: 54px;
  padding: 0 28px;
  border-radius: 999px;
  border: 1px solid rgba(22, 57, 109, 0.2);
  color: #1d3f76;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  font-family: 'SF Pro Text', 'Avenir Next', 'PingFang SC', sans-serif;
  font-size: 18px;
  font-weight: 660;
  line-height: 1;
  letter-spacing: 0.1px;
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease,
    border-color 180ms ease;
}

.hero-actions .btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(20, 51, 100, 0.15);
}

.hero-actions .btn.primary {
  border-color: rgba(17, 45, 93, 0.2);
  color: #ffffff;
  background:
    linear-gradient(140deg, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0) 42%),
    linear-gradient(93deg, #113267 0%, #1a4e96 52%, #1d5cac 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.24),
    0 8px 16px rgba(16, 47, 99, 0.14);
}

.hero-actions .btn.primary:hover {
  background:
    linear-gradient(140deg, rgba(255, 255, 255, 0.36), rgba(255, 255, 255, 0) 42%),
    linear-gradient(93deg, #0f2d5d 0%, #18498d 52%, #1b55a0 100%);
}

.hero-actions .btn:active {
  transform: translateY(0);
}

.hero-actions .btn:focus-visible {
  outline: 2px solid rgba(24, 79, 158, 0.42);
  outline-offset: 2px;
}

.hero-actions .btn.disabled {
  opacity: 1;
  color: #8d9ebc;
  border-color: rgba(141, 158, 188, 0.28);
  background: rgba(255, 255, 255, 0.52);
  font-weight: 620;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.hero-visual {
  position: relative;
  min-height: 500px;
}

.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(0.4px);
  pointer-events: none;
}

.glow-1 {
  width: 470px;
  height: 304px;
  top: -8px;
  right: -84px;
  background: radial-gradient(ellipse at center, rgba(240, 227, 255, 0.62), rgba(240, 227, 255, 0));
}

.glow-2 {
  width: 350px;
  height: 230px;
  top: 240px;
  right: -16px;
  background: radial-gradient(ellipse at center, rgba(246, 237, 255, 0.68), rgba(246, 237, 255, 0));
}

.trail {
  position: absolute;
  border-radius: 50%;
  border: 1.6px solid rgba(255, 255, 255, 0.8);
  pointer-events: none;
  animation: drift 13s ease-in-out infinite;
}

.trail-1 {
  width: 460px;
  height: 250px;
  top: 12px;
  right: -46px;
  transform: rotate(18deg);
}

.trail-2 {
  width: 404px;
  height: 236px;
  top: 150px;
  right: -24px;
  transform: rotate(-8deg);
  border-style: dashed;
  border-color: rgba(255, 255, 255, 0.66);
  animation-delay: 1s;
}

.trail-3 {
  width: 310px;
  height: 188px;
  top: 292px;
  right: 26px;
  transform: rotate(10deg);
  border-color: rgba(255, 255, 255, 0.54);
  animation-delay: 2.2s;
}

.spark {
  position: absolute;
  color: rgba(166, 108, 211, 0.56);
  font-size: 23px;
  animation: twinkle 4.9s ease-in-out infinite;
}

.spark-1 {
  top: 64px;
  right: 276px;
}

.spark-2 {
  top: 204px;
  right: 74px;
  color: rgba(250, 173, 126, 0.74);
  animation-delay: 1.6s;
}

.spark-3 {
  top: 344px;
  right: 244px;
  color: rgba(176, 133, 225, 0.6);
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
    padding: 40px 20px 28px;
  }

  .hero-content {
    grid-template-columns: 1fr 0.9fr;
    gap: 16px;
    margin-top: 8px;
  }

  .hero-visual {
    min-height: 420px;
  }

  h1 {
    font-size: clamp(50px, 7vw, 76px);
  }

  h2 {
    font-size: clamp(22px, 3.7vw, 32px);
  }

  .trail-1 {
    width: 352px;
    height: 208px;
    right: -18px;
  }

  .trail-2 {
    width: 290px;
    height: 182px;
    top: 112px;
    right: -8px;
  }

  .trail-3 {
    width: 246px;
    height: 154px;
    top: 218px;
    right: 10px;
  }

  .spark-1 {
    right: 202px;
  }

  .spark-2 {
    right: 46px;
  }

  .spark-3 {
    right: 168px;
  }
}

@media (max-width: 767px) {
  .portal {
    min-height: 100vh;
  }

  .hero-shell {
    min-height: 100vh;
    padding: 24px 16px 20px;
  }

  .hero-content {
    grid-template-columns: 1fr;
    margin-top: 0;
  }

  h1 {
    letter-spacing: -1.8px;
  }

  h2 {
    margin-top: 12px;
  }

  .hero-actions {
    margin-top: 26px;
    gap: 10px;
  }

  .hero-actions .btn {
    flex: 1;
    min-width: 132px;
    text-align: center;
    height: 50px;
    font-size: 16px;
    padding: 0 18px;
  }

  .hero-visual {
    min-height: 260px;
  }

  .glow-1 {
    width: 230px;
    height: 154px;
    top: 8px;
    right: 0;
  }

  .glow-2 {
    width: 190px;
    height: 128px;
    top: 136px;
    right: 20px;
  }

  .trail-1 {
    width: 220px;
    height: 140px;
    top: 14px;
    right: 8px;
  }

  .trail-2 {
    width: 188px;
    height: 118px;
    top: 88px;
    right: 18px;
  }

  .trail-3 {
    width: 156px;
    height: 94px;
    top: 144px;
    right: 24px;
  }

  .spark-1 {
    top: 26px;
    right: 152px;
    font-size: 18px;
  }

  .spark-2 {
    top: 118px;
    right: 46px;
    font-size: 17px;
  }

  .spark-3 {
    top: 170px;
    right: 122px;
    font-size: 17px;
  }
}
</style>
