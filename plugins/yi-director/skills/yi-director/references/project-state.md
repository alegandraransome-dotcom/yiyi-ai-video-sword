<!-- BEGIN MODULE 08 -->

# 08｜项目状态与接力
## 以一 V2.0｜Production State & Handoff｜Beta

> 08不是第二本剧本，也不是聊天记录仓库。只保存“未来继续工作仍会改变正确答案”的信息。

## 目录

1. 两层状态与最小结构
2. 可选长期引用与状态优先级
3. State Promotion、Cleanup与TURN_HANDOFF
4. Handoff、WORKING_STATE与Brief
5. 生成模式、更新与冲突

# 一｜两层状态

1. PROJECT_STATE：长期、稳定、跨较长制作仍需继承。
2. TURN_HANDOFF：每轮覆盖的短期工作接力。

超长单轮可临时维护WORKING_STATE，结束后只提升仍有价值的信息。

# 二｜PROJECT_STATE最小结构

```text
<PROJECT_STATE>
PROJECT:
CURRENT_POSITION:
CHARACTER_STATE:
WORLD_STATE:
ASSET_STATE:
GLOBAL_BASELINES:
LOCKS:
PROTECTED:
OPEN:
</PROJECT_STATE>
```

PROJECT只写会影响执行的项目名称、制作形态、画幅、生成管线；CURRENT_POSITION必须具体到真正做到哪里；CHARACTER_STATE只写当前阶段Delta；WORLD_STATE只存持续现状/不可逆结果；ASSET_STATE只写当前采用哪个版本/该回读哪个资产；GLOBAL_BASELINES只存稳定视觉/摄影/光影/声音基线；LOCKS只存以后默认不重新讨论的确认事实/冻结决定；PROTECTED存WEI-K/Key Shot Value/低频TAKE-K；OPEN只写未来真的要处理的问题。


## 二-A｜可选长期引用｜只有真的会改变未来正确答案才存

按项目需要，PROJECT_STATE可以在现有字段内部记录：
- `Performance DNA = 已建立 / 回读位置`；
- `Continuous Ambience Baseline = 当前稳定空间底声`；
- `Voice Asset = 已确认引用 / 未指定`；
- `Asset Adapter = 当前实际平台 / 工作流`。
- `Lighting Rig = 当前场次主要光源地图 / 曝光层级 / 可回读位置`；
- `Video Export = Target / Version / Host / Mode / UI Settings / Reference Map / Verified At`。

这些不是新增必填字段，也不把08变成资产或平台百科。只有会影响后续正确输出时才存；平台Adapter或光线母版发生变化，只更新当前有效值。

# 三｜状态优先级

```text
CURRENT CHARACTER STATE > BASE CHARACTER ASSET
CURRENT WORLD STATE > BASE SCENE ASSET
IRREVERSIBLE RESULT > REFERENCE INITIAL STATE
CURRENT STATE = BASE STATE + ACCUMULATED CHANGES
```

# 四｜只保存当前有效态

```text
STATE STORES PRESENT TRUTH, NOT FULL HISTORY
```

酒杯满→半杯→空，08最终只需“酒杯：当前为空”。历史过程由剧本/正式分镜保存。

# 五｜State Promotion

```text
SHOT DETAIL
↓ 下一镜需要
WORKING_STATE
↓ 下一轮/当前生成段需要
TURN_HANDOFF
↓ 跨场/跨较长制作仍需要
PROJECT_STATE
```

判断：这个事实是否会改变未来一个正确决定？不会就不记录。

# 六｜State Cleanup

旧状态被新状态覆盖就删除旧值；OPEN被解决就从OPEN删除并写入正式状态。不得同时保存“待确认”和“已确认”的同一事实。

# 七｜TURN_HANDOFF

固定六项：

```text
<TURN_HANDOFF>
POSITION:
STATE:
LOCKS:
PROTECTED:
NEXT:
REREAD:
</TURN_HANDOFF>
```

POSITION只写当前工作边缘：现在停在哪里、下一道边界是什么。正常生产不要列一长串“已经完成1、2、3、4……”历史。

STATE只写下一轮一开始必须知道的当前状态，不复制PROJECT_STATE。局部修订且下一轮很可能继续同一修改时，可临时记录 `CURRENT ARTIFACT` 与 `PATCH SCOPE`；修改结束后清理，不新增长期字段。

LOCKS只写本轮新增或下一轮马上用到的Lock。**00里的通用运行法则不反复塞入LOCKS，除非当前TEST/DEBUG正专门验证它。**

PROTECTED只写下一轮容易丢、丢了会破坏观看/导演价值的东西。

NEXT必须是动作；REREAD明确NEXT前应优先恢复的真实内容，不写“重新读全部模板”。

# 八｜Handoff不绑架下一轮

```text
READ NEW USER REQUEST → VALIDATE PREVIOUS HANDOFF → KEEP / MODIFY / DISCARD NEXT
LATEST USER REQUEST > PREVIOUS HANDOFF
```

# 九｜Handoff每轮覆盖

Turn N Handoff → Turn N+1读取 → 完成工作 → 写新Handoff。不累计历史Handoff。

# 十｜WORKING_STATE

长单轮可临时维护当前镜头/人物进出/关键道具/门等状态。复杂动作完成、视频段完成、场次完成、不可逆变化、主要人物进出、关键道具变化时刷新。

# 十一｜Brief / Blueprint

08不复制全文。可记录`Brief = LOCKED / Blueprint = LOCKED`，真正正式制作时回读原内容。若没有独立文件，不得假装存在。

# 十二｜生成模式与音色

项目固定生成模式进PROJECT_STATE；Mixed只写项目级Mixed，具体段2.0/2.5留正式分镜/Handoff。音色只做资产引用/段头标记，不建立Voice QA。

# 十三｜更新与冲突

PROJECT_STATE按变化更新；TURN_HANDOFF每轮覆盖。

若08与真实Source冲突：制作人员最新决定优先，其次原剧本/正式Source，再检查08是否过期并更新。但基础Source初始状态不能倒灌覆盖确认事件：

```text
BASE FACT + CONFIRMED STORY EVENTS = CURRENT FACT
```

<!-- END MODULE 08 -->


---
