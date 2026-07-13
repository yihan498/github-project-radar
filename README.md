# GitHub 项目深度推荐雷达

一个面向 Codex 的每日 GitHub 开源项目发现、冷存与深度分析工作流。

它每天从新项目、经典项目、近期活跃项目和经过多日观测验证的 star 上升项目中选择一个值得研究的仓库，保存关键一手材料，并生成约 8,000–12,000 个中文字符的来源驱动分析。

## 已实现能力

- 使用 GitHub API 建立每日候选池。
- 保存多日 star 观测；首次观测不会被误写成“暴涨”。
- 按日期冷存仓库源码、Git bundle、API 元数据、关键文档和文件校验值。
- 在写作前检查 README、文档和源码是否足以支撑深度分析。
- 区分仓库事实、分析推断和借鉴建议。
- 对长文使用版本化文件名，并为每版保存版本说明。
- 可由 Codex 自动任务每日运行。

## 目录结构

```text
skills/github-project-radar/   Codex Skill、配置、分析规范和执行脚本
data/candidates/               每日候选项目快照
data/daily/                    每日最终选择与交付记录
data/observations.json         跨日 star 观测历史
cold-storage/                  按项目与日期保存的冷存材料
reports/                       版本化中文深度分析
```

## 手动运行

发现候选项目：

```powershell
python skills/github-project-radar/scripts/radar.py discover --workspace .
```

冷存选定项目：

```powershell
python skills/github-project-radar/scripts/radar.py archive --workspace . --repo owner/repository
```

设置 `GITHUB_TOKEN` 可以提高 GitHub API 调用限额；不设置时使用匿名 API。

之后完整阅读 [`skills/github-project-radar/SKILL.md`](skills/github-project-radar/SKILL.md)，按照其中的来源充分性门槛和版本化规则完成分析。

## 今日示例

- 深度分析：[`reports/2026-07-13/nagisanzenin--engram-v1.md`](reports/2026-07-13/nagisanzenin--engram-v1.md)
- 版本说明：[`reports/2026-07-13/version-note-v1.md`](reports/2026-07-13/version-note-v1.md)
- 当日记录：[`data/daily/2026-07-13.json`](data/daily/2026-07-13.json)

## 证据原则

- 只有拿到 substantive README、文档和相关源码时，才生成长篇“原项目分析”。
- 只有标题、简介或 API 元数据时，只能生成公开信息概览。
- 缺失材料保持为 `missing` 或 `not verified`，不能转写成负面事实。
- star 上升必须由至少两个本地观测点支持。
- 主结论建立在覆盖充分、测量稳定的证据上；探索性观察单独标注。

## 数据与版权

冷存材料用于研究、审计和版本追踪。被分析项目仍遵循各自许可证；引用与再分发前应检查对应仓库的许可条款。分析文稿避免大段复制原文，并提供项目路径或链接作为证据索引。

