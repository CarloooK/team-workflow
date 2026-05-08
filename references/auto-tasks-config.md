# 在 Mela（云服务器）上配置的自动任务

## 1. mela-gateway-watchdog（每 3 分钟）

**用途：** 检查 Mela Discord gateway 是否健康，异常时自动重启。

**创建命令：**
```bash
hermes cron create \
  --name mela-gateway-watchdog \
  --schedule "every 3m" \
  --prompt '检查 Mela gateway 健康状态。执行: python3 /home/admin/.hermes/scripts/mela-gateway-watchdog.py
如果输出包含"restarting"或"Gateway process NOT found"，视为异常。
如果输出包含"Gateway healthy"，视为正常。' \
  --deliver local
```

**依赖脚本：** `~/.hermes/scripts/mela-gateway-watchdog.py` — 由 `setup.sh` 同步（参考 `references/mela-gateway-setup.md`）

**验证：**
```bash
hermes cron list | grep mela-gateway-watchdog
# 确认 next_run_at 是最近的时间
```

---

## 2. team-workflow-sync（每 30 分钟）

**用途：** 拉取 team-workflow 仓库的远程更新，自动执行 setup.sh 同步到本地 Hermes 配置。

**创建命令：**
```bash
hermes cron create \
  --name team-workflow-sync \
  --schedule "every 30m" \
  --workdir /home/admin/team-workflow \
  --prompt '检查 team-workflow 仓库是否有远程更新。执行:
cd /home/admin/team-workflow && git fetch origin 2>&1

然后执行: git log HEAD..origin/master --oneline | head -5

如果有新提交（git log 有输出），执行:
git pull --rebase && bash setup.sh

如果没有新提交，输出 "Already up to date" 即可。' \
  --deliver local
```

**验证：**
```bash
hermes cron list | grep team-workflow-sync
# 确认 next_run_at 是最近的时间
```

> **注意：** `--workdir` 参数会让该 job 顺序执行（不与其它 job 并行），这是为了确保 git 操作不会冲突。
> `enabled_toolsets: ["terminal"]` 限制 job 只加载终端工具，节省 token。

---

## 检查所有 cron 任务

```bash
hermes cron list
```
