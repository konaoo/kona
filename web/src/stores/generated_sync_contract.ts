// 由 scripts/generate_sync_contracts.py 自动生成，不要手改。

export const GENERATED_SYNC_BOOTSTRAP_DOMAINS = ['portfolio', 'cash_assets', 'other_assets', 'liabilities', 'history', 'overview_all', 'rates'] as const

export type GeneratedSyncDomain = typeof GENERATED_SYNC_BOOTSTRAP_DOMAINS[number]

export const GENERATED_SYNC_BOOTSTRAP_QUOTE_INCLUDE = ['portfolio', 'rates'] as const

export const GENERATED_QUOTE_POLICY_DEFAULT = {
  interval_open_sec: 5,
  interval_closed_sec: 120,
  interval_us_extended_sec: 10,
} as const

export const GENERATED_WEB_CACHE_TTL_MS = {
  STATIC: 300000,
  QUOTES: 60000,
} as const

export const GENERATED_AUTH_BOOTSTRAP_TIMEOUT_MS = 2500
