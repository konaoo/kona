<template>
  <div class="hero">
    <div class="hero-inner">
      <div class="hero-left">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          GLOBAL ASSET DESK · v1.0
        </div>
        <h1 class="hero-title">
          全球资产<br>
          <span class="hero-title-accent">一站式管理</span>
        </h1>
        <p class="hero-sub">
          跨市场资产统一管理，实时盈亏追踪。<br>
          <strong>港股、美股、A股、基金</strong>，收益数据触手可及。
        </p>
        <div class="hero-actions">
          <RouterLink to="/app/login" class="btn-primary">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            进入网页版
          </RouterLink>
          <a :href="apkUrl" class="btn-ghost" target="_blank">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 16a7 7 0 0 1 14 0v1H5v-1z"/><line x1="12" y1="3" x2="12" y2="5"/><line x1="5.5" y1="5.5" x2="7" y2="7"/><line x1="18.5" y1="5.5" x2="17" y2="7"/><circle cx="9" cy="13" r="1"/><circle cx="15" cy="13" r="1"/></svg>
            安卓版
          </a>
          <div class="hover-qr-wrap">
            <a href="#" class="btn-ghost">
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a4 4 0 0 1 4 4v.5A4.5 4.5 0 0 0 20.5 11H21a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1h-.5A4.5 4.5 0 0 0 16 19.5V20a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-.5A4.5 4.5 0 0 0 3.5 15H3a1 1 0 0 1-1-1v-2a1 1 0 0 1 1-1h.5A4.5 4.5 0 0 0 8 6.5V6a4 4 0 0 1 4-4z"/></svg>
              苹果版
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
        <div class="hero-stats">
          <div class="hero-stat">
            <div class="stat-num">5<em>个</em></div>
            <div class="stat-label">支持市场</div>
          </div>
          <div class="stat-divider"></div>
          <div class="hero-stat">
            <div class="stat-num">100%</div>
            <div class="stat-label">数据实时同步</div>
          </div>
          <div class="stat-divider"></div>
          <div class="hero-stat">
            <div class="stat-num">∞</div>
            <div class="stat-label">资产数量上限</div>
          </div>
        </div>
      </div>

      <!-- PHONE -->
      <div class="hero-right">
        <div class="phone-scene">
          <div class="phone-glow"></div>

          <!-- Float: 今日收益 top-right -->
          <div class="float-card fc-today">
            <div class="fc-label">今日收益</div>
            <div class="fc-value">+¥3,472</div>
            <div class="fc-sub">↑ 较昨日 +0.86%</div>
          </div>

          <!-- Float: 市场快照 bottom-left -->
          <div class="float-card fc-market">
            <div class="fc-label">市场快照</div>
            <div class="fc-row"><span class="fc-mkt">恒生指数</span><span class="fc-up">+1.24%</span></div>
            <div class="fc-row"><span class="fc-mkt">纳斯达克</span><span class="fc-dn">-0.38%</span></div>
            <div class="fc-row"><span class="fc-mkt">沪深300</span><span class="fc-up">+0.91%</span></div>
          </div>

          <div class="phone-shell">
            <div class="phone-notch"></div>
            <div class="phone-screen">
              <div class="p-header">
                <div class="p-brand">
                  <div class="p-logo">M</div>
                  <span class="p-name">咔咔记账</span>
                </div>
                <div class="p-actions">
                  <div class="p-icon"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#828a9e" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg></div>
                  <div class="p-icon"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#828a9e" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></div>
                </div>
              </div>
              <div class="p-scroll">
                <div class="p-hero-card">
                  <div class="p-hero-label">总资产 (CNY)</div>
                  <div class="p-hero-val">¥ 248,631</div>
                  <div class="p-hero-row">
                    <span class="p-change">+¥3,472 今日</span>
                    <span class="p-pill">市场开放中</span>
                  </div>
                </div>
                <div class="p-stock">
                  <div class="p-ticker-icon blue">MSFT</div>
                  <div class="p-stock-main">
                    <div class="p-stock-name">微软</div>
                    <div class="p-stock-code">NASDAQ · US</div>
                    <div class="p-progress"><div class="p-anchor"></div><div class="p-progress-fill up" style="width:28%"></div></div>
                  </div>
                  <div class="p-stock-right">
                    <div class="p-stock-val">¥29,840</div>
                    <div class="p-badge up">+8.42%</div>
                  </div>
                </div>
                <div class="p-stock">
                  <div class="p-ticker-icon orange">9988</div>
                  <div class="p-stock-main">
                    <div class="p-stock-name">阿里巴巴</div>
                    <div class="p-stock-code">港交所 · HK</div>
                    <div class="p-progress"><div class="p-anchor"></div><div class="p-progress-fill dn" style="width:16%"></div></div>
                  </div>
                  <div class="p-stock-right">
                    <div class="p-stock-val">¥11,520</div>
                    <div class="p-badge dn">-3.18%</div>
                  </div>
                </div>
                <div class="p-stock">
                  <div class="p-ticker-icon green">600</div>
                  <div class="p-stock-main">
                    <div class="p-stock-name">贵州茅台</div>
                    <div class="p-stock-code">沪深 · A</div>
                    <div class="p-progress"><div class="p-anchor"></div><div class="p-progress-fill up" style="width:20%"></div></div>
                  </div>
                  <div class="p-stock-right">
                    <div class="p-stock-val">¥38,490</div>
                    <div class="p-badge up">+11.52%</div>
                  </div>
                </div>
              </div>
              <div class="p-nav">
                <div class="p-nav-item active">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#5b8def" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
                  <div class="p-nav-line"></div>
                </div>
                <div class="p-nav-item"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#545c72" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg><div class="p-nav-line"></div></div>
                <div class="p-nav-item">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none"><rect width="24" height="24" rx="8" fill="url(#fg)"/><line x1="12" y1="7" x2="12" y2="17" stroke="white" stroke-width="2" stroke-linecap="round"/><line x1="7" y1="12" x2="17" y2="12" stroke="white" stroke-width="2" stroke-linecap="round"/><defs><linearGradient id="fg" x1="0" y1="0" x2="24" y2="24"><stop stop-color="#5b8def"/><stop offset="1" stop-color="#4a7be0"/></linearGradient></defs></svg>
                  <div class="p-nav-line"></div>
                </div>
                <div class="p-nav-item"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#545c72" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg><div class="p-nav-line"></div></div>
                <div class="p-nav-item"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#545c72" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg><div class="p-nav-line"></div></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

const props = defineProps<{ apkUrl?: string; iosQrText?: string; iosQrImageUrl?: string }>()

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
.hero {
  min-height: 100vh;
  padding-top: 96px; /* 58px nav + 30px ticker + 8px gap */
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

/* Background orb glow */
.hero::before {
  content: '';
  position: absolute;
  width: 700px; height: 700px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(91,141,239,0.14) 0%, transparent 65%);
  filter: blur(60px);
  top: -100px; left: -100px;
  pointer-events: none;
  animation: orbDrift 10s ease-in-out infinite;
}

.hero::after {
  content: '';
  position: absolute;
  width: 500px; height: 500px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(240,39,158,0.10) 0%, transparent 65%);
  filter: blur(60px);
  bottom: 50px; right: 5%;
  pointer-events: none;
  animation: orbDrift 14s ease-in-out infinite reverse;
}

@keyframes orbDrift {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, 20px); }
}

.hero-inner {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1320px;
  margin: 0 auto;
  padding: 60px 40px 60px 120px;
  display: grid;
  grid-template-columns: 460px 1fr;
  align-items: center;
  gap: 20px;
}

.hero-badge {
  display: inline-flex; align-items: center; gap: 7px;
  height: 26px; padding: 0 11px; border-radius: 999px;
  border: 1px solid rgba(212,175,100,0.3);
  background: rgba(212,175,100,0.07);
  color: var(--gold);
  font-family: 'JetBrains Mono', monospace; font-size: 9px; font-weight: 500; letter-spacing: 0.1em;
  margin-bottom: 22px;
}

.badge-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--gold); animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.8)} }

.hero-title {
  font-size: clamp(36px, 3.8vw, 56px);
  font-weight: 800;
  line-height: 1.08;
  letter-spacing: -.03em;
  margin-bottom: 18px;
}

.hero-title-accent {
  background: linear-gradient(135deg, #5b8def, #a78bfa, #f05a55);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

.hero-sub {
  font-size: 15px; color: var(--text-sub); line-height: 1.7;
  max-width: 420px; margin-bottom: 36px;
}

.hero-sub strong { color: var(--text); font-weight: 600; }

.hero-actions {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  margin-bottom: 44px;
}

.btn-primary {
  height: 46px; padding: 0 22px; border-radius: 13px; border: none;
  background: linear-gradient(135deg, #5b8def, #4a7be0);
  color: #fff; font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 700;
  cursor: pointer; display: inline-flex; align-items: center; gap: 7px;
  box-shadow: 0 6px 20px rgba(74,123,224,0.32), inset 0 1px 0 rgba(255,255,255,0.18);
  text-decoration: none; transition: transform .18s, box-shadow .18s;
}
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(74,123,224,0.42), inset 0 1px 0 rgba(255,255,255,0.18); }

.btn-ghost {
  height: 46px; padding: 0 18px; border-radius: 13px;
  border: 1px solid var(--border-bright);
  background: rgba(255,255,255,0.05);
  color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 600;
  cursor: pointer; display: inline-flex; align-items: center; gap: 7px;
  text-decoration: none; backdrop-filter: blur(6px);
  transition: background .18s, border-color .18s, transform .18s;
}
.btn-ghost:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.2); transform: translateY(-1px); }
.btn-ghost.dim { background: rgba(255,255,255,0.03); opacity: 0.7; pointer-events: none; }

.btn-icon { width: 16px; height: 16px; flex-shrink: 0; }

.hover-qr-wrap {
  position: relative;
  display: inline-flex;
}

.qr-tooltip {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(10px);
  background: rgba(17,19,26,0.95);
  border: 1px solid var(--border-bright);
  padding: 12px;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 50;
  backdrop-filter: blur(10px);
  white-space: nowrap;
  pointer-events: none;
  min-width: 140px;
}

.hover-qr-wrap:hover .qr-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(4px);
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

.hero-stats {
  display: flex; align-items: center; gap: 24px;
  padding-top: 28px; border-top: 1px solid var(--border);
}

.stat-num { font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 600; color: var(--text); line-height: 1; margin-bottom: 3px; }
.stat-num em { color: var(--blue); font-style: normal; font-size: 13px; }
.stat-label { font-size: 11px; color: var(--text-muted); }
.stat-divider { width: 1px; height: 28px; background: var(--border); }

/* PHONE MOCKUP */
.hero-right {
  display: flex; justify-content: center; align-items: center;
  position: relative;
}

.phone-scene {
  position: relative;
  width: 300px;
}

.phone-glow {
  position: absolute;
  width: 350px; height: 350px;
  background: radial-gradient(circle, rgba(91,141,239,0.22) 0%, transparent 70%);
  border-radius: 50%; filter: blur(40px);
  top: 50%; left: 50%; transform: translate(-50%,-50%);
  z-index: 0; pointer-events: none;
}

.phone-shell {
  position: relative; z-index: 1;
  width: 300px;
  background: linear-gradient(180deg, #1c1f2a 0%, #141720 100%);
  border-radius: 44px;
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: 0 40px 80px rgba(0,0,0,0.65), inset 0 0 0 1px rgba(255,255,255,0.04), inset 0 1px 0 rgba(255,255,255,0.12);
  overflow: hidden;
  animation: phoneFloat 6s ease-in-out infinite;
}

@keyframes phoneFloat {
  0%,100% { transform: translateY(0) rotate(.8deg); }
  50% { transform: translateY(-10px) rotate(-.4deg); }
}

.phone-notch {
  position: absolute; top: 14px; left: 50%; transform: translateX(-50%);
  width: 72px; height: 8px; background: #000; border-radius: 999px; z-index: 10;
}

.phone-screen {
  width: 100%; min-height: 580px; padding-top: 38px;
  background: #0d0e12;
  display: flex; flex-direction: column; position: relative;
}

.p-header {
  padding: 10px 14px 8px;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}

.p-brand { display: flex; align-items: center; gap: 7px; }

.p-logo {
  width: 26px; height: 26px; border-radius: 7px;
  background: linear-gradient(135deg, #5b8def, #4a7be0);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: #fff;
}

.p-name { font-size: 12px; font-weight: 700; color: #e4e5ea; }

.p-actions { display: flex; gap: 5px; }
.p-icon { width: 22px; height: 22px; border-radius: 6px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; }

.p-scroll {
  flex: 1; padding: 10px 12px 70px;
  display: flex; flex-direction: column; gap: 7px; overflow: hidden;
}

.p-hero-card {
  background: linear-gradient(135deg, rgba(91,141,239,0.16), rgba(74,123,224,0.05) 40%, rgba(26,29,37,0.96));
  border: 1px solid rgba(255,255,255,0.07); border-radius: 11px; padding: 11px;
}

.p-hero-label { font-size: 8px; color: #828a9e; margin-bottom: 4px; }
.p-hero-val { font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 600; color: #f0f4ff; letter-spacing: -.01em; margin-bottom: 7px; }
.p-hero-row { display: flex; align-items: center; justify-content: space-between; }
.p-change { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #3ecf82; font-weight: 500; }
.p-pill { font-size: 8px; font-weight: 600; padding: 2px 6px; border-radius: 999px; border: 1px solid rgba(62,207,130,0.3); background: rgba(62,207,130,0.1); color: #3ecf82; }

.p-stock {
  background: linear-gradient(180deg, rgba(26,29,37,0.94), rgba(23,26,34,0.97));
  border: 1px solid rgba(255,255,255,0.055); border-radius: 9px;
  padding: 8px 10px; display: flex; align-items: center; gap: 8px;
}

.p-ticker-icon {
  width: 30px; height: 30px; border-radius: 7px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-family: 'JetBrains Mono', monospace; font-size: 8px; font-weight: 700;
}

.p-ticker-icon.blue { background: rgba(91,141,239,0.14); border: 1px solid rgba(91,141,239,0.22); color: #739bf0; }
.p-ticker-icon.orange { background: rgba(224,107,58,0.12); border: 1px solid rgba(224,107,58,0.22); color: #e06b3a; }
.p-ticker-icon.green { background: rgba(62,207,130,0.10); border: 1px solid rgba(62,207,130,0.22); color: #3ecf82; }

.p-stock-main { flex: 1; min-width: 0; }
.p-stock-name { font-size: 10px; font-weight: 700; color: #edf1fa; margin-bottom: 1px; }
.p-stock-code { font-family: 'JetBrains Mono', monospace; font-size: 8px; color: #575d6e; margin-bottom: 4px; }
.p-progress { height: 2px; background: rgba(255,255,255,0.06); border-radius: 1px; position: relative; }
.p-progress-fill { position: absolute; top: 0; bottom: 0; border-radius: 1px; }
.p-progress-fill.up { left: 50%; background: #f05a55; }
.p-progress-fill.dn { right: 50%; background: #3ecf82; }
.p-anchor { position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: rgba(255,255,255,0.25); }

.p-stock-right { text-align: right; flex-shrink: 0; }
.p-stock-val { font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 600; color: #e3e9f7; margin-bottom: 2px; }
.p-badge { font-size: 8px; font-weight: 600; padding: 1px 5px; border-radius: 999px; }
.p-badge.up { color: #f05a55; background: rgba(240,90,85,0.12); }
.p-badge.dn { color: #3ecf82; background: rgba(62,207,130,0.12); }

.p-nav {
  position: absolute; bottom: 0; left: 0; right: 0; height: 54px;
  background: linear-gradient(180deg, rgba(13,16,27,0.98), rgba(11,14,22,1));
  border-top: 1px solid rgba(255,255,255,0.06);
  display: grid; grid-template-columns: repeat(5, 1fr);
  padding-bottom: 4px;
}

.p-nav-item { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; }
.p-nav-line { width: 16px; height: 2px; border-radius: 1px; }
.p-nav-item.active .p-nav-line { background: var(--blue); }

/* Floating cards */
.float-card {
  position: absolute; z-index: 3;
  background: rgba(16,18,26,0.92);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 13px;
  padding: 11px 13px;
  box-shadow: 0 16px 36px rgba(0,0,0,0.45);
}

.fc-label { font-size: 9px; color: var(--text-muted); margin-bottom: 3px; letter-spacing: .03em; }
.fc-value { font-family: 'JetBrains Mono', monospace; font-size: 17px; font-weight: 600; color: var(--green); margin-bottom: 2px; }
.fc-sub { font-size: 9px; color: var(--text-muted); }

.fc-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.fc-row:last-child { border: none; }
.fc-mkt { font-size: 9px; font-weight: 600; color: var(--text-sub); }
.fc-up { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--red); }
.fc-dn { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--green); }

/* Card 1: top-right, overlapping phone right edge */
.fc-today {
  right: -90px; top: 65px; width: 142px;
  animation: flt1 5s ease-in-out infinite;
}

@keyframes flt1 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-7px)} }

/* Card 2: bottom-left, overlapping phone left edge */
.fc-market {
  left: -80px; bottom: 85px; width: 136px;
  animation: flt2 7s ease-in-out infinite;
}

@keyframes flt2 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(7px)} }

@media (max-width: 900px) {
  .hero-inner { grid-template-columns: 1fr; padding: 40px 24px; }
  .hero-right { display: none; }
}
</style>
