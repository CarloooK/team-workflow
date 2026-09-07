# AI → 纯规则引擎迁移指南 (Node.js)

当项目从依赖外部 AI CLI（如 OpenClaw `infer model run`）迁移到纯规则/正则引擎时，按此 checklist 操作。

## 触发场景

- 项目从 Hermes/Claude Code 切换过来，不再需要 OpenClaw
- 外部 AI CLI 在目标环境不存在或不可用
- 测试因 spawnSync 外部 AI 进程而卡死
- 简化部署（移除外部 AI 依赖）

## 迁移步骤

### Step 1: 识别所有 AI 调用点

```bash
# 在 src/ 中搜索所有 AI 相关调用
grep -rn "spawnSync.*openclaw\|infer.*model\|OPENCLAW_BIN\|analyzeIntentWithAI" src/ --include="*.js"
grep -rn "spawnSync.*infer\|openclaw" src/ --include="*.js"
```

典型模式：
- `src/core/intent-analyzer.js` — 核心意图分析模块，含 AI + regex fallback
- `src/email/refresh.js` — 收到新回复时调用 AI 分析
- `src/email/generator.js` — 可能含死代码（OPENCLAW_BIN 声明 + buildAIPrompt）

### Step 2: 评估哪些 AI 调用可被纯规则替代

适合纯规则替代的场景：
- **意图分析/分类**（高/中/低意愿）→ 正则关键词匹配
- **情感分析** → 关键词评分
- **模板填充/生成** → 仅模板字符串替换（如项目实际用的是模板+placeholder，不是 AI 生成）

不适合纯规则替代的场景：
- 需要理解上下文语义（复杂回复解析）
- 自由文本翻译
- 内容摘要生成

### Step 3: 替换核心模块

1. 从核心模块（如 `intent-analyzer.js`）删除 `analyzeIntentWithAI()`、`mapAIIntentToLevel()` 等函数
2. 修改 `sortByIntent()` 等函数，去掉 `config` 参数（仅用于 AI prompt）
3. 更新 `module.exports`，只导出纯逻辑函数

### Step 4: 更新所有调用方

```bash
# 搜索所有 import/require
grep -rn "require.*intent-analyzer\|require.*analyzeIntentWithAI" src/ --include="*.js"
```

典型修改：
- `refresh.js`: `const { analyzeIntent, analyzeIntentWithAI } = require(...)` → `const { analyzeIntent } = require(...)`
- 去掉 `analyzeIntentWithAI()` 调用分支，只保留纯 `analyzeIntent()`

### Step 5: 清理死代码

```bash
# 在 genrator/其他模块中搜索
grep -rn "OPENCLAW_BIN\|spawnSync\|buildAIPrompt" src/ --include="*.js"
```

删除：
- `require('child_process')` 如果不再需要 spawnSync
- `OPENCLAW_BIN` 声明
- `buildAIPrompt()` 函数及其 export
- 任何不再使用的 AI prompt 模板字符串

### Step 6: 拆分 CLI 入口（可选）

如果核心模块同时包含纯函数和 CLI runner：

1. 核心模块 → 只保留纯函数（可测试、无 I/O）
2. `src/cli/<name>.js` → 新 CLI 入口，通过 config.js 加载多租户配置
3. 更新 `run.sh` 等包装脚本指向新 CLI

### Step 7: 更新测试

1. 删除或替换 AI 相关测试用例
2. 新增边界测试（空输入、无 last_reply、多语言混杂文本等）
3. 移除 mock AI 的需要
4. 确认测试不再卡死（`--timeout 5000` 应快速完成）

### Step 8: 验证

```bash
npm test                         # 全部通过
node src/cli/intent.js           # 新 CLI 正常工作
```

## 常见的陷阱

### 1. 测试卡死在 spawnSync
AI 模块中 `spawnSync('openclaw', ['infer', 'model', 'run', ...])` 在无 OpenClaw 环境会 hang。`--timeout` 参数传给 spawnSync 也不一定能生效（有些命令会忽略）。**修复方案：直接删除 AI 路径，不要加 mock 或 --no-ai 标志。**

### 2. 残留的内联字典
Phase 2（共享数据提取）后，检查是否仍有文件内联定义了应从 `shared/` 导入的字典：
```bash
grep -n "COUNTRY_CONTINENT\|COUNTRY_MAP" src/io/excel-reader.js
```

### 3. 过时的注释
重构后 `src/` 文件注释仍写着 `node scripts/xxx.js`。批量替换：
```bash
grep -rn "node scripts/" src/ --include="*.js"
```

### 4. 导出接口不一致
移除 AI 函数后，其他文件的 `require()` 会因符号不存在而报错。每次都 grep 确认所有引用点。
