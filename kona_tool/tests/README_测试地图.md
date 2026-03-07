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

它主要在保这些东西：

- 基础接口能不能正常返回
- Web 配置接口口径
- App 版本和下载配置
- 分析页概览 / 日历相关基础逻辑
- 持仓、收益、快照的很多核心默认行为

一句大白话：

`这是后端主链路的基础防线。`

如果它挂了，通常不是小修小补，而是核心行为变了。

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
