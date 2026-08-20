# 架构

## 三层分离

1. **开发源**：`runtime/`、`manifest.yaml`、Schema 与内部 Skill 描述。这里只改模块，不手改发行单文件。
2. **发行包**：`.yios` 是纯数据 ZIP；不含 Python、项目状态、原始上游 Skill 或历史档案。
3. **本轮 Runtime**：编译器根据任务、人格、状态和按需 Skill 只拼装本轮需要的内容。

`archive/beta3/frozen-monolith.md` 是不可变黄金基线。`runtime/canonical-order.txt` 中的 18 个文件按顺序拼接必须与该基线逐字节一致。

## 内容主干选择

- Beta-R2 的工业 Skill 吸收判断总体有效，但自己标注 A–E 未测试，因此只作 baseline。
- Beta-3 在 R2 上完成第二轮兼并，加入 Module 10、迁移总账与 T1–T10 回归协议，因此成为唯一主干。
- 两个 skill RAR 的解压内容完全相同；公开仓库仅保留可合法分发的 ACTING 证据与 CINEDANCE/LIRA 来源占位说明，它们都不是运行依赖。
- 原始 Skill 中被 Beta-3 拒绝的固定 Beat 数、全局三分法、默认一镜到底、FOV 替代 mm、固定平台路由等不得回流。

## 模块层

| 模块 | 职责 | 默认生产加载 |
|---|---|---|
| 00 | 权限、人格种子、回读门、阶段门、路由与输出纪律 | 永远 |
| 01 | 薇、恒与搭档协议 | 按人格/正式任务 |
| 02 | 剧本统筹与开拍准备 | 统筹、导演、正式制作 |
| 03 | 完整导演设计 | 导演、正式、修改、资产 |
| 04 | 镜头执行与连续性 | 正式、修改、资产 |
| 05 | 正式分镜 | 仅正式制作/正式回写 |
| 06 | 回读与工作续接 | 继续、修改、复看、资产重建 |
| 07 | 成片复看与返工 | 仅复看 |
| 08 | 项目状态与接力 | 永远 |
| 09 | 迁移记录与测试 | 仅维护 |
| 10 | 资产与图像适配 | 仅资产/图片 |

`00` 与 `08` 由固定 Manifest 不变量和编译器共同注入，不依赖提示词自觉。源目录、`.yios` 和直接 API 构造都不能排除它们。

## 内部 Skill

`internal-skills/` 只描述已经审计并适配后的能力：

- `acting-directing`：进入 02/03/05/07；
- `video-execution`：进入 03/04/05；
- `asset-production`：进入 03/04/06/10。

它们只引用运行模块，不复制三份原始 Skill 全文。Skill 不能把当前 mode 提升到另一个阶段：其模块全集若超出当前 mode 边界，编译器直接拒绝。

编译器构造时只读取一次 Canonical Runtime，把验证后的文本复制进内部不可变快照；后续编译不再活读源文件或外部 Reader，避免验证后漂移。

## 运行模式

Manifest 当前定义：startup、preproduction、directing、formal-production、continuation、local-revision、review-rework、asset-production、wei-first-read、heng-decision、maintenance、full-runtime。

`full-runtime` 只用于兼容与审计；正常工作应使用路由后的最小充分 Runtime。
