# 咔咔记账 - Portfolio Management System

[![Version](https://img.shields.io/badge/version-v12.0.0-blue.svg)](https://github.com/konaoo/kona)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Flet](https://img.shields.io/badge/flet-0.80.0+-purple.svg)](https://flet.dev/)

个人投资组合管理系统，支持多资产类型（A股、港股、美股、基金）的实时行情监控和盈亏分析。

## 📁 项目结构

```
kona/
├── HI/                    # Flet 移动端应用
│   ├── main.py           # 移动端入口
│   ├── flet.yaml         # 打包配置
│   ├── api.py            # API 客户端
│   ├── auth/             # 用户认证模块
│   └── pages/            # 页面组件
│
└── kona_tool/            # Flask 后端服务
    ├── app.py            # 服务端入口
    ├── config.py         # 配置文件
    ├── core/             # 核心业务逻辑
    │   ├── db.py        # 数据库管理
    │   ├── price.py     # 价格获取
    │   ├── auth.py      # 用户认证
    │   └── ...
    ├── templates/        # Web 模板
    └── requirements.txt  # Python 依赖
```

## ✨ 核心功能

### 📱 移动端 (HI)
- ✅ **多平台支持** - iOS / Android / Web
- ✅ **实时行情** - 支持 A股/港股/美股/基金
- ✅ **资产管理** - 持仓、现金、其他资产、负债
- ✅ **盈亏分析** - 日/月/年度收益统计
- ✅ **市场快讯** - 实时财经新闻
- ✅ **用户认证** - 邮箱验证码登录

### 🖥️ 服务端 (kona_tool)
- ✅ **RESTful API** - 标准化接口设计
- ✅ **多数据源** - 新浪、腾讯、东方财富、FT
- ✅ **智能识别** - 自动识别股票代码类型
- ✅ **缓存机制** - 60秒缓存减少请求
- ✅ **多用户支持** - JWT 认证
- ✅ **数据库优化** - 9个索引提升性能
- ✅ **每日快照** - 自动保存资产历史

## 🚀 快速开始

### 服务端部署

#### 1. 克隆项目
```bash
git clone https://github.com/konaoo/kona.git
cd kona/kona_tool
```

#### 2. 安装依赖
```bash
pip3 install -r requirements.txt
```

#### 3. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置 JWT_SECRET
nano .env
```

生成随机密钥：
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 4. 启动服务
```bash
python3 app.py
```

服务将运行在 `http://0.0.0.0:5003`

### 移动端打包

#### Android APK
```bash
cd HI
flet build apk
```

#### iOS IPA
```bash
cd HI
flet build ipa
```

## 🔧 配置说明

### 环境变量 (.env)

```bash
# JWT 认证密钥（必须设置）
JWT_SECRET=your-super-secret-jwt-key

# 数据库路径（可选）
DATABASE_PATH=/path/to/portfolio.db

# 服务器配置（可选）
HOST=0.0.0.0
PORT=5003
DEBUG=False

# 日志级别（可选）
LOG_LEVEL=INFO
```

### Flet 配置 (HI/flet.yaml)

```yaml
name: 咔咔记账
description: Portfolio Management App
version: 1.0.0

dependencies:
  flet: ">=0.80.0"
  python-dotenv: ">=1.0.0"
  requests: ">=2.31.0"

android:
  package: com.kona.portfolio
  permissions:
    - android.permission.INTERNET
```

## 📚 API 文档

### 认证相关

#### 登录
```http
POST /api/auth/login
Content-Type: application/json

{
  "user_id": "用户唯一ID",
  "email": "user@example.com"
}
```

### 资产相关

#### 获取持仓
```http
GET /api/portfolio
Authorization: Bearer {token}
```

#### 添加资产
```http
POST /api/portfolio/add
Authorization: Bearer {token}
Content-Type: application/json

{
  "code": "000001",
  "name": "平安银行",
  "qty": 100,
  "price": 10.5,
  "curr": "CNY"
}
```

#### 获取价格（批量）
```http
POST /api/prices/batch
Content-Type: application/json

{
  "codes": ["000001", "600000", "gb_AAPL"]
}
```

### 分析相关

#### 盈亏概览
```http
GET /api/analysis/overview?period=all
Authorization: Bearer {token}
```

#### 收益日历
```http
GET /api/analysis/calendar?type=day
Authorization: Bearer {token}
```

更多 API 请查看 [API 文档](kona_tool/README.md)

## 🎯 支持的资产类型

| 资产类型 | 代码格式 | 示例 |
|---------|---------|------|
| A股 (上海) | `sh{代码}` | `sh600000` (浦发银行) |
| A股 (深圳) | `sz{代码}` | `sz000001` (平安银行) |
| A股 (北交所) | `bj{代码}` | `bj430047` |
| 港股 | `hk{代码}` | `hk00700` (腾讯) |
| 美股 | `gb_{代码}` | `gb_AAPL` (苹果) |
| 场外基金 | `f_{代码}` | `f_161725` |
| FT 基金 | `ft_{ISIN}` | `ft_LU0320765059` |

## 🛠️ 技术栈

### 后端
- **Python 3.9+**
- **Flask 3.0** - Web 框架
- **SQLite** - 数据存储
- **APScheduler** - 任务调度
- **Flask-Limiter** - API 速率限制
- **PyJWT** - JWT 认证

### 前端
- **Flet** - 跨平台移动端框架
- **Python** - 业务逻辑

### 数据源
- 新浪财经 - 股票实时行情
- 腾讯财经 - 股票行情备用
- 东方财富 - 基金数据
- 天天基金 - 基金净值
- Financial Times - 海外基金

## 📊 数据库优化

项目使用 SQLite 数据库，并针对查询性能创建了以下索引：

```sql
-- 持仓查询优化
CREATE INDEX idx_portfolio_user_id ON portfolio(user_id);
CREATE INDEX idx_portfolio_code ON portfolio(code);

-- 交易记录优化
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_code ON transactions(code);

-- 资产查询优化
CREATE INDEX idx_cash_assets_user_id ON cash_assets(user_id);
CREATE INDEX idx_other_assets_user_id ON other_assets(user_id);
CREATE INDEX idx_liabilities_user_id ON liabilities(user_id);

-- 快照查询优化
CREATE INDEX idx_daily_snapshots_date ON daily_snapshots(date);
CREATE INDEX idx_daily_snapshots_user_id ON daily_snapshots(user_id);
```

## 🔒 安全性

- ✅ JWT Token 认证
- ✅ 环境变量加密密钥
- ✅ API 速率限制（防止滥用）
- ✅ 敏感数据不提交 Git

## 📈 性能优化

- ✅ 数据库索引优化（9个索引）
- ✅ API 缓存机制（60秒 TTL）
- ✅ 批量价格获取接口
- ✅ 异步任务调度

## 🐛 常见问题

### 1. Flet 打包报错：`ModuleNotFoundError: No module named 'requests'`

**解决方案**：确保 `HI/flet.yaml` 文件存在并包含所有依赖。

### 2. JWT_SECRET 警告

**解决方案**：创建 `.env` 文件并设置 `JWT_SECRET` 环境变量。

### 3. 数据库锁定错误

**解决方案**：SQLite 不支持高并发，生产环境建议使用 PostgreSQL。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[MIT License](LICENSE)

## 📮 联系方式

- GitHub: [@konaoo](https://github.com/konaoo)
- Email: your-email@example.com

---

**🚀 Generated with [Claude Code](https://claude.com/claude-code)**

## 🎉 更新日志

### v12.0.0 (2026-01-19)
- ✨ 重构项目结构，统一管理前后端代码
- 🔒 优化 JWT_SECRET 安全配置
- ⚡ 添加数据库索引提升查询性能
- 📦 集成 APScheduler、Flask-Limiter
- 🐛 修复 Flet App 打包依赖问题
- 📝 完善环境变量配置

更多历史版本请查看 [CHANGELOG.md](kona_tool/CHANGELOG.md)
