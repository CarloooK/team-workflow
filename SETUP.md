# Machine Setup Guide

所有 bot 机器的 team-workflow 初始化指引。
配好后通过 `bash setup.sh` 同步，cron 自动保持最新。

## 目录

| 机器 | 角色 | 状态 | 初始配置 |
|------|------|------|---------|
| Lenovo WSL | Xiaoxin（协调员） | ✅ 已完成 | [指引](#xiaoxinwsl) |
| Dell PC | XPS（系统架构师） | ✅ 已完成 | [指引](#xpsdell) |
| MacMini | CarloMac（实现者） | ⬜ 待配置 | [指引](#carlomacmacmini) |
| 云服务器 | Mela（QA） | ✅ 已完成 | [指引](#mela云服务器) |

---

## Xiaoxin（WSL）

**状态**: ✅ 已完成

已配置项：
- `~/team-workflow` 已克隆
- `setup.sh` 已运行，skill/模板/references 已同步到 `~/.hermes/`
- cron 每 30 分钟自动巡检（已注册，job id: bcdeeff78560）
- code-review-graph v2.3.2 已安装

---

## XPS（Dell PC）

**状态**: ⬜ 待配置

目标机器：Dell PC，Windows 或 WSL2 + Hermes Agent。

### 前置条件

- [ ] Hermes Agent 已安装并运行
- [ ] GitHub SSH key 已配置并有 repo 读取权限
- [ ] `uv` 或 `pipx` 已安装（可选，用于 code-review-graph）

### 初始化命令

```bash
# 1. 克隆工作流仓库
git clone git@github.com:CarloooK/team-workflow.git ~/team-workflow

# 2. 同步到本地 Hermes
cd ~/team-workflow && bash setup.sh

# 3. 验证
ls ~/.hermes/skills/software-development/hermes-multi-agent-pipeline/
# 应看到: SKILL.md, templates/ (4个SOUL.md), references/ (多个.md)

# 4. 可选 - 安装 code-review-graph
uv tool install code-review-graph
cd ~/projects/LogisticSystem && code-review-graph build
```

### 验证

在 Discord 发送 `@XPS 测试同步状态`，XPS 应回复确认已同步。

---

## CarloMac（MacMini）

**状态**: ⬜ 待配置

目标机器：MacMini，macOS + Hermes Agent。

### 前置条件

- [ ] Hermes Agent 已安装并运行
- [ ] GitHub SSH key 已配置并有 repo 读取权限

### 初始化命令

```bash
# 1. 克隆工作流仓库
git clone git@github.com:CarloooK/team-workflow.git ~/team-workflow

# 2. 同步到本地 Hermes
cd ~/team-workflow && bash setup.sh

# 3. 验证
ls ~/.hermes/skills/software-development/hermes-multi-agent-pipeline/
```

### 验证

在 Discord 发送 `@CarloMac 测试同步状态`，CarloMac 应回复确认已同步。

---

## Mela（云服务器）

**状态**: ✅ 已完成

已配置项：
- `~/team-workflow` 已克隆
- `setup.sh` 已运行，skill/模板/references 已同步到 `~/.hermes/`
- `discord-mela` profile 已创建，SOUL.md 使用 `<@ID>` 格式
- `mela-gateway-watchdog` cron（每 3 分钟）
- `team-workflow-sync` cron（每 30 分钟）


---

## 日常同步（所有机器通用）

```bash
# 手动同步（当知道有更新时）
cd ~/team-workflow && git pull && bash setup.sh
```

推送通知通过 cron 自动完成（仅 Xiaoxin 的 WSL 配置了 cron）。

## 故障排除

| 症状 | 原因 | 解决 |
|------|------|------|
| `git clone` 失败 | SSH key 没配或没权限 | `ssh -T git@github.com` 测试连通性 |
| `setup.sh` 报错 | ~/.hermes 路径不存在 | 先确认 Hermes Agent 已安装 |
| skill 没加载 | 文件名或路径不对 | 确认 SKILL.md 在 `software-development/hermes-multi-agent-pipeline/` 下 |
