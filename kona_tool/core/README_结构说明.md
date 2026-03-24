# kona_tool/core 目录说明

`kona_tool/core/` 是后端真正的核心逻辑区。

如果说：

- `app.py` 是总入口
- `admin_routes.py` 是一部分后台路由入口

那 `core/` 就是这套后端的大脑和内脏。

这里不是“工具函数目录”那么简单，而是已经承担了项目里最重要的大部分业务逻辑。

---

## 1. 这个目录是干什么的

当前 `core/` 主要负责这些事：

- 数据库访问
- 资产代码识别
- 资产市场分类
- 股票和基金取价
- 价格缓存与价格源切换
- 快照计算
- 分析相关底层逻辑
- 认证和系统辅助能力
- 后台策略与权限

一句话：

`core/ 现在本质上是“后端核心业务总包”。`

这也是为什么后端后续如果要真正工程化，第一优先级一定是先梳理这里。

---

## 2. 当前文件结构

```text
core/
├─ admin/               # 管理后台相关规则
├─ asset_type.py        # 资产类型判断
├─ auth.py              # 认证相关
├─ db_admin_state.py    # refresh token / 邀请码 / 后台审计 / 接口策略 / 运行时配置 / 巡检报表
├─ db_asset_accounts.py # 交易记录 / 现金资产 / 其他资产 / 负债 CRUD
├─ db_portfolio.py      # 持仓 / 交易 / 已实现盈亏 / 组合兼容迁移
├─ db_snapshots.py      # 快照写入 / 历史曲线 / sync 版本号
├─ db_analysis.py       # 分析概览 / 收益日历 / 排行
├─ db_maintenance.py    # 休市日清理 / 快照修复
├─ db_users.py          # 用户查询 / 登录活跃打点 / 密码初始化 / 用户表兼容迁移 / 数据重绑
├─ db_schema.py         # 数据库建表 / 兼容补列 / 基础索引
├─ db.py                # 数据库访问与大量业务口径
├─ email.py             # 邮件相关
├─ fund.py              # 基金取价
├─ ip_region.py         # IP 地域识别
├─ market_calendar.py   # 市场交易日/开闭市判断
├─ news.py              # 快讯抓取与缓存
├─ parser.py            # 资产代码标准化
├─ policy_runtime.py    # 后台策略开关读取
├─ price.py             # 统一取价入口与缓存
├─ portfolio_metrics.py # 实时持仓指标统一口径
├─ portfolio_read_service.py # 实时持仓读侧服务
├─ history_read_service.py # 历史曲线读侧服务
├─ analysis_read_service.py # 分析页读侧服务
├─ request_trace.py     # 请求级阶段耗时记录
├─ snapshot.py          # 快照计算与保存
├─ source_health.py     # 行情源健康状态
├─ stock.py             # 股票与部分海外基金取价
├─ trend.py             # 首页/投资页趋势线取数
├─ system.py            # 系统辅助能力
└─ utils.py             # 公共工具
```

---

## 3. 按职责怎么理解

### 3.1 资产识别层

这几份文件主要负责“一个代码到底是什么资产”：

- [parser.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/parser.py)
- [asset_type.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/asset_type.py)
- [market_calendar.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/market_calendar.py)

它们负责：

- 标准化代码
- 判断 A 股 / 港股 / 美股 / 基金
- 判断市场对应交易日和开闭市状态

这部分是后面所有价格、收益、快照计算的前提。

### 3.2 价格系统

这几份文件组成当前的行情系统：

- [price.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/price.py)
- [stock.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/stock.py)
- [fund.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/fund.py)
- [source_health.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/source_health.py)

职责分工大致是：

- `price.py`
  - 统一入口
  - 缓存
  - 批量取价
  - 特殊映射
- `stock.py`
  - A 股、港股、美股、部分 `ft_` 资产取价
- `fund.py`
  - 普通基金、`968xxx` 基金取价
- `trend.py`
  - 给首页和投资页提供“近期估值趋势”统一接口
  - 股票 / 场内 ETF 取历史收盘，场外基金取历史净值
  - F10 历史为空时，对 `968xxx` 这类海外基金会回退到海外基金历史净值页
- `source_health.py`
  - 行情源健康信息

这是当前后端最敏感、最容易出线上口径问题的区域。

### 3.3 数据与口径中心

最重的一份文件是：

- [db.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db.py)
- [db_asset_accounts.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_asset_accounts.py)
- [db_portfolio.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_portfolio.py)
- [db_snapshots.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_snapshots.py)
- [db_analysis.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_analysis.py)
- [db_maintenance.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_maintenance.py)

它不只是“数据库工具”，而是当前后端的大型数据中心。

它里面同时承担：

- SQLite 连接管理
- 表初始化
- 持仓、交易、现金、负债读写
- 快照读写
- 分析数据查询
- 收益统计
- 后台巡检结果存储

这轮已经先把“交易记录 + 资产账户 CRUD”从 `db.py` 里抽成：

- [db_asset_accounts.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_asset_accounts.py)

这轮也把“持仓交易 + 已实现盈亏”从 `db.py` 里抽成：

- [db_portfolio.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_portfolio.py)

这轮还把“快照写入 + 历史曲线 + sync 版本号”从 `db.py` 里抽成：

- [db_snapshots.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_snapshots.py)

这轮还把“分析概览 / 收益日历 / 排行”从 `db.py` 里抽成：

- [db_analysis.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_analysis.py)

这轮还把“休市日清理 / 快照修复”从 `db.py` 里抽成：

- [db_maintenance.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_maintenance.py)

这轮也继续把“后台状态与认证辅助”从 `db.py` 里抽成：

- [db_admin_state.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_admin_state.py)

这轮还把“用户与登录状态”从 `db.py` 里抽成：

- [db_users.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db_users.py)

也就是：

- `db.py` 继续当数据库主入口
- 但资产账户细节、持仓交易、快照写入、分析查询、清理修复、邀请码、refresh token、后台审计日志、接口策略、运行时配置、用户登录状态、用户表兼容迁移这些，不再继续全塞在一个超大文件里

一句大白话：

`db.py 现在已经不只是“访问数据库”，而是“很多业务规则也堆进去了”。`

所以以后如果真要做后端分层，这个文件一定是重点。

### 3.3.1 读侧服务边界

这轮又补了几份读侧服务：

- [portfolio_read_service.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/portfolio_read_service.py)
- [history_read_service.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/history_read_service.py)
- [analysis_read_service.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/analysis_read_service.py)
- [portfolio_metrics.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/portfolio_metrics.py)

它们解决的不是“把文件拆小”这么表面的事，而是：

- handler 不再自己查库、取价、拼口径
- `app_factory.py` 不再继续长匿名闭包和临时读模型组装
- 同一条读链路的职责边界更清楚：谁查库、谁补价格、谁拼最终返回，一眼能看懂

现在可以按这个理解：

- `db_schema.py`：负责数据库结构初始化和兼容补齐
- `db*.py`：负责数据访问
- `*_read_service.py`：负责读模型组装
- `portfolio_metrics.py`：负责实时持仓统一指标口径

也就是：

`数据访问` 和 `读侧组装` 终于不是继续揉在一起了。

### 3.4 快照与收益计算

这部分主要在：

- [snapshot.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/snapshot.py)

它负责：

- 按当前持仓和价格计算资产统计
- 计算总资产、累计盈亏、当日盈亏
- 调用数据库写入每日快照
- 处理分市场收益拆分

这里和：

- [db.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db.py)
- [price.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/price.py)
- [market_calendar.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/market_calendar.py)

耦合很深。

### 3.5 管理后台与策略开关

这部分主要是：

- [policy_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/policy_runtime.py)
- [/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin)

当前它们负责：

- 策略是否启用
- 后台行为规则
- 用户管理相关规则
- 后台读缓存与运营配置
- 后台概览 / 用户统计 helper
- 后台巡检 / provider test / 价格告警服务

这说明后台逻辑现在也已经深入到了 `core/`。

这轮后台治理后，`core/admin/` 里又进一步明确成：

- [README_结构说明.md](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/README_结构说明.md)
- [constants.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/constants.py)
- [cache.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/cache.py)
- [runtime_config.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/runtime_config.py)
- [dashboard.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/dashboard.py)
- [monitoring.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/monitoring.py)

也就是：

- 后台共享逻辑优先往 `core/admin/` 收
- 路由文件只保留后台接口入口和少量参数解析

### 3.6 认证、系统与辅助模块

这几份更像配套模块：

- [auth.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/auth.py)
- [email.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/email.py)
- [ip_region.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/ip_region.py)
- [news.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/news.py)
- [system.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/system.py)
- [utils.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/utils.py)

这里面有的是正式业务能力，有的是通用辅助能力。

其中：

- `news.py` 已经不是单纯工具，而是一个完整的快讯抓取缓存模块
- `utils.py` 才更接近传统意义上的公共工具

### 3.7 请求链路诊断

这轮后端线上排障又往前走了一步：

- [request_trace.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/request_trace.py)
- [request_runtime.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/request_runtime.py)

现在一次 API 请求，除了原来的：

- `request_id`
- `path`
- `status`
- `duration_ms`

还会补：

- `X-Trace-Stage-Count`
- `X-Trace-Stage-Total-Ms`

并且日志里会带阶段摘要，比如：

- `portfolio.db`
- `portfolio.quotes`
- `portfolio.rates`
- `analysis.rank.assemble`

以后查线上慢请求、偶发超时、某个用户说“今天特别卡”的问题，会比以前更容易分清到底慢在哪一段。

这轮又往前补到了更多高频接口：

- `sync/bootstrap`
- `market/status`
- `market/indices`
- `price`
- `prices/batch`
- `rates`
- `search`

也就是说：

现在不只是投资页和分析页读链路能看阶段耗时，行情和同步这类高频链路也能更快定位慢点。

---

## 4. 当前最大的结构问题

### 4.1 `db.py` 太重

目前最明显的问题就是：

- [db.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/db.py)

太大、太重、职责太多。

它现在既像：

- 数据访问层

又像：

- 一部分业务规则层

这会带来两个问题：

- 查逻辑时不容易定位
- 后续拆分会很痛

### 4.2 价格系统横跨多个文件，规则容易散

现在价格相关逻辑分散在：

- `parser.py`
- `asset_type.py`
- `price.py`
- `stock.py`
- `fund.py`
- `market_calendar.py`

这不是错，但如果没有统一文档，就非常容易“改这里忘那里”。

你前面遇到的那些价格口径问题，本质上就说明这块必须靠文档和测试兜住。

### 4.3 `core/` 已经不只是 `core/`

它现在已经混了：

- 数据
- 价格
- 快照
- 认证
- 后台策略
- 快讯

所以后面真正工程化时，不能再把它当成一个模糊大目录继续涨。

---

## 5. 这个目录以后应该怎么治理

先别急着大拆代码，先按这个顺序来：

### 第一步：先文档分层

先让人看懂：

- 哪些是价格
- 哪些是数据库
- 哪些是快照
- 哪些是后台策略
- 哪些是认证和系统辅助

### 第二步：再测试分层

让测试和这些职责对应起来，比如：

- 价格源测试
- 快照口径测试
- 分析口径测试
- 数据访问测试

### 第三步：最后才是代码分层

后面如果真要拆，合理方向大致会是：

- 资产识别
- 价格系统
- 数据访问
- 快照与分析
- 后台策略
- 认证与系统辅助

但这一步不要急着现在就做。

---

## 6. 当前结论

`kona_tool/core/` 现在就是整个后端最重要、也最复杂的目录。

它的问题不是“代码不能跑”，而是：

`职责太多，边界还不够清楚。`

所以现在最正确的动作，不是马上暴力重构，而是：

- 先把结构讲清楚
- 先把规则写清楚
- 先把高风险逻辑文档化
- 再决定真正拆哪里

这也是为什么后面的工程整改，应该优先围着这里展开。
