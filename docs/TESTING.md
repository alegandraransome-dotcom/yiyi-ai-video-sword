# 测试与晋级

## 离线结构门

```bash
yi validate .
python -m unittest discover -s tests -v
```

当前离线门覆盖：

- 18 个源文件可逆重组为冻结 Beta-3；
- Archive SHA-256 不漂移；
- UTF-8/LF、模块 marker 与代码围栏配对；
- 所有 mode 恰好一次包含 00/08；
- Manifest 重索引也不能绕过固定模块布局、00/08、人格与 mode 边界；
- 正式模式含 03/04/05 且不含 09/10；
- 资产模式含 10 且不含 05；
- 薇/恒模块隔离；
- `WEI_REPORT` 内容寻址、typed gate、项目/任务/状态/编译上下文与 stale 检查；
- 状态严格 Schema 语义、有限标准 JSON、create-only 初始化与并发原子 compare-and-swap；
- `.yios` 路径、符号链接、成员、Canonical Runtime 与 SHA-256 完整性；
- 源文件和自定义 Reader 在验证后变化时，编译器仍只使用构造期不可变快照；
- 两次构建字节一致；
- Beta-3 T1–T10 fixture 数量与总分完整。

## 行为门

`evals/beta3-regression.yaml` 把原协议改成显式 fixture：T1–T3 共享状态，其余案例各自声明前置状态，避免换场后又隐式返回旧场导致串扰。

2026-08-20 的隔离内部盲测覆盖 20 个断言并得到 20/20，记录见 `evals/results/2026-08-20-internal-blind-run.md`。它验证了向前输出的基本吸收，但外部模型与人工导演审查仍未完成；离线 CI 也不能证明：

- 薇恒是否真的形成两种独立判断；
- 表演是否自然；
- 群体反应是否有生命；
- 资产反打是否视觉上正确；
- 正式分镜是否达到可拍质量。

晋级规则：20/20 才进入真实项目长链；18–19 只做窄补丁；稳定版另需 20–30+ 轮真实项目压力测试。
