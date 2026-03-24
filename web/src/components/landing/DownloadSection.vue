<template>
  <div class="download-wrap">
    <section class="download" id="download">
      <div class="section-header">
        <h2 class="section-title">随时随地掌握你的资产</h2>
        <p class="section-sub">网页端、安卓、iOS 三端数据实时同步，一个账号，全平台畅用。</p>
      </div>
      <div class="download-cards">
        <RouterLink to="/app/login" class="dl-card web">
          <div class="dl-icon web"><svg viewBox="0 0 24 24" fill="none" stroke="#739bf0" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></div>
          <div class="dl-platform">WEB</div>
          <div class="dl-title">网页版</div>
          <div class="dl-desc">无需安装，浏览器直接访问，完整功能体验。</div>
          <div class="dl-btn"><svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>立即进入</div>
        </RouterLink>
        <a :href="apkUrl" class="dl-card android" target="_blank">
          <div class="dl-icon android"><svg viewBox="0 0 24 24" fill="none" stroke="#3ecf82" stroke-width="2"><path d="M5 16a7 7 0 0 1 14 0v1H5v-1z"/><line x1="12" y1="3" x2="12" y2="5"/><line x1="5.5" y1="5.5" x2="7" y2="7"/><line x1="18.5" y1="5.5" x2="17" y2="7"/><circle cx="9" cy="13" r="1"/><circle cx="15" cy="13" r="1"/></svg></div>
          <div class="dl-platform">ANDROID</div>
          <div class="dl-title">安卓版</div>
          <div class="dl-desc">下载 APK 安装包，支持安卓 8.0 及以上版本。</div>
          <div class="dl-btn"><svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>安卓版</div>
        </a>
        <div class="hover-qr-wrap">
          <a href="#" class="dl-card ios">
            <div class="dl-icon ios"><svg viewBox="0 0 24 24" fill="none" stroke="#e4e5ea" stroke-width="2"><path d="M12 2a4 4 0 0 1 4 4v.5A4.5 4.5 0 0 0 20.5 11H21a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1h-.5A4.5 4.5 0 0 0 16 19.5V20a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-.5A4.5 4.5 0 0 0 3.5 15H3a1 1 0 0 1-1-1v-2a1 1 0 0 1 1-1h.5A4.5 4.5 0 0 0 8 6.5V6a4 4 0 0 1 4-4z"/></svg></div>
            <div class="dl-platform">iOS</div>
            <div class="dl-title">苹果版</div>
            <div class="dl-desc">App Store 即将上线，可先扫码加入内测群。</div>
            <div class="dl-btn"><svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="18" height="18" rx="2"/><rect x="7" y="7" width="3" height="3"/><rect x="14" y="7" width="3" height="3"/><rect x="7" y="14" width="3" height="3"/><rect x="14" y="14" width="3" height="3"/></svg>苹果版</div>
          </a>
          <div class="qr-tooltip" v-if="iosQrImageUrl || iosQrText">
            <img
              v-if="showQrImage"
              :src="iosQrImageUrl"
              alt="iOS QR Code"
              class="qr-img"
              @error="handleQrImageError"
            />
            <div v-else class="qr-fallback">
              <div class="qr-fallback-icon">iOS</div>
              <div class="qr-fallback-title">二维码暂时不可用</div>
              <div class="qr-fallback-desc">当前图片资源已失效，请稍后再试或联系管理员更新。</div>
            </div>
            <div v-if="iosQrText" class="qr-text">{{ iosQrText }}</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

const props = defineProps<{
  apkUrl?: string
  iosQrText?: string
  iosQrImageUrl?: string
}>()

const qrImageLoadFailed = ref(false)

const showQrImage = computed(() => Boolean(props.iosQrImageUrl) && !qrImageLoadFailed.value)

watch(
  () => props.iosQrImageUrl,
  () => {
    qrImageLoadFailed.value = false
  },
)

function handleQrImageError() {
  qrImageLoadFailed.value = true
}
</script>

<style scoped>
section.download {
  padding: 100px 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-eyebrow {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 500;
  letter-spacing: .14em; color: var(--blue); margin-bottom: 14px;
}

.section-title {
  font-size: clamp(26px, 3vw, 40px); font-weight: 800;
  letter-spacing: -.03em; line-height: 1.1; margin-bottom: 14px; color: var(--text);
}

.section-sub { font-size: 15px; color: var(--text-sub); line-height: 1.65; max-width: 480px; }

.section-header { text-align: center; margin-bottom: 60px; }
.section-header .section-sub { margin: 0 auto; }

.download-cards { display: flex; align-items: center; justify-content: center; gap: 14px; margin-top: 44px; flex-wrap: wrap; }

.dl-card {
  background: rgba(17,19,26,0.9); border: 1px solid var(--border); border-radius: 18px;
  padding: 22px 20px; min-width: 250px; flex: 1; text-align: left;
  transition: border-color .22s, transform .22s, box-shadow .22s;
  text-decoration: none; display: flex; flex-direction: column; cursor: pointer;
  height: 100%;
}

.dl-card:hover { transform: translateY(-4px); box-shadow: 0 18px 38px rgba(0,0,0,0.28); }
.dl-card.web:hover { border-color: rgba(91,141,239,0.3); }
.dl-card.android:hover { border-color: rgba(62,207,130,0.3); }
.dl-card.ios:hover { border-color: rgba(255,255,255,0.18); }

.dl-icon {
  width: 40px; height: 40px; border-radius: 11px;
  display: flex; align-items: center; justify-content: center; margin-bottom: 13px;
}

.dl-icon.web { background: rgba(91,141,239,0.13); border: 1px solid rgba(91,141,239,0.22); }
.dl-icon.android { background: rgba(62,207,130,0.11); border: 1px solid rgba(62,207,130,0.22); }
.dl-icon.ios { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.13); }
.dl-icon svg { width: 20px; height: 20px; }

.dl-platform { font-size: 9px; font-weight: 600; color: var(--text-muted); letter-spacing: .06em; margin-bottom: 3px; }
.dl-title { font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 5px; }
.dl-desc { font-size: 11px; color: var(--text-sub); line-height: 1.4; white-space: nowrap; }

.dl-btn {
  display: inline-flex; align-items: center; gap: 4px;
  margin-top: 13px; height: 28px; padding: 0 11px; border-radius: 999px;
  font-size: 11px; font-weight: 700;
}

.dl-card.web .dl-btn { background: rgba(91,141,239,0.16); color: #739bf0; border: 1px solid rgba(91,141,239,0.26); }
.dl-card.android .dl-btn { background: rgba(62,207,130,0.13); color: #3ecf82; border: 1px solid rgba(62,207,130,0.22); }
.dl-card.ios .dl-btn { background: rgba(255,255,255,0.06); color: var(--text-sub); border: 1px solid rgba(255,255,255,0.11); }

.hover-qr-wrap {
  position: relative;
  flex: 1;
  display: flex;
}

.qr-tooltip {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(0);
  background: rgba(17,19,26,0.98);
  border: 1px solid rgba(255,255,255,0.12);
  padding: 12px;
  border-radius: 14px;
  box-shadow: 0 12px 34px rgba(0,0,0,0.6);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  opacity: 0;
  visibility: hidden;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 50;
  backdrop-filter: blur(14px);
  white-space: nowrap;
  pointer-events: none;
  min-width: 140px;
}

.hover-qr-wrap:hover .qr-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(8px);
}

.qr-img {
  width: 120px;
  height: 120px;
  border-radius: 8px;
  object-fit: cover;
  background: #fff;
}

.qr-fallback {
  width: 156px;
  min-height: 120px;
  border-radius: 10px;
  border: 1px dashed rgba(255,255,255,0.16);
  background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
  padding: 14px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
}

.qr-fallback-icon {
  min-width: 46px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid rgba(91,141,239,0.26);
  background: rgba(91,141,239,0.12);
  color: #8cb0ff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.qr-fallback-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
}

.qr-fallback-desc {
  font-size: 11px;
  line-height: 1.5;
  color: var(--text-sub);
}

.qr-text {
  font-size: 12px;
  color: var(--text);
  font-weight: 600;
}

@media (max-width: 900px) {
  section.download { padding: 70px 24px; }
}
</style>
