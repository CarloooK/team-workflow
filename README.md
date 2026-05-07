# Team Workflow

Bot team 的工作流定义仓库。所有机器（WSL, Dell PC, MacMini, 云服务器）从这里同步配置。

## 同步状态

| 机器 | 角色 | 状态 |
|------|------|------|
| Lenovo WSL | Xiaoxin（协调员） | ✅ 已配（含 cron 自动巡检） |
| Dell PC | XPS（系统架构师） | ⬜ 待配置 — [SETUP.md](SETUP.md) |
| MacMini | CarloMac（实现者） | ⬜ 待配置 — [SETUP.md](SETUP.md) |
| 云服务器 | Mela（QA） | ⬜ 待配置 — [SETUP.md](SETUP.md) |

> 初始化指引详见 [SETUP.md](SETUP.md)

## 目录结构

```
team-workflow/
├── pipeline/          ← 流水线 skill（核心工作流定义）
├── profiles/          ← 每个 bot 的 SOUL.md 模板
├── references/        ← 使用指南、踩坑总结
├── SETUP.md           ← 各机器初始化指引
├── setup.sh           ← 一键同步到本地 ~/.hermes/
└── README.md
```

## 新机器初始化

```bash
# 1. 克隆
git clone git@github.com:CarloooK/team-workflow.git ~/team-workflow

# 2. 同步到 Hermes
cd ~/team-workflow && bash setup.sh

# 3. 验证
ls ~/.hermes/skills/software-development/hermes-multi-agent-pipeline/
```

## 日常同步（当流程有更新）

自动：每 30 分钟 cron 巡检（仅在 Xiaoxin 的 WSL 上）
手动：`cd ~/team-workflow && git pull && bash setup.sh`

## 如何修改流程

1. 改 `pipeline/SKILL.md`（或其他文件）
2. 本地 `git commit`（不 push）
3. `@Carlo 流程有更新，请审批推送`
4. Carlo 批准后 `git push`
5. 其他机器自动或手动同步

## 团队成员

| 角色 | 机器 | 职能 |
|------|------|------|
| **Carlo** | Any PC | 需求、最终审批 |
| **Xiaoxin** | Lenovo WSL | 协调、配置、发布、文档 |
| **XPS** | Dell PC | 系统架构、可行性分析 |
| **Mela** | 云服务器 | 质量保证、测试、代码审查 |
| **CarloMac** | MacMini | 实现、创意编码 |
