<template>
  <div class="landing-page">
    <TickerBar />
    <NavBar />
    <HeroSection :apk-url="apkUrl" :ios-qr-text="iosQrText" :ios-qr-image-url="iosQrImageUrl" />
    <FeaturesSection />
    <MarketsSection />
    <DownloadSection :apk-url="apkUrl" :ios-qr-text="iosQrText" :ios-qr-image-url="iosQrImageUrl" />
    <Footer />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { api } from '../shared/http'
import TickerBar from '../components/landing/TickerBar.vue'
import NavBar from '../components/landing/NavBar.vue'
import HeroSection from '../components/landing/HeroSection.vue'
import FeaturesSection from '../components/landing/FeaturesSection.vue'
import MarketsSection from '../components/landing/MarketsSection.vue'
import DownloadSection from '../components/landing/DownloadSection.vue'
import Footer from '../components/landing/Footer.vue'

const apkUrl = ref('/download/apk')
const iosQrText = ref('扫码下载苹果版')
const iosQrImageUrl = ref('')

function applyLandingScrollMode() {
  document.documentElement.classList.add('landing-scroll')
  document.body.classList.add('landing-scroll')
}

function cleanupLandingScrollMode() {
  document.documentElement.classList.remove('landing-scroll')
  document.body.classList.remove('landing-scroll')
}

onMounted(async () => {
  applyLandingScrollMode()
  try {
    const payload = await api.get<{ apk_download_url?: string, ios_qr_text?: string, ios_qr_image_url?: string }>('/api/web/config', false)
    if (payload.apk_download_url && payload.apk_download_url.trim() !== '') {
      apkUrl.value = payload.apk_download_url
    }
    if (payload.ios_qr_text) iosQrText.value = payload.ios_qr_text
    if (payload.ios_qr_image_url) iosQrImageUrl.value = payload.ios_qr_image_url
  } catch {
    // keep fallback config
  }
})

onUnmounted(() => {
  cleanupLandingScrollMode()
})
</script>

<style>
/* Global styles specifically for the Landing Page that mimics the original HTML */
.landing-scroll {
  overflow-y: auto !important;
  overflow-x: hidden !important;
  height: auto !important;
}

.landing-page {
  --bg: #0a0b0e;
  --surface: #11131a;
  --surface-2: #181b24;
  --border: rgba(255,255,255,0.07);
  --border-bright: rgba(255,255,255,0.13);
  --gold: #d4af64;
  --text: #e4e5ea;
  --text-muted: #545c72;
  --text-sub: #828a9e;
  --green: #3ecf82;
  --red: #f05a55;
  --blue: #5b8def;
  --r: 16px;

  background: var(--bg);
  color: var(--text);
  font-family: 'DM Sans', sans-serif;
  overflow-x: hidden;
  min-height: 100vh;
}

.landing-page * {
  box-sizing: border-box;
}
</style>
