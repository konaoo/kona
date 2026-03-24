// 由 scripts/generate_sync_contracts.py 自动生成，不要手改。

const List<String> generatedSyncBootstrapDomains = <String>[
  'portfolio',
  'cash_assets',
  'other_assets',
  'liabilities',
  'history',
  'overview_all',
  'rates',
];

const List<String> generatedSyncBootstrapQuoteInclude = <String>[
  'portfolio',
  'rates',
];

const Map<String, int> generatedQuotePolicyDefault = <String, int>{
  'interval_open_sec': 5,
  'interval_closed_sec': 120,
  'interval_us_extended_sec': 10,
};

const int generatedAuthBootstrapTimeoutMs = 2500;
