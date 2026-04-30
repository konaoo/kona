type AssetLike = Record<string, unknown> | null | undefined

export function isFundAsset(item: AssetLike): boolean {
  const market = String(item?.category || item?.market || '').toLowerCase()
  if (market === 'fund') return true
  const assetType = String(item?.asset_type || '').toLowerCase()
  if (assetType === 'fund') return true
  const code = String(item?.code || '').toLowerCase()
  return code.startsWith('f_') || code.startsWith('ft_')
}

export function shouldShowFundNavMeta(item: AssetLike): boolean {
  return isFundAsset(item) && Boolean(item?.navUpdatePending)
}

export function isStaleFund(item: AssetLike, now = new Date()): boolean {
  if (!isFundAsset(item)) return false
  if (!Boolean(item?.navUpdatePending)) return false
  const latestNavDate = readLatestNavDate(item)
  if (!latestNavDate) return true
  return !isDateToday(latestNavDate, now)
}

export function readLatestNavDate(item: AssetLike): string | null {
  const raw = String(item?.latest_nav_date ?? item?.latestNavDate ?? '').trim()
  return raw || null
}

export function formatLatestNavDateText(value: string | null): string | null {
  const text = String(value || '').trim()
  if (!text) return null
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(text)
  if (!match) return text
  return `${match[2]}-${match[3]}`
}

export function isDateToday(value: string, now = new Date()): boolean {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(value || '').trim())
  if (!match) return false
  const y = Number(match[1])
  const m = Number(match[2])
  const d = Number(match[3])
  if (!Number.isFinite(y) || !Number.isFinite(m) || !Number.isFinite(d)) return false
  return now.getFullYear() === y && now.getMonth() + 1 === m && now.getDate() === d
}
