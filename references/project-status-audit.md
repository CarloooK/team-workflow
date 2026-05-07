# Project Status Audit — Coordinator's Standard Procedure

When Carlo asks "看一下这个项目" / "当前计划有哪些" / "未完成任务", perform
a **6-layer survey** of the repo. This produces a comprehensive status report
in ~2 minutes via subagent delegation.

## Audit Layers (in order)

```
┌─────────────────────────────────┐
│ 1. Plans       .hermes/plans/   │  ← Scope: planned but not started
├─────────────────────────────────┤
│ 2. Changes     openspec/changes/│  ← Scope: in-flight feature branches
├─────────────────────────────────┤
│ 3. Backlog     openspec/backlog/│  ← Scope: future enhancements
├─────────────────────────────────┤
│ 4. Progress    openspec/records/│  ← Scope: what's been done before
├─────────────────────────────────┤
│ 5. Reviews     openspec/records/│  ← Scope: known issues needing fix
├─────────────────────────────────┤
│ 6. Issues      gh issue list    │  ← Scope: GitHub-tracked items
└─────────────────────────────────┘
```

## Delegation Prompt (for delegate_task)

Use this when the project is too large to inspect file-by-file. Set
`toolsets=["terminal","file"]` and `role="orchestrator"`:

```
项目路径: <absolute-path>

请完成以下审查，输出一个完整的未完成任务报告（中文）：

1. .hermes/plans/ 目录：列出所有计划文档，每个文档的标题、状态、创建日期
2. openspec/changes/ 目录：列出所有 changes 子目录，每个 change 的状态
   检查 tasks.md 中是否有未完成项
3. openspec/backlog/：读取需求差距分析，列出所有待办项
4. openspec/records/progress/：读取最新进度文档，记录已完成和未完成
5. openspec/records/review/：读取审查报告，列出需跟进项
6. GitHub Issues：gh issue list 查看 open issues
7. 检查 ARCHITECTURE.md 和 CMD.md 中是否有 TODO 或 FIXME

请逐项阅读文件内容，不只列文件名。输出格式：
每个类别下列出具体内容，标注"已完成"/"进行中"/"待开始"/"待修复"。
```

## Output Format

Present to Carlo as a markdown summary with three columns:

| Category | Count | Status |
|----------|-------|--------|
| Phase A (修复) | N | ✅ / ⏳ |
| 关键问题 (H/M/L) | N | ⏳ 待修复 |
| 功能增强 | N | ⏳ 待开始 |
| 外部对接 | N | ⏳ 待开始 |

Include a **priority suggestion** at the bottom based on:
- Security/correctness issues first (H1-H5 style)
- Already-planned features second (plans/ exist)
- Wishlist items last (backlog Phase C)

## Common Pitfalls

- **changes/ 目录有已完成代码但 proposal.md 仍为 Draft** — 文档状态滞后于代码，需要批量更新
- **.hermes/plans/ 文件全部未勾选** — 计划存在但从未执行，可能是暂停时留下的
- **审查报告可能已过时** — 先确认报告的 git commit 是否在最新代码之前，避免报已修的假 bug
- **README 底部"已知问题"** — 常包含不被任何跟踪系统记录的待办项
- **GitHub Issues = 0 不代表无待办** — 很多项目的待办只在目录文件中
