# 文档导航

## 1. 先说结论

你说得对，现在 `docs/` 目录确实很乱。

问题主要有 3 个：

1. 文件名大量是英文
2. 同时混着长期文档、交接文档、接口文档、原型文档
3. 普通人第一眼不知道该先看哪一个

所以这份文件的作用就是：

`把 docs 目录翻译成人能看懂的导航页。`

以后你先看这份，不要直接在 `docs/` 里硬猜。

---

## 2. 如果你是要快速了解项目，先看这些

### 第一优先级

- [项目总览（主仓库 README）](/Users/kona/Desktop/kaka/kona_repo/README.md)
  作用：看项目是干什么的、技术栈是什么、主仓库结构是什么

- [工作区骨架说明](/Users/kona/Desktop/kaka/项目结构.md)
  作用：看整个 `kaka` 工作区怎么组织

- [版本记录](/Users/kona/Desktop/kaka/kona_repo/CHANGELOG.md)
  作用：看每一版到底改了什么

- [资产识别与价格逻辑](/Users/kona/Desktop/kaka/kona_repo/docs/资产识别与价格逻辑.md)
  作用：看代码怎么识别 A股、港股、美股、基金，以及分别去哪取价格

- [资产收益计算逻辑](/Users/kona/Desktop/kaka/kona_repo/docs/资产收益计算逻辑.md)
  作用：看成本价、adjustment、当日盈亏、累计盈亏、快照和分析页口径

- [接口与页面对照图](/Users/kona/Desktop/kaka/kona_repo/docs/接口与页面对照图.md)
  作用：看某个页面到底吃哪些接口、后端入口在哪

- [状态管理职责图](/Users/kona/Desktop/kaka/kona_repo/docs/状态管理职责图.md)
  作用：看 Flutter 和 Web 到底是谁在管状态、哪里重复了

---

## 3. 如果你是要看产品和业务逻辑，优先看这些

- [资产同步与盈亏算法口径](/Users/kona/Desktop/kaka/kona_repo/docs/资产同步与盈亏算法口径.md)
  作用：看资产、收益、刷新这类核心口径

- [资产收益计算逻辑](/Users/kona/Desktop/kaka/kona_repo/docs/资产收益计算逻辑.md)
  作用：看成本、摊薄后成本、当日盈亏、累计盈亏和历史快照的关系

- [接口与页面对照图](/Users/kona/Desktop/kaka/kona_repo/docs/接口与页面对照图.md)
  作用：看页面、状态和接口之间的对应关系

- [价格源 / 基金净值 / 快照与盈亏口径交接](/Users/kona/Desktop/kaka/kona_repo/docs/价格源与快照盈亏口径说明.md)
  作用：看价格源、基金净值、快照、价格异常巡检这些逻辑

- [分析页日历与分市场收益说明](/Users/kona/Desktop/kaka/kona_repo/docs/分析页日历与分市场收益说明.md)
  作用：看分析页日历和分市场收益怎么算

- [登录态、生物识别与持久化说明](/Users/kona/Desktop/kaka/kona_repo/docs/登录态与生物识别说明.md)
  作用：看登录、会话保持、生物识别相关逻辑

---

## 4. 如果你是要看运维和部署，优先看这些

- [运维手册](/Users/kona/Desktop/kaka/kona_repo/docs/运维手册.md)
  作用：常规运维怎么做

- [线上运维与发布操作图](/Users/kona/Desktop/kaka/kona_repo/docs/线上运维与发布操作图.md)
  作用：看从本地修改、验收、推 GitHub 到腾讯云生效的完整流程

- [维护说明](/Users/kona/Desktop/kaka/kona_repo/docs/维护说明.md)
  作用：偏维护、巡检、排障

- [请求追踪与排障手册](/Users/kona/Desktop/kaka/kona_repo/docs/请求追踪与排障手册.md)
  作用：看怎么用 `request_id` 串 Web、Flutter、后端和 CI，快速定位接口问题

- [部署说明](/Users/kona/Desktop/kaka/kona_repo/docs/部署说明.md)
  作用：怎么发版、怎么部署

- [腾讯云迁移交接](/Users/kona/Desktop/kaka/kona_repo/docs/腾讯云迁移说明.md)
  作用：看现在线上环境怎么来的、迁移时做了什么

- [腾讯云切换检查清单](/Users/kona/Desktop/kaka/kona_repo/docs/腾讯云切换检查清单.md)
  作用：偏切换和迁移检查，不是日常第一入口

---

## 5. 如果你是要看接口，优先看这些

- [接口总览](/Users/kona/Desktop/kaka/kona_repo/docs/接口总览.md)
  作用：后端接口清单

- [接口详细说明](/Users/kona/Desktop/kaka/kona_repo/docs/接口详情.md)
  作用：接口参数和返回细节

- [接口导入说明](/Users/kona/Desktop/kaka/kona_repo/docs/接口导入说明.md)
  作用：接口导入或接入相关说明

- [Swagger 说明](/Users/kona/Desktop/kaka/kona_repo/docs/Swagger说明.md)
  作用：Swagger 文档入口说明

- [OpenAPI 文件](/Users/kona/Desktop/kaka/kona_repo/docs/openapi.yaml)
  作用：给工具、接口平台或自动化使用

- [Swagger 页面](/Users/kona/Desktop/kaka/kona_repo/docs/swagger-ui.html)
  作用：本地查看接口文档页面

---

## 6. 如果你是要看 Web / 前端改动历史，优先看这些

- [Web 变更时间线](/Users/kona/Desktop/kaka/kona_repo/docs/Web变更时间线.md)
  作用：看 Web 这块过去怎么改过

- [前端搭建说明](/Users/kona/Desktop/kaka/kona_repo/docs/前端搭建说明.md)
  作用：看 Web/前端环境怎么起

- [管理后台功能手册 V2](/Users/kona/Desktop/kaka/kona_repo/docs/管理后台功能手册V2.md)
  作用：看后台页面和功能

- [状态管理职责图](/Users/kona/Desktop/kaka/kona_repo/docs/状态管理职责图.md)
  作用：看前端状态层的边界和当前重复点

---

## 7. 已清理的阶段性或重复文档

之前那批阶段性说明和原型文件已经从主仓库清掉了，不再继续维护。

处理原则是：

- 入口导航只保留现在还真实存在、还会继续更新的主文档
- 已经过期的阶段性说明，不再继续挂在主导航里
- 以后如果还有一次性方案稿或原型，优先放到更明确的目录里，不要长期留在 `docs/` 主层

---

## 8. `docs/` 目录现在最大的问题

说白了，现在这里不是“没有文档”，而是“文档太多但没有中文总导航”。

所以当前最合理的策略不是马上全改文件名，而是：

1. 先保留原文件，避免打断现有链接
2. 用这份 `README.md` 做中文导航
3. 后面再慢慢把真正长期有价值的文档改成中文命名
4. 旧的、重复的、阶段性文档，再考虑归档

---

## 9. 你现在最值得先看的 5 份

如果你现在只想快速掌控项目，先看这 5 份就够：

1. [主仓库 README](/Users/kona/Desktop/kaka/kona_repo/README.md)
2. [项目结构](/Users/kona/Desktop/kaka/项目结构.md)
3. [版本记录](/Users/kona/Desktop/kaka/kona_repo/CHANGELOG.md)
4. [资产识别与价格逻辑](/Users/kona/Desktop/kaka/kona_repo/docs/资产识别与价格逻辑.md)
5. [资产收益计算逻辑](/Users/kona/Desktop/kaka/kona_repo/docs/资产收益计算逻辑.md)
