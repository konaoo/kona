<template>
  <div class="markets-wrap">
    <section class="markets" id="markets">
      <div class="section-header">
        <h2 class="section-title">全球三大市场统一管理</h2>
        <p class="section-sub">无论你的资产分布在哪里，咔咔记账都为你整合在同一个界面。</p>
      </div>
      <div class="markets-grid">
        <div class="market-card">
          <span class="mkt-flag">🇭🇰</span>
          <div class="mkt-name">香港股市</div>
          <div class="mkt-desc">港交所全市场覆盖，支持港元实时价格与盈亏计算。</div>
          <div><span class="mkt-tag hk">HKEX</span></div>
        </div>
        <div class="market-card">
          <span class="mkt-flag">🇺🇸</span>
          <div class="mkt-name">美国股市</div>
          <div class="mkt-desc">纳斯达克 / NYSE 全市场，美元资产实时追踪。</div>
          <div><span class="mkt-tag us">NASDAQ · NYSE</span></div>
        </div>
        <div class="market-card">
          <span class="mkt-flag">🇨🇳</span>
          <div class="mkt-name">A股市场</div>
          <div class="mkt-desc">沪深两市全覆盖，支持股票与场内基金。</div>
          <div><span class="mkt-tag a">上交所 · 深交所</span></div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
section.markets {
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

.markets-wrap {
  background: linear-gradient(180deg, transparent, rgba(91,141,239,0.025) 40%, transparent);
  border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
}

.markets-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }

.market-card {
  background: rgba(17,19,26,0.7); border: 1px solid var(--border); border-radius: 15px; padding: 20px;
  transition: border-color .2s, background .2s, transform .2s;
}

.market-card:hover { border-color: rgba(255,255,255,0.13); background: rgba(20,22,30,0.9); transform: translateY(-2px); }
.mkt-flag { font-size: 22px; margin-bottom: 9px; display: block; }
.mkt-name { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.mkt-desc { font-size: 11px; color: var(--text-muted); line-height: 1.4; }
.mkt-tag { display: inline-block; margin-top: 9px; font-size: 9px; font-weight: 700; letter-spacing: .06em; padding: 2px 7px; border-radius: 4px; }
.mkt-tag.hk { color: #e06b3a; background: rgba(224,107,58,0.12); }
.mkt-tag.us { color: #5b8def; background: rgba(91,141,239,0.12); }
.mkt-tag.a  { color: #3ecf82; background: rgba(62,207,130,0.12); }

@media (max-width: 900px) {
  section.markets { padding: 70px 24px; }
  .markets-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
