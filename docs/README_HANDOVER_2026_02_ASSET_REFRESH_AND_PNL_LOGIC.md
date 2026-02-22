# 资产刷新与收益口径接管手册（2026-02）

本文档面向“新开 Codex 会话的接手者”，用于快速理解本轮连续改动的完整上下文、当前线上/客户端行为、验收方式和边界。

适用仓库路径：

- `/Users/kona/Desktop/kaka/kona_repo`

---

## 1. 背景与目标

本轮连续改动集中解决了 4 类问题：

1. 收益日历历史日 `day_pnl` 被错误压成 `0`（尤其 `2026-02-16` 到 `2026-02-20`）。
2. 需要按市场展示收益拆分（`A/HK/US/Fund/unallocated`），并支持历史回填。
3. App 每次启动都全量拉取，弱网体验差，需要增量刷新（bootstrap 版本驱动）。
4. 投资页/首页在休市与弱网场景显示不稳定（休市清零、重开后现价像成本价、累计收益短暂异常）。

当前目标口径（已落地）：

1. 休市显示“最近收盘价 + 冻结日涨跌”，不是强制 `0`。
2. 行情失败回退链：实时价 -> 上次缓存价 -> 收盘快照价 -> 成本价。
3. 首页累计与投资资产口径走快照/行情估值，不再固定成本口径。
4. 启动优先读缓存，后台增量刷新，不再默认全量轰炸请求。
5. 首页不显示“资产更新时间/行情更新时间”文本。

---

## 2. 变更时间线（关键提交）

按时间先后（新到旧）：

- `706fa58`：Flutter 休市冻结显示 + 价格回退链 + 首页去更新时间文案。
- `cc15c8c`：Flutter 休市重开时保持行情缓存稳定。
- `89955b3`：新增 `/api/sync/bootstrap`，引入版本驱动增量刷新。
- `01dc000`：收益日历/分市场修复文档（runbook）。
- `e2a1fd0`：分市场日历接口 + 分市场回填流程。
- `bc30dc9`：`day_pnl` 修复与 `day_pnl` 回填脚本。
- `e1ec204`：交易所日历依赖不完整时的历史口径恢复。

---

## 3. 后端改动总览

### 3.1 收益日历与回填

已落地能力：

1. 修复交易日 `day_pnl` 被“快照写入时段休市”错误压零的问题。
2. 新增 `day_pnl` 历史回填脚本：
   - `/Users/kona/Desktop/kaka/kona_repo/kona_tool/scripts/backfill_day_pnl_from_total_delta.py`
3. 新增分市场拆分表：
   - `daily_snapshot_market_breakdowns`
4. 新增分市场查询接口：
   - `GET /api/analysis/calendar/market_breakdown`
5. 新增分市场回填脚本：
   - `/Users/kona/Desktop/kaka/kona_repo/kona_tool/scripts/backfill_market_breakdown.py`

历史回填原则：

1. 有证据则按市场归因。
2. 无证据不硬分配，进入 `unallocated`。
3. `source=estimated` 不代表逐笔成交级精确归因。

详细见：

- `/Users/kona/Desktop/kaka/kona_repo/docs/README_ANALYSIS_CALENDAR_MARKET_BREAKDOWN.md`

### 3.2 增量同步接口（Bootstrap）

接口：

- `POST /api/sync/bootstrap`

实现位置：

- `/Users/kona/Desktop/kaka/kona_repo/kona_tool/app.py`
- `/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db.py`

职责：

1. 读取客户端 `client_versions`。
2. 返回服务器 `versions`、`changed`、`data`（仅变化域）。
3. 同时返回 `market_status` 与 `quote_policy`（开休市轮询策略）。

版本域（当前）：

- `portfolio`
- `cash_assets`
- `other_assets`
- `liabilities`
- `history`
- `overview_all`
- `rates`

版本计算规则（`core/db.py:get_sync_versions`）：

1. 资产域：`max(updated_at)+count+user_id`。
2. `history`：`max(date)+count+user_id`。
3. `overview_all`：`max(daily_snapshots.updated_at)+count+user_id`。
4. `rates`：按汇率快照时间生成版本。

---

## 4. Flutter 改动总览

核心文件：

- `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart`
- `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/main.dart`
- `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/invest_page.dart`
- `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/home_page.dart`

### 4.1 启动与刷新策略

1. 冷启动后恢复会话：
   - `hydrateFromCache()` 先渲染本地缓存。
   - `refreshAll()` 再走 `refreshByVersion()`（默认增量）。
2. `refreshByVersion()` 调 `/api/sync/bootstrap`：
   - 仅刷新 `changed` 域。
   - 失败时降级全量刷新（兜底）。
3. `MainApp` 定时器仅负责行情刷新（`refreshPricesOnly`），并按 `quote_policy` 调整间隔。

### 4.2 休市冻结显示（已从“休市=0”改为“冻结值”）

当前口径：

1. `investDayPnl` 不再按 market open 才计算。
2. 只要该标的有有效价格且有 `yclose`，就沿用该价格对象的 `change`（冻结）。
3. 休市状态主要用于刷新频率，不再强制把日涨跌清零。

### 4.3 行情失败回退链

已实现顺序：

1. 实时返回（本次 `prices/batch`）。
2. 内存中上次有效行情（当前 `_prices`）。
3. 本地持久化快照（新增 `price_snapshots` 域）。
4. 成本价（`item.price`）最终兜底。

数据结构新增：

1. `AppState` 新增 `_priceSnapshots`。
2. 新增 `resolvePriceInfo` / `resolvePriceInfoByCode` 统一解析。
3. `saveHomeCache()` 同步保存 `price_snapshots`。

### 4.4 首页口径与显示

1. 首页 `totalInvest` 重算改为 `investTotalMV`（价格口径，带回退）。
2. 移除首页“资产更新/行情更新/离线缓存”文本展示。

### 4.5 投资页口径

1. 持仓行现价/当日盈亏改为走 `resolvePriceInfoByCode`。
2. 休市时显示冻结价，不再回到成本价。

---

## 5. 现网可观察行为（最终）

### 5.1 开市

1. 行情按开放市场高频刷新（默认 5 秒）。
2. 投资页现价/日涨跌实时变化。

### 5.2 休市

1. 行情降频（默认 120 秒）。
2. 投资页显示最近收盘冻结价与冻结日涨跌，不清零。
3. 杀进程重开时，若网络不可用仍可用快照价恢复显示。

### 5.3 弱网/断网

1. 增量刷新失败可降级全量尝试。
2. 行情失败保留已有值（内存/本地快照），不是直接成本价。
3. 只有在没有任何可用价格证据时，才回退成本价。

---

## 6. 验收清单（手工）

### 6.1 App 侧（休市场景）

1. 首开投资页：现价不应整体等于成本价。
2. 当日盈亏：不应全 0（应冻结为上次有效值）。
3. 杀进程重开：持仓、现价、当日盈亏应立即可见。
4. 手动下拉：可刷新；失败也不应清成 0 或成本价。
5. 首页：不再显示“资产更新时间/行情更新时间”文本。

### 6.2 API 侧

1. 首次请求（无 client_versions）应返回 `changed` 包含全部域：

```bash
curl -s -X POST http://127.0.0.1:5003/api/sync/bootstrap \
  -H 'Content-Type: application/json' \
  -d '{"include":["portfolio","cash_assets","other_assets","liabilities","history","overview_all","rates"],"client_versions":{}}'
```

2. 二次请求（带上返回的 `versions`）应返回 `changed: []`：

```bash
curl -s -X POST http://127.0.0.1:5003/api/sync/bootstrap \
  -H 'Content-Type: application/json' \
  -d '{"include":["portfolio","cash_assets","other_assets","liabilities","history","overview_all","rates"],"client_versions":{"cash_assets":"<v>","history":"<v>","liabilities":"<v>","other_assets":"<v>","overview_all":"<v>","portfolio":"<v>","rates":"<v>"}}'
```

### 6.3 DB 侧（收益日历）

1. `daily_snapshots` 的 `2026-02-17~2026-02-20` 应为非零 `day_pnl`（已修复）。
2. 分市场表可查：

```bash
cd /home/ec2-user/portfolio/kona_tool
python3 - <<'PY'
import sqlite3
db="/home/ec2-user/portfolio/kona_tool/portfolio.db"
uid="<user_id>"
conn=sqlite3.connect(db); conn.row_factory=sqlite3.Row
cur=conn.cursor()
for r in cur.execute("""
SELECT date, market, day_pnl, source
FROM daily_snapshot_market_breakdowns
WHERE COALESCE(user_id,'')=? AND date BETWEEN '2026-02-16' AND '2026-02-20'
ORDER BY date, CASE market
  WHEN 'a' THEN 1 WHEN 'hk' THEN 2 WHEN 'us' THEN 3 WHEN 'fund' THEN 4 WHEN 'unallocated' THEN 5 ELSE 9 END
""",(uid,)):
    print(r["date"], r["market"], float(r["day_pnl"]), r["source"])
conn.close()
PY
```

---

## 7. 回填命令（生产常用）

### 7.1 修复 `day_pnl`

```bash
cd /home/ec2-user/portfolio/kona_tool
python3 scripts/backfill_day_pnl_from_total_delta.py \
  --db-path /home/ec2-user/portfolio/kona_tool/portfolio.db \
  --dry-run \
  --start-date 2026-02-01 \
  --end-date 2026-02-28

python3 scripts/backfill_day_pnl_from_total_delta.py \
  --db-path /home/ec2-user/portfolio/kona_tool/portfolio.db \
  --apply \
  --start-date 2026-02-01 \
  --end-date 2026-02-28
```

### 7.2 回填分市场

```bash
cd /home/ec2-user/portfolio/kona_tool
python3 scripts/backfill_market_breakdown.py \
  --db-path /home/ec2-user/portfolio/kona_tool/portfolio.db \
  --user-id <user_id> \
  --start-date 2026-02-16 \
  --end-date 2026-02-20 \
  --dry-run

python3 scripts/backfill_market_breakdown.py \
  --db-path /home/ec2-user/portfolio/kona_tool/portfolio.db \
  --user-id <user_id> \
  --start-date 2026-02-16 \
  --end-date 2026-02-20 \
  --apply
```

---

## 8. 已知限制与边界

1. 历史分市场若缺少交易/仓位证据，无法恢复真实市场归因，只能 `estimated + unallocated`。
2. `exchange_calendars` 覆盖年份不足会出现告警日志（例如仅到 2025-12-31）。
3. 当前行情通道仍是轮询，不是 WebSocket。
4. Flutter test 中 `flutter_secure_storage` 相关 `MissingPluginException` 为测试环境常见噪音，不影响业务结论。

---

## 9. 新会话接手建议

若在新 Codex 会话继续处理此模块，建议按以下顺序阅读：

1. `/Users/kona/Desktop/kaka/kona_repo/README.md`
2. `/Users/kona/Desktop/kaka/kona_repo/docs/README_ANALYSIS_CALENDAR_MARKET_BREAKDOWN.md`
3. `/Users/kona/Desktop/kaka/kona_repo/docs/README_HANDOVER_2026_02_ASSET_REFRESH_AND_PNL_LOGIC.md`（本文）
4. 再看代码：
   - `/Users/kona/Desktop/kaka/kona_repo/kona_tool/app.py`
   - `/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db.py`
   - `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/providers/app_state.dart`
   - `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/main.dart`
   - `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/pages/invest_page.dart`

