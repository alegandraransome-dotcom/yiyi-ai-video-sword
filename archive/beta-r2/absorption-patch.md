# 以一 V2.0 Beta-R2｜Skill Absorption Patch

> 目的：吸收外部成熟工业Skill中真正补足以一短板的能力。  
> 原则：不重写Beta-R2已证明有效的导演、回读、状态、Patch Scope与正式分镜核心；不把平台技巧冒充导演哲学。

## 来源与正确职责

### ACTING SYSTEM
吸收范围：人物表演层。
- Behavior under pressure；
- Objective / Obstacle / Stakes / Tactic / Beat / Subtext；
- Listening & assessment；
- Physical Business；
- Proxemics / Status；
- Eye Life；
- Scene adaptation。

### CINEDANCE V4
吸收范围：视频执行工程与模型Prompt编译层。
- current-shot isolation；
- first-frame occupancy；
- spatial blocking；
- optics / physical camera behavior；
- physics / lighting priority；
- action timing；
- prompt density；
- reference hierarchy。

### LIRA
吸收范围：AI图像资产生产与资产局部编辑。
- character / location / prop asset routing；
- stable image-prompt discipline；
- minimal CHANGE + exhaustive PRESERVE；
- asset versions / variants；
- model-specific image workflow。
不把LIRA当视频镜头导演。

### Cinema Studio 4.0生产资料
吸收范围：工业生产证据与流程经验。
- assets first；
- asset = text descriptor + image reference；
- shot card；
- spatial map；
- master shot as stability tool；
- one-change-per-iteration；
- repeated failure → change the shot, not just the wording；
- visual bible baked into assets/preproduction。

---

# PATCH 02｜剧本统筹与开拍准备

## 新增：表演行为脊柱

```text
OBJECTIVE
→ OBSTACLE / STAKES
→ CURRENT TACTIC
→ PRESSURE / NEW INFORMATION
→ ASSESSMENT
→ TACTIC CHANGE / CHOICE
→ VISIBLE BEHAVIOR
```

与既有：

```text
STIMULUS → REACTION → CHOICE → ACTION
```

并行。

情绪词不能独立构成可执行表演。

## 新增：资产生产契约

```text
ASSET =
REFERENCE IMAGE
+ STABLE DESCRIPTOR
+ STATE / VARIANT
+ VERSION
```

08只保存当前版本/状态与回读位置，不复制整段Descriptor。

## 新增：SCENE SPATIAL ANCHOR

复杂场景可使用：
- Blocking；
- 场景母版；
- 极短master shot；
- spatial map；
- 或组合。

空间锚不等于成片必须先放大全景。

---

# PATCH 03｜导演设计

## D3新增：Physical Business

人物有自然任务时，让身体继续真实生活。  
重要强调可来自：

```text
ONGOING BUSINESS
→ LINE / EVENT HITS
→ BUSINESS STOPS
```

不为了“手别闲着”硬加动作。

## D3新增：Proxemics / Status

关系变化通过：
- 靠近 / 后退 / 冻结；
- 谁让位；
- 谁先移开视线；
- 谁动得更少；
- 谁碰谁的东西；
表现。

## D3新增：Eye Life

重要反应内部判断：
- gaze target；
- eyes lead thought；
- blink / gaze changes with beat；
- controlled stillness ≠ frozen eyes。

不机械逐镜写微眼跳。

---

# PATCH 04｜镜头执行与连续性

## 新增：Physical Causality Library

```text
GRAVITY
MASS
INERTIA
FRICTION
CONTACT
WEIGHT TRANSFER
COLLISION
FOLLOW-THROUGH
MATERIAL RESPONSE
```

只调用相关项。

武器、门、液体、脚步、布料、碎屑等必须有真实cause → change/contact → result。

## 新增：CURRENT-SHOT ISOLATION

模型最终Prompt是密封的当前镜头文档。

禁止依赖：
- 上一镜；
- 继续；
- same as before；
- previous / as above；
- 不出镜人物；
- stale tags；
- 制作历史。

```text
PAST EVENTS + CURRENT STATE
→ PRESENT TRUTH
→ WRITE PRESENT TRUTH DIRECTLY
```

## 新增：First-Frame Occupancy｜按需

只有当首帧位置决定生成成败时明确锁第一帧。  
不禁止有导演价值的空镜与延迟揭示。

## 新增：Action-State Tactic｜条件性

高风险动作可从already mid-action开始。  
这是生成战术，不取消导演因果。

---

# PATCH 05｜正式分镜

## 【表演】升级

重要Beat可以写：

```text
OBJECTIVE / TACTIC
→ STIMULUS / PRESSURE
→ ASSESSMENT
→ VISIBLE REACTION
→ CHOICE / TACTIC CHANGE
→ ACTION
```

## 新增：Director Script → Model Prompt Compiler

```text
DIRECTOR SCRIPT
→ EXECUTION PREFLIGHT
→ CURRENT-SHOT COMPILATION
→ MODEL-FACING PROMPT
```

导演脚本允许继承：
```text
PROJECT BASELINE → SCENE DELTA → SHOT DELTA
```

模型Prompt独立生成时必须自包含，密度优先给：
- current state；
- active references；
- spatial blocking / first frame；
- optics；
- timed action；
- physics；
- lighting；
- performance；
- audio；
- known local failure locks。

不把会议文字、旧场历史、无用角色/道具、漂亮但无控制价值的形容词塞给模型。

---

# PATCH 07｜成片复看与返工

## Surgical Iteration

```text
CHANGE ONE THING
→ KEEP EVERYTHING THAT WORKS
→ LOG VERDICT
```

局部失败优先窄修。

同一核心问题多轮失败后：
- 拆镜；
- 改机位；
- 改动作路径；
- 减少并发；
- 用反应 / 结果 / 环境 / 画外动作 / 声音桥获得等价影视结果。

不无限重写一句Prompt。

---

# 不吸收为全局硬规则

以下内容保留为工具/项目特定经验，不升级成以一导演法则：

- 所有镜头必须rule of thirds；
- hero shot必须表演强度4+；
- 每句台词后固定1秒静默；
- 每场成片必须先放1秒master wide；
- 完整Descriptor必须在人类正式分镜逐镜复制；
- 固定某个具体工具型号为永恒路由；
- 为生成稳定牺牲WEI-K / Key Shot；
- 用prompt工程覆盖导演设计。

---

# 字母测试

- **A｜Acting Behavior Test**
- **B｜Current-Shot Compiler Test**
- **C｜Physical Causality Test**
- **D｜Asset Workflow Test**
- **E｜Real Scene Stress Test**

测试结果只决定窄补丁，不因一处失败重写整个系统。
