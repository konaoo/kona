<script setup lang="ts">
type InvestTotal = {
  mv: number
  dayPnl: number
  dayRate: number
  floatPnl: number
  floatRate: number
  totalPnl: number
  totalRate: number
}

type DistributionItem = {
  name: string
  percent: number
  value: number
  color: string
}

type DistributionSlice = DistributionItem & {
  start: number
  end: number
}

defineProps<{
  currentCurrency: string
  investTotal: InvestTotal
  distributionData: DistributionItem[]
  slices: DistributionSlice[]
  masked: (text: string) => string
  formatCurrency: (value: number, signed?: boolean, integerOnly?: boolean) => string
  valueClass: (value: number) => string
  formatPct: (value: number) => string
  describeArc: (
    x: number,
    y: number,
    radius: number,
    startAngle: number,
    endAngle: number
  ) => string
}>()
</script>

<template>
  <div class="stats-grid">
    <div class="hero-card">
      <div class="card-label">投资总资产 ({{ currentCurrency }})</div>
      <div class="main-val">{{ masked(formatCurrency(investTotal.mv)) }}</div>
      <div class="stats-row">
        <div class="stat-item">
          <span class="sl">当日盈亏</span>
          <div class="sv-group" :class="valueClass(investTotal.dayPnl)">
            <span class="sv-amt">{{ masked(formatCurrency(investTotal.dayPnl, true, true)) }}</span>
            <span class="sv-pct">{{ formatPct(investTotal.dayRate) }}</span>
          </div>
        </div>
        <div class="stat-item">
          <span class="sl">持仓盈亏</span>
          <div class="sv-group" :class="valueClass(investTotal.floatPnl)">
            <span class="sv-amt">{{ masked(formatCurrency(investTotal.floatPnl, true, true)) }}</span>
            <span class="sv-pct">{{ formatPct(investTotal.floatRate) }}</span>
          </div>
        </div>
        <div class="stat-item">
          <span class="sl">累计盈亏</span>
          <div class="sv-group" :class="valueClass(investTotal.totalPnl)">
            <span class="sv-amt">{{ masked(formatCurrency(investTotal.totalPnl, true, true)) }}</span>
            <span class="sv-pct">{{ formatPct(investTotal.totalRate) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="dist-card">
      <div class="card-title">资产分布</div>
      <div class="dist-content">
        <div class="chart-container">
          <svg viewBox="0 0 100 100" class="donut-svg">
            <circle
              cx="50"
              cy="50"
              r="35"
              fill="transparent"
              stroke="var(--surface-divider)"
              stroke-width="12"
            />
            <g v-for="(slice, i) in slices" :key="i">
              <circle
                v-if="slice.percent >= 99.99"
                cx="50"
                cy="50"
                r="35"
                fill="transparent"
                :stroke="slice.color"
                stroke-width="12"
                class="donut-slice"
              />
              <path
                v-else
                :d="describeArc(50, 50, 35, slice.start * 3.6, slice.end * 3.6)"
                :stroke="slice.color"
                stroke-width="12"
                fill="none"
                stroke-linecap="round"
                class="donut-slice"
              />
            </g>
            <text x="50" y="47" text-anchor="middle" class="chart-center-val">
              {{ distributionData.length }}
            </text>
            <text x="50" y="62" text-anchor="middle" class="chart-center-lbl">资产</text>
          </svg>
        </div>
        <div class="legend-list">
          <div v-for="item in distributionData" :key="item.name" class="legend-item">
            <div class="legend-left">
              <span class="dot" :style="{ background: item.color }"></span>
              <span class="ln">{{ item.name }}</span>
            </div>
            <span class="lp">{{ item.percent.toFixed(1) }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: 1.8fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.hero-card {
  background: linear-gradient(135deg, rgba(91, 141, 239, 0.1), rgba(74, 123, 224, 0.05));
  border: 1px solid rgba(91, 141, 239, 0.2);
  border-radius: 28px;
  padding: 32px;
  display: flex;
  flex-direction: column;
}

.card-label {
  font-size: 13px;
  color: var(--sub);
  margin-bottom: 12px;
  font-weight: 600;
}

.main-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 42px;
  font-weight: 800;
  margin-bottom: 24px;
  letter-spacing: -1px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  padding: 4px 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sl {
  font-size: 11px;
  color: var(--muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sv-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sv-amt {
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 800;
  white-space: nowrap;
  letter-spacing: -0.5px;
}

.sv-pct {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  opacity: 0.9;
}

.sv-group.up {
  color: var(--red);
}

.sv-group.dn {
  color: var(--green);
}

.dist-card {
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: 28px;
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--text);
}

.dist-content {
  display: flex;
  align-items: center;
  gap: 32px;
  flex: 1;
}

.chart-container {
  position: relative;
  width: 110px;
  height: 110px;
  flex-shrink: 0;
}

.donut-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.chart-center-val {
  fill: var(--text);
  font-size: 20px;
  font-weight: 800;
  font-family: 'JetBrains Mono', monospace;
  transform: rotate(90deg);
  transform-origin: center;
}

.chart-center-lbl {
  fill: var(--sub);
  font-size: 9px;
  font-weight: 600;
  transform: rotate(90deg);
  transform-origin: center;
}

.donut-slice {
  transition: stroke-dasharray 0.5s var(--easing-out);
}

.legend-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
}

.legend-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.legend-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-item .ln {
  color: var(--sub);
  font-weight: 500;
}

.legend-item .lp {
  font-weight: 700;
  color: var(--text);
  font-family: 'JetBrains Mono', monospace;
}

:global([data-theme='light']) .hero-card,
:global([data-theme='light']) .dist-card {
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.06);
}

:global([data-theme='light']) .hero-card {
  background: linear-gradient(180deg, #ffffff, #f6f9ff);
  border-color: rgba(91, 141, 239, 0.16);
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .hero-card {
    padding: 24px 20px;
    border-radius: 24px;
  }

  .main-val {
    font-size: 34px;
    margin-bottom: 18px;
  }

  .stats-row {
    gap: 8px;
  }

  .sv-amt {
    font-size: 15px;
  }

  .sv-pct {
    font-size: 10px;
  }

  .sl {
    font-size: 10px;
  }

  .card-label {
    font-size: 12px;
    margin-bottom: 8px;
  }

  .dist-card {
    padding: 24px 20px;
    border-radius: 24px;
  }

  .dist-content {
    gap: 16px;
  }

  .chart-container {
    width: 90px;
    height: 90px;
  }

  .legend-item {
    font-size: 12px;
  }
}
</style>
