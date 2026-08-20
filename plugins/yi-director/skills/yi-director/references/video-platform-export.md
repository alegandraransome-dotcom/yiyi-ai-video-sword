# 视频平台成稿导出

> 本模块不重新导演。它把已经确认的正式生成段编译成某个视频平台可直接使用的当前段成稿。正式分镜是母稿；平台成稿是一次有目标、有版本边界的导出物。

## 目录

1. 成品边界
2. 何时启动
3. 导出流水线
4. Export Contract
5. 活动引用与首帧
6. UI设置与Prompt正文分离
7. 通用成稿结构
8. 光影、对白与时序
9. Seedance适配
10. Higgsfield适配
11. 平台事实新鲜度
12. 隐藏发送门

## 一｜成品边界

区分四种交付：

```text
FORMAL_SCRIPT
GENERIC_VIDEO_PROMPT
SEEDANCE_PROMPT
HIGGSFIELD_PROMPT
```

`FORMAL_SCRIPT`是可读、可审、可继续修改的导演母稿，保留：

- `【场景】【出场人物】【道具】【音色】【生成】`；
- `【段任务】【入口】【出口】`；
- 每镜`【摄影】【表演】【声场】`；
- 按需`【光影基线】【连续性锁】`。

它本身已具备较强直接投喂能力。平台导出不是把它判为“不可用”，而是为特定平台进一步做当前段密封、引用映射、模式绑定、UI分离和发送前检查。

平台导出不得静默改剧情、改镜头、删台词、补台词、重做光影或改变入口/出口。若母稿本身矛盾，退回正式分镜修正，再重新导出。

## 二｜何时启动

只有以下情况启动：

- 用户明确说“平台成稿、可直接复制、导出到Seedance/Higgsfield”；
- 用户明确要求“只给最终视频提示词”；
- 当前任务本身就是把已确认分镜转换为某个平台输入。

用户只要正式分镜、完整脚本、导演方案或修改某镜时，保持现有中文正式格式，不自动压成平台稿。

平台未知时输出`GENERIC_VIDEO_PROMPT`。不猜模型名、按钮、标签、参考槽位或参数。

## 三｜导出流水线

```text
FORMAL SEGMENT
→ EXPORT CONTRACT
→ GENERIC EXPORT CORE
→ TARGET ADAPTER
→ PROMPT BODY + OPTIONAL UI CARD
→ SILENT SEND GATE
```

导出是编译，不是再创作。任何会改变导演结果的决定必须回到母稿。

## 四｜Export Contract

内部先冻结当前段：

- Source：场次、序号、当前正式段；
- Target：平台、模型版本、宿主界面；
- Mode：T2V / I2V / R2V / Extend / Edit / 未确认；
- Duration / Aspect / Audio：已确认值；
- Exact Dialogue：逐字台词；
- Active Reference Map：当前人物、场景、道具、声音与精确标签；
- Current State：伤势、服装阶段、持握、位置、破坏、情绪惯性；
- First Visible Frame；
- Shot Form：单一连续观察 / 受控多镜头 / 外部分段；
- Time Blocks；
- Optics + Visible Result；
- Lighting Baseline + Shot Delta；
- Local Failure Locks；
- UI-only Settings。

缺失项只有在会改变正确结果时才问；否则标记未确认并使用通用导出，不编造。

## 五｜活动引用与首帧

### Active Reference Map

- 只激活当前段真正出现、被听见或被引用的素材；
- 用户提供的`@tag`、文件名和引用编号原样保留；
- 不发明tag，不擅自重命名；
- 每个tag必须能追溯到用户提供或平台当前已有的素材；
- 旧场角色、旧道具、旧Prompt和旧tag全部清理；
- 风格参考不得覆盖人物身份、空间、动作、光学和光影事实。

段头的`【出场人物】`和`【道具】`是制作清单，不等于所有项目资产都必须进入当前镜头。只把当前段实际需要的项目编译进Prompt。

### First Visible Frame

第一帧写已经成立的可见状态：人物位置与姿势、关键道具、摄影机观察点、主要光向、动作入口。

允许有意空镜；不允许无任务空镜。I2V/R2V已有首帧或视频来源时，文字只补充参考没有锁定的动作、摄影、光影和声音，不与输入画面争夺身份或空间。

## 六｜UI设置与Prompt正文分离

Prompt正文写：当前可见/可听世界、动作、摄影、光影、声音、连续性和必要模型控制。

UI设置卡只在用户要求“带参数”或当前工作确实需要时提供：

```text
平台 / 宿主：
模型 / 版本：
模式：
时长：
画幅：
分辨率 / fps / 音频：
参考槽位 / 权重：
Seed / 其他UI字段：
```

未知值写“未确认”或省略。除非平台明确要求，不在Prompt正文机械重复已经由UI锁定的画幅、分辨率、fps、seed和模式。

## 七｜通用成稿结构

平台没有固定语法时，使用紧凑自然语言，可保留用户熟悉的标题。推荐信息顺序：

```text
CURRENT SEGMENT + ACTIVE REFERENCES
→ FIRST FRAME
→ SHOT FORM / CAMERA
→ TIME-BLOCKED VISIBLE ACTION
→ PERFORMANCE + DIALOGUE
→ LIGHTING + MATERIAL RESPONSE
→ AUDIO
→ END STATE
→ LOCAL FAILURE LOCKS
```

不要求所有标题逐字出现。强信号优先于长Prompt；只写当前段，不能靠“同上、继续上一段”维持关键事实。

## 八｜光影、对白与时序

### 光影编译

把导演光影判断压成可见结果，至少明确：

- 主要来源与世界方向；
- 人物/关键道具/背景的明暗层级；
- 必须保护的肤色、高光、暗部或材质；
- 摄影机移动和切镜后怎样连续；
- 光影变化的真实触发与结束状态。

不要只写“cinematic lighting / 高级冷暖对比”。也不要把整套灯光分析塞进Prompt。

### 对白与口型

- 台词按母稿逐字复制，禁止少词、加词、改词；
- 台词语言保持原剧本，不自动翻译；
- 按制作人员要求检查可说时长；当前项目若采用每秒约2.5–3.5个英文单词，就据此核算而不是删改台词；
- 只有当前说话者动嘴，其他人物倾听；
- Prior Audio只作为声音刺激，不把画外说话者拉入画面。

### 时序

时间块连续且总时长不超过已确认上限。每块只放物理上能同时完成的角色动作、摄影机动作、道具变化、光影变化和声音事件。

## 九｜Seedance适配

长期不变的核心：当前段隔离、准确引用、首帧承诺、动作时序、对白锁、光向连续、UI分离和隐藏发送门。

当前平台事实属于易变信息。官方资料在2026-08-20可确认：

- Seedance 2.0支持文字、图像、音频、视频混合输入与15秒多镜头音视频生成；
- Seedance 2.5支持最长30秒单次音视频生成、扩展、多模态参考和更精细编辑；
- 不同宿主界面的可用模式、标签语法和UI字段可能不同。

官方来源：

- `https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0`
- `https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5`

执行纪律：

- 精确保留用户提供的`@tag`，每个tag都在Active Reference Map中且当前段确实使用；
- 用户未提供tag时不发明；
- T2V / I2V / R2V / Extend / Edit按当前界面或用户说明确认；
- 不全局强制英文。提示词语言服从用户、项目和当前宿主；英文台词始终保持英文；
- 15/30秒是当前已确认版本能力边界时才使用，不把它写成所有未来版本的永久规则。

## 十｜Higgsfield适配

Higgsfield是宿主工作流，不等于一个固定底层模型。先确认当前选择的模型和界面。

其官方资料强调摄影机运动、镜头、光影可以由Prompt、固定参数或组合控制；如果当前界面提供真实参数，优先用UI锁定可锁定的运动、起止构图、镜头和光源，不让文字重复承担全部机械控制。

官方来源：

- `https://higgsfield.ai/blog/ai-video-camera-control`
- `https://higgsfield.ai/camera-controls`

若Higgsfield中调用Seedance，只复用Seedance的内容语义；不假定两个宿主拥有相同tag、按钮名、参考槽位或参数。没有当前UI证据时，给通用Prompt，不编造控制项。

## 十一｜平台事实新鲜度

区分：

```text
STABLE CORE
vs.
VOLATILE ADAPTER FACTS
```

稳定核心可长期保存；模型名、时长、参考上限、tag语法、音频模式和UI字段必须带版本意识。

优先级：

```text
CURRENT USER UI / USER TEST
> CURRENT OFFICIAL DOCUMENTATION
> VERIFIED PROJECT ADAPTER
> OLD ADAPTER MEMORY
```

适配器与当前界面冲突时服从当前界面并更新项目状态。无法核实时回退通用导出；只有差异会改变结果时才问一个关键问题。

## 十二｜隐藏发送门

交付前内部确认：

1. 是否从正确的正式段导出，母稿没有被静默改写？
2. 每个tag是否有真实来源、当前使用且原样保留？
3. 是否清除了旧角色、旧道具、旧场景和旧Prompt残片？
4. 第一帧是否完整并与入口状态一致？
5. 时间块是否连续、物理可完成且不超已确认时长？
6. 台词是否逐字一致、语言未改、时长可承载？
7. 是否只有说话者动嘴，Prior Audio没有被视觉化？
8. 空间、伤势、服装、持握、光向和灯光状态在切镜后是否继承？
9. UI字段是否与Prompt正文分离，未知参数没有被猜测？
10. 平台事实是否适用于当前版本与宿主？
11. 光影是否有来源、层级、曝光重点和可见结果？
12. 用户若只要Prompt，是否隐藏了合同、UI卡、QA和解释？

不输出检查表。发现问题直接修成正确成稿。
