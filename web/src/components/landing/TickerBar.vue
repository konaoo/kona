<template>
  <div class="ticker-bar">
    <div class="ticker-track">
      <div class="ticker-item"><span class="ticker-dot"></span>恒生指数<span class="t-up">+1.24%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>纳斯达克<span class="t-dn">-0.38%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>沪深300<span class="t-up">+0.91%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>标普500<span class="t-up">+0.62%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>道琼斯<span class="t-up">+0.44%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>日经225<span class="t-dn">-0.67%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>富时100<span class="t-up">+0.33%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>恒生科技<span class="t-up">+2.10%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>恒生指数<span class="t-up">+1.24%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>纳斯达克<span class="t-dn">-0.38%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>沪深300<span class="t-up">+0.91%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>标普500<span class="t-up">+0.62%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>道琼斯<span class="t-up">+0.44%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>日经225<span class="t-dn">-0.67%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>富时100<span class="t-up">+0.33%</span></div>
      <div class="ticker-item"><span class="ticker-dot"></span>恒生科技<span class="t-up">+2.10%</span></div>
    </div>
  </div>
</template>

<style scoped>
.ticker-bar {
  position: fixed;
  top: 58px; left: 0; right: 0;
  height: 30px;
  background: rgba(10,11,14,0.88);
  backdrop-filter: blur(12px);
  overflow: hidden;
  z-index: 180;
  display: flex;
  align-items: center;
}

.ticker-track {
  display: flex;
  gap: 48px;
  animation: ticker 38s linear infinite;
  white-space: nowrap;
  padding-left: 100%;
}

@keyframes ticker {
  from { transform: translateX(0); }
  to { transform: translateX(-100%); }
}

.ticker-item {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-sub);
  flex-shrink: 0;
}

.ticker-dot { width: 4px; height: 4px; border-radius: 50%; background: var(--text-muted); flex-shrink: 0; }
.t-up { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--red); }
.t-dn { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--green); }
</style>
