<template>
  <section class="features" id="features">
    <div class="section-header">
      <h2 class="section-title">专为投资者设计的每一个细节</h2>
      <p class="section-sub">从单日收益到长期盈亏，从个股持仓到全局资产，一切尽在掌控。</p>
    </div>
    <div class="features-grid">
      <div class="feature-card">
        <div class="f-icon blue"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div>
        <div class="f-title">实时盈亏追踪</div>
        <div class="f-desc">每日、每月、每年的盈亏数据实时计算，收益日历让你对每一天的表现一目了然。</div>
        <div class="f-chart">
          <div class="f-bar up" style="height:60%"></div><div class="f-bar up" style="height:40%"></div>
          <div class="f-bar up" style="height:80%"></div><div class="f-bar dn" style="height:30%"></div>
          <div class="f-bar up" style="height:70%"></div><div class="f-bar up" style="height:90%"></div>
          <div class="f-bar dn" style="height:20%"></div><div class="f-bar up" style="height:100%"></div>
        </div>
      </div>
      <div class="feature-card">
        <div class="f-icon green"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
        <div class="f-title">多账户隔离管理</div>
        <div class="f-desc">支持创建多个独立账户，按策略分仓管理，每个账户独立核算盈亏。</div>
      </div>
      <div class="feature-card">
        <div class="f-icon gold"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></div>
        <div class="f-title">多货币自动换算</div>
        <div class="f-desc">HKD / USD / CNY 实时汇率换算，全球资产统一视角，无需手动折算。</div>
      </div>
      <div class="feature-card wide">
        <div class="f-icon purple"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg></div>
        <div class="f-title">市场资讯聚合</div>
        <div class="f-desc">宏观、公司、交易、政策四维度资讯精准分类，重要事件高亮提醒，直接关联到持仓标的，掌握每一个影响你账户的市场动态。</div>
      </div>
      <div class="feature-card">
        <div class="f-icon red"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div>
        <div class="f-title">盈亏排行榜</div>
        <div class="f-desc">自动计算全持仓标位的收益率排名，快速定位你的明星资产和拖累仓位。</div>
      </div>
    </div>
  </section>
</template>

<style scoped>
section.features {
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

.features-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
}

.feature-card {
  background: linear-gradient(180deg, rgba(20,22,30,0.92), rgba(16,18,26,0.96));
  border: 1px solid var(--border); border-radius: 18px; padding: 26px;
  position: relative; overflow: hidden;
  transition: border-color .22s, transform .22s;
}

.feature-card:hover { border-color: rgba(91,141,239,0.26); transform: translateY(-3px); }
.feature-card.wide { grid-column: span 2; }

.f-icon {
  width: 42px; height: 42px; border-radius: 11px;
  display: flex; align-items: center; justify-content: center; margin-bottom: 16px;
}

.f-icon.blue { background: rgba(91,141,239,0.13); border: 1px solid rgba(91,141,239,0.22); color: #739bf0; }
.f-icon.green { background: rgba(62,207,130,0.11); border: 1px solid rgba(62,207,130,0.22); color: #3ecf82; }
.f-icon.gold { background: rgba(212,175,100,0.11); border: 1px solid rgba(212,175,100,0.22); color: var(--gold); }
.f-icon.red { background: rgba(240,90,85,0.11); border: 1px solid rgba(240,90,85,0.22); color: #f05a55; }
.f-icon.purple { background: rgba(167,139,250,0.11); border: 1px solid rgba(167,139,250,0.22); color: #a78bfa; }
.f-icon svg { width: 20px; height: 20px; }

.f-title { font-size: 16px; font-weight: 700; color: var(--text); margin-bottom: 7px; }
.f-desc { font-size: 13px; color: var(--text-sub); line-height: 1.6; }

.f-chart { display: flex; align-items: flex-end; gap: 3px; height: 44px; margin-top: 18px; }
.f-bar { flex: 1; border-radius: 3px 3px 0 0; transition: height .4s ease; }
.f-bar.up { background: linear-gradient(180deg, rgba(240,90,85,0.8), rgba(240,90,85,0.3)); }
.f-bar.dn { background: linear-gradient(180deg, rgba(62,207,130,0.7), rgba(62,207,130,0.3)); }

@media (max-width: 900px) {
  section.features { padding: 70px 24px; }
  .features-grid { grid-template-columns: 1fr; }
  .feature-card.wide { grid-column: span 1; }
}
</style>
