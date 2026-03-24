# kona_tool 测试地图

这份文档不是讲怎么写测试，而是讲：

`现在这些测试文件，分别在保什么。`

这样以后你看到 CI 红叉，或者 AI 说“某个测试挂了”，你至少知道它是在保哪条逻辑，不会只看到一串文件名发懵。

---

## 1. 先说结论

`kona_tool/tests/` 现在已经不是“随便补几个测试”的状态了。

它大致已经覆盖了这几条主线：

- 后端基础接口
- 管理后台接口
- 登录与密码流程
- 资产代码识别
- 价格源优先级
- 价格缓存与容灾
- 快照 / 收益 / 日历口径
- 数据迁移与用户隔离
- 运维脚本与告警脚本

问题不在“没有测试”，而在：

`测试很多，但没有一张人话地图。`

---

## 2. 按主题看测试

### 2.1 后端基础接口与核心口径

最重要的一组是：

- [test_api_baseline.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_api_baseline.py)
- [test_analysis_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_analysis_api.py)
- [test_asset_account_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_asset_account_api.py)
- [test_market_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_market_api.py)
- [test_market_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_market_runtime.py)
- [test_misc_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_misc_api.py)
- [test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py)
- [test_portfolio_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_runtime.py)
- [test_quote_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_quote_api.py)
- [test_request_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_request_runtime.py)
- [test_snapshot_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_snapshot_runtime.py)
- [test_startup_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_startup_runtime.py)
- [test_sync_bootstrap_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_sync_bootstrap_api.py)
- [test_web_entry_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_web_entry_api.py)

它主要在保这些东西：

- 基础接口能不能正常返回
- Web 配置接口口径
- App 版本和下载配置
- 分析页概览 / 日历相关基础逻辑
- 持仓、收益、快照的很多核心默认行为

一句大白话：

`这是后端主链路的基础防线。`

如果它挂了，通常不是小修小补，而是核心行为变了。

请求运行时基础设施现在也单独补了一组：

- [test_request_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_request_runtime.py)

它主要保这些逻辑：

- 认证安全审计日志脱敏
- API 分组策略拦截
- 强制改密挡板
- 用户最近活跃打点节流
- 后台写操作审计落库

一句话：

`以后如果你改的是 request_runtime 这层请求钩子和审计基础设施，先跑这组。`

快照运行时现在也单独补了一组：

- [test_snapshot_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_snapshot_runtime.py)

它主要保这些逻辑：

- 测试态快照改成同步执行
- 异步快照节流与防并发
- 快照保存后的市场拆分落库
- 后台调度单次执行

一句话：

`以后如果你改的是 snapshot_runtime 这层快照运行时服务，先跑这组。`

投资交易运行时现在也单独补了一组：

- [test_portfolio_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_runtime.py)

它主要保这些逻辑：

- 持仓代码和币种标准化
- 请求幂等命中
- 撤销令牌生成 / 领取 / 释放
- 多币种金额换算

一句话：

`以后如果你改的是 portfolio_runtime 这层交易运行时基础设施，先跑这组。`

市场状态运行时现在也单独补了一组：

- [test_market_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_market_runtime.py)

它主要保这些逻辑：

- 市场状态缓存命中
- 强制刷新绕过缓存
- 返回结构保持稳定

一句话：

`以后如果你改的是 market_runtime 这层市场状态缓存基础设施，先跑这组。`

启动期运行时现在也单独补了一组：

- [test_startup_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_startup_runtime.py)

它主要保这些逻辑：

- 运行指标令牌校验
- 浏览器自动打开
- 启动期线程拉起
- 启动时预取器初始化

一句话：

`以后如果你改的是 startup_runtime 这层启动支撑基础设施，先跑这组。`

其中现在已经单独拎出一组“交易链”测试：

- [test_portfolio_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_api.py)

它主要保这些接口：

- 持仓新增 / 加仓 / 减仓 / 修改
- 现金买入 / 撤销
- 纠错删除
- 交易链幂等
- 快照触发 / 快照修复基础行为

一句话：

`以后如果你改的是 portfolio / snapshot 这条主交易链，先看这组。`

分析链现在也已经单独拎出一组：

- [test_analysis_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_analysis_api.py)

它主要保这些接口：

- 分析页概览
- 收益日历
- 日历年份 / 月份切换
- 分析排行
- 历史快照与未来快照过滤口径

一句话：

`以后如果你改的是 analysis 这条链，先跑这组，不要再先翻大基线。`

资产账户和交易记录这条链也已经单独拎出一组：

- [test_asset_account_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_asset_account_api.py)

它主要保这些接口：

- 交易记录列表
- 现金账户增删改
- 其他资产必填校验
- 负债金额校验

一句话：

`以后如果你改的是 cash_assets / other_assets / liabilities / transactions，先跑这组。`

这轮结构治理后，这条链在代码里的主要落点变成了：

- [db_asset_accounts.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_asset_accounts.py)
- [asset_account_handlers.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/asset_account_handlers.py)
- [asset_account_routes.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/asset_account_routes.py)

也就是说以后这块出问题，先别再去 `db.py` 里全局乱翻，先从这几处找入口。

持仓交易与已实现盈亏这条链，这轮也有了更清楚的数据库落点：

- [db_portfolio.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_portfolio.py)

它主要承接：

- 持仓增删改
- 买入 / 卖出 / 撤销
- 已实现盈亏统计
- 组合表兼容迁移

快照写入和历史曲线这条链，这轮也有了更清楚的数据库落点：

- [db_snapshots.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_snapshots.py)

它主要承接：

- daily_snapshots 结构兼容迁移
- 快照写入 / 分市场快照
- 历史曲线读取
- sync 版本号计算

分析链这轮也有了更清楚的数据库落点：

- [db_analysis.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_analysis.py)

它主要承接：

- 分析概览
- 收益日历
- 分市场收益日历
- 盈亏排行

清理与修复相关的链路，这轮也有了更清楚的数据库落点：

- [db_maintenance.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_maintenance.py)

它主要承接：

- 休市日清理预览 / 执行
- 指定日期 day_pnl 修复

和后台状态、邀请码、refresh token、运营配置更相关的那条链，这轮也有了更清楚的数据库落点：

- [db_admin_state.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_admin_state.py)

它主要承接：

- refresh token 生命周期
- 邀请码池与消耗
- 后台写操作审计日志
- 后台接口策略
- 运营配置持久化
- 价格巡检 / 行情测试报表快照

所以以后如果你改的是这条链，也不用再先在 `db.py` 里整页搜索。

用户与登录状态这条链，这轮也有了更清楚的数据库落点：

- [db_users.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_users.py)

它主要承接：

- 用户基础查询
- 登录 / 活跃时间打点
- 用户资料修改
- 密码初始化与后台重置
- 用户表兼容迁移 / 用户名归一化
- 本地数据重绑预览与执行

也就是说以后如果你改的是认证后半段、用户资料、管理员重绑数据，先从这里找。

同步引导也已经单独拎出一组：

- [test_sync_bootstrap_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_sync_bootstrap_api.py)

它主要保这些接口：

- `sync/bootstrap` 的版本比较
- changed domains 返回范围
- rates / quote_policy / market_statuses 输出结构

一句话：

`以后如果你改的是客户端增量同步入口，先看这组，不要再回大基线里找。`

市场状态和首页指数也已经单独拎出一组：

- [test_market_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_market_api.py)

它主要保这些接口：

- 市场开休市状态
- 首页指数数据

一句话：

`以后如果你改的是 market/status 或 market/indices，先跑这组。`

杂项接口里和真实业务入口更相关的那部分，也已经单独拎出一组：

- [test_misc_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_misc_api.py)

它主要保这些接口：

- `/health`
- `/api/history`
- `/api/asset/trends`

一句话：

`以后如果你改的是 history / asset trends / 健康检查，先看这组。`

报价链也已经单独拎出一组：

- [test_quote_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_quote_api.py)

它主要保这些接口：

- 单价查询
- 批量报价
- 汇率
- 搜索
- 美股盘前盘后合并口径

一句话：

`以后如果你改的是 price / prices/batch / rates / search，先跑这组。`

Web 入口壳子现在也已经单独拎出一组：

- [test_web_entry_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_web_entry_api.py)

它主要保这些入口：

- `/`
- `/app/*`
- `/admin/*`
- `/assets/*`
- 旧入口跳转和缓存头

一句话：

`以后如果你改的是 Web 门户入口、SPA 壳子或静态资源缓存规则，先跑这组。`

### 2.2 管理后台接口

这组测试主要保后台：

- [test_admin_api_foundation.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_admin_api_foundation.py)
- [test_admin_api_policies.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_admin_api_policies.py)
- [test_admin_invites.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_admin_invites.py)
- [test_admin_users_password_reset.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_admin_users_password_reset.py)

分别大致负责：

- 管理员权限和后台总览
- 后台策略开关和限流策略
- 邀请码生成、查询、撤销、导出
- 管理员重置用户密码、踢下线

一句话：

`这组是在保后台能不能正常管人、管策略、管邀请码。`

### 2.3 登录、密码和安全流程

这组测试主要保认证：

- [test_auth_force_password_change.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_auth_force_password_change.py)
- [test_auth_password_flow.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_auth_password_flow.py)
- [test_auth_rate_limit.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_auth_rate_limit.py)
- [test_refresh_token_cleanup.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_refresh_token_cleanup.py)

它们主要在保：

- 首次改密 / 强制改密
- 登录密码相关流程
- 登录接口限流
- refresh token 过期清理

如果这组挂了，通常影响的是：

- 用户登录
- 会话续期
- 密码安全

### 2.4 资产识别与市场分类

这组测试主要保“代码到底是什么资产”：

- [test_market_code_normalization.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_market_code_normalization.py)
- [test_market_calendar.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_market_calendar.py)
- [test_calendar_weekend.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_calendar_weekend.py)

它们主要在保：

- 代码标准化
- 市场归类
- 交易日 / 周末 / 休市判断

这类测试虽然不显眼，但它们一旦错，后面价格、快照、收益都会跟着歪。

### 2.5 价格源优先级

这组是近期最关键的一组：

- [test_stock_source_order.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_stock_source_order.py)
- [test_fund_source_priority.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_fund_source_priority.py)

它们主要在保：

- A 股先用哪个源
- 港股先用哪个源
- 美股先用哪个源
- 普通基金先用哪个源
- `968xxx` 海外基金怎么选源
- `ft_*` 海外基金 / 互认基金怎么选源

一句话：

`只要你改了价格源优先级，这组就最容易挂。`

### 2.6 价格缓存与容灾

这组测试保的是“取价失败时别直接炸”：

- [test_price_cache.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_price_cache.py)
- [test_price_resilience.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_price_resilience.py)
- [test_fund_quote_mode.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_fund_quote_mode.py)
- [test_search_timeout.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_search_timeout.py)
- [test_http_utils.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_http_utils.py)

它们主要在保：

- 缓存命中和跳过重复请求
- 行情源失败时回退到 stale 缓存
- `f_` 误标场内 ETF 时能不能纠偏
- 搜索接口超时时能不能尽快返回部分结果
- HTTP 工具层是否稳

一句话：

`这组是价格系统的抗打击能力。`

### 2.7 快照、收益和分析口径

这组直接关系到你最在意的数字：

- [test_market_breakdown.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_market_breakdown.py)
- [test_api_baseline.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_api_baseline.py)

其中重点是：

- 分市场收益拆分
- 日历数据
- `day_pnl / total_pnl`
- 分析页概览口径
- 历史快照相关逻辑

它们不是全部独立拆开，所以目前还是有一部分口径测试混在 `test_api_baseline.py` 里。

### 2.8 数据迁移、数据作用域和用户隔离

这组主要保“数据别串台”：

- [test_portfolio_schema_migration.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_schema_migration.py)
- [test_portfolio_user_scope.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_portfolio_user_scope.py)
- [test_data_rebind.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_data_rebind.py)

它们主要在保：

- 表结构迁移
- 多用户数据隔离
- 数据重绑逻辑

如果这组挂了，风险通常不只是显示错，而是可能串用户数据。

### 2.9 运维和脚本

这组主要保后端脚本和运维能力：

- [test_backup_restore_scripts.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_backup_restore_scripts.py)
- [test_price_health_alert_script.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_price_health_alert_script.py)
- [test_price_health_api.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_price_health_api.py)

它们主要在保：

- 备份恢复脚本
- 价格健康告警脚本
- 价格健康接口

这组更偏运维，不一定天天碰，但对线上稳定性很关键。

### 2.10 杂项支撑

还有一些单项测试：

- [test_ip_region.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_ip_region.py)

这类不属于主线大模块，但也在保某个具体辅助能力。

---

## 3. 哪几组测试最值得重点看

如果你只想抓住最关键的，优先看这 5 组：

1. [test_api_baseline.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_api_baseline.py)  
   后端主链路基线

2. [test_stock_source_order.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_stock_source_order.py)  
   股票价格源优先级

3. [test_fund_source_priority.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_fund_source_priority.py)  
   基金价格源优先级

4. [test_price_resilience.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_price_resilience.py)  
   价格容灾与错路纠偏

5. [test_admin_api_foundation.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/tests/test_admin_api_foundation.py)  
   管理后台基础能力

---

## 4. 当前测试体系还差什么

现在测试已经不算弱了，但还差 3 件事：

### 4.1 缺一份更清楚的“测试层级”

现在文件虽然不少，但还没有完全按层拆成：

- 单元测试
- 接口测试
- 回归测试
- 口径测试

很多东西还是按“问题驱动”长出来的。

### 4.2 价格 / 快照 / 分析口径还有些测试混在大基线里

比如：

- `test_api_baseline.py`

现在很重要，但也有点偏重，里面塞了很多不同主题。

后面如果继续工程化，应该逐步拆得更清楚。

### 4.3 缺一份“改什么就该先跑哪些测试”的对照表

这点很实用，后面可以补。

比如：

- 改价格源，就先跑哪几份
- 改后台，就先跑哪几份
- 改快照口径，就先跑哪几份

---

## 5. 最实用的使用方法

以后你或 AI 改代码时，可以按这个简化判断：

### 改价格源

优先看：

- `test_stock_source_order.py`
- `test_fund_source_priority.py`
- `test_price_resilience.py`

### 改收益、快照、分析口径

优先看：

- `test_api_baseline.py`
- `test_market_breakdown.py`
- `test_market_calendar.py`

### 改后台

优先看：

- `test_admin_api_foundation.py`
- `test_admin_api_policies.py`
- `test_admin_invites.py`

### 改登录和密码

优先看：

- `test_auth_password_flow.py`
- `test_auth_force_password_change.py`
- `test_auth_rate_limit.py`

---

## 6. 一句结论

`kona_tool/tests/` 现在已经有不少真正在保线上逻辑的测试了。`

最大问题不是“没有测试”，而是：

`这些测试缺一张人能看懂的地图。`

现在这份文档，就是先把这张地图补上。
