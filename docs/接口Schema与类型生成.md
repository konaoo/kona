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

---

## 3. Flutter 端类型生成（可选）

> 这一步需要 Java 环境（openapi-generator 会用到）。

执行：

```bash
scripts/generate_openapi_types_flutter.sh
```

输出目录：

- `/Users/kona/Desktop/kaka/kona_repo/flutter/lib/generated/openapi`

说明：

- 生成后 **请检查编译体量**，必要时再决定要不要提交到仓库。
- 这一步目前是“可选流程”，先把脚本固化，后续再逐步启用。

---

## 4. 验收与收口

完成后至少确认：

1. `openapi.yaml` 中新增/调整字段准确。
2. Web 端生成文件更新成功。
3. 生成文件没有被手工改写。
4. 如果走了路径补齐脚本，记得把 TODO 区域逐步补完整。

一句话：

`API 口径更新了，类型必须同步。`
