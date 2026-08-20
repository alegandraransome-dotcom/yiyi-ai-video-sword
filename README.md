# 以一｜薇 × 恒导演运行时

这是把原始设计、Beta-R2“正赛”、Beta-3“分支”和经审计的工业能力正式工程化后的单一公开仓库。

当前唯一运行内容主干仍是 **V2.0 Beta-3**；公开工程分发版本为 **2.0.0-beta.4**，Beta-R2 只保留为历史基线。开发态使用 Markdown + YAML，工程发布态生成一个可校验、可复现的 `.yios` 单文件包。面向 ChatGPT/Codex 用户的独立 Skills 插件从 **0.1.0** 起步；这只是安装与分发层，不把 Beta-3 规则冒充成新的导演内核。

> 当前状态：`RULE INSTALLED / EXTERNAL TEST PENDING`。结构、安全与编译测试已经自动化；一次隔离的内部盲测得到 T1–T10 **20/20**，但还不能替代外部模型、人工导演复核和真实项目长链压力测试。本版本仍是 Beta，不得改称 Final。

## 已解决的问题

- 将 111 KB 单体母版拆成 18 个可逆重组的源文件，重新拼接后与原 Beta-3 **逐字节一致**。
- 把 `00 + 08` 从提示词约定升级为编译器不可绕过的常驻核心。
- Module 09 只进入维护模式；Module 10 只在资产/图片任务进入，避免污染正式分镜。
- 薇与恒使用两次独立 Runtime 编译；薇看不到恒的人格模块与方案。
- `WEI_REPORT` 绑定项目 ID、完整状态摘要、run/task、源版本和实际薇编译摘要；恒的核心 API 只接受已验证冻结件。
- 项目状态使用显式 JSON Schema、跨平台文件锁、唯一临时文件、目录 fsync 和原子 revision compare-and-swap。
- `.yios` 使用安全路径、逐文件 SHA-256、Canonical Runtime 重组校验、固定时间与无压缩 ZIP，跨构建保持同一字节。
- GitHub CI 自动执行模块、路由、隔离、状态、包完整性、路径穿越和双构建复现测试。

## 结构

```text
manifest.yaml                 路由、人格、模式、模块和流水线唯一配置
runtime/                      00–10 可编辑运行源
internal-skills/              已审计后的表演、视频执行、资产生产适配器
schemas/                      项目状态、接力和 WEI_REPORT Schema
src/yi_runtime/               Python 编译器、路由器、状态和打包器
evals/                        Beta-3 T1–T10 行为回归 fixture
plugins/yi-director/          可安装的 ChatGPT/Codex 纯 Skills 插件
.agents/plugins/              GitHub Marketplace 索引
archive/                      黄金基线与公开来源记录，永不进入正常 Runtime
tests/                        可离线复现的结构与安全测试
dist/                         构建产物（不入 Git）
```

## 给 ChatGPT/Codex 用户：安装以一导演

插件版适合不使用 Python CLI、只想在对话里制作 AI 短剧的用户。它包含导演 Skill 和随包参考资料，不包含 MCP 服务器，不需要额外的以一账号或 API Key，也不会自行连接发布者服务器。GitHub 只负责分发与更新；安装完成后，日常使用不需要持续联动 GitHub。

先添加本仓库 Marketplace：

```bash
codex plugin marketplace add alegandraransome-dotcom/yiyi-ai-video-sword --ref main
```

然后刷新或重新打开 Skills/Plugins 页面，在目录中选择“以一导演”并安装。安装后可直接上传剧本和已有资产，再说“先做开拍筹备”“按 9:16、每段 15 秒做正式分镜”“只优化叙事光影”或“导出平台可直接复制成稿”。

仓库 Marketplace 用于测试和定向分发，不等同于已进入所有用户可见的通用插件目录。通用发布仍需发布者在 OpenAI Platform 完成身份验证、上传 Skills-only 包、审核并点击发布。插件详情见 [`plugins/yi-director/README.md`](plugins/yi-director/README.md)。

仓库维护者可生成只包含插件白名单文件的确定性上传包：

```bash
python tools/build_chatgpt_plugin.py
```

输出位于 `dist/yi-director-plugin-0.1.0.zip`，并同时生成 SHA-256 校验文件；`dist/` 继续作为本地构建目录，不提交进 Git。

## 快速开始

要求 Python 3.11+。

```bash
python -m pip install -e .
yi validate .
python -m unittest discover -s tests -v
yi build . --output dist/YI_Director_Runtime_v2.0.0-beta.4.yios
yi inspect dist/YI_Director_Runtime_v2.0.0-beta.4.yios
```

任务路由：

```bash
yi route "直接正式做33-1"
yi route "第4镜不行，人物离太近"
yi route "以一，构图"
yi route "看片返工，这个视频又多手了"
```

生成项目状态并编译当前任务：

```bash
yi state-init --project "她背叛的亿万富翁" --format 9:16 --pipeline Mixed --output .yi-state/project.json
yi compile --task "直接正式做33-1" --state .yi-state/project.json --output run/formal-runtime.md
```

## 薇 → 冻结 → 恒

```bash
# 1. 编译薇的独立首轮；这里不加载恒的人格模块
yi compile --mode wei-first-read --state .yi-state/project.json --output run/wei-runtime.md

# 2. 生成与当前源、状态和路由绑定的报告模板
yi wei-template --state .yi-state/project.json --run-id run-001 --task-id scene-33-1 --output run/wei-report.json

# 3. 让薇填写 observations / flags / protected_values / open_questions 后冻结
FROZEN_REPORT="$(yi freeze-wei run/wei-report.json --output-dir .yi-state/reports/wei \
  | python -c 'import json, sys; print(json.load(sys.stdin)["frozen_report"]')"

# 4. 状态 revision 未变化时，恒只读取冻结件
yi compile --mode heng-decision --state .yi-state/project.json \
  --wei-report "${FROZEN_REPORT}" \
  --run-id run-001 --task-id scene-33-1 \
  --output run/heng-runtime.md
```

若薇 Pass 使用了 `--inject`，生成模板与恒 Pass 必须使用同一组 `--inject`，否则冻结件会被判定为 stale。当前 Beta-3 没有允许进入 `wei-first-read` 边界的内部 Skill，因此不要传 `--skill` / `--wei-skill`；这些参数只为未来显式放行且仍不跨模式边界的 Skill 保留。

薇与恒两次 Pass 之间不得更新项目状态。恒完成 Gate 后，才提交下一 revision。

## 版本与测试纪律

- `main`：Beta-4 公开分发主干；运行内容仍锁定 Beta-3 Canonical Runtime。
- `archive/beta-r2/`：只保存 Beta-R2 基线，不回灌为同级规则。
- 标签：`v2.0.0-beta.4`。
- 内部盲测记录在 `evals/results/2026-08-20-internal-blind-run.md`；它通过了 20 个断言，但不等于外部验收。
- 20/20：可进入真实项目长链压力测试。
- 18–19：只做窄补丁。
- 稳定 `v2.0.0` 还需要真实项目 20–30+ 轮无状态漂移压力测试。

## 公开仓库边界

本仓库可以公开查看，但依据根目录 `LICENSE` 属于 proprietary source-available，并不自动授予再分发、再许可或修改权。`plugins/yi-director/` 另有一项有限的安装与使用许可，允许用户在遵守插件 [使用条款](plugins/yi-director/TERMS.md) 的前提下制作和商业化自己的音视频成品。权属未解决的 CINEDANCE、LIRA 原文和原始设计附件不进入公开历史；仓库只保留来源占位说明与经审计的内部适配。详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 [archive/SOURCES.yaml](archive/SOURCES.yaml)。

更详细的设计见 [架构](docs/ARCHITECTURE.md)、[包格式](docs/PACKAGE_FORMAT.md)、[运行协议](docs/RUNTIME_PROTOCOL.md)、[状态模型](docs/STATE_MODEL.md)、[测试说明](docs/TESTING.md) 和 [GitHub 发行清单](docs/GITHUB_RELEASE.md)。
