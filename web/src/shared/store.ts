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
  [k: string]: unknown
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
})

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

    const value = currentPrice * qty
    const cost = costPrice * qty
    const totalPnl = value - cost + adjustment
    const dayPnl = open && yclose > 0 ? (currentPrice - yclose) * qty : 0
    const dayPnlRate = open && yclose > 0 ? ((currentPrice - yclose) / yclose) * 100 : 0
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
      dayPnl,
      dayPnlRate,
      totalPnlRate,
      session: String(quote.session || 'closed'),
      marketOpen: open,
    }
  })
})

const summary = computed(() => {
  const totalValue = rows.value.reduce((sum, row) => sum + row.value, 0)
  const totalPnl = rows.value.reduce((sum, row) => sum + row.totalPnl, 0)
  const todayPnl = rows.value.reduce((sum, row) => sum + row.dayPnl, 0)
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
  const codes = state.portfolio.map((item) => String(item.code || '')).filter(Boolean)
  if (!codes.length) {
    state.quotes = {}
    return
  }
  state.quotes = await api.post<Record<string, Quote>>('/api/prices/batch', { codes }, true)
}

async function loadRates() {
  state.rates = await api.get<Record<string, number>>('/api/rates', false)
}

async function refreshAll() {
  state.loading = true
  try {
    await Promise.all([loadMarketStatus(), loadPortfolio(), loadRates()])
    await loadQuotes()
  } finally {
    state.loading = false
  }
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
    loadPortfolio,
    loadQuotes,
    loadMarketStatus,
  }
}
