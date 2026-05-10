#!/bin/bash
# gateway-watchdog.sh — 系统级 gateway 保活脚本
# 不依赖 Hermes cron（gateway 掉了 Hermes cron 也跑不了）
# 用 Linux 系统 cron 每 2 分钟执行一次
#
# 机器适配（通过环境变量或参数）:
#   PROFILE=<profile-name>    Hermes 配置名（默认 discord-xiaoxin）
#   RESTART_CMD=<command>     启动命令（默认 tmux 启动 gateway）

set -e

PROFILE="${PROFILE:-discord-xiaoxin}"
LOG_DIR="$HOME/.hermes/logs"
LOG_FILE="$LOG_DIR/gateway-watchdog.log"
PIDFILE="$LOG_DIR/gateway-watchdog.pid"
MAX_DOWNTIME_SEC=600   # 掉线超过 10 分钟则视为严重故障
MIN_RESTART_INTERVAL=60  # 至少间隔 60 秒才重启（防抖）

mkdir -p "$LOG_DIR"

# 防止两个 watchdog 同时跑
if [ -f "$PIDFILE" ]; then
    OLD_PID=$(cat "$PIDFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        exit 0  # 已有实例在跑
    fi
fi
echo $$ > "$PIDFILE"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# 检查 gateway 是否活跃
check_gateway() {
    # 方法1: tmux session 检查
    if tmux has-session -t gateway 2>/dev/null; then
        # 进一步检查进程是否还活着
        local PID
        PID=$(tmux list-panes -t gateway -F "#{pane_pid}" 2>/dev/null | head -1)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            return 0  # 正常
        fi
        # tmux session 在但进程死了 — 清理
        tmux kill-session -t gateway 2>/dev/null
    fi

    # 方法2: 检查有没有 hermes gateway 进程在跑（兜底）
    if pgrep -f "hermes gateway run.*$PROFILE" > /dev/null 2>&1; then
        return 0  # 有进程但没 tmux — 也算活着
    fi

    return 1  # 彻底挂了
}

restart_gateway() {
    log "Gateway 掉线，尝试重启 (profile=$PROFILE)..."

    # 清理残留
    tmux kill-session -t gateway 2>/dev/null || true
    pkill -f "hermes gateway run.*$PROFILE" 2>/dev/null || true
    sleep 2

    # 启动新 gateway
    tmux new-session -d -s gateway "hermes gateway run --profile $PROFILE --replace 2>&1 | tee -a $LOG_DIR/gateway.log"

    # 等待几秒检查是否启动成功
    sleep 5
    if tmux has-session -t gateway 2>/dev/null; then
        log "✅ Gateway 重启成功"
    else
        log "❌ Gateway 启动失败 — tmux session 未创建"
        # 尝试直接启动（不用 tmux）
        nohup hermes gateway run --profile "$PROFILE" --replace \
            >> "$LOG_DIR/gateway.log" 2>&1 &
        log "尝试 nohup 模式启动 (PID: $!)"
    fi
}

# 主逻辑
if check_gateway; then
    # 正常运行 — 静默，不写日志
    exit 0
else
    # 防抖：上次重启距离现在不到 MIN_RESTART_INTERVAL 秒，跳过
    LAST_RESTART=$(grep "Gateway 重启成功\|启动失败" "$LOG_FILE" 2>/dev/null | tail -1 | grep -oP '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
    if [ -n "$LAST_RESTART" ]; then
        LAST_EPOCH=$(date -d "$LAST_RESTART" +%s 2>/dev/null || echo 0)
        NOW_EPOCH=$(date +%s)
        ELAPSED=$((NOW_EPOCH - LAST_EPOCH))
        if [ "$ELAPSED" -lt "$MIN_RESTART_INTERVAL" ]; then
            # 上次重启太近，跳过本次（防无限重启）
            log "⏳ 上次重启仅 ${ELAPSED}s 前，跳过本次重启（防抖）"
            exit 0
        fi
    fi

    log "⚠️ Gateway 检测到掉线"
    restart_gateway
fi
