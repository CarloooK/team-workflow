# Mela Gateway 搭建与健康检查

> 适用机器：云服务器（Mela QA bot）
> 参考资料：`scripts/mela-gateway-watchdog.py`

## 1. 安装流水线 skill 和 SOUL

```bash
cd ~/team-workflow && git pull && bash setup.sh
```

同步后复制对应 SOUL.md 到 profile：

```bash
cp ~/.hermes/skills/.../templates/soul-mela.md ~/.hermes/profiles/discord-mela/SOUL.md
```

## 2. 安装 systemd service（长期运行）

Gateway 必须通过 systemd 管理，不能用 foreground。foreground 模式退出后不会自动重启。

```bash
# 先停掉任何旧 foreground 进程
pkill -f "discord-mela" 2>/dev/null; sleep 3

# 安装 systemd unit（自动创建 hermes-gateway-<profile>.service）
hermes gateway install --profile discord-mela

# 启动
hermes gateway start --profile discord-mela

# 验证
hermes gateway status --profile discord-mela
```

期望输出：

```
● hermes-gateway-discord-mela.service - Hermes Agent Gateway
     Active: active (running) since ...
   Main PID: 12345 (python)
✓ User gateway service is running
✓ Systemd linger is enabled (service survives logout)
```

## 3. 验证连接

```bash
tail -5 ~/.hermes/profiles/discord-mela/logs/gateway.log
```

确认有：

```
[Discord] Connected as Mela#5095
✓ discord connected
Cron ticker started (interval=60s)
```

## 4. 安装健康检查 cron

健康检查脚本位于 `~/.hermes/scripts/mela-gateway-watchdog.py`，由 setup.sh 同步或手动复制。

使用 cron job 配置（运行在 Hermes cron 中）：

```bash
hermes cron create \
  --name mela-gateway-watchdog \
  --schedule "every 2m" \
  --prompt '检查 Mela gateway 健康状态。执行: python3 ~/.hermes/scripts/mela-gateway-watchdog.py
          如果输出包含"restart"或"Gateway process NOT found"，视为异常。
          否则视为正常。' \
  --deliver local
```

## 5. watchdog 脚本工作原理

脚本位于 `~/.hermes/scripts/mela-gateway-watchdog.py`，每次运行检查三项：

1. **进程存活** — `pgrep -f discord-mela` 能找到 gateway 进程
2. **日志新鲜度** — gateway.log 修改时间在 3 分钟内
3. **CLOSE-WAIT socket** — gateway 进程自身没有 stuck socket

三项全过 → 输出 `Gateway healthy (PID=X, log age=Ys)`

任意一项失败 → 执行 `systemctl --user restart hermes-gateway-discord-mela`，等待 12 秒后验证

### 设计的陷阱与修复

**陷阱 1：pkill 导致 token 冲突**

旧版 watchdog 用 `pkill -f discord-mela` 杀掉进程，然后手动 `hermes gateway run` 启动。这会导致：
- pkill 杀掉旧进程的同时，`--replace` 模式的新进程也在启动
- Discord API 收到同一个 token 的两次连接请求 → `token already in use`
- gateway 报错退出

**修复：** 用 `systemctl --user restart hermes-gateway-discord-mela` 替代。systemd 保证先 stop 再 start，不会出现竞态。

**陷阱 2：CLOSE-WAIT 误报**

旧版 `check_sockets` 用 `str(pid) in result.stdout` 在 ss 输出中搜索 PID。但 ss 输出格式包含多个进程（如 hermes CLI 会话也有 socket），导致匹配到其他进程的 CLOSE-WAIT。

**修复：** 使用精确匹配 `f"pid={pid}," in line` 或 `f",pid={pid}" in line`，只检查 gateway 自己的 PID。

**陷阱 3：foreground gateway 退出后不会自动恢复**

`hermes gateway run` 是前台进程。SSH 断开、CLI 会话结束后进程退出 → gateway 掉线，没人重启。

**修复：** 安装 systemd service 并用 `hermes gateway start` 管理。systemd 的 `Restart=on-failure` 策略 + 健康检查 cron 双重保障。

## 6. 调试命令速查

```bash
# 查看服务状态
systemctl --user status hermes-gateway-discord-mela

# 实时日志
journalctl --user -u hermes-gateway-discord-mela -f

# 手动运行健康检查
python3 ~/.hermes/scripts/mela-gateway-watchdog.py

# 检查 gateway 日志最后 N 行
tail -30 ~/.hermes/profiles/discord-mela/logs/gateway.log

# 查看 cron 列表（检查 watchdog 是否注册）
hermes cron list
```
