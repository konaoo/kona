# kona_tool 目录说明

## 1. 目录用途

`kona_tool/` 是咔咔记账项目的 Python 后端工程目录。

当前它不只是 API 服务目录，还同时承载：

- Web API
- 认证
- 持仓与交易逻辑
- 行情/价格源处理
- 快照任务
- 分析数据
- 管理后台接口
- 部分静态资源与模板

这也是当前整个项目里结构复杂度最高的目录。

---

## 2. 当前核心子目录

```text
kona_tool/
├─ app.py            # 主入口
├─ analysis_handlers.py # 分析页请求参数解析 / 概览日历排行处理
├─ analysis_routes.py # 分析页概览 / 日历 / 排行入口
├─ asset_account_handlers.py # 资产账户 / 交易记录处理
├─ asset_account_routes.py  # 现金 / 其他资产 / 负债 / 交易记录入口
├─ auth_routes.py    # 认证路由入口
├─ market_handlers.py # 市场状态 / 首页指数处理
├─ market_routes.py  # 市场状态 / 首页指数 / 同步引导入口
├─ market_runtime.py # 市场状态缓存与强制刷新运行时
├─ misc_routes.py    # 旧页兼容跳转 / 历史 / 健康检查入口
├─ misc_handlers.py  # 历史 / 趋势 / 健康检查处理
├─ news_routes.py    # 快讯页 / 快讯接口入口
├─ portfolio_handlers.py # 投资持仓 / 交易 / 快照处理
├─ portfolio_runtime.py # 持仓标准化 / 幂等 / 撤销 / 多币种换算运行时
├─ portfolio_routes.py # 投资持仓 / 交易 / 快照入口
├─ quote_handlers.py # 单价 / 批量报价 / 汇率 / 搜索处理
├─ quote_routes.py   # 单价 / 批量报价 / 汇率 / 搜索入口
├─ request_runtime.py # 请求钩子 / 安全审计 / 接口分组限流 / 后台写审计
├─ snapshot_runtime.py # 异步快照 / 快照节流 / 后台快照调度运行时
├─ startup_runtime.py # 指标令牌校验 / 浏览器自动打开 / 启动线程拉起
├─ sync_handlers.py  # sync/bootstrap 增量同步引导处理
├─ system_routes.py  # 公开配置 / 系统路由入口
├─ web_entry_handlers.py # Web 门户 / SPA / 兼容跳转处理
├─ web_entry_routes.py # Web 门户 / SPA 入口 / 静态测试页入口
├─ core/             # 核心逻辑
├─ migrations/       # 数据迁移
├─ scripts/          # 后端脚本
├─ static/           # 静态资源
├─ templates/        # 模板
├─ tests/            # 后端测试
├─ archive/          # 历史归档
├─ portfolio.db      # 本地 SQLite 数据文件
└─ requirements.txt  # Python 依赖
```

其中 `core/` 当前又承担了多个职责，包括：

- 数据库访问
- 价格获取
- 代码解析
- 基金逻辑
- 股票逻辑
- 分析相关逻辑

---

## 3. 应该放什么

这个目录应该放：

- 后端源码
- 后端测试
- 数据迁移
- 后端专属脚本
- 必要的静态资源和模板

更直白一点：

- 能直接参与后端运行的，才适合放这里
- 只是本地排障、临时查看、一次性手工处理的，不该长期留在这里

---

## 4. 不应该放什么

这个目录不应该长期混放：

- 无说明的历史垃圾
- 本地临时调试文件
- 不受控的数据备份
- 与后端无关的客户端构建产物
- 根目录运行日志
- 一次性注册脚本
- 手工查看数据库的小脚本

另外这些东西要明确识别为“特殊目录”，不能和主源码混为一谈：

- `archive/`
- `portfolio.db`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`

---

## 5. 当前逻辑

`kona_tool/` 当前本质上是一个“大后端包”，而不是干净分层后的服务目录。

它把很多角色揉在一起了：

- API 入口
- 业务服务
- 数据访问
- 报价抓取
- 快照任务
- 管理接口
- 页面静态资源

这套结构早期能跑，但现在复杂度已经很高。

所以后续对整个项目做工程化时，第一优先级应该是梳理这里。

说白了：

`这个目录现在最像“功能都塞进来了”，而不是“边界已经设计好”。`

---

## 6. 关键规则

### 6.1 `app.py` 是入口，不应该无限膨胀

当前主入口在：

- [app.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/app.py)

后续任何新增能力，都应该警惕继续把路由、业务编排、数据逻辑全塞进这里。

### 6.2 `core/` 是当前逻辑集中区

当前最重要的核心模块都在：

- [/Users/kona/Desktop/kaka/kona_repo/kona_tool/core](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core)

这里后续需要继续细分，至少要逐步区分：

- 价格源逻辑
- 数据访问
- 分析逻辑
- 任务逻辑
- 管理后台逻辑

### 6.3 数据文件和源码要分开认知

当前目录里有：

- `portfolio.db`

这说明当前目录同时混着：

- 源码
- 配置
- 运行数据

这在本地开发阶段能接受，但在长期工程治理里，必须明确这是结构风险点。

### 6.4 任务和服务耦合较深

当前快照、巡检、补数、价格处理等逻辑，都和后端主工程耦合很深。

所以后续治理时，要重点识别：

- 哪些属于同步 API
- 哪些属于后台任务
- 哪些属于运维脚本

### 6.5 根目录要尽量只留正式入口和正式资源

`kona_tool/` 根目录更适合留这些东西：

- `app.py`
- `analysis_handlers.py`
- `analysis_routes.py`
- `asset_account_handlers.py`
- `asset_account_routes.py`
- `auth_routes.py`
- `market_handlers.py`
- `market_routes.py`
- `market_runtime.py`
- `misc_handlers.py`
- `misc_routes.py`
- `news_routes.py`
- `portfolio_handlers.py`
- `portfolio_runtime.py`
- `portfolio_routes.py`
- `quote_handlers.py`
- `quote_routes.py`
- `request_runtime.py`
- `snapshot_runtime.py`
- `startup_runtime.py`
- `sync_handlers.py`
- `system_routes.py`
- `web_entry_handlers.py`
- `web_entry_routes.py`
- `admin_routes.py`
- `config.py`
- `wsgi.py`
- `requirements.txt`
- `market_holidays.json`
- `portfolio.db`
- 正式子目录

不应该继续往根目录塞：

- `app.log`
- `test_db.py`
- `register_konae.py`
- `__pycache__/`
- `.pytest_cache/`
- `.DS_Store`

这类东西要么归档，要么直接清掉。

### 6.6 文件放置规则

以后往 `kona_tool/` 放文件，按这套规则判断：

- 路由入口和启动文件：放根目录
- 核心业务逻辑：放 `core/`
- 数据迁移：放 `migrations/`
- 后端专属脚本：放 `scripts/`
- 正式测试：放 `tests/`
- 静态资源：放 `static/`
- 模板：放 `templates/`
- 历史归档：放 `archive/` 或仓库级 `archive/`

如果一个文件说不清“为什么必须留在根目录”，默认就不该放根目录。

---

## 7. 当前结论

`kona_tool/` 是当前项目的复杂度中心，也是后续最值得优先梳理的目录。

后面如果继续深化这套目录文档，建议下一步直接单独补：

- `kona_tool/core/README_结构说明.md`
- `kona_tool/scripts/README.md`
- `kona_tool/tests/README.md`
- `kona_tool/static/README.md`

因为真正的结构治理，最终一定会落到这里。
