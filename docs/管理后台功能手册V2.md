# Admin Console V2 README（邀请码管理 + APP 用户管理 + 接口策略管理）

更新时间：2026-02-13

## 1. 目标与范围

本次改造在现有 `/admin/*` 模板后台基础上完成，不新建独立 SPA。

已落地能力：
- 邀请码管理：生成、列表、作废、导出、统计（批次/状态）
- APP 用户管理：启用/禁用、管理员角色切换、管理员重置临时密码、强制改密、强制下线
- 接口策略管理：上游通道开关 + API 分组开关/限流，策略持久化到数据库并运行时即时生效
- 认证硬约束：`must_change_password=1` 时，仅允许改密/登出/me
- 管理写操作统一审计（admin_audit_logs）

## 2. 数据库变更

### 2.1 users 表新增字段（Migration 009）
- `must_change_password INTEGER NOT NULL DEFAULT 0`
- `password_reset_at TIMESTAMP NULL`
- `password_reset_by TEXT NULL`

### 2.2 新增策略表（Migration 010）
表：`admin_api_policies`
- `id INTEGER PK`
- `scope_key TEXT UNIQUE NOT NULL`
- `scope_type TEXT NOT NULL`（`upstream` / `api_group`）
- `enabled INTEGER NOT NULL DEFAULT 1`
- `limit_per_min INTEGER NULL`
- `note TEXT NULL`
- `updated_by TEXT`
- `updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

默认策略（自动初始化）：
- `upstream.price`
- `upstream.rate`
- `upstream.news`
- `api.auth`（120/min）
- `api.portfolio`（240/min）
- `api.news`（120/min）

### 2.3 用户编号规则（Migration 011）
- `user_number` 作为对外用户编号
- 编号起始：`10000`
- 分配规则：每新注册用户 `+1`
- 迁移脚本：`migrations/011_resequence_user_numbers.py`
  - 会将现有用户按 `created_at,id` 重排为 `10000..`

## 3. Admin API（新增/增强）

### 3.1 用户管理
- `POST /api/admin/users/password/reset`
  - 入参：`user_id`, `temp_password?`, `force_change=true`
  - 出参：`status`, `user_id`, `must_change_password`, `revoked_refresh_tokens`, `temp_password?`
- `POST /api/admin/users/sessions/revoke`
  - 入参：`user_id`
  - 出参：`status`, `user_id`, `revoked_refresh_tokens`
- `POST /api/admin/users/update`
  - 已支持：`is_admin`, `status`

### 3.2 接口策略管理
- `GET /api/admin/apis/policies`
- `POST /api/admin/apis/policies/update`
  - 入参：`scope_key`, `enabled?`, `limit_per_min?`, `note?`
- `POST /api/admin/apis/policies/batch_update`
  - 入参：`items[]`

### 3.3 邀请码运营增强
- `GET /api/admin/invites/stats`
- 已保留：`/api/admin/invites/generate|list|revoke|export`

## 4. Auth 行为补充

`POST /api/auth/login` 的 `user` 包含 `must_change_password`。

当 `must_change_password=1` 时，除以下白名单外，其余业务接口返回：
- HTTP `403`
- `{"error":"Password change required","code":"PASSWORD_CHANGE_REQUIRED"}`

白名单：
- `/api/auth/password/change`
- `/api/auth/logout`
- `/api/auth/me`

## 5. 后台页面变化（模板）

文件：
- `kona_tool/templates/admin_users.html`
- `kona_tool/templates/admin_invites.html`
- `kona_tool/templates/admin_apis.html`
- `kona_tool/templates/admin_login.html`

已完成：
- 新增后台登录页：`/admin/login`（使用现有账号密码登录后校验 admin 权限）
- 后台页面未登录自动跳转登录页，支持“退出登录”
- 后台会话支持 `access+refresh`：access 过期后自动刷新并重试请求，降低频繁跳登录
- 用户页新增：管理员切换、重置密码、强制下线、需改密展示
- 邀请码页新增：统计卡、筛选联动、迁移入口
- 接口页新增：策略表（启停/限流/备注）与健康检测同页
- 写操作统一二次确认 + toast 反馈

## 6. 关键实现文件

- `kona_tool/admin_routes.py`
- `kona_tool/app.py`
- `kona_tool/core/auth.py`
- `kona_tool/core/db.py`
- `kona_tool/core/policy_runtime.py`
- `kona_tool/core/admin/policies.py`
- `kona_tool/core/admin/user_admin.py`
- `kona_tool/core/price.py`
- `kona_tool/core/news.py`
- `kona_tool/core/system.py`
- `kona_tool/migrations/009_add_user_force_password_change.py`
- `kona_tool/migrations/010_add_admin_api_policies.py`

## 7. 上线顺序（建议）

1. 拉取代码并执行迁移
2. 重启服务
3. 用管理员账号登录后台验证用户页/邀请码页/接口页
4. 观察 48 小时（403/429/审计日志）后再清理兼容逻辑

参考命令：

```bash
cd /home/ec2-user/portfolio/kona_tool
KONA_DATABASE_PATH=/home/ec2-user/portfolio/kona_tool/portfolio.db python3 migrations/009_add_user_force_password_change.py
KONA_DATABASE_PATH=/home/ec2-user/portfolio/kona_tool/portfolio.db python3 migrations/010_add_admin_api_policies.py
sudo systemctl restart kona.service
curl -sS http://127.0.0.1:5003/health
```

## 8. 测试

本次改动相关测试：
- `kona_tool/tests/test_admin_users_password_reset.py`
- `kona_tool/tests/test_auth_force_password_change.py`
- `kona_tool/tests/test_admin_api_policies.py`
- `kona_tool/tests/test_admin_api_foundation.py`
- `kona_tool/tests/test_admin_invites.py`
- `kona_tool/tests/test_auth_rate_limit.py`

本地执行：

```bash
cd /Users/kona/Desktop/kaka/kona_repo/kona_tool
../.venv/bin/python -m pytest -q \
  tests/test_admin_users_password_reset.py \
  tests/test_auth_force_password_change.py \
  tests/test_admin_api_policies.py \
  tests/test_admin_api_foundation.py \
  tests/test_admin_invites.py \
  tests/test_auth_rate_limit.py
```

## 9. 数据边界（安全）

- 服务端保存：用户业务数据 + 用户资料（用户名/昵称/头像等）+ 密码哈希 + refresh token 哈希
- 服务端不保存：生物特征原始数据（指纹/面容）
- 生物识别校验由 iOS/Android 系统完成

## 10. 对你当前账号体系的说明

- 登录方式：`用户名 + 密码`
- 注册方式：`用户名 + 密码 + 邀请码`
- 邀请码为一次性，可作废，可批次管理
- 管理员可直接重置用户临时密码并触发强制改密

---

## 11. 运营后台体验重构（全中文运营版）

本次新增的运营向改造点：

- 后台页面文案统一为中文业务语义，技术字段仅在“查看技术详情”中展示
- 菜单重构为：运营总览 / 用户中心 / 邀请码中心 / 接口与策略 / 数据运维 / 系统配置 / 操作审计
- 全局统一确认弹窗（普通确认、风险确认、确认词确认）
- 全局统一详情抽屉（替代 alert/prompt）
- 全局统一错误文案映射（后端英文错误自动转中文运营文案）

新增接口（保持兼容，不破坏旧接口）：

- `GET /api/admin/meta/dictionaries`：下发状态/动作/策略中文词典
- `GET /api/admin/summary/todo`：运营待办事项（邀请码、通道、失败操作等）
- `GET /api/admin/users/sessions/count?user_id=...`：预估在线会话数
- `POST /api/admin/data/snapshot/cleanup_weekend/preview`：周末收益清理预览
- `GET /api/admin/data/backup/latest`：最近备份信息
- `POST /api/admin/config/reset`：配置恢复默认值（单项/全部）
- `GET /api/admin/audit/export`：按筛选条件导出审计 CSV
