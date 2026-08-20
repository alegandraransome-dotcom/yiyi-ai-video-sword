# GitHub 公开仓库与发行清单

## 仓库边界

目标仓库：`alegandraransome-dotcom/yiyi-ai-video-sword`。

公开历史必须从经过清理的快照开始，不能推送私有仓库的旧 Git 对象。公开树不得包含：

- 原始 `可以.docx` 设计附件；
- 权属未确认的 CINEDANCE、LIRA 原文；
- 私有构建缓存、项目状态或运行期报告。

ACTING 证据按上游 MIT License 分发；完整许可证见
`THIRD_PARTY_NOTICES.md`。本项目自身仍受根目录 proprietary `LICENSE`
约束，公开可见不等于开源授权。

## 仓库设置

- `main` 开启 Branch protection；要求 CI 的 Python 3.11、3.13、3.14 全部通过。
- 禁止 force-push 和删除受保护分支。
- Releases 启用 Immutable Releases。
- Actions 默认权限保持只读；Release Job 单独声明 `contents: write`。
- 保持 Secret scanning 与 Dependabot alerts 开启。

## 发版门

1. 工作树必须 clean；`main` 必须包含目标提交。
2. `manifest.yaml`、`pyproject.toml` 和 Tag 版本必须一致。
3. 本地执行单元测试、`yi validate .` 和双构建字节比较。
4. 创建 annotated Tag，并确认它与 `main` 指向同一提交：

```bash
git tag -a v2.0.0-beta.4 -m "YI Director Runtime 2.0.0 beta 4"
test "$(git rev-list -n1 v2.0.0-beta.4)" = "$(git rev-parse main)"
git push origin main
git push origin v2.0.0-beta.4
```

5. Release workflow 会先跑 Python 3.11、3.13、3.14 三版本矩阵。
6. 下载 `.yios` 与同名 `.sha256` 到同一目录，执行：

```bash
sha256sum -c YI_Director_Runtime_v2.0.0-beta.4.yios.sha256
```

`.yios` 的包内索引用于内容一致性检查；GitHub Release 的外部 checksum
与不可变设置用于发行来源校验。
