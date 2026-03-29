<template>
  <div class="portal">
    <section class="hero" aria-label="咔咔记账首页主视觉">
      <div class="bg" aria-hidden="true">
        <span class="blob b1"></span>
        <span class="blob b2"></span>
        <span class="blob b3"></span>
        <span class="grid"></span>
        <span class="sparkle s1"></span>
        <span class="sparkle s2"></span>
        <span class="sparkle s3"></span>
      </div>

      <div class="container">
        <header class="topbar">
          <div class="brand">
            <img class="brand-logo" alt="咔咔记账 logo" src="/assets/logo.png" />
            <div class="brand-text">
              <div class="brand-name">咔咔记账</div>
            </div>
          </div>
        </header>

        <main class="content">
          <section class="left">
            <h1 class="title">咔咔记账</h1>
            <p class="subtitle">一站式管理全球市场资产</p>

            <div class="actions">
              <RouterLink class="btn primary" to="/app/login">进入网页版</RouterLink>
              <a
                class="btn ghost"
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
          </section>

          <section class="right" aria-label="product visual">
            <div class="phone">
              <div class="phone-top">
                <span class="cam"></span>
              </div>

              <div class="screen">
                <div class="screen-glow" aria-hidden="true"></div>

                <div class="app-mark">
                  <img class="app-logo" alt="咔咔记账 logo" src="/assets/logo.png" />
                </div>

                <div class="float f1" aria-hidden="true"></div>
                <div class="float f2" aria-hidden="true"></div>
                <div class="float f3" aria-hidden="true"></div>
              </div>
            </div>
          </section>
        </main>
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
    const payload = await api.get<{ apk_download_url?: string }>('/api/web/config', false)
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

.hero {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(900px 600px at 18% 18%, rgba(255, 120, 80, 0.2), transparent 60%),
    radial-gradient(860px 640px at 82% 22%, rgba(255, 60, 160, 0.16), transparent 58%),
    radial-gradient(860px 620px at 70% 92%, rgba(99, 102, 241, 0.18), transparent 55%),
    linear-gradient(135deg, #fff7f1 0%, #f2f7ff 55%, #f6f2ff 100%);
}

.bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.blob {
  position: absolute;
  border-radius: 999px;
  filter: blur(44px);
  opacity: 0.9;
  animation: float 11s ease-in-out infinite;
  transform: translateZ(0);
}

.b1 {
  width: 520px;
  height: 520px;
  left: -170px;
  top: -170px;
  background: radial-gradient(circle at 30% 30%, rgba(255, 90, 120, 0.7), rgba(255, 180, 80, 0.22));
}

.b2 {
  width: 560px;
  height: 560px;
  right: -200px;
  top: 40px;
  background: radial-gradient(circle at 30% 30%, rgba(255, 70, 170, 0.55), rgba(99, 102, 241, 0.2));
  animation-delay: -3s;
}

.b3 {
  width: 560px;
  height: 560px;
  right: 90px;
  bottom: -260px;
  background: radial-gradient(circle at 30% 30%, rgba(99, 102, 241, 0.55), rgba(56, 189, 248, 0.2));
  animation-delay: -6s;
}

.grid {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(15, 23, 42, 0.07) 1px, transparent 1px);
  background-size: 18px 18px;
  mask-image: radial-gradient(circle at 30% 30%, #000 0%, transparent 55%);
  opacity: 0.55;
}

.sparkle {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 4px;
  background: linear-gradient(135deg, #ff4d8d, #6366f1);
  box-shadow: 0 12px 26px rgba(99, 102, 241, 0.22);
  opacity: 0.85;
}

.s1 {
  left: 14%;
  top: 22%;
  transform: rotate(18deg);
}

.s2 {
  left: 62%;
  top: 14%;
  transform: rotate(-10deg);
}

.s3 {
  left: 78%;
  top: 70%;
  transform: rotate(22deg);
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(18px);
  }
}

.container {
  position: relative;
  max-width: 1180px;
  margin: 0 auto;
  padding: 26px 28px 34px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 6px 18px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(240, 39, 158, 0.2);
  object-fit: cover;
}

.brand-text {
  line-height: 1.05;
}

.brand-name {
  font-weight: 900;
  letter-spacing: 0.2px;
  color: #0f172a;
}

.brand-sub {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(15, 23, 42, 0.5);
  font-weight: 800;
  letter-spacing: 1.6px;
}

.content {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 34px;
  align-items: center;
  padding: 26px 6px 0;
}

.eyebrow {
  margin: 0 0 16px;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 3px;
  color: rgba(15, 23, 42, 0.45);
}

.title {
  margin: 0;
  font-size: 72px;
  font-weight: 950;
  letter-spacing: -1.2px;
  line-height: 1.05;
  color: #0f172a;
}

.subtitle {
  margin: 18px 0 0;
  font-size: 22px;
  font-weight: 800;
  color: rgba(15, 23, 42, 0.68);
}

.actions {
  margin-top: 34px;
  display: flex;
  gap: 14px;
  align-items: center;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  font-weight: 900;
  letter-spacing: 0.2px;
  border-radius: 18px;
  padding: 14px 22px;
  transition: transform 220ms ease, box-shadow 220ms ease, background 220ms ease;
  user-select: none;
}

.btn.primary {
  color: #fff;
  background: linear-gradient(135deg, #ff4d8d, #6366f1);
  box-shadow: 0 18px 46px rgba(99, 102, 241, 0.26);
}

.btn.primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 26px 64px rgba(99, 102, 241, 0.32);
}

.btn.ghost {
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(15, 23, 42, 0.12);
  color: rgba(15, 23, 42, 0.78);
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.1);
}

.btn.ghost:hover {
  transform: translateY(-2px);
}

.btn.disabled {
  cursor: not-allowed;
  opacity: 0.7;
  box-shadow: none;
}

.right {
  display: flex;
  justify-content: flex-end;
}

.phone {
  width: 380px;
  border-radius: 36px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 26px 70px rgba(15, 23, 42, 0.18);
  padding: 14px;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  transform: translateZ(0);
  transition: transform 220ms ease, box-shadow 220ms ease;
}

.phone:hover {
  transform: translateY(-4px) rotate(-0.2deg);
  box-shadow: 0 34px 90px rgba(15, 23, 42, 0.2);
}

.phone-top {
  height: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 10px;
}

.cam {
  width: 74px;
  height: 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
}

.screen {
  position: relative;
  height: 460px;
  border-radius: 28px;
  overflow: hidden;
  background:
    radial-gradient(520px 320px at 30% 20%, rgba(255, 90, 150, 0.24), transparent 60%),
    radial-gradient(520px 320px at 70% 25%, rgba(99, 102, 241, 0.22), transparent 58%),
    radial-gradient(520px 320px at 50% 85%, rgba(56, 189, 248, 0.18), transparent 60%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.72));
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.screen-glow {
  position: absolute;
  inset: -40px;
  background:
    radial-gradient(380px 280px at 25% 25%, rgba(255, 77, 141, 0.28), transparent 60%),
    radial-gradient(380px 280px at 75% 30%, rgba(99, 102, 241, 0.26), transparent 60%);
  filter: blur(22px);
  opacity: 0.9;
}

.app-mark {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 2;
}

.app-logo {
  width: 120px;
  height: 120px;
  border-radius: 28px;
  box-shadow: 0 18px 46px rgba(240, 39, 158, 0.2);
  object-fit: cover;
}

.app-caption {
  font-size: 12px;
  font-weight: 950;
  letter-spacing: 3px;
  color: rgba(15, 23, 42, 0.48);
}

.float {
  position: absolute;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.12);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: 3;
  animation: bob 6.8s ease-in-out infinite;
}

.f1 {
  width: 56px;
  height: 56px;
  left: 22px;
  top: 88px;
}

.f2 {
  width: 72px;
  height: 72px;
  right: 28px;
  top: 140px;
  animation-delay: -2.3s;
}

.f3 {
  width: 64px;
  height: 64px;
  right: 60px;
  bottom: 86px;
  animation-delay: -3.8s;
}

@keyframes bob {
  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(14px);
  }
}

@media (max-width: 980px) {
  .content {
    grid-template-columns: 1fr;
    gap: 22px;
  }

  .right {
    justify-content: flex-start;
  }

  .title {
    font-size: 62px;
  }

  .phone {
    width: min(420px, 100%);
  }
}

@media (max-width: 520px) {
  .container {
    padding: 18px 16px 22px;
  }

  .title {
    font-size: 50px;
  }

  .actions {
    flex-direction: column;
    align-items: stretch;
  }

  .btn {
    width: 100%;
  }

  .screen {
    height: 420px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .blob,
  .float {
    animation: none;
  }

  .phone,
  .btn {
    transition: none;
  }
}
</style>
