<!-- BEGIN MODULE 06 -->

# 06｜回读与工作续接
## 以一 V2.0｜Reread & Realignment Methods

> 00负责“每轮记得判断回读”。06负责“复杂情况下到底怎么回读”。本文件不是每轮常驻全文。

## 目录

1. 回读动作与影响深度
2. 整集层级与新场景切换
3. Revision、Patch与资产返工路由
4. REREAD_DEBT、Fresh/Stale与外部研究
5. 长单轮、Problem-Directed Reopen与轮末接力

# 一｜两种动作

**Source Reread**：真实重新读取剧本、资产说明、前一场、Brief、Blueprint、既有正式稿。

**Capability Refresh**：把相关专业规则重新提到注意力前排。

不要把二者混成“全文重背模板”。

# 二｜回读深度跟影响范围走

### FOCUS REREAD
局部修正：当前镜、前后必要镜头、当前状态、相关专业能力。

### SCENE REALIGN
新场景/整段重做：当前场剧本、前场必要出口、当前人物、空间/资产、当前状态、Brief/Blueprint、Protected Values、当前专业能力。

### FULL REALIGN
新项目/新集/明确“以一”/大规模重做/正式整集：项目事实、故事位置、当前状态、冻结决定、保护项、项目基线、必要专业能力。

Full Realign ≠ 全文重新读所有文件。

# 三｜正式整集层级

整集开始一次Full Realign；每进入一场Scene Realign；同一场继续Focus Refresh按需。不要每场把整套项目重新全文开机。

# 四｜新场景切换

旧状态必须判断：

```text
INHERIT / EXPIRE / ISOLATE
```

**INHERIT**：跨场仍有效，如伤势、已损坏道具、永久失去物品、连续服装状态、持续世界结果。

**EXPIRE**：只属于上一场的瞬时背景动作、局部姿态、不再存在的临时物件位置。

**ISOLATE**：不同场景母版不互相污染。上一场炸开的门不能自动出现在新场景；上一场群演位置不能带到新大厅。

若新场明确是上一场直接空间连续，则按真实连续关系继承。

# 五｜Revision

修改已有成品时先恢复：`CURRENT ARTIFACT / CURRENT PATCH SCOPE / CURRENT LOCKS`。

```text
REQUESTED CHANGE + STRICTLY NECESSARY DEPENDENT ADJUSTMENTS
```

用户只改剑尖：改剑尖；握持逻辑必须同步时做必要微调；不顺便改服装、背景、机位、光影；不把正式脚本任务切换成图片生成任务。如果局部变化确实破坏相邻剪辑/Blocking，可扩大到必要相邻范围，但不获得无关重设计权限。

同一修改因为失败而重试时，默认仍是同一个Artifact、同一个Patch Scope，并继承“其他不变”；只重试执行，不重新解释交付物类型。


### PATCH / REDESIGN / REBUILD分层
局部修改先判断到底是哪一种：
- `PATCH`：原成品成立，只改一个明确局部；
- `SHOT REDESIGN`：原镜观察方式 / 动作结构不成立，需要换镜头；
- `SCENE REDESIGN`：场次调度或镜头序列本身错误；
- `ASSET REBUILD`：基础资产 / 空间母版本身错误。

不要拿PATCH语言去重画整场，也不要把需要REBUILD的问题伪装成“再加几个限制词”。


## Revision Router｜资产问题不要在分镜里硬救

当问题判定为`ASSET REBUILD`或同场景视图几何已经无法靠局部脚本修复时：

```text
06 REVISION
→ 恢复已确认世界 / Blocking / 摄影事实
→ 按需加载10资产与图像生产适配层
→ 修 / 重建资产
→ 更新ASSET_STATE
→ 再回03 / 04 / 05继续
```

不要为了省一次资产返工，让正式分镜永久背着错误场景母版工作。

平台适配信息如果已经明显过时或与当前UI冲突，标记`ADAPTER_STALE`，重新确认后再使用；不允许旧Adapter反过来改剧情与导演事实。

# 六｜REREAD_DEBT

下一阶段必须读某内容但当前无法访问时记录，例如：`正式铺镜前必须重读 Scene 4 前场出口`。下一轮REREAD_GATE优先偿还，不假装已读。

# 七｜Fresh / Stale / Invalid

FRESH=刚恢复且无变化；STALE=经历大段新信息、长输出、阶段切换、新资产、用户纠错、研究、场景切换、正式交付前；INVALID=用户明确改变事实/决定。

Fresh内容不得仅因“回读很重要”重复读取。

# 八｜外部研究以后

```text
EXTERNAL RESEARCH → 提取有用机制 → YI REALIGN → 检查是否适合当前项目 → 应用
```

不要搜索完别人怎么拍就忘掉当前项目。

# 九｜长单轮工作

长单轮内部可维护临时WORKING_STATE。自然刷新节点：复杂动作完成、视频段完成、场次完成、不可逆状态改变、主要人物进出、关键道具状态改变。不要每写一句就更新。

# 十｜Problem-Directed Reopen

最终检查发现问题时只重开问题指向能力：手部→04；人物情绪→03表演；光线→03光影；正式稿啰嗦→05；状态回滚→08。局部错误不自动触发全系统重跑。

# 十一｜每轮结束

TURN_HANDOFF只记录当前边缘状态，不写历史总结。正常生产不要写“此前已完成1、2、3、4……”；只写现在停哪、当前必须继承什么、新增Lock、不能丢什么、下一步、下一步先读什么。

<!-- END MODULE 06 -->
