# 状态模型

项目状态不是无限增长的日志，而是“长期事实 + 当前接力”。

## 长期状态

- 项目名称、画幅、生成管线；
- 人物与场景当前阶段；
- 视觉、摄影、光影、声音基线；
- 世界规则；
- 冻结导演决定；
- 长期保护项。

## 当前接力

`HANDOFF` 固定六个主字段：

```text
POSITION
STATE
LOCKS
PROTECTED
NEXT
REREAD
```

不可访问但需要恢复的 Source 放入可选 `REREAD_DEBT`，不能伪造为已经回读。

## 状态公式

每个需要严格连续的实体保存：

```text
Current State = Base State + Accumulated Changes
```

`current_state` 是当前唯一有效事实。基础资产不能把已经炸开的门、已经湿透的衣服、已经移动的道具或已经发生的伤势重置。

## 并发与提交

- 状态有单调递增 `revision`。
- 每个项目状态在初始化时获得不可变 `project_id`；规范 JSON 的 SHA-256 用于冻结上下文绑定。
- 状态只接受标准 JSON：对象键必须是字符串，数值必须有限；`NaN` / `Infinity` 一律拒绝。
- 初始化是锁内 create-only；已存在的状态只能通过带 revision 的 CAS 提交更新。
- 写入口共享同一个锁；锁内完成读取、revision 检查和写入。
- 写入使用唯一临时文件、文件 fsync、原子替换，再 fsync 父目录。
- 提交时必须携带 `expected_revision`；不匹配即拒绝覆盖。
- 薇与恒两次 Pass 之间不得提交新 revision。
- Handoff 每轮覆盖；历史过程由 Git/外部日志负责，不塞入当前状态。
