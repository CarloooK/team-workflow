# Matt Pocock Skills 完整移植部署记录

> 日期: 2026-08-20 | 操作: Mela
> 来源: https://github.com/mattpocock/skills
> 状态: ✅ 25 个 skill 完整移植为 Hermes 格式（Mela 机器已部署）
> 区别: 见下方「与融合版的区别」，本记录是**完整忠实移植**，非 CarloMac 08-03 的**选择性融合**

---

## 概述

将 Matt Pocock 的 "Skills for Real Engineers" 仓库**完整移植**为 Hermes 格式，共 25 个 skill。

与 08-03 CarloMac 的「融合版」根本区别：这次是**忠实移植**——保留 Matt 原文语义，
不添加 `diff_implement` 角色约束、不映射到 OpenSpec 目录结构、不改写流程为项目定制。
适合想原汁原味使用 Matt 方法论、或作为独立方法库参考的场景。

---

## 部署清单（25 个）

### software-development（16 个）
| skill | 类型 | 说明 |
|-------|------|------|
| ask-matt | user | 路由器：按场景推荐用哪个 skill |
| codebase-design | model | 深模块设计词汇（module/interface/depth/seam） |
| domain-modeling | model | 领域模型精炼 + ADR 记录 |
| grill-with-docs | user | 拷问式盘问 + 顺带建 CONTEXT.md/ADR |
| implement | user | Spec/Ticket → 代码，驱动 TDD + 收尾 review |
| improve-codebase-architecture | user | 扫描代码找深模块机会，出 HTML 报告 |
| prototype | model | 一次性原型回答设计问题 |
| research | model | 后台 agent 查资料，产出带引用的 md |
| setup-matt-pocock-skills | user | 每仓库跑一次：issue tracker/label/文档布局 |
| to-spec | user | 当前对话 → spec 发布到 tracker |
| to-tickets | user | 计划/spec → tracer-bullet tickets（带 blocking edges） |
| triage | user | issue/PR 状态机分类 + agent-ready brief |
| wayfinder | user | 超大工作 → 决策 ticket 地图，逐个解决 |
| wizard | model | 生成交互式 bash 向导（只有人能做的步骤） |
| migrate-to-shoehorn | model | 测试文件 `as` 断言 → @total-typescript/shoehorn |
| scaffold-exercises | model | 生成练习题目录结构（section/problem/solution） |

### productivity（7 个）
| skill | 类型 | 说明 |
|-------|------|------|
| grill-me | user | 拷问式盘问（委托 grilling） |
| grilling | model | 盘问底层原语（design tree / frontier） |
| handoff | user | 对话压缩成 handoff 文档 |
| teach | user | 多会话教学，当前目录做有状态工作区 |
| to-questionnaire | user | 决策 → 给他人填的问卷 |
| wait-what | user | 消息没听懂时重新用大白话解释 |
| writing-for-agents | model | 写 agent 消费的文档（skills/AGENTS.md） |

### devops（2 个）
| skill | 类型 | 说明 |
|-------|------|------|
| git-guardrails-claude-code | model | Claude Code hooks 阻断危险 git 命令 |
| setup-pre-commit | model | Husky + lint-staged pre-commit hooks |

> 「user」= user-invoked（编排型，仅用户主动调用）；「model」= model-invoked（纪律型，agent 可自动抓取）

---

## 与融合版（CarloMac, 08-03）的区别

| 维度 | 融合版（08-03） | 本次完整移植（08-20） |
|------|-----------------|----------------------|
| 范围 | 选择性 6 个 | 完整 25 个（作者 README 列出的全部） |
| 内容 | 改造版：加 diff_implement、映射 OpenSpec、去硬编码 | 忠实版：保留 Matt 原文语义 |
| 分类 | 全放 software-development | 按功能分 software-development / productivity / devops |
| 跨引用 | 内联 prompt + related_skills 声明 | 转成 `skill_view(name=...)` |
| tdd / diagnosing-bugs | 用已有的 test-driven-development / systematic-debugging 替代 | 本次也删除了（见下），保留已有版本 |
| 适用 | AI_BountyBoard 项目定制流程 | 通用方法库 / 原汁原味参考 |

**结论**：两份不冲突，是同一上游的两种落地方式。融合版服务于项目流水线，完整版服务于方法库。按需选用。

---

## 删除的 4 个重叠（保留已有的 Hermes 版本）

| 删除（Matt 版） | 保留已有（Hermes 版） |
|----------------|----------------------|
| tdd | test-driven-development |
| diagnosing-bugs | systematic-debugging |
| code-review | requesting-code-review |
| resolving-merge-conflicts | git-merge-conflict-resolution |

删除后已同步改写 ask-matt / codebase-design / implement 的 `related_skills` 和正文引用，
指向保留的 Hermes 版本，无悬空引用。

---

## 转换规则（要点）

1. **frontmatter**：Claude 的 `name/description/disable-model-invocation` → Hermes 的
   `name/description/version/author/license/metadata.hermes.tags+related_skills`；
   `disable-model-invocation: true` → description 加 `User-invoked.` 前缀 + `user-invoked` tag
2. **跨引用**：`Call the Skill tool with X`（含 calls/calling、twice-for 变体）→ `skill_view(name='X')`
3. **辅助文件**：`*.md` → `references/`，脚本 → `scripts/`，丢弃 `agents/openai.yaml`
4. **相对链接**：`[x](tests.md)` → `[x](references/tests.md)`

---

## 可复用工具

本次转换流程已沉淀为 Hermes skill：

- `~/.hermes/skills/software-development/import-external-skills/`
  - `SKILL.md`：转换规则 + 6 条踩坑 + 验证清单
  - `scripts/convert_external_skills.py`：可复用批量转换引擎（含 mattpocock 全量映射示例）

以后导入任意外部 skills 仓库，改脚本里的 `ROOT` 和 `SKILLS` 表即可。

---

## 同步到其他机器

```bash
# 方法 1: 直接复制 skill 文件（分类目录对拷）
rsync -av ~/.hermes/skills/software-development/{ask-matt,codebase-design,domain-modeling,grill-with-docs,implement,improve-codebase-architecture,migrate-to-shoehorn,prototype,research,scaffold-exercises,setup-matt-pocock-skills,to-spec,to-tickets,triage,wayfinder,wizard} <target>:~/.hermes/skills/software-development/
rsync -av ~/.hermes/skills/productivity/{grill-me,grilling,handoff,teach,to-questionnaire,wait-what,writing-for-agents} <target>:~/.hermes/skills/productivity/
rsync -av ~/.hermes/skills/devops/{git-guardrails-claude-code,setup-pre-commit} <target>:~/.hermes/skills/devops/

# 方法 2: 用可复用脚本在目标机器重新转换（推荐，幂等）
#   git clone --depth 1 https://github.com/mattpocock/skills /tmp/mattpocock-skills
#   在目标机器跑 import-external-skills 的 scripts/convert_external_skills.py
```
