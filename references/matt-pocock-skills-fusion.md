# Matt Pocock Skills 融合部署经验

> 日期: 2026-08-03 | 操作: CarloMac
> 来源: https://github.com/mattpocock/skills
> 状态: ✅ 全部部署完成

---

## 概述

将 Matt Pocock 的 "Skills for Real Engineers" 方法论融合到 Hermes Agent + OpenSpec 工作流中。核心理念：不创建平行流程，而是强化现有管道的上游（需求对齐）和下游（审查分类）。

---

## 部署清单

### 新增技能（6个，全部位于 `~/.hermes/skills/software-development/`）

| 技能 | 分类 | 角色 | 说明 |
|------|:----:|:----:|------|
| `grill-me` | P0 | PM/SE | 动手前结构化盘问，一题一问，逐个决策树分支 |
| `domain-modeling` | P0 | PM/SE | 术语表精炼 + ADR 记录 + 场景挑战 |
| `to-tickets` | P0 | PM/SE | 需求→可执行 Task Card 拆解 + 分批调度 |
| `code-review` | P0 | PM/SE | 七维度审查：契约/性能/安全/逻辑/错误/风格/测试 |
| `triage` | P0 | PM/SE | Bug 四级分类 + 归属路由 + 发布阻断识别 |
| `implement` | P1 | DEV | Spec+TC→代码，角色感知（diff_implement 检查） |

### 复用已有技能（2个，无需新建）

| 技能 | 覆盖 Matt 原技能 | 说明 |
|------|:---------------:|------|
| `test-driven-development` | tdd | 完整 RED-GREEN-REFACTOR 流程 |
| `systematic-debugging` | diagnosing-bugs | 4 阶段根因分析 |

---

## 融合工作流

```
Phase 0:  grill-me          → 结构化盘问，达成共识（不存档）
Phase 1:  domain-modeling   → 术语写入 PRD "领域术语"章节
Phase 1:  PRD 编写           → openspec/specs/03-需求规格/
Phase 2:  User Stories      → openspec/specs/03-需求规格/
Phase 3:  to-tickets        → openspec/records/progress/TCxx.md
Phase 4:  implement          → DEV 按 TC 写代码
Phase 5:  code-review        → docs/reviews/code-review-YYYY-MM-DD.md
Phase 6:  QA 测试            → docs/bug-list-vX.md
Phase 7:  triage             → Bug 分级 + 优先级 + 归属
Phase 8:  PO 审批            → Git Tag → 上线
```

---

## 关键架构决策

### 1. 角色配置化（替代硬编码）

**之前**：CarloMac/Mela/Xiaoxin 角色硬编码在 skill 和 USER.md 中。

**之后**：每项目通过 `openspec/project-roles.yaml` 定义：

```yaml
project: <name>
roles:
  PM/SE:
    handle: CarloMac
    diff_implement: false   # 绝不生成 diff
    skills: [grill-me, domain-modeling, to-tickets, code-review, triage]
  DEV:
    handle: Mela
    diff_implement: true
    skills: [implement, test-driven-development, systematic-debugging]
  QA:
    handle: Xiaoxin
    skills: [test-planning, bug-reporting]
```

**收益**：同一 Agent 在不同项目可扮演不同角色。CarloMac 在 AI_BountyBoard 是 PM/SE（不改代码），换到个人项目可以是 DEV（写代码）。

### 2. 文档不割裂

Matt 技能产出的文档全部映射到现有 OpenSpec 结构，不建立平行目录：

| Matt 约定 | 映射到 |
|-----------|--------|
| CONTEXT.md（术语表） | PRD "领域术语"章节 |
| docs/adr/ | openspec/specs/05-架构决策/ |
| Code review | docs/reviews/code-review-YYYY-MM-DD.md |
| Task cards | openspec/records/progress/TCxx.md |

### 3. diff_implement 硬约束

每个 skill 在生成代码前检查 `project-roles.yaml`：
- `false` → 输出方案指导 + 文件清单，不生成 diff
- `true` → 正常生成代码

### 4. 技能间引用

Matt 原版使用 Claude Code 的 `/slash-command` 委托模式（grill-me → /grilling）。Hermes 改为：
- 内联完整 prompt 到 SKILL.md body
- 通过 `metadata.hermes.related_skills` 声明依赖
- Agent 无需特殊命令，正常加载 skill 即可

---

## 踩坑记录

### 坑 1: 记忆工具 target='user' 匹配失败

**现象**：`memory(action='replace', target='user')` 的 `old_text` 匹配不到 user store 条目，显示的是 memory store 的 entries。

**根因**：工具 bug — current_entries 在 replace 失败时展示的是 memory store，而非 user store。

**解决**：直接编辑 `~/.hermes/memories/USER.md`（§ 分隔符格式），用 `patch` 工具写入。

### 坑 2: skill description 中的冒号

**现象**：`skill_manage(action='create')` 报 YAML parse error: `mapping values are not allowed here`。

**根因**：description 字段中的 `:` 被 YAML 解析为 key-value 分隔符。

**解决**：description 用双引号包裹 `description: "..."`。

### 坑 3: P1 技能 tdd/diagnosing-bugs 无需新建

**发现**：Hermes 已有 `test-driven-development` 和 `systematic-debugging`，质量高于 Matt 原版。直接映射即可，无需移植。

**教训**：先检查 `~/.hermes/skills/` 再决定是否移植。

---

## 同步到其他机器

其他机器获取这些技能的方法：

```bash
# 方法 1: 直接复制技能文件
scp -r carlomac:~/.hermes/skills/software-development/{grill-me,domain-modeling,to-tickets,code-review,triage,implement} \
    ~/.hermes/skills/software-development/

# 方法 2: 从本仓库同步（如果 skills/ 目录已加入 team-workflow）
cd ~/team-workflow && git pull
cp -r skills-fusion/* ~/.hermes/skills/software-development/
```

---

## 验证清单

- [x] grill-me: 能发起结构化盘问，一题一问
- [x] domain-modeling: 术语写入 PRD 章节，不创建 CONTEXT.md
- [x] to-tickets: 从 User Story 生成 TCxx.md
- [x] code-review: 七维度检查，产出 review doc
- [x] triage: 四级分类（P0/P1/P2/P3），区分纯Bug/需求变更/UI打磨
- [x] implement: 尊重 diff_implement，PM 模式不写代码
- [x] USER.md 角色信息已更新
- [x] project-roles.yaml 已创建
- [x] pm-requirements-decomposition skill 已去硬编码
- [x] dev-workflow.md 已去硬编码

---

## 相关文件

| 文件 | 路径 |
|------|------|
| 融合方案原文 | `AI_BountyBoard/docs/matt-pocock-fusion-plan.md` |
| 角色配置 | `AI_BountyBoard/openspec/project-roles.yaml` |
| 开发流程 | `AI_BountyBoard/docs/dev-workflow.md` |
| 技能目录 | `~/.hermes/skills/software-development/` |
| User Profile | `~/.hermes/memories/USER.md` |
