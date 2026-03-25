# Portfolio Management System v12.0

一个现代化的投资组合管理系统，支持A股、港股、美股、基金等多种资产的实时行情监控和盈亏分析。

## 主要特性

- **多资产支持**: 支持A股、港股、美股、场外基金、互认基金、FT基金等
- **实时行情**: 集成多个数据源（新浪、腾讯、东方财富、天天基金、FT等）
- **智能代码解析**: 自动识别并标准化各种证券代码格式
- **SQLite数据库**: 高效的数据存储和查询
- **批量价格获取**: 优化前端性能，减少API请求次数
- **缓存机制**: 自动缓存价格数据，减少重复请求
- **多货币支持**: 自动汇率转换（USD、HKD、CNY）
- **交易记录**: 完整的交易历史记录
- **暗色模式**: 支持明暗主题切换
- **隐私模式**: 可隐藏敏感数据
- **导出功能**: 支持截图导出

## 项目结构

```
kona_tool/
├── app.py                 # 薄入口（对外导出 app/db/limiter；保留单测 patch 点）
├── app_factory.py         # 组装工厂（创建 app + 注册蓝图 + hook，不启动后台线程）
├── runtime_bootstrap.py   # dev 启动入口（后台线程/调度 + app.run）
├── wsgi.py                # gunicorn 入口（生产用 wsgi:app）
├── config.py              # 配置文件（.env + 环境变量）
├── core/                  # 核心逻辑（数据库/价格源/快照/分析/认证等）
├── scripts/               # 运维/补数/巡检脚本
├── tests/                 # 后端单测
├── static/                # 静态资源（web 构建产物、下载等）
├── templates/             # 模板
├── migrations/            # 数据迁移
├── requirements.txt       # Python 依赖
└── README_STRUCTURE.md    # 目录职责说明（更靠谱，优先看这个）
```

## 快速开始

### 环境要求

- Python 3.10+（CI 门禁跑 3.10/3.11；线上用 `.venv/bin/python`）
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python app.py
```

程序启动后会自动在浏览器中打开 `http://127.0.0.1:52345`

## API接口

### 获取单个价格
```
GET /api/price?code=sh600000
```

### 批量获取价格
```
POST /api/prices/batch
{
  "codes": ["sh600000", "sz000001", "f_110017"]
}
```

### 获取汇率
```
GET /api/rates
```

### 获取持仓数据
```
GET /api/portfolio
```

### 添加资产
```
POST /api/portfolio/add
{
  "code": "sh600000",
  "name": "浦发银行",
  "qty": 1000,
  "price": 10.0,
  "curr": "CNY"
}
```

### 更新资产
```
POST /api/portfolio/update
{
  "code": "sh600000",
  "field": "qty",
  "val": 2000
}
```

### 删除资产
```
POST /api/portfolio/delete
{
  "code": "sh600000"
}
```

### 加仓
```
POST /api/portfolio/buy
{
  "code": "sh600000",
  "price": 11.0,
  "qty": 500
}
```

### 减仓
```
POST /api/portfolio/sell
{
  "code": "sh600000",
  "price": 11.5,
  "qty": 300
}
```

### 获取交易记录
```
GET /api/transactions?limit=100
```

### 搜索股票
```
GET /api/search?q=600000
```

## 代码格式说明

- **场外基金**: `f_110017` (易方达增强回报债券A)
- **沪市股票**: `sh600000` (浦发银行)
- **深市股票**: `sz000001` (平安银行)
- **港股**: `hk00700` (腾讯)
- **美股**: `gb_aapl` (苹果)
- **FT基金**: `ft_LU1116320737` (汇丰贝莱德基金)

### 智能识别

输入以下格式会自动转换：
- 纯数字 `110017` -> `f_110017`
- `600000` -> `sh600000`
- `000001` -> `sz000001`
- `900901` -> `sh900901`（沪B，币种 USD）
- `200002` -> `sz200002`（深B，币种 HKD）
- `00700.HK` -> `hk00700`
- `AAPL` -> `gb_aapl`

## 配置说明

编辑 `config.py` 可以自定义以下配置：

- 服务器地址和端口
- API超时时间
- 重试次数和延迟
- 缓存过期时间
- 默认汇率
- 数据库路径

## 数据迁移

从旧版本CSV迁移到新版本数据库：

```python
from core.db import DatabaseManager
import config

db = DatabaseManager(str(config.DATABASE_PATH))
db.backup_from_csv(str(config.BACKUP_CSV_PATH))
```

## 注意事项

1. 首次运行会自动创建数据库
2. 价格数据有60秒缓存
3. 部分API可能有访问限制
4. 建议定期备份数据库文件

## 版本历史

### v12.0.1 (当前版本)
- 修复 B股币种识别：
  - `sh900xxx -> USD`
  - `sz200xxx -> HKD`
- 增加历史持仓 B股币种自动回填（幂等执行）
- 与 Flutter/Web 币种显示口径对齐，避免 `market='a'` 覆盖 `curr`

### v12.0
- 全新 Flutter / Vue3 多端支持与重构
- 新增投资收益分析、日历视图、快照统计
- 新增安全认证、指纹登录及管理控制台
- 完全兼容腾讯云轻量服务器自动部署

### v10.0
- 重构架构，模块化设计
- 改用SQLite数据库
- 添加批量价格API
- 优化前端性能
- 添加缓存机制
- 完善错误处理和日志

### v9.0
- 修复基金价格获取
- 优化代码解析

### v8.0
- 集成天天基金接口
- 支持场外基金

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request
