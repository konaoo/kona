<script setup lang="ts">
import { toNumber } from '@/shared/format'
import AssetLogo from '@/components/base/AssetLogo.vue'
import type { InvestHoldingDisplayRow } from '@/stores/investHoldingRows'

type HoldingView = 'card' | 'row'

const selectedTab = defineModel<string>('selectedTab', { required: true })
const holdingsView = defineModel<HoldingView>('holdingsView', { required: true })

defineProps<{
  rows: InvestHoldingDisplayRow[]
  masked: (text: string) => string
  formatHoldingCurrency: (value: number) => string
  getMarketName: (market: string) => string
  getQtyFontSize: (value: string | number) => string
  formatLocal: (value: any) => string
  quoteLabel: (row: any) => string
  quoteMetaLabel: (row: any) => string
  valueClass: (value: number) => string
  dayPnlRateLabel: (row: any) => string
  dayPnlAmountLabel: (row: any) => string
  formatPnlOriginal: (value: number, curr?: string) => string
  getCurrencySymbol: (curr?: string) => string
  formatAssetPrice: (value: unknown) => string
  formatPct: (value: number) => string
}>()

defineEmits<{
  (event: 'add-asset'): void
  (event: 'open-asset', row: InvestHoldingDisplayRow): void
}>()
</script>

<template>
  <div class="holdings-section">
    <div class="h-header">
      <div class="section-label">持仓明细</div>
      <button class="add-asset-btn mobile-add-btn" @click="$emit('add-asset')">
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
        >
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        添加资产
      </button>
    </div>
    <div class="h-filters">
      <div class="tabs" style="width: fit-content">
        <button
          v-for="tab in ['all', 'a', 'hk', 'us', 'fund']"
          :key="tab"
          class="tab"
          :class="{ active: selectedTab === tab }"
          @click="selectedTab = tab"
        >
          {{
            tab === 'all'
              ? '全部'
              : tab === 'hk'
                ? '港股'
                : tab === 'us'
                  ? '美股'
                  : tab === 'a'
                    ? 'A股'
                    : '基金'
          }}
        </button>
      </div>
      <div class="h-actions">
        <button class="add-asset-btn" @click="$emit('add-asset')">
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          添加资产
        </button>
        <div class="view-toggle">
          <button :class="{ active: holdingsView === 'card' }" @click="holdingsView = 'card'">
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
              <rect x="0" y="0" width="7" height="7" rx="1.5" fill="currentColor" />
              <rect x="9" y="0" width="7" height="7" rx="1.5" fill="currentColor" />
              <rect x="0" y="9" width="7" height="7" rx="1.5" fill="currentColor" />
              <rect x="9" y="9" width="7" height="7" rx="1.5" fill="currentColor" />
            </svg>
          </button>
          <button :class="{ active: holdingsView === 'row' }" @click="holdingsView = 'row'">
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
              <rect x="0" y="1" width="16" height="2.5" rx="1.2" fill="currentColor" />
              <rect x="0" y="6.5" width="16" height="2.5" rx="1.2" fill="currentColor" />
              <rect x="0" y="12" width="16" height="2.5" rx="1.2" fill="currentColor" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <div v-if="!rows || rows.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <div class="empty-text">暂无持仓数据</div>
    </div>

    <div v-else>
      <div v-if="holdingsView === 'card'" class="card-view-grid">
        <div
          v-for="(row, idx) in rows"
          :key="row?.code || `card-${idx}`"
          class="hcard"
          @click="row?.code && $emit('open-asset', row)"
        >
          <div
            class="hcard-accent-top"
            :style="{
              background: `linear-gradient(90deg, transparent, ${toNumber(row.dayPnl) >= 0 ? 'var(--red)' : 'var(--green)'} 40%, transparent)`
            }"
          ></div>

          <div class="hcard-header-row">
            <div class="h-icon-box">
              <AssetLogo
                :name="row.name"
                :code="row.code"
                :logo-url="row.logo_url"
                :market="row.market"
                :asset-type="row.asset_type"
              />
            </div>
            <div class="h-info-group">
              <div class="h-name-row">
                {{ row.name.length > 20 ? row.name.slice(0, 19) + '...' : row.name }}
              </div>
              <div class="h-meta-row">
                <span class="tag" :class="[row.category || row.market]">{{
                  getMarketName(row.category || row.market)
                }}</span>
                <span class="h-qty">
                  <span :style="{ fontSize: getQtyFontSize(formatLocal(row.amount)) }">{{
                    formatLocal(row.amount)
                  }}</span>
                  {{ row.unit }}
                </span>
              </div>
            </div>
            <div class="h-mv-right">
              {{ masked(formatHoldingCurrency(Number(row.mvCny) || 0)) }}
            </div>
          </div>

          <div class="h-price-row">
            <div class="h-price-main">
              <span class="h-price-val">{{ quoteLabel(row) }}</span>
              <span v-if="quoteMetaLabel(row)" class="h-price-meta">{{ quoteMetaLabel(row) }}</span>
            </div>
            <div
              class="h-price-tag badge"
              :class="row.dayPnlVisible ? valueClass(toNumber(row.dayPnlRate)) : 'muted'"
            >
              {{ dayPnlRateLabel(row) }}
            </div>
          </div>

          <div class="sparkline-box">
            <svg
              v-if="row.sparkReady"
              viewBox="0 0 120 40"
              width="100%"
              height="100%"
              preserveAspectRatio="none"
              fill="none"
            >
              <path
                :d="row.spark"
                :stroke="toNumber(row.dayPnl) >= 0 ? 'var(--red)' : 'var(--green)'"
                stroke-width="1.6"
                fill="none"
              />
            </svg>
            <div v-else class="trend-empty">暂无趋势</div>
          </div>

          <div class="holding-metrics">
            <div class="holding-metrics-grid">
              <div>
                <div class="metric-label">当日盈亏</div>
                <div
                  :class="[
                    row.dayPnlVisible
                      ? toNumber(row.dayPnl) >= 0
                        ? 'text-up'
                        : 'text-dn'
                      : 'text-muted'
                  ]"
                  class="metric-value strong"
                >
                  {{ dayPnlAmountLabel(row) }}
                </div>
              </div>
              <div>
                <div class="metric-label">累计盈亏</div>
                <div
                  :class="[toNumber(row.totalPnl) >= 0 ? 'text-up' : 'text-dn']"
                  class="metric-value strong"
                >
                  {{ masked(formatPnlOriginal(row.totalPnlRaw, row.curr)) }}
                </div>
              </div>
              <div>
                <div class="metric-label">成本价</div>
                <div class="metric-value muted">
                  {{ masked(getCurrencySymbol(row.curr) + formatAssetPrice(row.costPrice)) }}
                </div>
              </div>
              <div>
                <div class="metric-label">累计盈亏率</div>
                <div
                  :class="[toNumber(row.totalPnlRate) >= 0 ? 'text-up' : 'text-dn']"
                  class="metric-value strong"
                >
                  {{ formatPct(row.totalPnlRate) }}
                </div>
              </div>
            </div>
            <div class="position-bar-wrap">
              <div class="metric-label position-label">仓位</div>
              <div class="position-row">
                <span class="position-value">{{ formatPct(row.pct).replace('%', '') }}%</span>
                <div class="position-track">
                  <div
                    class="position-fill"
                    :style="{ width: `${Math.min(toNumber(row.pct), 100)}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="row-view-list">
        <div
          v-for="(row, idx) in rows"
          :key="row?.code || `row-${idx}`"
          class="hrow"
          @click="row?.code && $emit('open-asset', row)"
        >
          <div class="row-asset-cell">
            <div class="h-icon row-icon">
              <AssetLogo
                :name="row.name"
                :code="row.code"
                :logo-url="row.logo_url"
                :market="row.market"
                :asset-type="row.asset_type"
              />
            </div>
            <div>
              <div class="row-name">{{ row.name }}</div>
              <div class="row-tags">
                <span class="tag" :class="[row.category || row.market]">{{
                  getMarketName(row.category || row.market)
                }}</span>
              </div>
            </div>
          </div>

          <div class="row-metrics-grid">
            <div class="row-metric with-divider">
              <div class="metric-label">持仓数量</div>
              <div class="row-metric-value">{{ formatLocal(row.qty) }}</div>
            </div>
            <div class="row-metric with-divider">
              <div class="metric-label">现价</div>
              <div class="row-metric-value">{{ quoteLabel(row) }}</div>
              <div v-if="quoteMetaLabel(row)" class="h-price-cell-meta">
                {{ quoteMetaLabel(row) }}
              </div>
            </div>
            <div class="row-metric with-divider">
              <div class="metric-label">成本价</div>
              <div class="row-metric-value muted">
                {{ masked(getCurrencySymbol(row.curr) + formatAssetPrice(row.costPrice)) }}
              </div>
            </div>
            <div class="row-metric with-divider">
              <div class="metric-label">市值</div>
              <div class="row-metric-value">
                {{ masked(formatHoldingCurrency(Number(row.mvCny) || 0)) }}
              </div>
            </div>
            <div class="row-metric with-divider">
              <div class="metric-label">今日盈亏</div>
              <div
                :class="[
                  row.dayPnlVisible
                    ? toNumber(row.dayPnl) >= 0
                      ? 'text-up'
                      : 'text-dn'
                    : 'text-muted'
                ]"
                class="row-metric-value"
              >
                {{ dayPnlAmountLabel(row) }}
              </div>
              <div
                :class="[
                  row.dayPnlVisible
                    ? toNumber(row.dayPnl) >= 0
                      ? 'text-up'
                      : 'text-dn'
                    : 'text-muted'
                ]"
                class="row-metric-sub"
              >
                {{ dayPnlRateLabel(row) }}
              </div>
            </div>
            <div class="row-metric with-divider">
              <div class="metric-label">累计盈亏</div>
              <div
                :class="[toNumber(row.totalPnl) >= 0 ? 'text-up' : 'text-dn']"
                class="row-metric-value"
              >
                {{ masked(formatPnlOriginal(row.totalPnlRaw, row.curr)) }}
              </div>
              <div
                :class="[toNumber(row.totalPnl) >= 0 ? 'text-up' : 'text-dn']"
                class="row-metric-sub"
              >
                {{ formatPct(row.totalPnlRate) }}
              </div>
            </div>
            <div class="row-metric position-metric">
              <div class="row-position-head">
                <span class="metric-label">仓位</span>
                <span class="position-value">{{ formatPct(row.pct).replace('%', '') }}%</span>
              </div>
              <div class="row-position-track">
                <div
                  class="row-position-fill"
                  :style="{ width: `${Math.min(toNumber(row.pct), 100)}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.holdings-section {
  margin-top: 40px;
}

.h-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-label {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.h-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}

.view-toggle {
  display: flex;
  gap: 4px;
  background: var(--surface-soft);
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: 3px;
}

.view-toggle button {
  width: 32px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.view-toggle button.active {
  background: var(--surface-strong);
  color: var(--text);
}

.h-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.add-asset-btn {
  height: 28px;
  padding: 0 10px;
  border-radius: 6px;
  border: none;
  background: var(--surface-highlight);
  color: var(--blue);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}

.card-view-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 10px;
}

.hcard {
  position: relative;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px;
  cursor: pointer;
  transition:
    background 0.18s,
    transform 0.18s,
    box-shadow 0.18s;
  overflow: hidden;
}

.hcard:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  border-color: var(--border-b);
}

.hcard-accent-top {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
}

.h-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 800;
  color: #fff;
  margin-bottom: 12px;
}

.hcard-header-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.h-icon-box {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 10px;
  overflow: hidden;
}

.h-info-group {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.h-name-row {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.h-meta-row {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: nowrap;
  overflow: hidden;
}

.tag {
  flex-shrink: 0;
  white-space: nowrap;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.h-qty {
  font-size: 11px;
  color: var(--muted);
  font-weight: 500;
  white-space: nowrap;
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  flex: 0 0 auto;
}

.h-qty span {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
}

.tag.us {
  background: rgba(0, 122, 255, 0.1);
  color: #007aff;
}

.tag.hk {
  background: rgba(255, 149, 0, 0.1);
  color: #ff9500;
}

.tag.a {
  background: rgba(52, 199, 89, 0.1);
  color: #34c759;
}

.tag.fund {
  background: rgba(255, 204, 0, 0.1);
  color: #ffcc00;
}

.row-view-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hrow {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--s2);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 14px 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.hrow:hover {
  background: rgba(255, 255, 255, 0.03);
  border-color: var(--blue);
}

.badge.up {
  background: rgba(240, 90, 85, 0.12);
  color: var(--red);
}

.badge.dn {
  background: rgba(62, 207, 130, 0.12);
  color: var(--green);
}

.text-up {
  color: var(--red) !important;
}

.text-dn {
  color: var(--green) !important;
}

.empty-state {
  padding: 80px 0;
  text-align: center;
  background: var(--surface-faint);
  border: 1px dashed var(--border);
  border-radius: 32px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
  color: var(--muted);
}

.up {
  color: #f05a55 !important;
}

.dn {
  color: #3ecf82 !important;
}

.h-price-row {
  display: flex;
  align-items: baseline;
  justify-content: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}

.h-price-main {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  color: var(--text);
}

.h-price-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 700;
}

.h-price-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}

.h-price-tag.up {
  color: var(--red);
  background: rgba(240, 90, 85, 0.12);
}

.h-price-tag.dn {
  color: var(--green);
  background: rgba(62, 207, 130, 0.12);
}

.h-price-tag.muted {
  color: var(--muted);
  background: var(--surface-soft);
}

.h-price-meta,
.h-price-cell-meta {
  font-size: 10px;
  color: var(--muted);
  line-height: 1.2;
}

.h-price-cell-meta {
  margin-top: 3px;
}

.h-mv-right {
  margin-left: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  text-align: right;
}

.sparkline-box {
  height: 38px;
  margin-bottom: 10px;
  opacity: 0.85;
}

.trend-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed color-mix(in srgb, var(--border) 78%, transparent);
  border-radius: 10px;
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 0.02em;
  background: color-mix(in srgb, var(--surface-soft) 70%, transparent);
}

.holding-metrics {
  padding-top: 10px;
  border-top: 1px solid var(--surface-divider);
}

.holding-metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.metric-label {
  font-size: 10px;
  color: var(--muted);
  margin-bottom: 2px;
}

.metric-value,
.row-metric-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12.5px;
  font-weight: 600;
}

.metric-value.strong {
  font-weight: 600;
}

.metric-value.muted,
.row-metric-value.muted {
  color: var(--muted);
  font-weight: 500;
}

.position-bar-wrap {
  margin-top: 10px;
}

.position-label {
  margin-bottom: 4px;
}

.position-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.position-value {
  color: var(--blue);
  font-size: 12.5px;
  font-weight: 600;
  min-width: 54px;
}

.position-track {
  flex: 1;
  height: 3px;
  background: var(--surface-track);
  border-radius: 2px;
  overflow: hidden;
}

.position-fill {
  height: 100%;
  background: rgba(91, 141, 239, 0.7);
  border-radius: 2px;
}

.row-asset-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 240px;
  flex-shrink: 0;
}

.row-icon {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border: none;
  background: none;
}

.row-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
}

.row-tags {
  display: flex;
  gap: 5px;
  margin-top: 3px;
}

.row-metrics-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 12px;
  flex: 1;
  align-items: center;
}

.row-metric {
  padding: 0 12px;
}

.row-metric.with-divider {
  border-right: 1px solid var(--surface-divider);
}

.row-metric-sub {
  font-size: 11px;
  margin-top: 1px;
}

.position-metric {
  padding-right: 0;
}

.row-position-head {
  font-size: 10px;
  color: var(--muted);
  margin-bottom: 4px;
  display: flex;
  justify-content: space-between;
}

.row-position-track {
  height: 4px;
  background: var(--surface-track);
  border-radius: 3px;
  overflow: hidden;
}

.row-position-fill {
  height: 100%;
  background: linear-gradient(90deg, rgba(91, 141, 239, 0.5), rgba(91, 141, 239, 0.9));
  border-radius: 3px;
}

:global([data-theme='light']) .hcard,
:global([data-theme='light']) .hrow {
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.06);
}

@media (max-width: 900px) {
  .row-view-list > .hrow > div:nth-child(2) {
    display: none;
  }

  .h-header {
    margin-bottom: 12px;
  }

  .h-filters {
    margin-bottom: 16px;
  }

  .view-toggle {
    display: none !important;
  }

  .add-asset-btn {
    height: 32px;
    padding: 0 16px;
    font-size: 13px;
  }
}

.mobile-add-btn {
  display: none;
}

@media (max-width: 640px) {
  .mobile-add-btn {
    display: flex;
  }

  .h-actions .add-asset-btn:not(.mobile-add-btn) {
    display: none;
  }
}
</style>
