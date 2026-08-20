# Changelog

## 2.0.0-beta.4 — 2026-08-20

- 建立可公开发布的全新干净历史，不携带私有仓库旧对象。
- 移除原始设计附件，以及公开来源和再分发条款未确认的 CINEDANCE/LIRA 原文。
- 保留非原文来源占位说明、ACTING 的 MIT 归属与完整许可证文本。
- 运行时 18 模块及 Canonical Runtime SHA-256 保持不变。
- 明确本仓库是 proprietary source-available，不等同于开源授权。

## 2.0.0-beta.3 — 2026-08-20

- 选择 Beta-3 为唯一内容主干，Beta-R2 降为可追溯基线。
- 将 00–10 单体母版拆成 18 个可逆重组源文件。
- 新增 Manifest、任务路由、内部 Skill 映射和 12 个 Runtime 模式。
- 新增确定性 `.yios` 编译、完整性索引与安全读取。
- 新增薇/恒独立编译、`WEI_REPORT` 冻结与 stale 检查。
- 新增项目状态 Schema、原子保存和 revision 冲突保护。
- 加固 `.yios` Canonical Runtime、ZIP 元数据、符号链接、TOCTOU 与自嵌输出检查。
- 将恒冻结门下沉到核心编译 API，并绑定项目、任务、完整状态与实际薇编译上下文。
- 状态提交改为带文件锁的原子 CAS；输入块改为人格 allowlist。
- 修复否定句、重复肯定和显式模式切换的路由边界。
- 拒绝非有限数、非字符串对象键与非法项目 UUID；状态初始化改为锁内 create-only。
- 项目状态 Schema 改用包内自包含 `$ref`，Release 写权限缩到发布 Job。
- 将 Beta-3 T1–T10 转为显式 fixture，消除隐含前置条件。
- 新增离线单元测试和 GitHub Actions CI/Release 工作流。

内部隔离盲测为 20/20；外部模型、人工导演复核与长链压力测试仍待执行，本版本不是 Final。
