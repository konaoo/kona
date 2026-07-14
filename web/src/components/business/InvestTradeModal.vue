<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { api } from '@/shared/http'
import { toNumber } from '@/shared/format'
import { resolveErrorMessage } from '@/shared/errorText'
import { useLedgerScopeStore } from '@/stores/ledgerScope'
import { usePortfolioStore } from '@/stores/portfolio'

type TradeAction = 'add' | 'buy' | 'sell' | 'adjust'
type AdjustType = 'costPrice' | 'quantity' | 'dividend' | 'fee'

const props = defineProps<{
  show: boolean
  asset?: Record<string, any> | null
  mode?: TradeAction
}>()

const emit = defineEmits<{
  (e: 'update:show', val: boolean): void
  (e: 'success'): void
}>()

const internalShow = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const ledgerStore = useLedgerScopeStore()
const isEditMode = computed(() => Boolean(props.asset))
const actionMode = ref<Exclude<TradeAction, 'add'>>('buy')
const isAnimating = ref(false)
const modalVisible = ref(false)
const isSubmitting = ref(false)
const confirmBtnText = ref('确认添加')
const confirmBtnStyle = ref<Record<string, string>>({})

const query = ref('')
const searchResults = ref<any[]>([])
const searchError = ref('')
const isDropdownOpen = ref(false)
const selectedStock = ref<any>(null)
const price = ref('')
const qty = ref('')
const amount = ref('')
const adjustType = ref<AdjustType>('costPrice')
const adjustValue = ref('')
const note = ref('')
let searchTimeout: ReturnType<typeof setTimeout> | null = null

const adjustTypeOptions: Array<{ value: AdjustType; label: string }> = [
  { value: 'costPrice', label: '成本价' },
  { value: 'quantity', label: '数量' },
  { value: 'dividend', label: '分红' },
  { value: 'fee', label: '手续费' },
]

const marketMeta: Record<string, any> = {
  '港股': { color: '#e06b3a', bg: 'rgba(224,107,58,0.12)', label: '港股' },
  '美股': { color: '#5b8def', bg: 'rgba(91,141,239,0.12)', label: '美股' },
  'A股': { color: '#3ecf82', bg: 'rgba(62,207,130,0.12)', label: 'A股' },
  '基金': { color: '#b57adb', bg: 'rgba(181,122,219,0.12)', label: '基金' }
}

const accounts = ref<any[]>([])
const selectedAccount = ref<any>(null)

async function loadAccounts() {
  console.log('[DEBUG Modal] loadAccounts called')
  const portfolioStore = usePortfolioStore()
  
  // 优先从缓存获取
  let realAccounts = portfolioStore.cashAssets && portfolioStore.cashAssets.length > 0
    ? portfolioStore.cashAssets
    : []

  // 如果缓存为空，则异步发起一次加载
  if (realAccounts.length === 0) {
    try {
      console.log('[DEBUG Modal] Cache empty, loading from API...')
      await portfolioStore.loadCashAssets()
      realAccounts = portfolioStore.cashAssets || []
    } catch (err) {
      console.error('[DEBUG Modal] Failed to load accounts via store:', err)
    }
  }

  // 无论如何都要有兜底的外部资金选项，防止下拉框完全为空
  accounts.value = [
    ...realAccounts,
    { id: -999, name: '外部资金/初始转入', amount: null, curr: '', icon: '↗', iconBg: 'rgba(91,141,239,0.12)' }
  ]

  if (accounts.value.length > 0 && (!selectedAccount.value || !accounts.value.find(a => a.id === selectedAccount.value?.id))) {
    selectedAccount.value = accounts.value[0]
  }
  console.log('[DEBUG Modal] loadAccounts finished, accounts count:', accounts.value.length)
}
const isAcctDropdownOpen = ref(false)
const isCreateSheetOpen = ref(false)
const createAcctType = ref('cash')
const createCurr = ref('CNY')
const isCurrDropdownOpen = ref(false)
const newAcctName = ref('')
const newAcctBalance = ref('')
const nameErr = ref('')
const amountErr = ref('')

const currencies = [
  { code: 'CNY', name: '人民币', flag: '🇨🇳' },
  { code: 'USD', name: '美元', flag: '🇺🇸' },
  { code: 'HKD', name: '港币', flag: '🇭🇰' },
]

const selectCurrInfo = computed(() => currencies.find(c => c.code === createCurr.value) || currencies[0]!)
const currentHoldingQty = computed(() => toNumber(selectedStock.value?.holdingQty))
const currentRawCostPrice = computed(() => toNumber(selectedStock.value?.rawCostPrice ?? selectedStock.value?.price))
const currentAdjustment = computed(() => toNumber(selectedStock.value?.adjustment))
const isFundAdjustTarget = computed(() => {
  const marketType = String(selectedStock.value?.market_type || '').toLowerCase()
  const assetType = String(selectedStock.value?.asset_type || '').toLowerCase()
  return marketType === 'fund' || assetType === 'fund'
})
// removed unused currentDisplayCostPrice definition
const adjustValueStep = computed(() => {
  if (adjustType.value === 'quantity') return isFundAdjustTarget.value ? '0.0001' : '0.01'
  if (adjustType.value === 'costPrice') return (selectedStock.value?.digits || 2) >= 4 ? '0.0001' : '0.01'
  return '0.01'
})
const adjustInputLabel = computed(() => {
  if (adjustType.value === 'costPrice') return '目标成本价'
  if (adjustType.value === 'quantity') return '目标数量'
  if (adjustType.value === 'dividend') return '分红金额'
  if (adjustType.value === 'fee') return '手续费金额'
  return '调整金额'
})
const sheetTitle = computed(() => {
  if (!isEditMode.value) return '添加资产'
  if (actionMode.value === 'sell') return '卖出'
  if (actionMode.value === 'adjust') return '调整'
  return '买入'
})
function setConfirmButtonIdle() {
  if (!isEditMode.value) {
    confirmBtnText.value = '确认添加'
    confirmBtnStyle.value = {}
    return
  }
  if (actionMode.value === 'sell') {
    confirmBtnText.value = '确认卖出'
  } else if (actionMode.value === 'adjust') {
    confirmBtnText.value = '保存调整'
  } else {
    confirmBtnText.value = '确认买入'
  }
  confirmBtnStyle.value = {}
}

function formatInputValue(value: unknown, digits = 2): string {
  const amount = toNumber(value)
  return amount > 0 || amount < 0 ? amount.toFixed(digits) : ''
}

function normalizeAsset(item: Record<string, any>) {
  const market = String(item.market_type || item.market || 'a').toLowerCase()
  const assetType = String(item.asset_type || market || 'stock').toLowerCase()
  const marketType = market === 'stock' ? 'a' : market
  const isFund = marketType === 'fund' || assetType === 'fund'
  const currentPrice = toNumber(item.currentPrice ?? item.price)
  const rawCostPrice = toNumber(item.rawCostPrice ?? item.price ?? item.costPrice)
  return {
    ...item,
    code: String(item.code || ''),
    name: String(item.name || item.code || ''),
    market_type: marketType,
    asset_type: assetType,
    currency: String(item.currency || item.curr || 'CNY'),
    curr: String(item.curr || item.currency || 'CNY'),
    holdingQty: toNumber(item.qty),
    adjustment: toNumber(item.adjustment),
    rawCostPrice,
    price: currentPrice > 0 ? currentPrice : rawCostPrice,
    change: toNumber(item.change),
    change_pct: toNumber(item.change_pct ?? item.changePct),
    digits: isFund ? 4 : 2,
  }
}

function resolveSelectedLedgerId(): number | null {
  const rawLedgerId = selectedStock.value?.ledger_id ?? ledgerStore.currentLedgerId
  if (rawLedgerId == null || rawLedgerId === '') return null
  const ledgerId = Number(rawLedgerId)
  return Number.isFinite(ledgerId) ? ledgerId : null
}

function initializeForAsset(item: Record<string, any> | null | undefined) {
  if (!item) return
  selectedStock.value = normalizeAsset(item)
  query.value = ''
  isDropdownOpen.value = false
  applyModeDefaults()
}

function applyModeDefaults() {
  const asset = selectedStock.value
  if (!asset) {
    price.value = ''
    qty.value = ''
    amount.value = ''
    adjustType.value = 'costPrice'
    adjustValue.value = ''
    note.value = ''
    return
  }

  const digits = asset.digits || 2
  if (isEditMode.value && actionMode.value === 'adjust') {
    price.value = ''
    qty.value = ''
    amount.value = ''
    adjustType.value = 'costPrice'
    syncAdjustInputDefault()
    note.value = ''
    return
  }

  price.value = formatInputValue(asset.price, digits)
  qty.value = ''
  amount.value = ''
  adjustValue.value = ''
  note.value = ''
}

function resetForm() {
  query.value = ''
  searchResults.value = []
  searchError.value = ''
  isDropdownOpen.value = false
  selectedStock.value = null
  price.value = ''
  qty.value = ''
  amount.value = ''
  adjustType.value = 'costPrice'
  adjustValue.value = ''
  note.value = ''
  isAcctDropdownOpen.value = false
  isCreateSheetOpen.value = false
  isCurrDropdownOpen.value = false
  isSubmitting.value = false
  actionMode.value = 'buy'
  setConfirmButtonIdle()
}

watch(() => props.show, (val) => {
  console.log('[DEBUG Modal] watch props.show triggered, val:', val)
  if (val) {
    loadAccounts()
    modalVisible.value = true
    isAnimating.value = true
    setTimeout(() => { isAnimating.value = false }, 250)
    actionMode.value = props.mode && props.mode !== 'add' ? props.mode : 'buy'
    setConfirmButtonIdle()
    if (props.asset) {
      initializeForAsset(props.asset)
    } else {
      resetForm()
      setConfirmButtonIdle()
    }
  } else {
    isAnimating.value = true
    setTimeout(() => {
      modalVisible.value = false
      isAnimating.value = false
      resetForm()
    }, 200)
  }
})

watch(actionMode, () => {
  if (!props.show || !isEditMode.value) return
  searchError.value = ''
  applyModeDefaults()
  setConfirmButtonIdle()
})

watch(() => props.asset, (asset) => {
  if (!props.show || !asset) return
  initializeForAsset(asset)
})

watch(adjustType, () => {
  if (!props.show || !isEditMode.value || actionMode.value !== 'adjust') return
  syncAdjustInputDefault()
})

function formatAdjustInputValue(value: number, digits: number): string {
  if (!Number.isFinite(value)) return ''
  if (Math.abs(value) <= 1e-9) return '0'
  return value.toFixed(digits).replace(/\.?0+$/, '')
}

function syncAdjustInputDefault() {
  const holdingQty = currentHoldingQty.value
  if (adjustType.value === 'costPrice') {
    adjustValue.value = formatAdjustInputValue(currentRawCostPrice.value, selectedStock.value?.digits || 2)
    return
  }
  if (adjustType.value === 'quantity') {
    adjustValue.value = formatAdjustInputValue(holdingQty, isFundAdjustTarget.value ? 4 : 2)
    return
  }
  if (adjustType.value === 'dividend' || adjustType.value === 'fee') {
    adjustValue.value = ''
    return
  }
  adjustValue.value = formatAdjustInputValue(currentAdjustment.value, 2)
}

function resolveAdjustPayload():
  | { qty: number; price: number; adjustment: number }
  | { error: string } {
  const rawPrice = currentRawCostPrice.value
  const holdingQty = currentHoldingQty.value
  const currentAdj = currentAdjustment.value
  const parsedInput = parseFloat(adjustValue.value)

  if (!Number.isFinite(parsedInput)) {
    return { error: `请输入有效${adjustInputLabel.value}` }
  }

  if (adjustType.value === 'costPrice') {
    if (!holdingQty || holdingQty === 0) return { error: '当前持仓数量为 0，不能调整成本价' }
    if (!Number.isFinite(parsedInput)) return { error: '请输入有效成本价' }
    return {
      qty: holdingQty,
      price: parsedInput,
      adjustment: currentAdj,
    }
  }

  if (adjustType.value === 'quantity') {
    if (parsedInput === 0 || !Number.isFinite(parsedInput)) return { error: '目标数量不能为 0，清仓请用卖出或删除' }
    return {
      qty: parsedInput,
      price: rawPrice,
      adjustment: currentAdj,
    }
  }

  if (adjustType.value === 'dividend') {
    if (!holdingQty || holdingQty <= 0) return { error: '当前持仓数量无效，不能记录分红' }
    if (parsedInput <= 0) return { error: '分红金额必须大于 0' }
    return {
      qty: holdingQty,
      price: rawPrice,
      adjustment: currentAdj + parsedInput,
    }
  }

  if (adjustType.value === 'fee') {
    if (!holdingQty || holdingQty <= 0) return { error: '当前持仓数量无效，不能记录手续费' }
    if (parsedInput <= 0) return { error: '手续费金额必须大于 0' }
    return {
      qty: holdingQty,
      price: rawPrice,
      adjustment: currentAdj - parsedInput,
    }
  }

  return { error: '不支持的调整类型' }
}

function close() {
  if (isAnimating.value) return
  internalShow.value = false
}

const getMarketMeta = (market: string) => {
  const m = market?.toLowerCase()
  if (m === 'hk') return marketMeta['港股']
  if (m === 'us') return marketMeta['美股']
  if (m === 'fund') return marketMeta['基金']
  return marketMeta['A股']
}

const getMarketLabel = (market: string) => {
  const m = getMarketMeta(market)
  return m ? m.label : 'A股'
}

function formatDisplayCode(code: unknown): string {
  const raw = String(code || '').trim()
  if (!raw) return '--'
  if (raw === 'ft_LU1116320737') return 'BLK'

  let normalized = raw
  const lower = normalized.toLowerCase()
  if (lower.startsWith('gb_')) normalized = normalized.slice(3).toUpperCase()
  else if (lower.startsWith('f_')) normalized = normalized.slice(2)
  else if (lower.startsWith('ft_')) normalized = normalized.slice(3)
  else if (lower.startsWith('sh') || lower.startsWith('sz') || lower.startsWith('bj')) normalized = normalized.slice(2)

  if (normalized.toUpperCase().endsWith('.HK')) {
    normalized = normalized.slice(0, -3)
  }

  return normalized
}

function inferSearchMarket(item: Record<string, any>): string {
  const explicit = String(item.market_type || item.market || '').toLowerCase()
  if (explicit) return explicit

  const assetType = String(item.asset_type || '').toLowerCase()
  if (assetType === 'fund') return 'fund'

  const code = String(item.code || '').toLowerCase()
  if (code.startsWith('gb_')) return 'us'
  if (code.startsWith('sh') || code.startsWith('sz') || code.startsWith('bj')) return 'a'
  if (code.endsWith('.hk')) return 'hk'
  if (code.startsWith('f_') || code.startsWith('ft_')) return 'fund'
  return 'a'
}

function searchMarketLabel(item: Record<string, any>): string {
  const typeName = String(item.type_name || '').trim()
  if (typeName) return typeName
  return getMarketLabel(inferSearchMarket(item))
}

function searchDigits(item: Record<string, any>): number {
  return inferSearchMarket(item) === 'fund' || String(item.asset_type || '').toLowerCase() === 'fund' ? 4 : 2
}

function searchPrice(item: Record<string, any>): number | null {
  const candidates = [
    item.price,
    item.latest,
    item.latest_price,
    item.current_price,
    item.last_price,
    item.close,
  ]
  for (const candidate of candidates) {
    const value = toNumber(candidate)
    if (value > 0) return value
  }
  return null
}

function searchChangeAmount(item: Record<string, any>): number | null {
  const candidates = [item.change, item.amt, item.delta]
  for (const candidate of candidates) {
    if (candidate === null || candidate === undefined || candidate === '') continue
    const value = toNumber(candidate)
    if (Number.isFinite(value)) return value
  }
  return null
}

function searchChangePct(item: Record<string, any>): number | null {
  const directCandidates = [
    item.changePct,
    item.change_pct,
    item.chg,
    item.pct,
    item.change_percent,
  ]
  for (const candidate of directCandidates) {
    if (candidate === null || candidate === undefined || candidate === '') continue
    const value = toNumber(candidate)
    if (Number.isFinite(value)) return value
  }

  const amount = searchChangeAmount(item)
  const yclose = toNumber(item.yclose ?? item.pre_close ?? item.prev_close)
  if (amount !== null && yclose > 0) {
    return amount / yclose * 100
  }
  return null
}

function formatQuoteValue(value: number | null, digits = 2): string {
  if (value === null || !Number.isFinite(value)) return '--'
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  })
}

function formatSignedMove(value: number | null, digits = 2): string {
  if (value === null || !Number.isFinite(value)) return '--'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`
}

function moveTone(value: number | null): 'up' | 'down' | 'flat' {
  if (value === null || !Number.isFinite(value) || value === 0) return 'flat'
  return value > 0 ? 'up' : 'down'
}

const handleSearchInput = () => {
  searchError.value = ''
  const q = query.value.trim()
  if (!q) {
    searchResults.value = []
    isDropdownOpen.value = true
    return
  }

  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(async () => {
    try {
      const resp = await api.get(`/api/search?q=${encodeURIComponent(q)}`)
      searchResults.value = Array.isArray(resp) ? resp : []
      isDropdownOpen.value = true
    } catch (e) {
      console.error('Search failed', e)
    }
  }, 300)
}

const selectStock = (item: any) => {
  selectedStock.value = normalizeAsset(item)
  isDropdownOpen.value = false
  query.value = ''
  applyModeDefaults()
}

const clearSelection = () => {
  if (isEditMode.value) return
  selectedStock.value = null
  query.value = ''
  price.value = ''
  qty.value = ''
  amount.value = ''
}

const toggleAcct = () => { isAcctDropdownOpen.value = !isAcctDropdownOpen.value }
const selectAccount = (acct: any) => {
  selectedAccount.value = acct
  isAcctDropdownOpen.value = false
}
const selectAdjustType = (type: AdjustType) => {
  adjustType.value = type
}
const toggleCurr = () => { isCurrDropdownOpen.value = !isCurrDropdownOpen.value }

const openCreateSheet = () => {
  isAcctDropdownOpen.value = false
  isCreateSheetOpen.value = true
}

const closeCreateSheet = () => {
  isCreateSheetOpen.value = false
  isCurrDropdownOpen.value = false
  newAcctName.value = ''
  newAcctBalance.value = ''
  createAcctType.value = 'cash'
  createCurr.value = 'CNY'
  nameErr.value = ''
  amountErr.value = ''
}

const confirmCreateAcct = () => {
  let valid = true
  if (!newAcctName.value.trim()) { nameErr.value = '请输入账户名称'; valid = false } else { nameErr.value = '' }
  if (!newAcctBalance.value || Number(newAcctBalance.value) < 0) { amountErr.value = '请输入金额'; valid = false } else { amountErr.value = '' }
  if (!valid) return

  const typeIconMap: Record<string, string> = { cash: '💰', other: '📦', debt: '💳' }
  const typeBgMap: Record<string, string> = { cash: 'rgba(62,207,130,0.12)', other: 'rgba(91,141,239,0.12)', debt: 'rgba(240,90,85,0.12)' }
  const fmt = Number(newAcctBalance.value).toLocaleString('zh-CN', { maximumFractionDigits: 2 })
  const newAcct = {
    id: `acct_${Date.now()}`,
    name: newAcctName.value.trim(),
    amount: `${fmt} ${createCurr.value}`,
    icon: typeIconMap[createAcctType.value] || '💰',
    iconBg: typeBgMap[createAcctType.value] || 'rgba(62,207,130,0.12)',
  }

  accounts.value.push(newAcct)
  selectedAccount.value = newAcct
  closeCreateSheet()
}

const syncAmount = () => {
  const p = parseFloat(price.value) || 0
  const q = parseFloat(qty.value) || 0
  if (p > 0 && q > 0) {
    amount.value = (p * q).toFixed(2)
  } else {
    amount.value = ''
  }
}

const syncQty = () => {
  const p = parseFloat(price.value) || 0
  const a = parseFloat(amount.value) || 0
  if (p > 0 && a > 0) {
    qty.value = String(Math.floor(a / p))
  } else {
    qty.value = ''
  }
}

async function submitSuccess(label: string) {
  confirmBtnText.value = label
  confirmBtnStyle.value = { background: 'linear-gradient(135deg, #3ecf82 0%, #2db870 100%)' }
  setTimeout(() => {
    setConfirmButtonIdle()
    emit('success')
    close()
  }, 900)
}

function extractErrorMessage(error: any, fallback: string): string {
  return resolveErrorMessage(error, fallback)
}

async function handleConfirm() {
  if (!selectedStock.value) {
    searchError.value = '请先选择一个资产'
    return
  }

  isSubmitting.value = true
  searchError.value = ''

  try {
    const isExternal = (!selectedAccount.value || selectedAccount.value.id === -999)
    const cashId = isExternal ? null : selectedAccount.value.id

    if (!isEditMode.value) {
      const p = parseFloat(price.value)
      const q = parseFloat(qty.value)
      if (!Number.isFinite(p) || !Number.isFinite(q) || q === 0) {
        searchError.value = '价格和数量必须填入'
        return
      }
      if (!isExternal && (p <= 0 || q < 0)) {
        searchError.value = '从现金账户买入时，成本价和数量必须大于 0'
        return
      }

      if (isExternal) {
        const addPayload: Record<string, any> = {
          code: selectedStock.value.code,
          market: selectedStock.value.market_type || 'a',
          qty: q,
          price: p,
          name: selectedStock.value.name,
          curr: selectedStock.value.currency,
        }
        if (ledgerStore.currentLedgerId != null) {
          addPayload.ledger_id = ledgerStore.currentLedgerId
        }
        await api.post('/api/portfolio/add', addPayload)
      } else {
        await api.post('/api/portfolio/buy_with_cash', {
          code: selectedStock.value.code,
          name: selectedStock.value.name,
          price: p,
          qty: q,
          curr: selectedStock.value.currency,
          asset_type: selectedStock.value.asset_type || '',
          cash_asset_id: cashId
        })
      }
      await submitSuccess('✓ 已添加')
      return
    }

    if (actionMode.value === 'adjust') {
      const payload = resolveAdjustPayload()
      if ('error' in payload) {
        searchError.value = payload.error
        return
      }

      if (adjustType.value === 'dividend' || adjustType.value === 'fee') {
        const amountValue = parseFloat(adjustValue.value)
        const adjustmentPayload: Record<string, any> = {
          code: selectedStock.value.code,
          event_type: adjustType.value,
          amount: amountValue,
          curr: selectedStock.value.currency,
          note: note.value.trim(),
        }
        const ledgerId = resolveSelectedLedgerId()
        if (ledgerId != null) {
          adjustmentPayload.ledger_id = ledgerId
        }
        await api.post('/api/portfolio/adjustment_event', adjustmentPayload)
      } else {
        const modifyPayload: Record<string, any> = {
          code: selectedStock.value.code,
          qty: payload.qty,
          price: payload.price,
          note: note.value.trim(),
        }
        const ledgerId = resolveSelectedLedgerId()
        if (ledgerId != null) {
          modifyPayload.ledger_id = ledgerId
        }
        await api.post('/api/portfolio/modify', modifyPayload)
      }
      await submitSuccess('✓ 已调整')
      return
    }

    const p = parseFloat(price.value)
    const q = parseFloat(qty.value)
    if (!Number.isFinite(p) || p <= 0) {
      searchError.value = '请输入有效价格'
      return
    }
    if (!Number.isFinite(q) || q <= 0) {
      searchError.value = '请输入有效数量'
      return
    }

    if (actionMode.value === 'sell') {
      if (isExternal) {
        await api.post('/api/portfolio/sell', { code: selectedStock.value.code, price: p, qty: q })
      } else {
        await api.post('/api/portfolio/sell_to_cash', { code: selectedStock.value.code, price: p, qty: q, cash_asset_id: cashId })
      }
      await submitSuccess('✓ 已卖出')
    } else {
      if (isExternal) {
        await api.post('/api/portfolio/buy', { code: selectedStock.value.code, price: p, qty: q })
      } else {
        await api.post('/api/portfolio/buy_with_cash', {
          code: selectedStock.value.code,
          name: selectedStock.value.name,
          price: p,
          qty: q,
          curr: selectedStock.value.currency,
          asset_type: selectedStock.value.asset_type || '',
          cash_asset_id: cashId
        })
      }
      await submitSuccess('✓ 已买入')
    }
  } catch (e: any) {
    console.error('Invest trade error', e)
    searchError.value = extractErrorMessage(e, '保存失败，请重试')
  } finally {
    isSubmitting.value = false
  }
}

const closeSearchDropdown = () => { isDropdownOpen.value = false }
const closeAcctDropdown = () => { isAcctDropdownOpen.value = false }
const closeCurrDropdown = () => { isCurrDropdownOpen.value = false }

const handleDocClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.search-wrap')) closeSearchDropdown()
  if (!target.closest('.acct-wrap')) closeAcctDropdown()
  if (!target.closest('.curr-wrap')) closeCurrDropdown()
}

onMounted(() => document.addEventListener('click', handleDocClick))
onUnmounted(() => {
  document.removeEventListener('click', handleDocClick)
  if (searchTimeout) clearTimeout(searchTimeout)
})
</script>

<template>
  <teleport to="body">
    <div v-if="modalVisible" class="phone-bg-modal">
      <div 
        class="sheet-overlay-modal" 
        :class="{ 'opacity-0': !props.show }" 
        @click.self="close"
      ></div>

      <div class="sheet" :class="{ 'sheet-exiting': !props.show }">
        <div class="handle"></div>
        <div class="sheet-header">
          <div class="sheet-title">{{ sheetTitle }}</div>
          <button class="close-btn" @click="close" :disabled="isSubmitting">
            <svg width="9" height="9" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 1l8 8M9 1L1 9"/></svg>
          </button>
        </div>

        <div class="sheet-body">
          <div class="field-row">
            <div class="search-wrap">
              <div v-if="!selectedStock && !isEditMode" id="searchInputArea">
                <div class="search-input-row">
                  <input 
                    type="text" 
                    class="search-input" 
                    v-model="query" 
                    @input="handleSearchInput"
                    @focus="handleSearchInput"
                    placeholder="输入代码或名称" 
                    autocomplete="off" 
                  />
                  <button class="search-btn" @click="handleSearchInput">
                    <svg width="11" height="11" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="6" cy="6" r="4.5"/><path d="M9.5 9.5L12.5 12.5"/></svg>
                    搜索
                  </button>
                </div>
              </div>

              <div v-if="selectedStock && !isEditMode" class="selected-pill show">
                  <div class="sp-main">
                    <div class="sp-row">
                      <span class="sp-name" :title="selectedStock.name">
                        {{ selectedStock.name.length > 20 ? selectedStock.name.slice(0, 19) + '...' : selectedStock.name }}
                      </span>
                      <span class="sp-price">{{ formatQuoteValue(searchPrice(selectedStock), searchDigits(selectedStock)) }}</span>
                    </div>
                    <div class="sp-row sp-row-sub">
                      <div class="sp-meta-line">
                        <span 
                          class="sp-tag di-tag" 
                          :style="{ color: getMarketMeta(inferSearchMarket(selectedStock)).color, background: getMarketMeta(inferSearchMarket(selectedStock)).bg }"
                        >
                          {{ searchMarketLabel(selectedStock) }}
                        </span>
                        <span class="sp-meta-code">{{ formatDisplayCode(selectedStock.code) }}</span>
                      </div>
                      <span class="sp-move" :class="moveTone(searchChangePct(selectedStock))">
                        {{ searchChangePct(selectedStock) === null ? '--' : `${formatSignedMove(searchChangePct(selectedStock), 2)}%` }}
                      </span>
                    </div>
                  </div>
                <button v-if="!isEditMode" class="sp-x" @click="clearSelection">
                  <svg width="7" height="7" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M1 1l8 8M9 1L1 9"/></svg>
                </button>
              </div>

              <!-- Search Dropdown -->
              <div class="dropdown" :class="{ open: isDropdownOpen && !selectedStock && !isEditMode }">
                <div v-if="searchResults.length === 0" style="padding:14px;text-align:center;color:var(--text-muted);font-size:12px;">
                  <span v-if="query">未找到匹配资产</span>
                  <span v-else>请输入资产代码/名称</span>
                </div>
                <template v-else>
                  <div 
                    v-for="s in searchResults" 
                    :key="s.code"
                    class="dropdown-item" 
                    @click="selectStock(s)"
                  >
                    <div class="di-left">
                      <div class="di-main">
                        <div class="di-name" :title="s.name">{{ s.name.length > 20 ? s.name.slice(0, 19) + '...' : s.name }}</div>
                        <div class="di-meta">
                          <span class="di-tag" :style="{ color: getMarketMeta(inferSearchMarket(s)).color, background: getMarketMeta(inferSearchMarket(s)).bg }">{{ searchMarketLabel(s) }}</span>
                          <span class="di-code">{{ formatDisplayCode(s.code) }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="di-quote">
                      <div class="di-price">{{ formatQuoteValue(searchPrice(s), searchDigits(s)) }}</div>
                      <div class="di-move" :class="moveTone(searchChangePct(s))">
                        <span>{{ formatSignedMove(searchChangeAmount(s), searchDigits(s)) }}</span>
                        <span>{{ searchChangePct(s) === null ? '--' : `${formatSignedMove(searchChangePct(s), 2)}%` }}</span>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <div class="error-msg" :class="{ show: !!searchError }">{{ searchError }}</div>

          <!-- Account -->
          <div v-if="!isEditMode || actionMode !== 'adjust'" class="account-section">
            <div class="section-label">资产账户</div>
            <div class="field-row">
            <div class="acct-wrap">
              <div class="acct-trigger" :class="{ open: isAcctDropdownOpen }" @click="toggleAcct">
                <div class="acct-trigger-left">
                  <span class="acct-trigger-name">{{ selectedAccount?.name || '请选择资金账户' }}</span>
                  <span v-if="selectedAccount && selectedAccount.id !== -999" class="acct-trigger-amount">{{ selectedAccount?.curr }} {{ formatQuoteValue(selectedAccount?.amount) }}</span>
                </div>
                <svg class="acct-arrow" width="11" height="11" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4l4 4 4-4"/></svg>
              </div>
              <div class="acct-dropdown" :class="{ open: isAcctDropdownOpen }">
                <div 
                  v-for="a in accounts" :key="a.id"
                  class="acct-item" :class="{ selected: selectedAccount?.id === a.id }"
                  @click.stop="selectAccount(a)"
                >
                  <div class="acct-item-left">
                    <div class="acct-icon" :style="{ background: a.iconBg || 'rgba(91,141,239,0.12)' }">{{ a.icon }}</div>
                    <div class="acct-info">
                      <div class="acct-item-name">{{ a.name }}</div>
                      <div v-if="a.id !== -999" class="acct-item-amount">{{ a.curr }} {{ formatQuoteValue(a.amount) }}</div>
                    </div>
                  </div>
                  <svg class="acct-check" width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7l4 4 6-7"/></svg>
                </div>
                <!-- Add account button -->
                <div class="acct-add-item" @click.stop="openCreateSheet">
                  <div class="acct-add-icon"><svg width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="#5b8def" stroke-width="2.2" stroke-linecap="round"><path d="M7 1v12M1 7h12"/></svg></div>
                  <span class="acct-add-label">添加资金账户</span>
                </div>
              </div>
            </div>
            </div>
          </div>

          <div class="divider"></div>

          <div v-if="!isEditMode || actionMode !== 'adjust'" class="inputs-section">
            <div class="inputs-row">
              <div class="num-field">
                <div class="num-label">{{ isEditMode && actionMode === 'sell' ? '卖出价' : '单价' }}</div>
                <div class="num-wrap">
                  <input type="number" class="num-input" v-model="price" placeholder="0.00" step="0.01" @input="syncAmount" />
                </div>
              </div>
              <div class="num-field">
                <div class="num-label">数量</div>
                <div class="num-wrap">
                  <input type="number" class="num-input" v-model="qty" placeholder="0" step="1" @input="syncAmount" />
                </div>
              </div>
            </div>
            <div class="inputs-row amount-row">
              <div class="num-field num-field-amount">
                <div class="num-label">金额</div>
                <div class="num-wrap">
                  <input type="number" class="num-input" v-model="amount" placeholder="0.00" min="0" step="0.01" @input="syncQty" />
                </div>
              </div>
            </div>
          </div>

          <div v-else class="inputs-section">
            <div class="adjust-type-pills">
              <button
                v-for="option in adjustTypeOptions"
                :key="option.value"
                type="button"
                class="adjust-type-pill"
                :class="{ active: adjustType === option.value }"
                @click="selectAdjustType(option.value)"
              >
                {{ option.label }}
              </button>
            </div>
            <div class="inputs-row adjust-row">
              <div class="num-field">
                <div class="num-label">{{ adjustInputLabel }}</div>
                <div class="num-wrap">
                  <input type="number" class="num-input" v-model="adjustValue" placeholder="0.00" :step="adjustValueStep" />
                </div>
              </div>
            </div>
            <div class="inputs-row adjust-row" style="margin-top: 14px;">
              <div class="num-field" style="width: 100%;">
                <div class="num-label">备注 (可选)</div>
                <div class="num-wrap">
                  <input
                    type="text"
                    class="num-input"
                    style="text-align: left; padding: 0 12px; font-family: inherit;"
                    v-model="note"
                    placeholder="如：7月分红、富途盈亏分析补录"
                  />
                </div>
              </div>
            </div>
          </div>

        </div>

        <div class="sheet-actions">
          <button class="btn btn-cancel" @click="close" :disabled="isSubmitting">取消</button>
          <button class="btn btn-confirm" :style="confirmBtnStyle" :disabled="isSubmitting" @click="handleConfirm">
            {{ isSubmitting ? '处理中...' : confirmBtnText }}
          </button>
        </div>
      </div>
    </div>

    <!-- Create Account Sheet -->
    <div v-show="isCreateSheetOpen" class="create-sheet open">
      <div class="create-overlay" @click="closeCreateSheet"></div>
      <div class="create-panel">
        <div class="create-header">
          <div>
            <div class="create-title">添加资金账户</div>
            <div class="create-sub">账户名称和金额为必填项</div>
          </div>
          <button class="close-btn" @click="closeCreateSheet" style="flex-shrink:0;margin-top:2px;">
            <svg width="9" height="9" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 1l8 8M9 1L1 9"/></svg>
          </button>
        </div>
        <div class="create-body">
          <div class="create-field">
            <div class="create-field-label">账户类型</div>
            <div class="acct-type-tabs">
              <div class="acct-type-tab cash" :class="{ active: createAcctType === 'cash' }" @click="createAcctType = 'cash'">💰 现金资产</div>
              <div class="acct-type-tab other" :class="{ active: createAcctType === 'other' }" @click="createAcctType = 'other'">📦 其他资产</div>
              <div class="acct-type-tab debt" :class="{ active: createAcctType === 'debt' }" @click="createAcctType = 'debt'">💳 我的负债</div>
            </div>
          </div>
          <div class="create-field">
            <div class="create-field-label">币种</div>
            <div class="curr-wrap">
              <div class="curr-trigger" :class="{ open: isCurrDropdownOpen }" @click.stop="toggleCurr">
                <div class="curr-trigger-left">
                  <span>{{ selectCurrInfo?.flag }}</span>
                  <span class="curr-trigger-code">{{ selectCurrInfo?.code }}</span>
                  <span class="curr-trigger-name">{{ selectCurrInfo?.name }}</span>
                </div>
                <svg class="curr-arrow" width="11" height="11" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 4l4 4 4-4"/></svg>
              </div>
              <div class="curr-dropdown" :class="{ open: isCurrDropdownOpen }">
                <div 
                  v-for="c in currencies" :key="c.code"
                  class="curr-item" :class="{ selected: createCurr === c.code }" 
                  @click.stop="createCurr = c.code; isCurrDropdownOpen = false"
                >
                  <div class="curr-item-left">
                    <span class="curr-item-flag">{{ c.flag }}</span>
                    <span class="curr-item-code">{{ c.code }}</span>
                    <span class="curr-item-name">{{ c.name }}</span>
                  </div>
                  <svg class="curr-check" width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2 7l4 4 6-7"/></svg>
                </div>
              </div>
            </div>
          </div>
          <div class="create-field">
            <div class="create-field-label"><span class="required-dot"></span>账户名称</div>
            <div class="create-input-wrap" :class="{ error: nameErr }">
              <input class="create-input" type="text" v-model="newAcctName" placeholder="如：招商银行储蓄卡" maxlength="20" />
            </div>
            <div class="field-err" :class="{ show: nameErr }">{{ nameErr }}</div>
          </div>
          <div class="create-field">
            <div class="create-field-label"><span class="required-dot"></span>金额</div>
            <div class="create-input-wrap" :class="{ error: amountErr }">
              <input class="create-input mono" type="number" v-model="newAcctBalance" placeholder="0.00" min="0" step="0.01" />
              <span class="input-suffix">{{ createCurr }}</span>
            </div>
            <div class="field-err" :class="{ show: amountErr }">{{ amountErr }}</div>
          </div>
        </div>
        <div class="create-actions">
          <button class="create-btn create-btn-cancel" @click="closeCreateSheet">取消</button>
          <button class="create-btn create-btn-confirm" @click="confirmCreateAcct">创建账户</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<style scoped>
/* Scoped css mapped from prototype */
.phone-bg-modal { position: fixed; inset: 0; display: flex; align-items: flex-start; justify-content: center; z-index: 9999; overflow-y: auto; padding: 24px 0; -webkit-overflow-scrolling: touch; }
.sheet-overlay-modal { position: fixed; inset: 0; background: var(--overlay-soft); transition: opacity 0.2s; z-index: 1; }
.sheet-overlay-modal.opacity-0 { opacity: 0; }
.sheet { position: relative; width: 100%; max-width: 420px; background: var(--panel-elevated, #13151b); border-radius: 18px; border: 1px solid var(--border); box-shadow: var(--shadow-float); z-index: 10; overflow: visible; animation: popIn 0.22s cubic-bezier(0.34,1.2,0.64,1); margin: auto 16px; flex-shrink: 0; }
.sheet.sheet-exiting { animation: popOut 0.2s cubic-bezier(0.34,1.2,0.64,1) forwards; }
@keyframes popIn { from { opacity: 0; transform: scale(0.95) translateY(10px); } to { opacity: 1; transform: scale(1) translateY(0); } }
@keyframes popOut { from { opacity: 1; transform: scale(1) translateY(0); } to { opacity: 0; transform: scale(0.95) translateY(10px); } }
.handle { display: none; }
.sheet-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 20px 11px; border-bottom: 1px solid var(--border, rgba(255,255,255,0.07)); }
.sheet-title { font-size: 13.5px; font-weight: 500; color: var(--text-muted, #575d6e); letter-spacing: 0.02em; }
.close-btn { width: 24px; height: 24px; background: var(--surface-soft); border: none; cursor: pointer; border-radius: 50%; color: var(--sub); display: flex; align-items: center; justify-content: center; transition: background 0.15s, color 0.15s; }
.close-btn:hover { background: var(--surface-soft-hover); color: var(--text); }
.sheet-body { padding: 14px 20px 0; display: flex; flex-direction: column; gap: 10px; }
.action-tabs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.action-tab { height: 34px; border-radius: 9px; border: 1px solid var(--border); background: var(--panel-muted, #1a1d25); color: var(--sub); font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.18s; }
.action-tab.active { background: linear-gradient(135deg, rgba(91,141,239,0.16), rgba(74,123,224,0.08)); color: var(--blue); border-color: color-mix(in srgb, var(--blue) 35%, var(--border)); box-shadow: 0 6px 16px rgba(91,141,239,0.12); }
.account-section { display: flex; flex-direction: column; gap: 6px; }
.section-label { font-size: 11px; color: var(--sub); padding-left: 1px; }
.field-row { display: flex; align-items: center; gap: 10px; width: 100%; min-width: 0; }
.search-wrap { position: relative; flex: 1; min-width: 0; width: 100%; }
.search-input-row { display: flex; align-items: center; background: var(--panel-muted, #1a1d25); border: 1px solid var(--border); border-radius: 8px; transition: border-color 0.2s, box-shadow 0.2s; overflow: hidden; }
.search-input-row:focus-within { border-color: rgba(212,175,100,0.45); box-shadow: 0 0 0 3px rgba(212,175,100,0.07); }
.search-input { flex: 1; background: transparent; border: none; outline: none; color: var(--text); font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 500; padding: 9px 10px; letter-spacing: 0.04em; transform: translateY(1px); min-width: 0; }
.search-input::placeholder { color: var(--sub); font-family: 'DM Sans', sans-serif; text-transform: none; letter-spacing: 0; font-size: 12px; font-weight: 400; }
.search-btn { background: linear-gradient(135deg, #5b8def 0%, #4a7be0 100%); border: none; color: #fff; font-family: 'DM Sans', sans-serif; font-size: 11px; font-weight: 600; padding: 6px 11px; margin: 4px; border-radius: 5px; cursor: pointer; display: flex; align-items: center; gap: 4px; transition: opacity 0.2s, transform 0.15s; white-space: nowrap; flex-shrink: 0; }
.search-btn:hover { opacity: 0.88; }
.search-btn:active { transform: scale(0.96); }
.dropdown, .acct-dropdown, .curr-dropdown { position: absolute; top: calc(100% + 6px); left: 0; right: 0; background: var(--panel-elevated, #1a1d25); border: 1px solid var(--border-b); border-radius: 8px; overflow: hidden; z-index: 200; box-shadow: var(--shadow-float); display: none; animation: dropIn 0.18s cubic-bezier(0.34,1.4,0.64,1); }
.dropdown.open, .acct-dropdown.open, .curr-dropdown.open { display: block; }
.acct-dropdown {
  max-height: min(320px, calc(100vh - 260px));
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
}
.acct-dropdown::-webkit-scrollbar {
  width: 6px;
}
.acct-dropdown::-webkit-scrollbar-track {
  background: transparent;
}
.acct-dropdown::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.14);
  border-radius: 999px;
}
.acct-dropdown::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.22);
}
.curr-dropdown { z-index: 400; }
@keyframes dropIn { from { opacity: 0; transform: translateY(-5px) scale(0.97); } to { opacity: 1; transform: translateY(0) scale(1); } }
.dropdown-item, .acct-item, .curr-item { display: flex; align-items: center; justify-content: space-between; padding: 9px 12px; cursor: pointer; border-bottom: 1px solid var(--surface-divider); transition: background 0.12s; position: relative; }
.dropdown-item:last-child, .acct-item:last-child, .curr-item:last-child { border-bottom: none; }
.dropdown-item:hover, .acct-item:hover, .curr-item:hover { background: var(--surface-soft-hover); }
.dropdown-item.selected, .acct-item.selected, .curr-item.selected { background: color-mix(in srgb, var(--gold) 14%, transparent); }
.di-left { display: flex; align-items: center; gap: 9px; }
.di-main { display: flex; flex-direction: column; gap: 4px; }
.di-name { font-size: 13px; font-weight: 500; color: var(--text); }
.di-meta { display: flex; align-items: center; gap: 6px; }
.di-quote { min-width: 112px; display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.di-price { font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; color: var(--text); }
.di-move { display: flex; align-items: center; gap: 8px; font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 600; }
.di-move.up { color: var(--red, #f05a55); }
.di-move.down { color: var(--green, #3ecf82); }
.di-move.flat { color: var(--sub); }
.di-tag { font-size: 10px; font-weight: 600; padding: 1px 6px; border-radius: 4px; letter-spacing: 0.03em; }
.di-code { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--sub); letter-spacing: 0.04em; }
.selected-pill { display: none; align-items: center; gap: 7px; background: color-mix(in srgb, var(--gold) 12%, transparent); border: 1px solid color-mix(in srgb, var(--gold) 26%, transparent); border-radius: 6px; padding: 12px 14px; flex: 1; animation: fadeUp 0.2s ease; min-width: 0; overflow: hidden; }
.selected-pill.show { display: flex; }
.sp-summary { display: flex; flex-direction: column; gap: 8px; min-width: 0; flex: 1; }
.sp-summary.summary-edit { flex-direction: row; align-items: stretch; justify-content: space-between; gap: 16px; min-width: 0; width: 100%; overflow: hidden; }
.sp-summary-copy { display: flex; flex-direction: column; justify-content: center; gap: 6px; min-width: 0; flex: 1 1 auto; max-width: calc(100% - 240px); overflow: hidden; }
.sp-summary-name { display: block; max-width: 100%; font-size: 13px; font-weight: 600; color: var(--gold, #d4af64); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sp-summary-holding { font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600; color: var(--text); }
.sp-summary-metrics { display: flex; align-items: stretch; justify-content: flex-end; gap: 8px; flex: 0 0 232px; width: 232px; min-width: 232px; max-width: 232px; flex-shrink: 0; overflow: hidden; }
.sp-panel { display: flex; flex-direction: column; gap: 4px; min-width: 0; padding: 8px 10px; border-radius: 8px; background: rgba(18, 21, 29, 0.46); border: 1px solid rgba(212, 175, 100, 0.08); backdrop-filter: blur(8px); }
.sp-panel.compact { justify-content: center; min-height: 52px; width: 112px; min-width: 112px; max-width: 112px; }
.sp-panel-label { font-size: 10px; color: var(--sub); letter-spacing: 0.02em; }
.sp-panel-value { display: flex; align-items: baseline; gap: 6px; min-width: 0; font-family: 'JetBrains Mono', monospace; color: var(--text); }
.sp-panel-currency { flex-shrink: 0; font-size: 13px; font-weight: 700; }
.sp-panel-amount { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: clamp(11px, 1.35vw, 13px); font-weight: 700; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(3px); } to { opacity: 1; transform: translateY(0); } }
.sp-main { display: flex; flex-direction: column; gap: 3px; flex: 1 1 auto; min-width: 0; }
.sp-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; min-width: 0; }
.sp-row.sp-row-sub { gap: 8px; }
.sp-name { font-size: 13px; font-weight: 600; color: var(--text); flex: 1 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sp-meta-line { display: flex; align-items: center; gap: 0; flex: 1 1 auto; min-width: 0; overflow: hidden; }
.sp-meta-code { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--sub); min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sp-price { font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600; color: var(--text); flex-shrink: 0; text-align: right; white-space: nowrap; }
.sp-move { font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 600; min-width: 0; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sp-move.up { color: var(--red, #f05a55); }
.sp-move.down { color: var(--green, #3ecf82); }
.sp-move.flat { color: var(--sub); }
.sp-x { width: 17px; height: 17px; background: var(--surface-soft); border: none; border-radius: 50%; cursor: pointer; color: var(--sub); display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: background 0.15s, color 0.15s; }
.sp-x:hover { background: var(--surface-soft-hover); color: var(--text); }
.acct-wrap, .curr-wrap, .adjust-type-wrap { position: relative; flex: 1; }
.acct-trigger, .curr-trigger { display: flex; align-items: center; justify-content: space-between; background: var(--panel-muted, #1a1d25); border: 1px solid var(--border); border-radius: 8px; padding: 0 10px 0 12px; height: 38px; cursor: pointer; transition: border-color 0.2s, box-shadow 0.2s; user-select: none; }
.acct-trigger.open, .curr-trigger.open { border-color: rgba(212,175,100,0.45); box-shadow: 0 0 0 3px rgba(212,175,100,0.07); }
.acct-trigger-left, .curr-trigger-left { display: flex; align-items: center; gap: 8px; min-width: 0; }
.acct-trigger-name { font-size: 13px; font-weight: 500; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.acct-trigger-amount { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--sub); flex-shrink: 0; }
.acct-arrow, .curr-arrow { color: var(--sub); flex-shrink: 0; margin-left: 6px; transition: transform 0.2s; }
.acct-trigger.open .acct-arrow, .curr-trigger.open .curr-arrow { transform: rotate(180deg); }
.acct-item-left, .curr-item-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.acct-icon { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 15px; flex-shrink: 0; }
.acct-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.acct-item-name { font-size: 13px; font-weight: 500; color: var(--text); }
.acct-item-amount { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--sub); }
.acct-check, .curr-check { display: none; color: var(--gold, #d4af64); flex-shrink: 0; }
.acct-item.selected .acct-check, .curr-item.selected .curr-check { display: block; }
.acct-add-item { display: flex; align-items: center; gap: 9px; padding: 11px 13px; cursor: pointer; border-top: 1px solid var(--surface-divider); transition: background 0.12s; }
.acct-add-item:hover { background: var(--surface-soft-hover); }
.acct-add-icon { width: 30px; height: 30px; border-radius: 8px; background: rgba(91,141,239,0.1); border: 1px dashed rgba(91,141,239,0.35); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.acct-add-icon svg { color: #5b8def; }
.acct-add-label { font-size: 13px; font-weight: 500; color: #5b8def; }
.curr-item-code { font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; color: var(--text); min-width: 36px; }
.curr-item-name { font-size: 12px; color: var(--sub); }
.curr-item-flag { font-size: 16px; line-height: 1; }
.curr-trigger-code { font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; color: var(--text); }
.curr-trigger-name { font-size: 12px; color: var(--sub); }
.divider { height: 1px; background: var(--surface-divider); margin: 8px 0 12px; }
.inputs-section { display: flex; flex-direction: column; gap: 14px; }
.inputs-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.inputs-row.amount-row { grid-template-columns: 1fr; }
.inputs-row.adjust-row { grid-template-columns: 1fr; }
.adjust-type-pills { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 2px; margin-bottom: 2px; }
.adjust-type-pill { height: 32px; padding: 0 14px; border-radius: 999px; border: 1px solid var(--border); background: var(--panel-muted, #1a1d25); color: var(--sub); font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.18s; }
.adjust-type-pill:hover { color: var(--text); border-color: var(--border-b); }
.adjust-type-pill.active { background: linear-gradient(135deg, rgba(91,141,239,0.16), rgba(74,123,224,0.08)); color: var(--blue); border-color: color-mix(in srgb, var(--blue) 35%, var(--border)); box-shadow: 0 6px 16px rgba(91,141,239,0.12); }
.num-field { display: flex; flex-direction: column; gap: 8px; }
.num-field-amount { max-width: 100%; }
.num-label { font-size: 11px; color: var(--sub); }
.num-wrap { background: var(--panel-muted, #1a1d25); border: 1px solid var(--border); border-radius: 8px; display: flex; align-items: center; overflow: hidden; transition: border-color 0.2s, box-shadow 0.2s; }
.num-wrap:focus-within { border-color: rgba(99,149,235,0.6); box-shadow: 0 0 0 3px rgba(99,149,235,0.08); }
.num-wrap.readonly { background: var(--surface-faint); }
.num-input { flex: 1; min-width: 0; width: 100%; background: transparent; border: none; outline: none; color: var(--text); font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 500; padding: 10px 10px; }
.num-input::placeholder { color: var(--sub); font-size: 13px; font-family: 'DM Sans', sans-serif; font-weight: 400; }
.error-msg, .field-err { font-size: 10px; color: var(--red, #f05a55); display: none; padding-left: 1px; }
.error-msg.show, .field-err.show { display: block; }
.sheet-actions { display: flex; gap: 10px; padding: 18px 20px 20px; }
.btn { flex: 1; padding: 12px; border-radius: 8px; font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all 0.18s; }
.btn-cancel { background: var(--panel-muted, #1a1d25); color: var(--sub); border: 1px solid var(--border); }
.btn-cancel:hover { color: var(--text); border-color: var(--border-b); background: var(--surface-soft); }
.btn-confirm { background: linear-gradient(135deg, #5b8def 0%, #4a7be0 100%); color: #fff; box-shadow: 0 4px 16px rgba(74,123,224,0.3); }
.btn-confirm:hover { background: linear-gradient(135deg, #6a99f5 0%, #5a8bef 100%); }
.btn-confirm:active { transform: scale(0.98); }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.create-sheet { position: fixed; inset: 0; z-index: 10020; display: none; align-items: flex-start; justify-content: center; padding: 24px 0; overflow-y: auto; -webkit-overflow-scrolling: touch; }
.create-sheet.open { display: flex; }
.create-overlay { position: fixed; inset: 0; background: var(--overlay-strong); animation: fadeBg 0.18s ease; }
@keyframes fadeBg { from { opacity: 0; } to { opacity: 1; } }
.create-panel { position: relative; width: 100%; max-width: 360px; background: var(--panel-elevated, #13151b); border-radius: 16px; border: 1px solid var(--border); box-shadow: var(--shadow-float); flex-shrink: 0; margin: auto 16px; overflow: hidden; animation: popInCreate 0.22s cubic-bezier(0.34,1.3,0.64,1); }
@keyframes popInCreate { from { opacity: 0; transform: scale(0.93) translateY(8px); } to { opacity: 1; transform: scale(1) translateY(0); } }
.create-header { display: flex; align-items: flex-start; justify-content: space-between; padding: 18px 18px 14px; border-bottom: 1px solid var(--surface-divider); }
.create-title { font-size: 14px; font-weight: 600; color: var(--text); }
.create-sub { font-size: 11px; color: var(--sub); margin-top: 3px; }
.create-body { padding: 16px 18px; display: flex; flex-direction: column; gap: 14px; }
.acct-type-tabs { display: flex; background: var(--panel-muted, #1a1d25); border-radius: 9px; padding: 3px; gap: 2px; }
.acct-type-tab { flex: 1; text-align: center; padding: 7px 4px; border-radius: 7px; font-size: 12px; font-weight: 500; color: var(--sub); cursor: pointer; transition: all 0.18s; user-select: none; white-space: nowrap; }
.acct-type-tab:hover { color: var(--text); background: var(--surface-faint); }
.acct-type-tab.active { background: var(--surface-soft); color: var(--text); box-shadow: 0 1px 4px rgba(15,23,42,0.12); }
.acct-type-tab.active.cash { color: #3ecf82; }
.acct-type-tab.active.other { color: #5b8def; }
.acct-type-tab.active.debt { color: #f05a55; }
.create-field { display: flex; flex-direction: column; gap: 5px; }
.create-field-label { font-size: 11px; color: var(--sub); letter-spacing: 0.02em; display: flex; align-items: center; gap: 4px; }
.required-dot { width: 4px; height: 4px; border-radius: 50%; background: #5b8def; flex-shrink: 0; }
.create-input-wrap { background: var(--panel-muted, #1a1d25); border: 1px solid var(--border); border-radius: 8px; display: flex; align-items: center; transition: border-color 0.18s, box-shadow 0.18s; }
.create-input-wrap:focus-within { border-color: rgba(91,141,239,0.55); box-shadow: 0 0 0 3px rgba(91,141,239,0.08); }
.create-input-wrap.error { border-color: rgba(240,90,85,0.6); box-shadow: 0 0 0 3px rgba(240,90,85,0.07); }
.create-input { flex: 1; width: 100%; background: transparent; border: none; outline: none; color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 13px; padding: 9px 11px; }
.create-input.mono { font-family: 'JetBrains Mono', monospace; }
.create-input::placeholder { color: var(--sub); font-size: 12px; }
.input-suffix { font-size: 11px; color: var(--sub); padding-right: 10px; flex-shrink: 0; font-family: 'JetBrains Mono', monospace; }
.create-actions { display: flex; gap: 8px; padding: 0 18px 18px; }
.create-btn { flex: 1; padding: 11px; border-radius: 8px; font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all 0.18s; }
.create-btn-cancel { background: var(--panel-muted, #1a1d25); color: var(--sub); border: 1px solid var(--border); }
.create-btn-cancel:hover { color: var(--text); background: var(--surface-soft); }
.create-btn-confirm { background: linear-gradient(135deg, #5b8def 0%, #4a7be0 100%); color: #fff; box-shadow: 0 4px 12px rgba(74,123,224,0.25); }
.create-btn-confirm:hover { opacity: 0.92; }
.create-btn-confirm:active { transform: scale(0.98); }
@media (max-width: 560px) {
  /* Do not force 1 column for holding strips on mobile, keep 3 columns to save space */
  .holding-strip {
    grid-template-columns: repeat(3, 1fr);
  }
  .inputs-row {
    grid-template-columns: 1fr 1fr;
  }
  .inputs-row.adjust-row,
  .inputs-row.amount-row {
    grid-template-columns: 1fr;
  }
  .dropdown-item {
    align-items: flex-start;
  }
  .di-quote {
    min-width: 96px;
  }
  
  /* Make the font sizes slightly smaller inside the 3-column inputs on mobile to fit */
  .holding-value {
    font-size: 11px;
  }
  .num-input {
    font-size: 12px;
    padding: 8px 6px;
  }
  .num-label {
    font-size: 10px;
  }
}
</style>
