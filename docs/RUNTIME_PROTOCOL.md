# 运行协议

## 路由顺序

任务文本先命中高优先级专项路线，再由状态补充当前成品类型：

1. 资产/图片；
2. 成片复看；
3. 继续；
4. 局部修改；
5. 正式制作；
6. 剧本统筹；
7. 导演设计；
8. 无匹配时默认导演设计。

资产模式中的“只改一件事”继续留在资产模式，不升级成正式分镜或资产重建。

## 五个关键命令

| 用户意图 | 编译模式 | 核心处理 |
|---|---|---|
| 继续 | continuation | 00 → 08 → 06，先验证 NEXT/REREAD |
| 正式做 | formal-production | 00/08 + 01–05 |
| 改单镜 | local-revision | 00/08 + 03–06，按必要范围回读 |
| 以一，构图 | directing | 00/08 + 01–03 |
| 看片返工 | review-rework | 00/08 + 01/06/07 |

## 双人格隔离

薇 Pass 加载 `kernel-wei-seed`、`persona-wei` 与共享搭档协议，明确排除 `kernel-heng-seed`、`persona-heng` 以及所有 HENG 输出注入。

薇的可交付物是结构化 `WEI_REPORT`，不是思维链。报告包含观察、WEI-R/W/K/Q 标记、保护项和待确认问题，并绑定：

- canonical source SHA-256；
- stable project ID；
- project-state revision；
- canonical project-state digest；
- wei-first-read 模块路由 digest；
- 实际薇编译 digest（模块、Skill 和输入块摘要）；
- run ID 与 task ID。

冻结后文件名就是内容 SHA-256。恒 Pass 重新验证文件名、规范 JSON 和上述全部上下文；核心编译器还会按当前输入重编译薇 Pass，核对实际文本摘要。任一不一致即 stale，拒绝编译。通用编译 API 不接受字符串型 `WEI_REPORT`，验证对象也不能跨项目、源版本、run 或 task 重放。

恒只加载 `kernel-heng-seed`、`persona-heng`、共享协议、生产模块和冻结的 `WEI_REPORT`，不读取薇的私有记忆或未冻结原始输出。

## 输入块

输入块使用显式 allowlist：`PROJECT_STATE`、`CURRENT_SCRIPT`、`CURRENT_ASSETS`、`TASK_CONTEXT`。Wei 拒绝全部 `HENG_*`，Heng 拒绝全部未经验证的 `WEI_*`；`heng-decision` 的 `WEI_REPORT` 不能通过普通 `--inject` 绕过冻结流程。
