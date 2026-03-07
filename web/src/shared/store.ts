/**
 * 已废弃的旧 Web 共享 store。
 * 页面、布局和路由现在统一改走 ../stores/composables.ts。
 * 这个文件暂时保留，只作为历史兼容参考，不应该再新增职责。
 */
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
import { computeDisplayCostPrice } from './costBasis'
import { toNumber } from './format'

export type MarketCode = 'a' | 'hk' | 'us' | 'fund'
const ALL_SYNC_DOMAINS = [
  'portfolio',
  'cash_assets',
  'other_assets',
  'liabilities',
  'history',
  'overview_all',
  'rates',
] as const
type SyncDomain = typeof ALL_SYNC_DOMAINS[number]

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
  trading_day: boolean
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
  market_statuses?: Partial<Record<MarketCode, Partial<MarketStatus>>>
  market_status?: Partial<Record<MarketCode, boolean>>
  quote_policy?: Partial<QuotePolicy>
}

const MARKET_CODES: MarketCode[] = ['a', 'hk', 'us', 'fund']
const SYNC_VERSION_STORAGE_KEY = 'web_sync_versions_v1'
const STORE_CACHE_STORAGE_KEY = 'web_store_cache_v1'
const STORE_CACHE_STATIC_TTL_MS = 5 * 60_000
const STORE_CACHE_QUOTES_TTL_MS = 60_000
const AUTH_BOOTSTRAP_TIMEOUT_MS = 2500
const SYNC_BOOTSTRAP_STATIC_INCLUDE: SyncDomain[] = [...ALL_SYNC_DOMAINS]
const SYNC_BOOTSTRAP_QUOTE_INCLUDE: SyncDomain[] = ['portfolio', 'rates']
const DEFAULT_QUOTE_POLICY: QuotePolicy = {
  interval_open_sec: 5,
  interval_closed_sec: 120,
  interval_us_extended_sec: 10,
}

type StoreCachePayload = {
  userId: string
  savedAt: number
  quotesSavedAt?: number
  portfolio: PortfolioItem[]
  quotes: Record<string, Quote>
  rates: Record<string, number>
  marketStatus: Record<MarketCode, MarketStatus>
  allClosed: boolean
  quotePolicy: QuotePolicy
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

function normalizeUserId(user: User | null | undefined): string {
  const id = String(user?.id || '').trim()
  return id || 'guest'
}

function readStoreCacheRaw(): StoreCachePayload | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(STORE_CACHE_STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as StoreCachePayload
    if (!parsed || typeof parsed !== 'object') return null
    return parsed
  } catch {
    return null
  }
}

function clearStoreCache() {
  if (typeof window === 'undefined') return
  try {
    localStorage.removeItem(STORE_CACHE_STORAGE_KEY)
  } catch {
    // ignore storage errors
  }
}

const initialUser = readStoredUser<User>() || null
const state = reactive({
  bootstrapped: false,
  loading: false,
  token: readAccessToken(),
  refreshToken: readRefreshToken(),
  user: initialUser,
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
const bootstrapInflight = new Map<string, Promise<Set<SyncDomain>>>()
let autoRefreshConsumers = 0
let autoRefreshTimer: ReturnType<typeof setTimeout> | null = null

function activeUserId(): string {
  return normalizeUserId(state.user)
}

function hydrateStoreCache() {
  const cached = readStoreCacheRaw()
  if (!cached) return
  if (cached.userId !== activeUserId()) {
    clearStoreCache()
    return
  }

  const now = Date.now()
  const staticAge = now - Number(cached.savedAt || 0)
  if (!Number.isFinite(staticAge) || staticAge > STORE_CACHE_STATIC_TTL_MS) return

  state.portfolio = Array.isArray(cached.portfolio) ? cached.portfolio : []
  state.rates = cached.rates && typeof cached.rates === 'object' ? cached.rates : {}
  state.marketStatus = cached.marketStatus && typeof cached.marketStatus === 'object'
    ? cached.marketStatus
    : {} as Record<MarketCode, MarketStatus>
  state.allClosed = Boolean(cached.allClosed)
  if (cached.quotePolicy && typeof cached.quotePolicy === 'object') {
    state.quotePolicy = {
      interval_open_sec: normalizeInterval(
        cached.quotePolicy.interval_open_sec,
        DEFAULT_QUOTE_POLICY.interval_open_sec,
      ),
      interval_closed_sec: normalizeInterval(
        cached.quotePolicy.interval_closed_sec,
        DEFAULT_QUOTE_POLICY.interval_closed_sec,
      ),
      interval_us_extended_sec: normalizeInterval(
        cached.quotePolicy.interval_us_extended_sec,
        DEFAULT_QUOTE_POLICY.interval_us_extended_sec,
      ),
    }
  }

  const quotesAge = now - Number(cached.quotesSavedAt || 0)
  if (Number.isFinite(quotesAge) && quotesAge <= STORE_CACHE_QUOTES_TTL_MS) {
    state.quotes = cached.quotes && typeof cached.quotes === 'object' ? cached.quotes : {}
  }
}

function persistStoreCache(mode: 'static' | 'full' = 'full') {
  if (typeof window === 'undefined') return
  const prev = readStoreCacheRaw()
  const now = Date.now()
  const nextQuotes =
    mode === 'full'
      ? state.quotes
      : (Object.keys(state.quotes || {}).length ? state.quotes : (prev?.quotes || {}))
  const payload: StoreCachePayload = {
    userId: activeUserId(),
    savedAt: now,
    quotesSavedAt: mode === 'full' ? now : Number(prev?.quotesSavedAt || 0),
    portfolio: state.portfolio,
    quotes: nextQuotes,
    rates: state.rates,
    marketStatus: state.marketStatus,
    allClosed: state.allClosed,
    quotePolicy: state.quotePolicy,
  }
  try {
    localStorage.setItem(STORE_CACHE_STORAGE_KEY, JSON.stringify(payload))
  } catch {
    // ignore storage errors
  }
}

hydrateStoreCache()

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

function inferTradingDayFromReason(reason: string, open: boolean): boolean {
  if (open) return true
  const key = String(reason || '').toLowerCase()
  if (key === 'holiday_or_weekend') return false
  if (key === 'off_hours' || key === 'open_session') return true
  // "override" 在闭市时更接近“非交易日”语义（例如节假日强制休市）。
  if (key === 'override') return false
  return true
}

function normalizeMarketStatus(
  detail: Partial<MarketStatus> | undefined,
  openFallback: boolean,
): MarketStatus {
  const hasDetail = !!detail && Object.keys(detail).length > 0
  const open = typeof detail?.open === 'boolean' ? detail.open : openFallback
  const reason = String(detail?.reason || inferReason(open)).trim().toLowerCase() || inferReason(open)
  const tradingDay = typeof detail?.trading_day === 'boolean'
    ? detail.trading_day
    : hasDetail
      ? inferTradingDayFromReason(reason, open)
      : open
  return {
    open,
    reason,
    trading_day: tradingDay,
  }
}

function applyMarketStatuses(
  details?: Partial<Record<MarketCode, Partial<MarketStatus>>>,
  booleans?: Partial<Record<MarketCode, boolean>>,
) {
  if (!details && !booleans) return
  const next = {} as Record<MarketCode, MarketStatus>
  for (const m of MARKET_CODES) {
    next[m] = normalizeMarketStatus(details?.[m], Boolean(booleans?.[m]))
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
  for (const domain of ALL_SYNC_DOMAINS) {
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

function firstPositiveNumber(...values: unknown[]): number {
  for (const value of values) {
    const n = Number(value)
    if (Number.isFinite(n) && n > 0) {
      return n
    }
  }
  // Missing quote fallback must stay non-negative; negative cost should not become a market price.
  return 0
}

function isNavUpdatePendingAsset(item: PortfolioItem): boolean {
  const code = String(item.code || '').trim().toLowerCase()
  return code.startsWith('f_') || code.startsWith('ft_')
}

const rows = computed(() => {
  return state.portfolio.map((item) => {
    const quote = state.quotes[item.code] || {}
    const qty = toNumber(item.qty)
    const rawCostPrice = toNumber(item.price)
    const yclose = toNumber(quote.yclose)
    const currentPrice = firstPositiveNumber(
      quote.price,
      quote.regular_price,
      quote.premarket_price,
      quote.after_hours_price,
      yclose,
      rawCostPrice,
    )
    const adjustment = toNumber(item.adjustment)
    const market = inferMarket(item)
    const marketStatus = state.marketStatus[market]
    const open = Boolean(marketStatus?.open)
    const marketTradingDay = Boolean(marketStatus?.trading_day)
    const navUpdatePending = isNavUpdatePendingAsset(item)
    const effectiveSession = normalizeSession(quote.effective_session ?? quote.session)
    const usExtendedActive =
      market === 'us' &&
      (Boolean(quote.extended_active) || effectiveSession === 'pre' || effectiveSession === 'post')
    const dayPnlDisplayEnabled = !navUpdatePending && currentPrice > 0 && yclose > 0
    const dayPnlAggregateEnabled = dayPnlDisplayEnabled && (marketTradingDay || usExtendedActive)

    const value = currentPrice * qty
    const cost = rawCostPrice * qty
    const displayCostPrice = computeDisplayCostPrice(rawCostPrice, qty, adjustment)
    const totalPnl = value - cost + adjustment
    const dayPnlDisplay = dayPnlDisplayEnabled ? (currentPrice - yclose) * qty : 0
    const dayPnlRateDisplay = dayPnlDisplayEnabled ? ((currentPrice - yclose) / yclose) * 100 : 0
    const dayPnlAggregate = dayPnlAggregateEnabled ? dayPnlDisplay : 0
    const dayPnlRateAggregate = dayPnlAggregateEnabled ? dayPnlRateDisplay : 0
    const totalPnlRate = Math.abs(cost) > 0 ? (totalPnl / Math.abs(cost)) * 100 : 0

    return {
      ...item,
      market,
      qty,
      costPrice: rawCostPrice,
      rawCostPrice,
      displayCostPrice,
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
      marketTradingDay,
      marketStatusReason: marketStatus?.reason || '',
      usExtendedActive,
      navUpdatePending,
      dayPnlDisplayEnabled,
      dayPnlAggregateEnabled,
    }
  })
})

const summary = computed(() => {
  const totalValue = rows.value.reduce((sum, row) => sum + row.value, 0)
  const totalPnl = rows.value.reduce((sum, row) => sum + row.totalPnl, 0)
  const todayPnl = rows.value.reduce((sum, row) => sum + row.dayPnlAggregate, 0)
  const totalCostAbs = rows.value.reduce((sum, row) => sum + Math.abs(row.costPrice * row.qty), 0)
  return {
    totalValue,
    totalPnl,
    todayPnl,
    totalRate: totalCostAbs > 0 ? (totalPnl / totalCostAbs) * 100 : 0,
  }
})

async function bootstrap() {
  if (state.bootstrapped) return
  state.bootstrapped = true
  if (!state.token || !state.refreshToken) return
  let timeoutId: ReturnType<typeof setTimeout> | null = null
  try {
    const timeoutPromise = new Promise<never>((_, reject) => {
      timeoutId = setTimeout(() => reject(new Error('AUTH_BOOTSTRAP_TIMEOUT')), AUTH_BOOTSTRAP_TIMEOUT_MS)
    })
    const me = await Promise.race([api.get<User>('/api/auth/me', true), timeoutPromise])
    if (timeoutId) clearTimeout(timeoutId)
    state.user = me
    persistUser(me)
  } catch {
    if (timeoutId) clearTimeout(timeoutId)
    clearAuthState()
  }
}

function clearAuthState() {
  clearAuth()
  clearStoreCache()
  state.token = ''
  state.refreshToken = ''
  state.user = null
  state.portfolio = []
  state.quotes = {}
  state.marketStatus = {} as Record<MarketCode, MarketStatus>
  state.allClosed = false
  state.rates = {}
  state.quotePolicy = { ...DEFAULT_QUOTE_POLICY }
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
  const payload = await api.get<{ markets?: Partial<Record<MarketCode, Partial<MarketStatus>>>; all_closed?: boolean }>(
    '/api/market/status',
    false,
  )
  applyMarketStatuses(payload.markets)
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

function bootstrapIncludeKey(include: SyncDomain[]): string {
  return [...new Set(include)].sort().join(',')
}

function isSyncDomain(value: string): value is SyncDomain {
  return (ALL_SYNC_DOMAINS as readonly string[]).includes(value)
}

async function loadBootstrap(include: SyncDomain[] = SYNC_BOOTSTRAP_QUOTE_INCLUDE): Promise<Set<SyncDomain>> {
  const includeKey = bootstrapIncludeKey(include)
  const inflight = bootstrapInflight.get(includeKey)
  if (inflight) {
    return inflight
  }

  const request = (async () => {
    const clientVersions = include.reduce<Partial<Record<SyncDomain, string>>>((acc, domain) => {
      acc[domain] = state.syncVersions[domain] || ''
      return acc
    }, {})
    const payload = await api.post<BootstrapPayload>(
      '/api/sync/bootstrap',
      {
        include,
        client_versions: clientVersions,
      },
      true,
    )

    applyBootstrapVersions(payload.versions)
    applyMarketStatuses(payload.market_statuses, payload.market_status)
    applyQuotePolicy(payload.quote_policy)

    const changed = new Set(
      (payload.changed || [])
        .map((x) => String(x))
        .filter((x): x is SyncDomain => isSyncDomain(x)),
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
  })()

  bootstrapInflight.set(includeKey, request)
  try {
    return await request
  } finally {
    bootstrapInflight.delete(includeKey)
  }
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
    const changed = await loadBootstrap(SYNC_BOOTSTRAP_QUOTE_INCLUDE)
    if (!state.portfolio.length && !changed.has('portfolio')) {
      await loadPortfolio()
    }
    if (!Object.keys(state.rates).length && !changed.has('rates')) {
      await loadRates()
    }
  } catch {
    await loadMarketStatus()
  }

  await loadQuotes()
  persistStoreCache('full')
  scheduleAutoRefresh()
}

function startAutoRefresh() {
  autoRefreshConsumers += 1
  if (autoRefreshConsumers === 1) {
    scheduleAutoRefresh(800)
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
        const changed = await loadBootstrap(SYNC_BOOTSTRAP_STATIC_INCLUDE)
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
      persistStoreCache('full')
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
    const changed = await loadBootstrap(SYNC_BOOTSTRAP_STATIC_INCLUDE)
    if (!state.portfolio.length && !changed.has('portfolio')) {
      await loadPortfolio()
    }
    if (!Object.keys(state.rates).length && !changed.has('rates')) {
      await loadRates()
    }
  } catch {
    await Promise.all([loadPortfolio(), loadRates(), loadMarketStatus()])
  }
  persistStoreCache('static')
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
