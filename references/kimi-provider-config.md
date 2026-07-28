# Kimi / Moonshot Provider Configuration

Kimi (Moonshot) 在 Hermes 中提供两个 provider，base URL 不同，模型名必须精确匹配 API 返回。

## 两个 Provider

| Provider | Env Var | Base URL | 说明 |
|----------|---------|----------|------|
| `kimi-coding` | `KIMI_API_KEY` | `https://api.moonshot.ai/v1` | 国际版 |
| `kimi-coding-cn` | `KIMI_CN_API_KEY` | `https://api.moonshot.cn/v1` | 中国版 |

**中国大陆用户须用 `kimi-coding-cn`**，否则 API 走 `api.moonshot.ai` 会 401。

## 环境变量

```bash
# ~/.hermes/.env
KIMI_CN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 可用模型

通过 API 查询（不用猜）：

```bash
curl -s https://api.moonshot.cn/v1/models \
  -H "Authorization: Bearer $KIMI_CN_API_KEY" | jq -r '.data[].id'
```

当前可用（2026-07）：
- `kimi-k2.7-code`
- `kimi-k2.7-code-highspeed`
- `kimi-k3`
- `kimi-k2.6`
- `kimi-k2.5`

## 切换模型

```bash
# 命令行
hermes chat -m kimi-k2.7-code --provider kimi-coding-cn

# 设为默认
hermes config set model.default kimi-k2.7-code
hermes config set model.provider kimi-coding-cn

# 添加为 fallback（deepseek 挂了自动切）
hermes config set fallback_providers '[{"provider":"kimi-coding-cn","model":"kimi-k2.7-code"}]'
```

## 踩坑记录

### 1. 模型名必须精确

`kimi-k2-code` ❌ — 不存在。API 实际模型名是 `kimi-k2.7-code`。

### 2. 不要覆盖 base_url

```bash
# ❌ 错误：覆盖 base_url 会将 provider 变为 custom，无法解析 KIMI_API_KEY
hermes config set providers.kimi.base_url https://api.moonshot.cn/v1
```

直接使用正确的 provider（`kimi-coding-cn`），它内置了正确的 base_url。

### 3. 401 后必须 reset auth

Hermes 的 credential pool 在 401 后会标记 key 为 "auth failed" 并停止重试。
即使修复了配置，也需重置：

```bash
hermes auth list                          # 确认哪个 provider 的 key 被标记
hermes auth reset kimi-coding-cn          # 重置标记
```

### 4. 直连 curl 成功 ≠ Hermes 能用

如果 `curl https://api.moonshot.cn/v1/models` 返回 200 但 Hermes 报 401：
- 先确认 provider 是 `kimi-coding-cn`（不是 `kimi` 或 `kimi-coding`）
- 再 `hermes auth reset kimi-coding-cn`
- 用 `-v` 看实际请求的 base_url 和 provider
