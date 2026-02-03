# 咔咔记账 - Portfolio Management System

一个个人投资组合管理系统，后端为 Python Flask，前端为 Flutter（移动端/桌面端/Web）。
目标：换电脑或换人接手，也能快速理解项目结构、部署方式、运行方式和每个目录的作用。

**当前线上后端**：AWS 上运行 `kona_tool`。
**前端**：Flutter，位于本仓库的 `flutter/`。

---

**快速入口**

- 项目结构说明：`docs/STRUCTURE.md`
- 本地运行指南：`docs/RUNBOOK.md`
- 部署方式说明：`docs/DEPLOYMENT.md`
- Flutter 新电脑配置：`docs/FRONTEND_SETUP.md`
- API 清单：`docs/API.md`
- API 参数与返回：`docs/API_DETAILS.md`
- 后端模块说明：`docs/CORE_MODULES.md`
- 维护与备份：`docs/MAINTENANCE.md`

---

**一、仓库结构总览**

```
.
├─ .github/workflows/          # GitHub Actions 自动部署
├─ flutter/                    # Flutter 前端
├─ kona_tool/                  # 后端 Flask 项目
├─ archive/HI/                 # 旧版本代码（已归档，不再运行）
├─ docs/                       # 文档
└─ README.md
```

---

**二、前端（Flutter）**

**1) 目录结构**

```
flutter/
├─ lib/
│  ├─ main.dart                # 应用入口
│  ├─ config/                  # 主题、API 配置
│  ├─ models/                  # 数据模型
│  ├─ pages/                   # 页面
│  ├─ providers/               # 状态管理
│  ├─ services/                # API 调用
│  └─ widgets/                 # 组件
├─ assets/                     # 资源文件
├─ android/ ios/ web/ macos/ windows/ linux/   # 多平台支持
└─ pubspec.yaml                # 依赖与资源配置
```

**2) API 地址配置**

```
flutter/lib/config/api_config.dart
```

示例：
```
http://35.78.253.89:5003
```

本地开发时建议改成：
```
http://127.0.0.1:5003
```

**3) 前端运行（本地）**

```
cd flutter
flutter pub get
flutter run
```

---

**三、后端（kona_tool）**

**1) 目录结构**

```
kona_tool/
├─ app.py                      # Flask 入口
├─ core/                       # 核心业务逻辑
│  ├─ auth.py                  # 用户认证
│  ├─ db.py                    # 数据库管理
│  ├─ fund.py                  # 基金数据
│  ├─ news.py                  # 新闻数据
│  ├─ parser.py                # 证券代码解析
│  ├─ price.py                 # 价格与缓存
│  ├─ snapshot.py              # 截图/导出
│  ├─ stock.py                 # 股票数据
│  ├─ system.py                # 系统工具
│  └─ utils.py                 # 工具函数
├─ templates/                  # Web 页面模板
├─ migrations/                 # 数据库迁移
├─ requirements.txt            # Python 依赖
├─ config.py                   # 配置（端口、缓存、JWT、数据源等）
├─ portfolio.db                # SQLite 数据库
├─ app.pid                     # 后端进程 PID（自动部署用）
├─ rotate_log.sh               # 日志归档脚本
└─ archive/old_files/          # 归档的旧文件与测试文件
```

**2) 本地运行（后端）**

```
cd kona_tool
pip3 install -r requirements.txt
python3 app.py
```

默认端口：`config.py` 中设置（当前为 `5003`）。

**3) 常用 API（示例）**

- `GET /api/portfolio`
- `POST /api/prices/batch`
- `GET /api/rates`
- `GET /api/news/latest`
- `GET /api/analysis/overview`

完整接口详见 `kona_tool/app.py`。

---

**四、部署方式（AWS + GitHub Actions）**

部署流程：

1. 本地开发并 push 到 GitHub `main`
2. GitHub Actions 自动连接 AWS
3. 自动 `git pull` + 安装依赖 + 重启服务
4. 自动健康检查（请求 `/api/rates`）

部署文件：
```
.github/workflows/deploy.yml
```

---

**五、日志与自动维护**

- 日志文件：`kona_tool/app.log`
- 归档脚本：`kona_tool/rotate_log.sh`
- 自动归档：每周一凌晨 2 点（crontab）
- 归档路径：`kona_tool/archive/logs/`

---

**六、常用检查**

**1) 服务是否在运行**
```
ps -ef | grep "python3 app.py"
```

**2) 健康检查**
```
http://<服务器IP>:5003/api/rates
```

---

**七、数据与安全**

- `portfolio.db` 是核心数据，建议定期备份
- 生产环境必须设置 `JWT_SECRET`
- 部署私钥只放 GitHub Secrets
- 不要把 `.env` 或私钥提交到仓库

---

**八、归档说明**

- `archive/HI`：旧版本代码
- `kona_tool/archive/old_files`：旧测试文件与旧日志

---

**九、换电脑快速上手**

1. 克隆仓库
2. 后端运行：`kona_tool`
3. 前端运行：`flutter`
4. 确保前端 API 地址指向后端
5. 若部署到 AWS，检查 `deploy.yml` 和 GitHub Secrets

---

**十、进一步文档**

- 结构说明：`docs/STRUCTURE.md`
- 部署说明：`docs/DEPLOYMENT.md`
- 本地运行：`docs/RUNBOOK.md`
- Flutter 配置：`docs/FRONTEND_SETUP.md`
- API 清单：`docs/API.md`
- API 参数与返回：`docs/API_DETAILS.md`
- 后端模块说明：`docs/CORE_MODULES.md`
- 维护与备份：`docs/MAINTENANCE.md`
