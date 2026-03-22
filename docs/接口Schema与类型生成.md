# 接口 Schema 与类型生成

这份文档只讲一件事：

`API 的唯一口径怎么落到前端类型上。`

---

## 1. 统一规则

### 1.1 唯一口径

- 统一以 `docs/openapi.yaml` 作为接口 Schema 的唯一入口。
- 只要后端接口有新增/删除/字段调整，就要同步更新这份文件。

### 1.2 当前现实

`openapi.yaml` 目前覆盖还不完整，但它是“唯一入口”。  
后续改接口时，先补齐对应路径和字段，再让类型生成跟上。

补一条现在已经收过的规则：

- `接口总览.md` 和 `接口详情.md` 不再硬扫 `app.py`
- 现在统一按 Flask 实际路由表生成
- 所以蓝图里的真实接口也会被带出来

### 1.3 路径补齐（快速兜底）

如果只是为了先把“接口路径列表”补齐，可以执行：

```bash
python3 scripts/sync_openapi_paths.py
```

它会把当前后端实际路由中“缺失的路径”自动补到 `openapi.yaml`，并标记为待补字段的 TODO。
后续再逐条把字段补完整。

---

## 2. Web 端类型生成

### 2.1 命令

在仓库根目录执行：

```bash
scripts/generate_openapi_types_web.sh
```

或直接在 `web/` 里执行：

```bash
npm run gen:api
```

### 2.2 输出位置

生成文件在：

- `/Users/kona/Desktop/kaka/kona_repo/web/src/types/openapi.generated.ts`

这是 **自动生成文件**，不要手改。

当前确认过：

- `/api/portfolio/modify` 已经是新口径
- `/api/portfolio/adjustment_event`
- `/api/portfolio/transactions`

这些都会跟着 `openapi.yaml` 一起进 Web 类型文件。

另外现在已经补了投资主接口的稳定 `operationId`：

- `getPortfolio`
- `modifyPortfolioAsset`
- `addPortfolioAdjustmentEvent`
- `getPortfolioTransactions`

这样 Web / Flutter 生成出来的方法名会更稳定，不会每次都靠自动命名。

这一轮又往前推进了一步：

- 认证
- 分析
- 现金 / 其他资产 / 负债
- 行情 / 汇率 / 同步引导

这几组主 App 高频接口也已经补了稳定 `operationId`。

其中：

- `/api/portfolio/transactions` 现在是“混合记录列表”
- 同一条记录可能是交易、收益事件，或者修正记录
- 所以 Schema 里先按“一套公共结构 + 可选字段”描述，不强行拆得很死

---

## 3. Flutter 端类型生成

> 这一步需要 Java 环境（openapi-generator 会用到）。

执行：

```bash
scripts/generate_openapi_types_flutter.sh
```

输出目录：

- `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/generated/openapi`

说明：

- 脚本现在会先清掉旧的生成目录，再重新生成，避免陈旧文件继续污染分析结果。
- 生成后 **请检查编译体量**，必要时再决定要不要提交到仓库。
- 这一步现在已经可以正常跑通，不再只是“先留脚本”。
- 当前先把它用于“接口结构对齐”和“方法名稳定”，还没有要求业务层马上全量切到生成类型。
- 如果本机没装 Java，脚本现在会直接给中文提示，不会再一头雾水地失败。
- 当前还要额外注意一件事：
  - `脚本能生成成功` 不等于 `整个生成包已经能过 flutter analyze`
  - 现在投资主接口的方法名和模型已经稳定下来，但整份 `openapi.yaml` 里仍有少数通用 Schema 会生成出 Dart 不兼容代码
  - 所以后续如果要正式启用整包生成，还要继续清这批通用 Schema

---

## 4. 验收与收口

完成后至少确认：

1. `openapi.yaml` 中新增/调整字段准确。
2. Web 端生成文件更新成功。
3. 生成文件没有被手工改写。
4. 如果走了路径补齐脚本，记得把 TODO 区域逐步补完整。

一句话：

`API 口径更新了，类型必须同步。`
