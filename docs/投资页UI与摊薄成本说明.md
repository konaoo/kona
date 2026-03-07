# 投资弹窗 UI v2 + 摊薄成本展示交接文档（v1.0.24）

本文是 `v1.0.24` 的实现与验收总说明，覆盖 Flutter 与 Web 两端。

---

## 1. 目标与范围

### 1.1 目标

1. 在不改后端会计入账口径的前提下，把投资页“成本”展示升级为“卖出后摊薄成本”。
2. 将投资交易弹窗升级为 `ui优化.md v2` 视觉与交互，同时保留真实业务逻辑。
3. 统一资产新增/编辑弹窗为同一套新 UI 组件，减少多套交互并行维护成本。

### 1.2 范围

- Flutter：投资页、投资交易弹窗、资产新增/编辑弹窗、资金账户补建弹窗。
- Web：投资页成本展示与编辑默认值逻辑。
- Backend：仅同步默认客户端版本号（`CLIENT_APP_VERSION`）。

### 1.3 不在本次范围

- 不修改后端投资会计字段定义与记账口径。
- 不修改数据库 schema。
- 不扩展到投资详情页/导出页等非本次指定页面。

---

## 2. 核心业务口径

### 2.1 摊薄成本展示公式（前端展示层）

- `diluted_cost_total = qty * price - adjustment`
- `displayCostPrice = diluted_cost_total / qty`（`qty > 0`）
- `qty <= 0` 时回退 `price`

说明：允许负数成本显示，不做截断。

### 2.2 字段语义不变

- `price`：原始/会计均价（编辑、修正仍使用此值）。
- `adjustment`：累计已实现盈亏/调整值（继续参与累计盈亏口径）。

### 2.3 资金账户规则

1. `add/buy`：允许 `外部资金/初始转入`，同时仅显示同币种现金账户。
2. `sell`：必须选择同币种现金账户回款；若无匹配账户，下拉中显示 `+ 添加现金账户` 引导补建。
3. 卖出主界面不再显示“未找到 HKD 资金账户”红色告警卡片，避免重复干扰。

---

## 3. Flutter 实现说明

### 3.1 投资页成本展示

文件：
- `flutter/lib/pages/invest_page.dart`

实现要点：
1. 成本位显示从 `item.price` 改为 `displayCostPrice`（摊薄后）。
2. 累计盈亏仍沿用 `value - (qty*price) + adjustment`，未改口径。
3. 交易弹窗入口改为居中弹窗调用。

### 3.2 InvestTradeDialog（投资交易弹窗）

文件：
- `flutter/lib/widgets/invest_trade_dialog.dart`
- `flutter/lib/main.dart`
- `flutter/lib/pages/invest_page.dart`

实现要点：
1. 入口统一：`showInvestTradeSheet(...)`，支持 `sheet/centered` 两种 presentation。
2. 首页添加投资与投资页点击持仓均改为 `presentation: centered`。
3. 搜索交互收口：
   - 聚焦/输入不自动展开结果；
   - 仅点击搜索按钮后才展示下拉结果；
   - 搜索按钮内嵌输入框 suffix。
4. 账户下拉收口：
   - 去掉搜索账户与币种筛选 UI；
   - 仅列表选择，超出项滚动；
   - `add/buy` 支持外部资金；`sell` 同币种强约束。
5. 卖出无同币种账户：下拉内 `+ 添加现金账户`，弹出二级补建，成功后自动选中新建账户继续流程。

### 3.3 统一 AddAssetDialog（新增/编辑复用）

文件：
- `flutter/lib/widgets/add_asset_dialog.dart`
- `flutter/lib/widgets/add_funding_account_dialog.dart`

实现要点：
1. `AddAssetDialog` 重构为统一新 UI，支持：
   - `allowedAssetTypes`
   - `fixedAssetType`
   - `initialCashCurrency`
   - `lockCashCurrency`
   - `returnCreatedAssetId`
2. 首页添加资产、资产详情新增/编辑、资金账户补建均复用该组件。
3. 币种显示改为 emoji 国旗：`🇨🇳 CNY`、`🇺🇸 USD`、`🇭🇰 HKD`。
4. 修复币种下拉定位：Overlay 锚点绑定到触发框本体，避免下拉与触发框重叠偏移。
5. 修复资产币种覆盖范围：现金/其他/负债三类均可选币种。

### 3.4 AppState 币种透传修复

文件：
- `flutter/lib/providers/app_state.dart`

实现要点：
1. `addAsset/updateAsset` 对 `other/liability` 同步透传 `curr`。
2. optimistic add/update 对三类资产统一持有 `curr`，避免 UI 选择后被本地状态覆盖。

---

## 4. Web 实现说明

文件：
- `web/src/shared/costBasis.ts`
- `web/src/shared/store.ts`
- `web/src/pages/app/AppInvestPage.vue`

实现要点：
1. 新增 `computeDisplayCostPrice()` 统一摊薄成本公式。
2. `rows` 增加：
   - `rawCostPrice`：原始成本（编辑默认值来源）
   - `displayCostPrice`：摊薄后展示成本
3. 表格“成本/现价”中的成本行改为 `displayCostPrice`。
4. 编辑弹窗预填均价改为优先 `rawCostPrice`，避免把展示值误写回。
5. `totalPnl` 与现有收益口径不变。

---

## 5. 测试与验收

### 5.1 Flutter

新增/更新测试：
- `flutter/test/invest_trade_dialog_test.dart`
- `flutter/test/widget_test.dart`
- `flutter/test/invest_page_diluted_cost_test.dart`

覆盖重点：
1. 居中弹窗入口、搜索触发时机、按钮内嵌。
2. 账户规则：`add/buy` 外部资金、`sell` 同币种强约束与下拉补建。
3. 摊薄成本展示与编辑使用原始成本的回归。
4. 币种下拉展示与定位回归。

### 5.2 Web

新增测试：
- `web/tests/costBasis.test.ts`

覆盖重点：
1. 常规摊薄值。
2. 负成本值。
3. `qty=0` 回退原成本。

### 5.3 建议验收路径（真机）

1. 首页 -> 记一笔：切换现金/其他/负债，验证币种可选与下拉位置。
2. 投资页 -> 添加资产：搜索仅点击搜索后出结果，按钮在输入框内。
3. 投资页 -> 卖出港股（无 HKD 现金账户）：
   - 主界面无红色告警卡片；
   - 下拉有 `+ 添加现金账户`；
   - 新建后自动选中并可提交卖出。
4. 投资页列表：成本显示为摊薄后成本；编辑均价默认仍为原始 `price`。

---

## 6. 变更文件清单（核心）

- `flutter/lib/main.dart`
- `flutter/lib/pages/invest_page.dart`
- `flutter/lib/providers/app_state.dart`
- `flutter/lib/widgets/add_asset_dialog.dart`
- `flutter/lib/widgets/add_funding_account_dialog.dart`
- `flutter/lib/widgets/invest_trade_dialog.dart`
- `flutter/test/invest_trade_dialog_test.dart`
- `flutter/test/invest_page_diluted_cost_test.dart`
- `flutter/test/widget_test.dart`
- `web/src/shared/costBasis.ts`
- `web/src/shared/store.ts`
- `web/src/pages/app/AppInvestPage.vue`
- `web/tests/costBasis.test.ts`

---

## 7. 版本信息

- Flutter 版本：`1.0.24`
- 后端默认客户端版本：`1.0.24`
- 发布条目：见 `CHANGELOG.md` 的 `v1.0.24`

