# 钉钉管道搭建手册（DingTalk Pipeline Setup）

> 2026-09-01 建立。背景：Discord 国内直连不稳定（需 Windows 代理转发），
> 团队通信迁移至钉钉。Discord 配置保留但暂时禁用（不删除，可随时回切）。

## 一、架构

```
Carlo(PM, 人) ──钉钉群──┬── Xiaoxin-Bot  (SE/协调, profile: discord-xiaoxin)
                         ├── Mela-Bot     (DEV,    profile: mela)
                         └── Workbuddy-Bot(QA,     待建)
```

- 每个 bot = 一个钉钉「企业内部应用」（开通机器人能力，Stream 模式）
- 每个 bot = 一个独立 Hermes profile + 独立 gateway 实例（tmux 会话）
- 所有 bot 加入同一个钉钉群，靠 @提及 / 唤醒词 触发

## 二、钉钉开放平台侧（Carlo 操作）

1. https://open-dev.dingtalk.com → 开发者后台 → 应用开发 → **创建应用**（只填名称+描述，不需要 H5微应用）
2. 应用详情 → **应用能力 → 机器人** → 开启机器人配置
3. 机器人信息：名称/简介/图标(240×240) → **消息接收模式选 Stream 模式**（默认，免公网回调）
4. **版本管理与发布** → 创建版本并发布（⚠️ 配置修改必须发布后才生效）
5. 凭证与基础信息 → 复制 **Client ID（AppKey）** 和 **Client Secret（AppSecret）**
6. 测试期应用可见范围选「仅我可见」

## 三、Hermes 侧配置（Xiaoxin 执行）

### 依赖（装入 hermes venv）
```bash
~/.hermes/hermes-agent/venv/bin/pip install -i https://mirrors.aliyun.com/pypi/simple/ "dingtalk-stream>=0.20" httpx
```

### .env（每个 profile 一份）
```ini
DINGTALK_CLIENT_ID=<AppKey>
DINGTALK_CLIENT_SECRET=<AppSecret>
```
- 注意：Mela 等 bot 的 .env **不要保留** DISCORD_BOT_TOKEN（会与 Xiaoxin 抢 Discord 连接）
- 根 .env 与 profile .env 都要写（gateway 实际生效的是 profile 那份）

### config.yaml（profile 内，用 `hermes -p <profile> config set` 写入）
```yaml
dingtalk:
  require_mention: true
  mention_patterns: ["<bot名>", "<中文别名>"]
```

### 启动 gateway
```bash
# Xiaoxin（需要代理时加 export，钉钉直连不受影响）
tmux new-session -d -s gateway 'cd ~ && export https_proxy=http://172.23.0.1:26541 http_proxy=http://172.23.0.1:26541 HERMES_HOME=/home/chao/.hermes && hermes gateway run --replace 2>&1'
# Mela（纯钉钉，无需代理）
tmux new-session -d -s gateway-mela 'cd ~ && hermes -p mela gateway run --replace 2>&1'
```

### 验证
```bash
# 关键：INFO 日志写在文件里，不在 tmux 面板！
grep -E "Connecting|✓|✗|Gateway running" ~/.hermes/profiles/<profile>/logs/gateway.log | tail
# 期望输出：
#   Connecting to dingtalk...
#   ✓ dingtalk connected
#   Gateway running with N platform(s)
```

## 四、群内协作机制

### 添加机器人到群
群设置 → 群机器人 → 添加机器人 → 选择已发布的企业内部应用机器人（可多个共存）。

### 触发条件（二选一，满足即响应）
1. **@提及**：用户在群里 @某 bot（isInAtList 检测）
2. **唤醒词**：消息文本含 `mention_patterns` 中任意词（如"Mela"/"梅拉"），无需 @

### bot 间传话
- 首选：`@Mela 请实现 ...`（钉钉是否支持 bot 互 @ 待实测）
- 兜底（一定可靠）：`Mela 请实现 ...` — 唤醒词触发

## 五、限流须知

| 限制 | 数值 | 应对 |
|------|------|------|
| 发消息 | 20 条/分钟/机器人，超限静默 10 分钟 | 方案/长文发链接，不刷屏；多 bot 各自独立额度 |
| 普通机器人每日 | ~1000 条 | 讨论场景远够 |
| API | 40 次/秒/应用/接口 | 用不到 |

> 钉钉开放平台**不按消息量收费**，限流是保护机制不是计费。

## 六、已踩的坑（2026-09-01）

1. **gateway 日志位置**：INFO 日志写到 `~/.hermes/profiles/<profile>/logs/gateway.log`，
   tmux 面板只显示 WARNING+。排查连接问题先看 gateway.log，别被"面板没输出"误导。
2. **SIGUSR2 会杀进程**：faulthandler.register(chain=True) 转储栈后执行默认信号处理 = 终止。
   调试用 `py-spy dump`（需 sudo）或直接看日志，别发 SIGUSR2。
3. **私聊配对**：用户首次私聊 bot 会返回配对码，需执行
   `hermes -p <profile> pairing approve dingtalk <CODE>` 授权。
4. **profile 克隆**：`hermes profile create mela --clone-from discord-xiaoxin` 会连带复制
   .env 里的 Discord token 和旧唤醒词 — 必须改 DINGTALK 凭证、删 DISCORD_*、改 mention_patterns。
5. **config.yaml 保护**：profile 的 config.yaml 禁止直接 patch，用
   `hermes -p <profile> config set <key> <value>` 写入。
6. **发布才生效**：钉钉机器人配置改动必须发布新版本，否则不生效。
7. **gateway 进程树内不能 kill gateway**：CLI 会话若由 gateway 派生，kill/tmux kill-session 会被
   安全拦截（SIGTERM 传播）。重启目标 bot 用 `tmux send-keys -t <session> C-c` 再重发启动命令；
   Ctrl-C 可能连带退出外层 shell → 直接 `tmux kill-session` 后重建更干净（用 send-keys 也可以，
   注意 C-c 只杀进程不杀 tmux 会话时才省事）。
8. **Card edit failed: StreamingUpdateRequest**：Xiaoxin 日志常见 WARNING，钉钉卡片流式更新
   失败（StreamingUpdateRequest NoneType），不影响消息收发，可忽略。

## 七、待办

- [ ] Workbuddy-Bot：钉钉建应用 → profile → 同流程接入
- [x] Mela 的 SOUL.md 从克隆的 Xiaoxin 人设改为 DEV 角色
- [x] WSL 自启脚本加入 gateway 拉起（当前 gateway 不在 start-webui.sh）
- [ ] 实测 bot 间 @ 是否生效（否则统一用唤醒词）
- [ ] 团队协议 @语法 从 Discord 版切换为钉钉版
