# core/admin 目录说明

## 1. 目录用途

`core/admin/` 是管理后台的共享服务层。

它负责放：

- 后台共享常量
- 后台读缓存
- 运营配置读写规则
- 概览 / 用户统计 / 用户持仓 helper
- 巡检、provider test、价格告警这类后台服务逻辑

一句话：

`这里放后台跨路由复用的规则和服务，不放具体 Flask 路由。`

## 2. 应该放什么

- 后台多个路由都会用到的 helper
- 和后台业务直接相关，但不应该留在路由文件里的逻辑
- 后台巡检、报表、价格告警、provider test 这类服务能力

## 3. 不应该放什么

- 具体 `@bp.route(...)` 路由定义
- 和后台无关的通用工具
- 只为了某一个接口临时凑出来的一次性逻辑

## 4. 当前模块分工

- [constants.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/constants.py)
  后台共享常量、标签、运营配置键名、巡检常量
- [cache.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/cache.py)
  后台读缓存和用户持仓缓存
- [common.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/common.py)
  后台通用 helper
- [runtime_config.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/runtime_config.py)
  运行时配置与运营配置读写规则
- [dashboard.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/dashboard.py)
  概览、用户指标、留存、用户持仓 helper
- [monitoring.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/monitoring.py)
  巡检、价格告警、provider test
- [policies.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/policies.py)
  后台策略服务
- [user_admin.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/core/admin/user_admin.py)
  后台用户写操作服务

## 5. 当前规则

- 路由层只负责参数解析、鉴权、返回值组装
- 后台共享规则优先补到这里，不要再回塞到 [admin_routes.py](/Users/kona/Desktop/kaka/kona_repo/kona_tool/admin_routes.py)
- 如果某段逻辑只被一个后台路由使用，而且很短，可以继续留在对应路由文件里；但一旦跨路由复用，就应下沉到这里
