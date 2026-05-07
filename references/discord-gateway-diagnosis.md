# Discord Gateway 掉线诊断

## 快速诊断流程

当 Xiaoxin 无法在 Discord 上响应时：

1.  `ps aux | grep "hermes.*gateway"` — Gateway 是否在运行？
2.  `tail -10 ~/.hermes/logs/gateway.log` — 最近的日志
3.  `grep "Connected as" ~/.hermes/logs/gateway.log | tail -1` — 最后一次成功连接的时间
4.  `lsof ~/.hermes/state.db` — 谁锁住了 state.db？

## 常见原因

### 1. state.db 被当前 CLI 会话锁住（最常见）

**现象：** Gateway 进程在运行，日志显示启动横幅 + 3 条 WARNING（PyNaCl/davey/API key），但没有 "Connected as" 消息，且持续 30+ 秒无进展。

**根因：** Hermes CLI 会话和 Discord gateway 共享同一个 `~/.hermes/state.db`（SQLite）。**先启动的进程拿到写锁**，后启动的进程卡在初始化阶段。

```
正常时序: Gateway 启动 → 拿锁 → 连接 Discord → CLI 连接 → 共享正常
冲突时序: CLI 启动 → 拿锁 → Gateway 启动 → 无法拿锁 → 卡住
```

**检查：**
```bash
lsof ~/.hermes/state.db
# 如果 CLI session (hermes CLI 进程) 持有 FD 6ur, 7ur → 冲突确认
```

**修复：** 结束当前 Hermes CLI 会话，重新启动 gateway。

### 2. WSL 休眠导致 gateway 被杀死

**现象：** 日志最后一条在几小时前，无错误信息，gateway 进程不存在。

**根因：** WSL2 在宿主机待机/休眠时会暂停所有 VM 进程，恢复后 gateway 不会自动重启。

**修复：** 启动 gateway。
```bash
tmux new-session -d -s xiaoxin 'hermes gateway run --profile discord-xiaoxin --replace'
```

### 3. Bot Token 过期

**现象：** API 返回 401。

**检查：**
```bash
curl -s -H "Authorization: Bot <token>" https://discord.com/api/v10/users/@me
# HTTP 200 = 正常, 401 = token 无效
```

### 4. SQLite 锁文件残留

**现象：** 启动后出现 `database is locked` 警告。

**修复：**
```bash
rm -f ~/.hermes/state.db-shm ~/.hermes/state.db-wal
rm -f ~/.hermes/response_store.db-shm ~/.hermes/response_store.db-wal
```

## 完整重启流程

```bash
# 1. 停止当前 gateway
tmux kill-session -t xiaoxin 2>/dev/null

# 2. 清理锁文件
rm -f ~/.hermes/state.db-shm ~/.hermes/state.db-wal
rm -f ~/.hermes/response_store.db-shm ~/.hermes/response_store.db-wal

# 3. 启动
tmux new-session -d -s xiaoxin 'hermes gateway run --profile discord-xiaoxin --replace 2>&1 | tee -a ~/.hermes/logs/gateway.log'

# 4. 验证连接
sleep 20
grep "Connected as" ~/.hermes/logs/gateway.log | tail -1
```

## 架构备注

- Gateway 和 CLI 共享同一个 state.db — 无法同时运行两个独立的 Hermes Agent 会话
- 如果需要在 Discord bot 在线时通过 CLI 工作，需确保 gateway 先启动，CLI 后连接
- 跨机器部署（Dell/XPS, MacMini/CarloMac, 云/Mela）不存在此问题，因为每台机器有独立的 state.db
