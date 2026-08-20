<!-- BEGIN MODULE 09 -->

# 09｜迁移记录与测试
## 以一 V2.0｜Maintenance Only

> **正常导演生产不要加载本模块。**
> 09只用于版本维护、能力迁移、压力测试、缺口记录与下一阶段开发接力。
> 它存在于完整归档版中，是为了保证V1.93–V1.99的迁移证据没有在打包时消失；但它不是日常导演运行负载。

# 一｜V1.93–V1.99迁移

- V1.93 → `01｜薇与恒｜双导演协作`；人格种子进入00。
- V1.94 → `02｜剧本统筹与开拍准备`；权限进入00，状态进入08，详细摄影进入03。
- V1.95 → `03｜导演设计`；正式格式进入05，执行风险进入04。
- V1.96 → `04｜镜头执行与连续性`；状态进入08，连续性锁输出进入05。
- V1.97 → `05｜正式分镜脚本`；全局基线由03设计、08保存、05继承。
- V1.98 → 拆分：每轮触发进入00，复杂回读进入06，状态与接力进入08。
- V1.99-R1 → `07｜成片复看与返工`；保留轻量 KEEP / REGENERATE / REPAIR / REPLACE，不迁移重型根因树。

# 二｜祖先能力迁移

### V1.0
“每镜真的造画面”：
- 光影；
- 前中后景；
- 动作轨迹；
- 环境；
- 同期声；
→ 03摄影设计 + 05 Cinematography Minimum Image Duty。

### V1.9x
导演肌肉：
- 场景建立；
- 构图；
- 光影；
- 环境；
- 人物表演；
- 节奏；
- 关键镜头；
- 全局摄影；
- 声音；
→ 02 + 03 + 05。

### V1.92
认知 / 回读神经：
- 真实回读；
- 任务路由；
- 区块不必外显；
- 上下文重新定位；
→ 00 + 06 + 08。

旧“最小充分调用”只保留局部工作；
正式整场 / 整集要求完整导演能力 READY。

# 三｜迁移状态

允许：
- KEEP
- MERGED
- MOVED
- INTERNALIZED
- OBSOLETE（只有确认错误或真正被更强规则取代）

禁止：
> “为了精简直接删能力。”

# 四｜Beta测试结论

### V2.0 Beta
完整10项测试：**19 / 20**。

主要暴露：
- “只改剑尖”最终语义正确，但重复执行三次才稳定；
- 中间发生成品类型 / 输出路由漂移；
- 曾有一次内部执行文字泄漏；
- A / B 未确认音色资产时曾出现“继承当前项目人物音色资产”的假继承风险。

### Beta-R1补丁
只新增：
1. Artifact Type Lock
2. Patch Scope Lock
3. Retry Route Stability
4. User-Facing Output Gate
5. 未确认音色 → `【音色】未指定`

不重写01–04已通过的核心导演能力。

### Beta-R1定向复测
**10 / 10通过。**

已验证：
- 局部摄影强化只改目标镜；
- 恒可以主动调整焦段、T值、机位高度；
- 正式文本局部修改不会自行跳成图片；
- 同一修改重试保持同一Artifact与Patch Scope；
- 切回场次A后，场次B状态不污染；
- 未确认音色资产时正确写“未指定”。

# 五｜当前版本状态

当前可确认：

- 00–08运行链已通过Beta与Beta-R1测试；
- 剧本统筹 → 导演设计 → 写前执行预判 → 正式分镜可以连续工作；
- Protected Value可从统筹穿透到正式镜头；
- 当前连续状态优先于基础资产初始状态；
- Blocking锁空间，不自动锁摄影机；
- 生成模式未知不阻塞导演设计，只阻塞最终封装；
- 普通失败连接镜允许优先REPLACE为更稳、更成熟的影视镜头；
- 局部修改重试可以保持Artifact / Patch Scope稳定。

# 六｜Beta-2工业兼并记录

Beta-2仍然属于 **V2.0 Beta**，不是V2.01。

本轮以“补能力、不删导演肌肉”为原则，吸收三类成熟工业Skill / 生产经验：

### ACTING SYSTEM → 02 / 03 / 05 / 01
吸收：
- Behavior Under Pressure；
- Objective / Obstacle / Stakes / Tactics / Beats / Subtext；
- Listening / Assessment / Thought-before-word；
- Physical Life / Business / Proxemics / Status / Eye Life；
- Character Acting Master Profile（按需）。

不机械吸收：
- “强者永远安静、弱者永远吵”不作为铁律；
- 不允许为了活人感给每个角色强塞Business；
- 不允许改原台词来追求所谓自然对白。

### CINEDANCE → 03 / 04 / 05
吸收：
- Current Shot Facts / Context Isolation；
- First-Frame Commitment；
- 3D Location Map → 2D Frame；
- Gaze / Body Orientation分离；
- Optics先于泛化审美；
- 摄影机物理操作语言；
- Action Timing / Physics / Lighting Priority；
- Reference Hierarchy；
- Prompt Density Control；
- Multi-shot continuity；
- Positive Local Locks。

明确不吸收为硬规则：
- 不强制第一帧必须有人；
- 不默认Single Continuous Take；
- 不把Location reference变成锁摄影机；
- 不把所有镜头变成检查表输出。

### LIRA → 00 / 02 / 06 / 07，并保留外部资产适配层
核心吸收：
- minimal CHANGE / exhaustive PRESERVE；
- edit ≠ regeneration；
- Change Less / Lock More；
- 正向描述优先；
- 真实材质 / 技术光影优先于空洞Mood；
- 资产工作需要明确生成 / 编辑 / 重建的任务类型。

平台专用的Soul / NBP / Seedream / GPT Image路由不写死进导演核心；它们属于外部资产适配知识，避免平台更新污染V2.0导演系统。

明确不吸收：
- “所有画面强制三分法”；
- “视频永远只写states not transitions”；
- 固定字符数 / 固定平台参数作为导演铁律。

### Higgsfield Cinema Studio 4.0生产经验 → 02 / 03 / 05 / 07
吸收：
- Assets First作为优先级，而不是不可越过门禁；
- 每次生成段需要足够自包含的当前事实；
- one change at a time；
- give the model less freedom = 用空间 / Landmark / 动作事实减少无谓猜测；
- 反复失败时 simplify the shot, not the words；
- continuous ambience作为跨生成镜头空间粘合；
- editor-in-the-loop，生成阶段就预留Cutaway / Insert / Reaction。

# 七｜薇 × 恒可观察性状态

Beta-R1已经确认“可观察性”是测试覆盖缺口。Beta-2已经把它从09的建议升级成00 / 01 / 02的**正式运行规则**：

- 新项目 / 新重要场次筹备讨论必须显性出现一次；
- 整场 / 整集导演设计讨论、关键镜头、大段重做、重要成片复看必须按需显性出现；
- 二人必须输出不同职责的信息，不允许复述假装双人格；
- 正式05分镜正文重新隐藏；
- 普通低风险局部修改仍可内部运行。

**当前状态：RULE INSTALLED / TEST PENDING。**
只有Beta-2真实测试通过以后，才能写“人格可观察性已验证”。


# 七-A｜Beta-3工业兼并第二轮记录

Beta-3仍然属于**V2.0 Beta**。本轮不是重写Beta-2，而是把第一轮遗漏的工业能力继续补齐，并新增低频10 Adapter。

### ACTING｜第二轮吸收
`ADAPTED / MERGED`：
- Triggered Tics：习惯必须尽量有触发；
- Gait / Movement Signature；
- Mask + Crack Trigger；
- Softening Target（可选，不强制）；
- Transform, Don’t Delete：场景适配时保留行为发动机；
- Two Truths / Paradox作为关键人物深度工具；
- Ensemble Reaction Wave；
- State Inertia / cumulative degradation；
- Threat without wind-up作为类型工具；
- Bad Acting Atlas进入07低频复看；
- Performance Scale进入07内部校准。

`REJECTED AS HARD RULE`：
- 每个角色必须有Business；
- 每场固定2–4 Beats；
- 每场必须有人失败；
- 强者永远静 / 弱者永远吵；
- 每个英雄镜头都必须达到固定表演分；
- 每双眼睛必须有明显catchlight。

### CINEDANCE｜第二轮吸收
`ADAPTED / MERGED`：
- Shot Form / Cut Plan进入04编译；
- 专业参数 + 可见光学结果双描述；
- FOV作为可选生成控制，不替代mm / T值；
- Lens Character Across Cuts；
- Handheld Physicality；
- Landmark proximity的可操作锚定；
- Action Timing可执行块；
- 物理材料行为进一步细化；
- Dialogue / Prior Audio Context；
- Current-Segment Isolation；
- 内部多镜头不允许随机Cut / 状态重置。

`REJECTED AS HARD RULE`：
- 默认Single Continuous Take；
- 第一帧默认必须有人；
- FOV角度取代焦段；
- 所有镜头必须输出固定Prompt章节；
- 通过大Negative List控制镜头。

### LIRA｜第二轮吸收
`MOVED TO OPTIONAL ADAPTER`：
- 角色 / 场景 / 道具 / 图片编辑 / 纹理修复 / 反打换机位的生产路由；
- Natural prose / Positive-first / 技术光影 / 真实材料；
- Character / Location / Prop / Surgical Edit模板思想；
- Soul ID / reference优先于纯文字身份；
- Edit / Texture Pass / View Change / Rebuild任务分流；
- 反打 / 换机位必须重建新摄影机下的物体空间映射；
- 平台参数与Prompt内容分离的源工作流原则。

`NOT GLOBALIZED`：
- 所有画面强制三分法；
- 固定80–150词 / 1500–2000字符；
- 所有平台永久固定同一模型路由；
- 平台参数永远不能出现在文字里；如果制作人员工作流明确需要写，服从当前工作流。

### 兼并纪律
每个外部规则必须有去向：`KEEP / MERGED / ADAPTED / MOVED TO ADAPTER / REJECTED AS HARD RULE / DEFERRED FOR TEST`。禁止“看起来重复所以静默删除”。

# 七-B｜当前验证状态

Beta-R1已验证原有运行链和局部修改稳定性；Beta-2 / Beta-3新增工业能力仍需回归验证。

当前状态：
- CO-DIRECTOR VISIBILITY：RULE INSTALLED / TEST PENDING；
- ACTING SECOND PASS：RULE INSTALLED / TEST PENDING；
- OPTICS / CUT COMPILE：RULE INSTALLED / TEST PENDING；
- ASSET ADAPTER 10：INSTALLED / TEST PENDING。

# 八｜下一阶段

先进行Beta-3工业兼并回归测试，重点验证表演增强、镜头编译、资产协作与薇恒可观察性；通过后再进入真实项目长链压力测试。

随后使用真实：
- 剧本；
- 人物资产；
- 场景母版；
- Blocking；
- 道具；
- 长场次；
- 20–30+轮连续制作；

检验：
1. 长上下文后导演质量是否下降；
2. 继续 / 切场 / 回来 / 以一后状态是否漂移；
3. 03完整导演能力是否退化成模板化coverage；
4. 局部修改是否继续保持Artifact / Patch Scope；
5. 构图、光影、表演、声音和连续性是否持续在线；
6. 薇与恒在关键导演节点是否既可验证存在，又不会污染正式脚本。

只有真实项目暴露新问题时，再做窄补丁。

<!-- END MODULE 09 -->

---


