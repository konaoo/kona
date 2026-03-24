# web/tests

这个目录现在按用途分成 3 层，不再把正式测试和临时排障脚本混在一起。

## 1. 目录分层

```text
tests/
├─ unit/   # Vitest 单元测试，保共享函数和兼容壳
├─ e2e/    # Playwright 正式页面验收
└─ debug/  # 临时排障脚本，不进正式门禁
```

---

## 2. 运行方式

- `npm run test`
  - 跑 `unit/` 里的 Vitest 单元测试
- `npm run test:e2e`
  - 跑正式 Web 烟测，保登录和关键页面主链路
- `npm run test:e2e:all`
  - 跑 `e2e/` 里的全部 Playwright 页面验收
- `npm run test:e2e:debug`
  - 跑 `debug/` 里的临时排障脚本

---

## 3. 规则

1. 正式长期保的单元测试放 `unit/`
2. 正式长期保的页面验收放 `e2e/`
3. 临时调试脚本放 `debug/`
4. `debug/` 目录默认不进正式门禁
5. 如果某个调试脚本已经证明长期有价值，要么改成正式断言补进 `unit/` 或 `e2e/`，要么删掉，不要长期赖在 `debug/`

---

## 4. 当前结论

`web/tests` 以后应该是“能一眼看出哪些是门禁、哪些只是排障工具”的目录，而不是测试和调试脚本混放的工具箱。
