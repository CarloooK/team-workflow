# Gateway Watchdog + Session Recovery — 每台 Bot 的安装说明

## 每台机器都需要

### 1. 安装 watchdog 脚本

```bash
# 从 team-workflow 同步
mkdir -p ~/.hermes/scripts/
cp ~/team-workflow/pipeline/scripts/gateway-watchdog.sh ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/gateway-watchdog.sh
```

### 2. 配置系统 cron（每 2 分钟检查一次）

**Linux (Xiaoxin WSL, Mela 云服务器):**
```bash
(crontab -l 2>/dev/null; echo "*/2 * * * * bash \$HOME/.hermes/scripts/gateway-watchdog.sh") | crontab -
crontab -l  # 验证
```

**macOS (CarloMac MacMini):**
```bash
# macOS cron 同 Linux，但注意 PATH 可能不同（需全路径）
(crontab -l 2>/dev/null; echo "*/2 * * * * /bin/bash \$HOME/.hermes/scripts/gateway-watchdog.sh") | crontab -
crontab -l  # 验证
```

**Windows (XPS Dell PC):**
WSL 环境与 Xiaoxin 相同，同上 Linux 配置。

如果需要自定义 profile 名（不是 `discord-xiaoxin`），设置环境变量：
```bash
(crontab -l 2>/dev/null; echo "*/2 * * * * PROFILE=discord-xps bash \$HOME/.hermes/scripts/gateway-watchdog.sh") | crontab -
```

### 3. 验证 watchdog 生效

```bash
# 手动跑一次
bash ~/.hermes/scripts/gateway-watchdog.sh

# 查看日志
tail -5 ~/.hermes/logs/gateway-watchdog.log

# 日志格式示例:
# [2026-05-10 14:08:28] ⚠️ Gateway 检测到掉线
# [2026-05-10 14:08:28] Gateway 掉线，尝试重启 (profile=discord-xiaoxin)...
# [2026-05-10 14:08:35] ✅ Gateway 重启成功
```

### 4. SOUL.md 加入 Session Recovery

确保 SOUL.md 模板已同步自 team-workflow:
```bash
cd ~/team-workflow && bash setup.sh
```
或者在 `~/.hermes/profiles/<bot-name>/SOUL.md` 手动添加 Session Recovery 规则。

---

## 原理说明

### Watchdog 做了什么

```
Linux cron (每2分钟)
  └─ gateway-watchdog.sh
       ├─ 检查 tmux session "gateway" 是否存在
       ├─ 检查 gateway 进程是否存活
       ├─ 都正常 → 静默退出（不写日志不刷屏）
       └─ 异常 → 杀掉残留进程 → tmux 重启 → 等待5秒检查
              └─ 防抖: 如果上次重启不到60秒，跳过
```

### Session Recovery 做了什么

```
Gateway 重启后第一次启动:
  1. 读取 GitHub 上 docs/session/current.md
  2. 如果存在 → "@Carlo 我重启了，上次在讨论 <topic>，继续吗？"
  3. 如果不存在 → 正常待命
```

### 什么时候 session 文件被写入

| 阶段 | 写入内容 |
|------|---------|
| 讨论结束 | 写 plan 时同步写 session |
| Carlo 审批 | 更新 stage |
| 实现开始 | 更新 stage |
| PR 提交 | 更新 stage |
| 发布完成 | 删除 session 文件 |

---

## FAQ

**Q: cron 任务在 gateway 掉线时能跑吗？**
A: 能。Linux cron 是系统级服务，不依赖 Hermes 进程。

**Q: 如果 gateway 反复崩溃怎么办？**
A: 防抖机制：两次重启之间至少间隔 60 秒。如果每分钟都崩溃，watchdog 每 2 分钟检查一次，跳过大部分。日志里会看到 "⏳ 上次重启仅 Xs 前，跳过本次重启（防抖）"。

**Q: 手动重启 gateway 后 watchdog 会冲突吗？**
A: 不会。watchdog 只会在 gateway 不在运行时启动它。如果你手动启动了一个，watchdog 下次检查发现已经在了就静默退出。
