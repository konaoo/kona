# 行情/快讯性能与部署稳定性交接文档（v1.0.31）

本文覆盖 2026-03-05 主干性能与稳定性改造，重点是“用户打开页面先快，再补全”。

---

## 1. 目标与范围

### 1.1 目标

1. 把 A 股/港股/美股/基金报价改成速度优先策略，避免慢源拖慢整体响应。
2. 修复基金净值口径偏差，优先确认净值，减少“日期落后/差几分钱”反馈。
3. 快讯页改为“先看到近 50 条，再增量刷新”，提升首屏体感。
4. 稳定 CI 与部署冷启动，减少 GitHub 构建偶发失败。

### 1.2 范围

- Backend：报价聚合、基金源优先级、快讯缓存、bootstrap/market status。
- Flutter：快讯页刷新模型、market status 与报价刷新解耦。
- Web：报价刷新节奏、交易 optimistic rollback。
- CI：deploy 冒烟重试、测试稳定性修复。

### 1.3 不在本次范围

- 不改数据库 schema。
- 不改投资会计口径字段定义。
- 不扩展到 Web 管理端新页面。

---

## 2. 关键提交与主题映射

- `1132c19`：基金确认净值优先（Eastmoney F10）。
- `b241455`：基金新增腾讯 `jj` 备源回退。
- `45ed7c9`：四市场源优先级按速度重排。
- `1ce9e2f`：`/api/prices/batch` fast path + timeout + cache-first。
- `9b5e0d3`：慢源熔断与受控回退（Nasdaq/FT 不拖主链路）。
- `557fd53`：快讯 50 条预加载 + 增量刷新。
- `6e7325f`：快讯页主题兼容修复（hero decoration）。
- `1d5fcbe`：Flutter market status 刷新与报价刷新解耦。
- `55cd344`：Web 刷新 cadence 对齐 + optimistic rollback。
- `88bdb67` / `a641057` / `625dcad`：CI 与 deploy 稳定性补强。

---

## 3. 行情链路改造

### 3.1 总策略

统一采用：
- 先快源（低延迟、成功率高）。
- 再慢源兜底（允许慢，但不阻塞主链路）。
- 慢源启用熔断与冷却，连续失败后短期跳过。

### 3.2 基金（场外）

优先级：
1. Eastmoney F10 历史净值（确认净值）
2. Tencent `jj` 备源
3. 其他兜底链路

口径：
- 先取 `dwjz`（确认），仅缺失时回退 `gsz`（估算）。
- 避免估算值覆盖确认值导致日期回退。

### 3.3 A/HK/US/基金批量报价

- `/api/prices/batch` 支持 fast 获取路径。
- 请求可带 `timeout_ms`，服务端限制在安全窗口内。
- 先回缓存命中，再异步补慢源，降低 P95/P99。

### 3.4 慢源治理

- `source_health` 记录 success/failure/timeout。
- 对慢源（如 `nasdaq_quote`、`ft_fund`）应用更严格阈值：
  - 更低 fail threshold
  - 更长 cooldown
  - 更短单次 timeout

效果：
- 快源可用时，慢源不会把整批请求拖到秒级。
- 快源失败时，仍保留慢源兜底能力，不做硬放弃。

---

## 4. 快讯链路改造

### 4.1 后端

- 快讯缓存重构为“固定窗口 + 增量合并”。
- 默认优先返回近 50 条，旧快讯按容量裁剪。
- 刷新任务失败不清空已有缓存，避免前端空白闪烁。

### 4.2 前端（Flutter）

- 进入快讯页先渲染预加载列表（近 50 条）。
- 后续按增量刷新补新数据。
- 修复主题 API 兼容，避免因 `heroDecoration` getter 缺失导致页面异常。

用户体感：
- 打开快讯页更快看到内容。
- 新消息继续自动补进，不需要全量重绘。

---

## 5. Web 与 Flutter 一致性

### 5.1 Flutter

- `AppState` 中 market status 拉取与报价刷新拆开。
- 报价拉取不再被 market status 串行阻塞。

### 5.2 Web

- 对齐刷新 cadence 到同一策略窗口。
- 买卖交易引入 optimistic rollback：
  - 先本地更新提升响应
  - 失败自动回滚，防止脏状态残留

---

## 6. CI/部署稳定性改造

- deploy workflow 增加 `/api/market/status` 冷启动重试。
- baseline 测试修复 bootstrap/market status 边界。
- widget 测试补 Provider/Timer 清理，避免随机失败。

结果：
- 冷启动场景 false negative 明显减少。
- 主干绿勾稳定性提升。

---

## 7. 影响文件清单（核心）

Backend:
- `kona_tool/core/fund.py`
- `kona_tool/core/stock.py`
- `kona_tool/core/price.py`
- `kona_tool/core/system.py`
- `kona_tool/core/source_health.py`
- `kona_tool/core/utils.py`
- `kona_tool/core/news.py`
- `kona_tool/app.py`
- `kona_tool/config.py`

Flutter:
- `flutter/lib/providers/app_state.dart`
- `flutter/lib/pages/news_page.dart`
- `flutter/lib/services/api_service.dart`
- `flutter/lib/pages/home_page.dart`

Web:
- `web/src/pages/app/AppInvestPage.vue`
- `web/src/pages/app/AppHomePage.vue`
- `web/src/shared/store.ts`

CI:
- `.github/workflows/deploy.yml`
- `flutter/test/auth_boot_flow_test.dart`
- `kona_tool/tests/test_api_baseline.py`
- `kona_tool/tests/test_fund_source_priority.py`
- `kona_tool/tests/test_stock_source_order.py`

---

## 8. 验收建议

1. 基金校验：对比 `017811/018125/023350/023754/025209/025793` 新接口价格与目标值，确认确认净值优先。
2. 四市场测速：分别测 `601919/159655/HK1810/AAPL/025209`，观察首包延迟与回退行为。
3. 快讯体验：打开快讯页应先看到近 50 条，再自动增量刷新。
4. 部署链路：执行一次完整 GitHub deploy，确认 health + market status smoke 通过。

---

## 9. 后续建议（可选）

1. 对慢源增加独立异步补全队列，进一步压低首包尾延迟。
2. 为报价源健康状态增加管理端可视化（成功率/超时率/熔断状态）。
3. 快讯按“最新 N 分钟无缓存、旧数据缓存”做分层策略，兼顾实时性与成本。
