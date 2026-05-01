export type AssetAdjustmentType = 'cash' | 'other' | 'liability'

export type AssetAdjustmentRecord = {
  id?: number
  mode: string
  delta: number
  note: string
  balance_after: number
  created_at: string
}

type ApiGet = <T>(path: string) => Promise<T>

function toNumber(value: unknown, fallback = 0): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

export function normalizeAssetAdjustmentsPayload(payload: unknown): AssetAdjustmentRecord[] {
  const source = payload as { adjustments?: unknown } | null
  const rows = Array.isArray(source?.adjustments) ? source.adjustments : []
  return rows.map(row => {
    const item = (row || {}) as Record<string, unknown>
    return {
      id: Number.isFinite(Number(item.id)) ? Number(item.id) : undefined,
      mode: String(item.mode || ''),
      delta: toNumber(item.delta),
      note: String(item.note || ''),
      balance_after: toNumber(item.balance_after),
      created_at: String(item.created_at || ''),
    }
  })
}

export async function fetchAssetAdjustments(
  apiGet: ApiGet,
  assetType: AssetAdjustmentType,
  assetId: number,
): Promise<AssetAdjustmentRecord[]> {
  const payload = await apiGet<unknown>(`/api/assets/${assetType}/${assetId}/adjustments`)
  return normalizeAssetAdjustmentsPayload(payload)
}

export function currencySymbol(curr?: string): string {
  const code = String(curr || 'CNY').toUpperCase()
  if (code === 'USD') return '$'
  if (code === 'HKD') return 'HK$'
  return '¥'
}

export function formatAdjustmentAmount(
  record: Pick<AssetAdjustmentRecord, 'mode' | 'delta'>,
  curr?: string,
): string {
  const sign = record.mode === 'sub' ? '-' : '+'
  const value = Math.abs(toNumber(record.delta))
  return `${sign}${currencySymbol(curr)}${value.toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}
