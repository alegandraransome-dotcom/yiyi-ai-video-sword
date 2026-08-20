# `.yios` 包格式

`.yios` 是只读、纯数据、可复现的 ZIP 容器。

## 成员

```text
mimetype
manifest.yaml
LICENSE
runtime/**
schemas/**
evals/**
internal-skills/**
THIRD_PARTY_NOTICES.md
index.json
```

不会进入包：Python 编译器、当前项目状态、`archive/`、测试代码、GitHub 配置、历史发行物。

## 确定性规则

- `mimetype` 必须是第一项，内容固定为 `application/vnd.yi-director.yios`。
- 所有成员使用 UTF-8/LF；ZIP 路径使用正斜杠，不允许绝对路径、`.`、`..`、目录项或重复项。
- 时间固定为 `1980-01-01 00:00:00`，权限固定为 `0644`。
- 使用 `ZIP_STORED`，避免压缩库版本改变发行字节。
- `index.json` 规范化记录除自身外每个成员的大小和 SHA-256。
- `runtime/canonical-order.txt` 必须逐项匹配固定模块顺序；按其顺序重组的内容必须命中 `canonical_source_sha256`。
- CI 在两个干净路径重复构建并执行字节比较。

## 安全读取

读取器先拒绝路径穿越、符号链接、重复/未声明成员、目录项、非规范 ZIP 元数据、过大展开体积和缺失入口，再验证 `index.json` 与 Canonical Runtime，最后才向编译器交付同一份已验证内存快照。

包内索引提供一致性校验，不证明发行者身份。下载正式发行物时，还应使用 GitHub Release 提供的外部 `.sha256`；仓库启用 Immutable Releases 后再把 Release 视为不可变来源。
