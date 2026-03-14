# scripts

## 1. 目录用途

`scripts/` 是 `kona_repo` 的仓库级脚本目录。

它的定位不是“随手写点脚本就往里扔”，而是：

`存放服务整个仓库的长期可复用脚本。`

这里的“仓库级”意思是：

- 不只服务某一个页面
- 不只服务某一个平台
- 不直接属于某个运行时应用目录

典型适合放在这里的，是：

- 文档生成脚本
- 仓库级检查脚本
- 发布辅助脚本
- CI 辅助脚本

---

## 2. 当前目录里有什么

当前目录中已有：

- `generate_api_docs.py`
- `generate_api_details.py`
- `fix_snapshot_rates.py`
- `force_snapshot_now.py`
- `check_calendar.py`
- `check_calendar2.py`
- `test_pnl_debug.py`
- `check_calendar2_output.txt`
- `ci/check_repo_hygiene.sh`
- `ci/check_changelog_guard.sh`

---

## 3. 当前这些文件分别是什么

### 3.1 文档生成类

- `generate_api_docs.py`
  用途：从后端路由生成 API 文档总览。

- `generate_api_details.py`
  用途：从后端代码中提取更细的接口参数和返回信息。

这两类脚本符合 `scripts/` 的定位，属于长期可复用的仓库级脚本。

### 3.2 运维 / 补数类

- `fix_snapshot_rates.py`
  用途：一次性修复历史快照汇率问题。

- `force_snapshot_now.py`
  用途：强制重算并重打快照。

这类脚本有价值，但更偏后端运维和数据修复。
长期更适合归到：

- `kona_tool/scripts/`

### 3.3 仓库门禁类

- `ci/check_repo_hygiene.sh`
  用途：检查构建产物、缓存和本地数据库有没有误进 Git。

- `ci/check_changelog_guard.sh`
  用途：检查重要工程或业务改动是否同步补了 `CHANGELOG.md`。

这类脚本符合 `scripts/` 的定位，属于仓库级 CI / 发布守门脚本。

### 3.4 临时排障类

- `check_calendar.py`
- `check_calendar2.py`
- `test_pnl_debug.py`

这几类脚本主要用于排查：

- 日历问题
- 快照问题
- 盈亏计算问题

它们更像“调试工具”或“临时排障脚本”，不适合长期作为仓库骨架的一部分。

### 3.5 脚本输出产物

- `check_calendar2_output.txt`

这是脚本运行结果，不属于脚本本身。
长期不应该留在 `scripts/` 目录里。

---

## 4. 应该放什么

这个目录应该放：

- 长期维护的仓库级工具脚本
- 自动生成文档的脚本
- 发布和检查相关的辅助脚本
- 与整个仓库工程管理相关的脚本

---

## 5. 不应该放什么

这个目录不应该长期放：

- 一次性排障脚本
- 单次数据修复脚本
- 调试输出文件
- 临时实验脚本
- 某个子系统私有的运行脚本

这些东西会让 `scripts/` 变成：

`看起来啥都有，但谁都不敢信的黑盒目录。`

---

## 6. 当前目录的判断

当前 `scripts/` 目录是“半对半乱”的状态。

对的部分：

- API 文档生成脚本放这里是合理的

乱的部分：

- 混进了后端运维脚本
- 混进了临时排障脚本
- 还混进了输出结果文件

所以现在的问题不是这个目录不该存在，而是它还没有被治理。

---

## 7. 后续约束

从现在开始，建议定这几条规则：

1. `scripts/` 只保留长期有价值的仓库级脚本。
2. 后端专属运维脚本，优先放到 `kona_tool/scripts/`。
3. 临时排障脚本，不要长期留在仓库主结构里。
4. 脚本运行输出文件，不要放在 `scripts/` 根目录。
5. 每新增一个脚本，都要说明：
   - 谁会用
   - 解决什么问题
   - 是长期脚本还是临时脚本

---

## 8. 后续建议的整理方向

建议未来按下面的思路收敛：

### 保留在 `scripts/`

- `generate_api_docs.py`
- `generate_api_details.py`

### 迁移到 `kona_tool/scripts/`

- `fix_snapshot_rates.py`
- `force_snapshot_now.py`

### 迁移到临时目录或删除

- `check_calendar.py`
- `check_calendar2.py`
- `test_pnl_debug.py`
- `check_calendar2_output.txt`

---

## 9. 当前结论

`scripts/` 不是无关目录，它有存在价值。

但它未来应该是：

`仓库级工具目录`

而不是：

`所有临时脚本的垃圾桶`
