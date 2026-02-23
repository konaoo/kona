import { computed, reactive } from 'vue'
import { api } from './http'
import {
  clearAuth,
  persistAuth,
  persistUser,
  readAccessToken,
  readRefreshToken,
  readStoredUser,
} from './auth'
import { toNumber } from './format'

export type MarketCode = 'a' | 'hk' | 'us' | 'fund'
type SyncDomain = 'portfolio' | 'rates'

type User = {
  id?: string
  username?: string
  nickname?: string
  is_admin?: number | boolean
  [k: string]: unknown
}

type PortfolioItem = {
  code: string
  name?: string
  qty?: number
  price?: number
  curr?: string
  asset_type?: string
  adjustment?: number
  [k: string]: unknown
}

type MarketStatus = {
  open: boolean
  reason: string
}

type Quote = {
  price?: number
  yclose?: number
  session?: string
  effective_session?: string
  extended_active?: boolean
  [k: string]: unknown
}

type QuotePolicy = {
  interval_open_sec: number
  interval_closed_sec: number
  interval_us_extended_sec: number
}

type BootstrapPayload = {
  versions?: Partial<Record<string, string>>
  changed?: string[]
  data?: Record<string, unknown>
  market_status?: Partial<Record<MarketCode, boolean>>
  quote_policy?: Partial<QuotePolicy>
}

const MARKET_CODES: MarketCode[] = ['a', 'hk', 'us', 'fund']
const SYNC_VERSION_STORAGE_KEY = 'web_sync_versions_v1'
const DEFAULT_QUOTE_POLICY: QuotePolicy = {
  interval_open_sec: 5,
  interval_closed_sec: 120,
  interval_us_extended_sec: 10,
}

function readSyncVersions(): Partial<Record<SyncDomain, string>> {
  if (typeof window === 'undefined') return {}
  try {
    const raw = localStorage.getItem(SYNC_VERSION_STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as Partial<Record<SyncDomain, string>>
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

function persistSyncVersions(versions: Partial<Record<SyncDomain, string>>) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(SYNC_VERSION_STORAGE_KEY, JSON.stringify(versions))
  } catch {
    // ignore storage errors
  }
}

const state = reactive({
  bootstrapped: false,
  loading: false,
  token: readAccessToken(),
  refreshToken: readRefreshToken(),
  user: readStoredUser<User>() || null,
  authError: '',
  portfolio: [] as PortfolioItem[],
  quotes: {} as Record<string, Quote>,
  marketStatus: {} as Record<MarketCode, MarketStatus>,
  allClosed: false,
  rates: {} as Record<string, number>,
  quotePolicy: { ...DEFAULT_QUOTE_POLICY } as QuotePolicy,
  syncVersions: readSyncVersions() as Partial<Record<SyncDomain, string>>,
})

let refreshAllInflight: Promise<void> | null = null
let quotesInflight: Promise<void> | null = null
let autoRefreshConsumers = 0
let autoRefreshTimer: ReturnType<typeof setTimeout> | null = null

function inferMarket(item: PortfolioItem): MarketCode {
  const kind = String(item.asset_type || '').toLowerCase()
  if (kind === 'hk') return 'hk'
  if (kind === 'us') return 'us'
  if (kind === 'fund') return 'fund'
  if (kind === 'a') return 'a'
  const code = String(item.code || '').toLowerCase()
  if (code.startsWith('hk')) return 'hk'
  if (code.startsWith('gb_') || /^[a-z][a-z.\-]*$/i.test(code)) return 'us'
  if (code.startsWith('f_') || code.startsWith('ft_')) return 'fund'
  return 'a'
}

function inferReason(open: boolean): string {
  return open ? 'open_session' : 'off_hours'
}

function applyMarketStatusBooleans(raw?: Partial<Record<MarketCode, boolean>>) {
  if (!raw) return
  const next = {} as Record<MarketCode, MarketStatus>
  for (const m of MARKET_CODES) {
    const open = Boolean(raw[m])
    next[m] = { open, reason: inferReason(open) }
  }
  state.marketStatus = next
  state.allClosed = MARKET_CODES.every((m) => !next[m]?.open)
}

function normalizeInterval(sec: unknown, fallback: number): number {
  const n = Number(sec)
  if (!Number.isFinite(n) || n <= 0) return fallback
  return Math.round(n)
}

function applyQuotePolicy(policy?: Partial<QuotePolicy>) {
  if (!policy) return
  state.quotePolicy = {
    interval_open_sec: normalizeInterval(
      policy.interval_open_sec,
      state.quotePolicy.interval_open_sec || DEFAULT_QUOTE_POLICY.interval_open_sec,
    ),
    interval_closed_sec: normalizeInterval(
      policy.interval_closed_sec,
      state.quotePolicy.interval_closed_sec || DEFAULT_QUOTE_POLICY.interval_closed_sec,
    ),
    interval_us_extended_sec: normalizeInterval(
      policy.interval_us_extended_sec,
      state.quotePolicy.interval_us_extended_sec || DEFAULT_QUOTE_POLICY.interval_us_extended_sec,
    ),
  }
}

function applyBootstrapVersions(versions?: Partial<Record<string, string>>) {
  if (!versions) return
  let dirty = false
  for (const domain of ['portfolio', 'rates'] as SyncDomain[]) {
    const next = String(versions[domain] || '').trim()
    if (!next) continue
    if (state.syncVersions[domain] !== next) {
      state.syncVersions[domain] = next
      dirty = true
    }
  }
  if (dirty) {
    persistSyncVersions(state.syncVersions)
  }
}

function normalizeSession(raw: unknown): string {
  const text = String(raw || '').trim().toLowerCase()
  if (text === 'pre' || text === 'post' || text === 'regular') return text
  return 'closed'
}

const rows = computed(() => {
  return state.portfolio.map((item) => {
    const quote = state.quotes[item.code] || {}
    const qty = toNumber(item.qty)
    const costPrice = toNumber(item.price)
    const currentPrice = toNumber(quote.price, costPrice)
    const yclose = toNumber(quote.yclose)
    const adjustment = toNumber(item.adjustment)
    const market = inferMarket(item)
    const open = Boolean(state.marketStatus[market]?.open)
    const effectiveSession = normalizeSession(quote.effective_session ?? quote.session)
    const usExtendedActive =
      market === 'us' &&
      (Boolean(quote.extended_active) || effectiveSession === 'pre' || effectiveSession === 'post')
    const dayPnlDisplayEnabled = currentPrice > 0 && yclose > 0
    const dayPnlAggregateEnabled = dayPnlDisplayEnabled && (open || usExtendedActive)

    const value = currentPrice * qty
    const cost = costPrice * qty
    const totalPnl = value - cost + adjustment
    const dayPnlDisplay = dayPnlDisplayEnabled ? (currentPrice - yclose) * qty : 0
    const dayPnlRateDisplay = dayPnlDisplayEnabled ? ((currentPrice - yclose) / yclose) * 100 : 0
    const dayPnlAggregate = dayPnlAggregateEnabled ? dayPnlDisplay : 0
    const dayPnlRateAggregate = dayPnlAggregateEnabled ? dayPnlRateDisplay : 0
    const totalPnlRate = cost > 0 ? (totalPnl / cost) * 100 : 0

    return {
      ...item,
      market,
      qty,
      costPrice,
      currentPrice,
      yclose,
      value,
      totalPnl,
      dayPnl: dayPnlDisplay,
      dayPnlRate: dayPnlRateDisplay,
      dayPnlDisplay,
      dayPnlRateDisplay,
      dayPnlAggregate,
      dayPnlRateAggregate,
      totalPnlRate,
      session: effectiveSession,
      marketOpen: open,
      usExtendedActive,
      dayPnlDisplayEnabled,
      dayPnlAggregateEnabled,
    }
  })
})

const summary = computed(() => {
  const totalValue = rows.value.reduce((sum, row) => sum + row.value, 0)
  const totalPnl = rows.value.reduce((sum, row) => sum + row.totalPnl, 0)
  const todayPnl = rows.value.reduce((sum, row) => sum + row.dayPnlAggregate, 0)
  const totalCost = rows.value.reduce((sum, row) => sum + row.costPrice * row.qty, 0)
  return {
    totalValue,
    totalPnl,
    todayPnl,
    totalRate: totalCost > 0 ? (totalPnl / totalCost) * 100 : 0,
  }
})

async function bootstrap() {
  if (state.bootstrapped) return
  state.bootstrapped = true
  if (!state.token || !state.refreshToken) return
  try {
    const me = await api.get<User>('/api/auth/me', true)
    state.user = me
    persistUser(me)
  } catch {
    clearAuthState()
  }
}

function clearAuthState() {
  clearAuth()
  state.token = ''
  state.refreshToken = ''
  state.user = null
}

async function login(username: string, password: string) {
  state.authError = ''
  const payload = await api.post<Record<string, unknown>>('/api/auth/login', {
    username,
    password,
  }, false)
  const accessToken = String(payload.access_token || '')
  const refreshToken = String(payload.refresh_token || '')
  if (!accessToken || !refreshToken) {
    throw new Error('登录返回缺少 token')
  }
  state.token = accessToken
  state.refreshToken = refreshToken
  state.user = (payload.user || null) as User | null
  persistAuth(accessToken, refreshToken, state.user)
}

async function register(username: string, password: string, inviteCode: string) {
  const payload = await api.post<Record<string, unknown>>('/api/auth/register', {
    username,
    password,
    invite_code: inviteCode,
  }, false)
  const accessToken = String(payload.access_token || '')
  const refreshToken = String(payload.refresh_token || '')
  if (!accessToken || !refreshToken) {
    throw new Error('注册返回缺少 token')
  }
  state.token = accessToken
  state.refreshToken = refreshToken
  state.user = (payload.user || null) as User | null
  persistAuth(accessToken, refreshToken, state.user)
}

async function logout() {
  try {
    await api.post('/api/auth/logout', { refresh_token: state.refreshToken }, true)
  } catch {
    // ignore logout errors
  } finally {
    clearAuthState()
  }
}

async function loadMarketStatus() {
  const payload = await api.get<{ markets?: Record<MarketCode, MarketStatus>; all_closed?: boolean }>('/api/market/status', false)
  state.marketStatus = payload.markets || ({} as Record<MarketCode, MarketStatus>)
  state.allClosed = Boolean(payload.all_closed)
}

async function loadPortfolio() {
  const items = await api.get<PortfolioItem[]>('/api/portfolio?type=all', true)
  state.portfolio = Array.isArray(items) ? items : []
}

async function loadQuotes() {
  if (quotesInflight) {
    return quotesInflight
  }
  quotesInflight = (async () => {
    const codes = state.portfolio.map((item) => String(item.code || '')).filter(Boolean)
    if (!codes.length) {
      state.quotes = {}
      return
    }
    state.quotes = await api.post<Record<string, Quote>>('/api/prices/batch', { codes }, true)
  })()
  try {
    await quotesInflight
  } finally {
    quotesInflight = null
  }
}

async function loadBootstrap(include: SyncDomain[] = ['portfolio', 'rates']): Promise<Set<SyncDomain>> {
  const payload = await api.post<BootstrapPayload>(
    '/api/sync/bootstrap',
    {
      include,
      client_versions: {
        portfolio: state.syncVersions.portfolio || '',
        rates: state.syncVersions.rates || '',
      },
    },
    true,
  )

  applyBootstrapVersions(payload.versions)
  applyMarketStatusBooleans(payload.market_status)
  applyQuotePolicy(payload.quote_policy)

  const changed = new Set(
    (payload.changed || [])
      .map((x) => String(x))
      .filter((x): x is SyncDomain => x === 'portfolio' || x === 'rates'),
  )

  const data = payload.data || {}
  if (Object.prototype.hasOwnProperty.call(data, 'portfolio')) {
    const portfolio = data.portfolio
    state.portfolio = Array.isArray(portfolio) ? (portfolio as PortfolioItem[]) : []
  }
  if (Object.prototype.hasOwnProperty.call(data, 'rates')) {
    const rates = data.rates as Record<string, unknown>
    const nextRates: Record<string, number> = {}
    if (rates && typeof rates === 'object') {
      for (const [k, v] of Object.entries(rates)) {
        nextRates[k] = toNumber(v, 1)
      }
    }
    state.rates = nextRates
  }

  return changed
}

async function loadRates() {
  state.rates = await api.get<Record<string, number>>('/api/rates', false)
}

function hasAnyOpenMarket(): boolean {
  return MARKET_CODES.some((m) => Boolean(state.marketStatus[m]?.open))
}

function hasUsExtendedActive(): boolean {
  for (const item of state.portfolio) {
    if (inferMarket(item) !== 'us') continue
    const quote = state.quotes[item.code] || {}
    const effectiveSession = normalizeSession(quote.effective_session ?? quote.session)
    if (Boolean(quote.extended_active) || effectiveSession === 'pre' || effectiveSession === 'post') {
      return true
    }
  }
  return false
}

function nextQuoteIntervalMs(): number {
  const policy = state.quotePolicy
  const sec = hasAnyOpenMarket()
    ? policy.interval_open_sec
    : hasUsExtendedActive()
      ? policy.interval_us_extended_sec
      : policy.interval_closed_sec
  return Math.max(1, sec) * 1000
}

function clearAutoRefreshTimer() {
  if (!autoRefreshTimer) return
  clearTimeout(autoRefreshTimer)
  autoRefreshTimer = null
}

function scheduleAutoRefresh(delayMs?: number) {
  clearAutoRefreshTimer()
  if (autoRefreshConsumers <= 0) return
  autoRefreshTimer = setTimeout(() => {
    void refreshQuotesOnly()
  }, Math.max(0, delayMs ?? nextQuoteIntervalMs()))
}

async function refreshQuotesOnly() {
  try {
    const changed = await loadBootstrap(['portfolio', 'rates'])
    if (changed.has('portfolio') && !state.portfolio.length) {
      await loadPortfolio()
    }
    if (changed.has('rates') && !Object.keys(state.rates).length) {
      await loadRates()
    }
  } catch {
    await loadMarketStatus()
  }

  await loadQuotes()
  scheduleAutoRefresh()
}

function startAutoRefresh() {
  autoRefreshConsumers += 1
  if (autoRefreshConsumers === 1) {
    scheduleAutoRefresh(0)
  }
}

function stopAutoRefresh() {
  autoRefreshConsumers = Math.max(0, autoRefreshConsumers - 1)
  if (autoRefreshConsumers === 0) {
    clearAutoRefreshTimer()
  }
}

async function refreshAll() {
  if (refreshAllInflight) {
    return refreshAllInflight
  }
  refreshAllInflight = (async () => {
    state.loading = true
    try {
      try {
        const changed = await loadBootstrap(['portfolio', 'rates'])
        if (!state.portfolio.length && !changed.has('portfolio')) {
          await loadPortfolio()
        }
        if (!Object.keys(state.rates).length && !changed.has('rates')) {
          await loadRates()
        }
      } catch {
        await Promise.all([loadMarketStatus(), loadPortfolio(), loadRates()])
      }
      await loadQuotes()
    } finally {
      state.loading = false
    }
  })()
  try {
    await refreshAllInflight
  } finally {
    refreshAllInflight = null
  }
}

function invalidateSyncVersion(domain?: SyncDomain) {
  if (!domain) {
    for (const key of Object.keys(state.syncVersions) as SyncDomain[]) {
      delete state.syncVersions[key]
    }
    persistSyncVersions(state.syncVersions)
    return
  }
  if (state.syncVersions[domain]) {
    delete state.syncVersions[domain]
    persistSyncVersions(state.syncVersions)
  }
}

function markPortfolioDirty() {
  invalidateSyncVersion('portfolio')
}

function markRatesDirty() {
  invalidateSyncVersion('rates')
}

async function refreshStaticOnly() {
  try {
    const changed = await loadBootstrap(['portfolio', 'rates'])
    if (changed.has('portfolio') && !state.portfolio.length) {
      await loadPortfolio()
    }
    if (changed.has('rates') && !Object.keys(state.rates).length) {
      await loadRates()
    }
  } catch {
    await Promise.all([loadPortfolio(), loadRates(), loadMarketStatus()])
  }
}

async function refreshAllForce() {
  invalidateSyncVersion()
  await refreshAll()
}

export function useKonaStore() {
  return {
    state,
    rows,
    summary,
    isAuthenticated: computed(() => Boolean(state.token)),
    isAdmin: computed(() => Boolean(state.user && Number(state.user.is_admin || 0) === 1)),
    bootstrap,
    login,
    register,
    logout,
    refreshAll,
    refreshAllForce,
    refreshStaticOnly,
    refreshQuotesOnly,
    startAutoRefresh,
    stopAutoRefresh,
    markPortfolioDirty,
    markRatesDirty,
    loadPortfolio,
    loadQuotes,
    loadMarketStatus,
  }
}
