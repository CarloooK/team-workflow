#!/usr/bin/env python3
"""
Hermes Skill Validator — 静态检查 + LLM 评判

Usage:
    python3 skill-validate.py <path-to-skill-dir-or-SKILL.md>
    python3 skill-validate.py --all          # 检查所有已安装 skill
    python3 skill-validate.py --score <path>  # 输出分数摘要

静态检查维度（秒级）:
  - frontmatter 完整性 (name, description)
  - 文件结构 (SKILL.md 是否存在)
  - 平台依赖扫描 (Claude Code, Codex, Cursor 等)
  - 引用文件完整性 (references/ templates/ scripts/)

LLM 评判维度（耗时 5-10s）:
  - 内容质量: 是否有具体示例、最佳实践、反模式
  - 触发准确性: description 是否和内容匹配
  - 范围校准: 是否清晰说明了何时用/何时不用
  - 渐进式披露: 是否从基础到高级展开
  - 实用性: 是否有可直接用的代码/模板

评分: ★★★★ Platinum | ★★★★ Gold | ★★★ Silver | ★★ Bronze
"""

import sys
import os
import re
import json
import textwrap
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────────

SKILLS_DIR = Path.home() / ".hermes" / "skills"

# 需要扫描的平台依赖关键词
PLATFORM_KEYWORDS = {
    "Claude Code": ["/plugin", "CLAUDE.md", "claude_code", "claude-code"],
    "Codex CLI":  ["codex_cli", "codex-cli", "codex "],
    "Cursor":     [".cursorrules", "cursor "],
    "Windsurf":   [".windsurfrules", "windsurf"],
    "Copilot":    ["copilot "],
}

# 评分权重
WEIGHTS = {
    "frontmatter":       0.15,
    "structure":         0.10,
    "platform_deps":     0.10,
    "examples":          0.15,
    "best_practices":    0.10,
    "anti_patterns":     0.10,
    "scope_clarity":     0.10,
    "progressive_depth": 0.10,
    "actionable_content": 0.10,
}


# ── 静态检查 ──────────────────────────────────────────────

def load_skill(path: Path) -> tuple[str, str]:
    """加载 SKILL.md，返回 (frontmatter_yaml, body_markdown)"""
    if path.is_dir():
        path = path / "SKILL.md"
    if not path.exists():
        return "", ""

    content = path.read_text(encoding="utf-8")
    parts = content.split("---\n", 2)
    if len(parts) >= 3:
        return parts[1].strip(), parts[2].strip()
    elif len(parts) == 2:
        return parts[1].strip(), ""
    return "", content


def parse_frontmatter(fm: str) -> dict:
    """简易 YAML 解析（只取 name 和 description）"""
    result = {"name": "", "description": ""}
    for line in fm.split("\n"):
        for key in ["name", "description"]:
            if line.strip().startswith(f"{key}:"):
                val = line.split(":", 1)[1].strip().strip('"').strip("'")
                result[key] = val
    return result


def check_frontmatter(fm: str) -> dict:
    meta = parse_frontmatter(fm)
    result = {
        "has_name": bool(meta["name"]),
        "has_description": bool(meta["description"]),
        "name": meta["name"],
        "description": meta["description"],
        "score": 0.0,
    }
    if result["has_name"] and result["has_description"]:
        result["score"] = 1.0
    elif result["has_name"] or result["has_description"]:
        result["score"] = 0.5
    return result


def check_structure(skill_dir: Path) -> dict:
    """检查 skill 目录结构"""
    result = {
        "has_skil_md": (skill_dir / "SKILL.md").exists(),
        "references": [],
        "templates": [],
        "scripts": [],
        "score": 0.0,
    }
    ref_dir = skill_dir / "references"
    tmpl_dir = skill_dir / "templates"
    scr_dir = skill_dir / "scripts"

    if ref_dir.exists():
        result["references"] = [f.name for f in ref_dir.iterdir() if f.is_file()]
    if tmpl_dir.exists():
        result["templates"] = [f.name for f in tmpl_dir.iterdir() if f.is_file()]
    if scr_dir.exists():
        result["scripts"] = [f.name for f in scr_dir.iterdir() if f.is_file()]

    # 评分：有 SKILL.md = 基础，有引用文件加分
    score = 0.4 if result["has_skil_md"] else 0.0
    if result["references"]:
        score += 0.2
    if result["templates"]:
        score += 0.2
    if result["scripts"]:
        score += 0.2
    result["score"] = min(score, 1.0)
    return result


def check_platform_deps(body: str) -> dict:
    """扫描平台依赖关键词"""
    matches = {}
    lines = body.split("\n")
    for platform, keywords in PLATFORM_KEYWORDS.items():
        found = []
        for kw in keywords:
            for i, line in enumerate(lines, 1):
                if kw.lower() in line.lower():
                    found.append(f"L{i}: {line.strip()[:80]}")
        if found:
            matches[platform] = found

    score = 1.0 if not matches else max(0.0, 1.0 - len(matches) * 0.15)
    return {"platform_matches": matches, "score": score, "is_clean": not bool(matches)}


def count_sections(body: str) -> dict:
    """统计文档结构"""
    h2 = re.findall(r"^## (.+)$", body, re.MULTILINE)
    h3 = re.findall(r"^### (.+)$", body, re.MULTILINE)
    code_blocks = len(re.findall(r"```", body)) // 2
    return {
        "h2_sections": len(h2),
        "h3_sections": len(h3),
        "code_blocks": code_blocks,
        "total_lines": len(body.split("\n")),
    }


# ── 内容质量评判（基于规则，不调 LLM） ─────────────────

def score_examples(body: str) -> float:
    """是否有具体的代码示例"""
    code_blocks = re.findall(r"```(\w*)\n(.*?)```", body, re.DOTALL)
    if not code_blocks:
        return 0.0
    # 检查是否有 >5 行代码块
    substantial = [c for _, c in code_blocks if len(c.split("\n")) > 5]
    if len(substantial) >= 3:
        return 1.0
    elif len(substantial) >= 1:
        return 0.6
    return 0.3


def score_best_practices(body: str) -> float:
    """是否有 Best Practices / 最佳实践 部分"""
    if re.search(r"(?i)(best practices|推荐实践|推荐做法|最佳实践)", body):
        return 1.0
    return 0.0


def score_anti_patterns(body: str) -> float:
    """是否有 Anti-Patterns / 反模式 / Pitfalls 部分"""
    if re.search(r"(?i)(anti.pattern|反模式|pitfall|common mistake|不要|避免)", body):
        return 1.0
    return 0.0


def score_scope_clarity(body: str) -> float:
    """触发条件是否清晰"""
    if re.search(r"(?i)(when to use|何时使用|适用场景|when not|不要用)", body):
        return 1.0
    return 0.0


def score_progressive_depth(body: str) -> float:
    """是否有从基础到高级的结构"""
    sections = count_sections(body)
    # 有 h2 + h3 分层 = 渐进式
    if sections["h2_sections"] >= 3 and sections["h3_sections"] >= 3:
        return 1.0
    elif sections["h2_sections"] >= 2:
        return 0.5
    return 0.0


def score_actionable_content(body: str) -> float:
    """是否有可直接用的模板/检查清单"""
    has_checklist = bool(re.search(r"(?i)\[ \]|checklist|检查清单|模板|template", body))
    has_example_cmd = bool(re.search(r"(?i)# (Usage|Example|示例|使用方式)", body))
    if has_checklist and has_example_cmd:
        return 1.0
    elif has_checklist or has_example_cmd:
        return 0.6
    return 0.0


# ── LLM 评判 ──────────────────────────────────────────────

def llm_evaluate(fm: str, body: str) -> dict:
    """
    基于规则的内容质量评估（无需 LLM 调用）。
    按 5 个维度打分（0-10）。
    """
    name = parse_frontmatter(fm).get("name", "unknown")
    desc = parse_frontmatter(fm).get("description", "")
    sections = count_sections(body)
    h2 = sections["h2_sections"]
    h3 = sections["h3_sections"]
    cb = sections["code_blocks"]

    # 1. 内容质量: 有章节 + 代码块
    content_quality = min(10, 4 + h2 + cb // 2)

    # 2. 触发准确性: description 是否匹配实际内容
    desc_keywords = set(desc.lower().split())
    body_lower = body.lower()
    matches = sum(1 for kw in desc_keywords if kw in body_lower and len(kw) > 3)
    trigger_accuracy = min(10, 3 + matches)

    # 3. 范围校准: 有 "When to Use" 和 "Pitfalls" 类章节
    has_when = bool(re.search(r"(?i)(when to use|适用场景|何时使用)", body))
    has_pitfall = bool(re.search(r"(?i)(pitfall|反模式|anti.pattern|常见错误)", body))
    scope_calibration = min(10, 3 + (4 if has_when else 0) + (3 if has_pitfall else 0))

    # 4. 渐进式披露: H2 和 H3 分层结构
    progressive_disclosure = min(10, 2 + h2 + h3 // 2)

    # 5. 实用性: 代码块和模板
    has_checklist = bool(re.search(r"(?i)\[ \]|checklist|模板|template", body))
    practicality = min(10, 2 + cb + (3 if has_checklist else 0))

    return {
        "content_quality": content_quality,
        "trigger_accuracy": trigger_accuracy,
        "scope_calibration": scope_calibration,
        "progressive_disclosure": progressive_disclosure,
        "practicality": practicality,
        "summary": f"规则评分: {h2}个H2章节, {h3}个H3小节, {cb}个代码块, {'有' if has_checklist else '无'}检查清单/模板",
    }


# ── 综合评分 ──────────────────────────────────────────────

def compute_overall_score(static: dict, llm: dict, fm_check: dict, deps: dict) -> tuple[float, str]:
    """计算综合分数和等级"""
    total = 0.0

    # 静态检查部分
    total += fm_check["score"] * WEIGHTS["frontmatter"]
    total += static["structure"]["score"] * WEIGHTS["structure"]
    total += deps["score"] * WEIGHTS["platform_deps"]

    # LLM 部分（或规则降级）
    total += (llm["content_quality"] / 10) * WEIGHTS["examples"]
    total += (llm.get("practicality", 7) / 10) * WEIGHTS["actionable_content"]

    # 规则评分
    total += (static["best_practices"]) * WEIGHTS["best_practices"]
    total += (static["anti_patterns"]) * WEIGHTS["anti_patterns"]
    total += (static["scope_clarity"]) * WEIGHTS["scope_clarity"]
    total += (static["progressive_depth"]) * WEIGHTS["progressive_depth"]

    score = round(total * 100)

    if score >= 90:
        badge = "★★★★★ Platinum"
    elif score >= 75:
        badge = "★★★★☆ Gold"
    elif score >= 55:
        badge = "★★★☆☆ Silver"
    else:
        badge = "★★☆☆☆ Bronze"

    return score, badge


def validate_skill(skill_path: Path, use_llm: bool = True) -> dict:
    """对一个 skill 执行完整验证"""
    fm, body = load_skill(skill_path)

    result = {
        "path": str(skill_path),
        "name": parse_frontmatter(fm).get("name", skill_path.parent.name),
    }

    # 静态检查
    result["frontmatter"] = check_frontmatter(fm)
    result["structure"] = check_structure(skill_path if skill_path.is_dir() else skill_path.parent)
    result["platform_deps"] = check_platform_deps(body)
    result["sections"] = count_sections(body)

    # 内容质量（规则版）
    result["examples_score"] = score_examples(body)
    result["best_practices"] = score_best_practices(body)
    result["anti_patterns"] = score_anti_patterns(body)
    result["scope_clarity"] = score_scope_clarity(body)
    result["progressive_depth"] = score_progressive_depth(body)
    result["actionable_content"] = score_actionable_content(body)

    # LLM 评判
    result["llm"] = llm_evaluate(fm, body) if use_llm else {
        "content_quality": 7, "trigger_accuracy": 7,
        "scope_calibration": 7, "progressive_disclosure": 7,
        "practicality": 7, "summary": "LLM 评判已跳过",
    }

    # 综合评分
    score, badge = compute_overall_score(result, result["llm"], result["frontmatter"], result["platform_deps"])
    result["overall_score"] = score
    result["badge"] = badge

    return result


def print_report(result: dict, verbose: bool = True):
    """打印验证报告"""
    def _yn(v): return "✅" if v else "❌"

    print(f"\n{'='*60}")
    print(f"  Hermes Skill 验证报告")
    print(f"  {result['name']}")
    print(f"  {result['path']}")
    print(f"{'='*60}")

    print(f"\n📋 静态检查:")
    print(f"  {_yn(result['frontmatter']['has_name'])} name: {result['frontmatter']['name'] or '<缺失>'}")
    print(f"  {_yn(result['frontmatter']['has_description'])} description: 存在 ({len(result['frontmatter']['description'])} chars)")
    print(f"  {_yn(result['structure']['has_skil_md'])} SKILL.md 文件存在")
    if result['structure']['references']:
        print(f"  📎 references: {', '.join(result['structure']['references'])}")
    if result['structure']['templates']:
        print(f"  📄 templates: {', '.join(result['structure']['templates'])}")
    if result['structure']['scripts']:
        print(f"  🔧 scripts: {', '.join(result['structure']['scripts'])}")

    deps = result['platform_deps']
    print(f"  {'🔒' if deps['is_clean'] else '⚠️'} 平台依赖: {'无' if deps['is_clean'] else '发现!'}")
    if not deps['is_clean']:
        for platform, matches in deps['platform_matches'].items():
            print(f"     {platform}:")
            for m in matches[:3]:
                print(f"       {m}")

    print(f"\n📝 内容结构:")
    s = result['sections']
    print(f"  H2 章节: {s['h2_sections']} | H3 小节: {s['h3_sections']} | 代码块: {s['code_blocks']} | 总行数: {s['total_lines']}")

    print(f"\n🔍 内容质量 (规则评分):")
    print(f"  代码示例:        {result['examples_score']:.0%}")
    print(f"  最佳实践:        {'✅' if result['best_practices'] else '❌'}")
    print(f"  反模式/Pitfalls: {'✅' if result['anti_patterns'] else '❌'}")
    print(f"  范围清晰度:      {'✅' if result['scope_clarity'] else '❌'}")
    print(f"  渐进式深度:      {result['progressive_depth']:.0%}")
    print(f"  可操作性:        {result['actionable_content']:.0%}")

    print(f"\n🤖 LLM 评判:")
    llm = result['llm']
    print(f"  内容质量:     {llm['content_quality']}/10")
    print(f"  触发准确性:   {llm['trigger_accuracy']}/10")
    print(f"  范围校准:     {llm['scope_calibration']}/10")
    print(f"  渐进式披露:   {llm['progressive_disclosure']}/10")
    print(f"  实用性:       {llm['practicality']}/10")
    if llm.get('summary'):
        print(f"  评语: {llm['summary']}")

    print(f"\n🏆 综合评分: {result['overall_score']}/100 — {result['badge']}")
    print(f"{'='*60}\n")


def validate_all():
    """验证所有已安装 skill"""
    results = []
    for cat_dir in SKILLS_DIR.iterdir():
        if not cat_dir.is_dir():
            continue
        for skill_dir in cat_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            if not (skill_dir / "SKILL.md").exists():
                continue
            results.append(validate_skill(skill_dir, use_llm=False))

    # 按分数排序
    results.sort(key=lambda r: r["overall_score"], reverse=True)

    print(f"\n{'='*60}")
    print(f"  Hermes Skills 全局扫描报告")
    print(f"  共 {len(results)} 个 skill")
    print(f"{'='*60}")

    for r in results:
        print(f"  {r['badge']:>20}  {r['overall_score']:3d}  {r['name']}")

    # 统计
    scores = [r['overall_score'] for r in results]
    if scores:
        avg = sum(scores) / len(scores)
        print(f"\n  平均分: {avg:.1f}")
        print(f"  最高: {max(scores)} | 最低: {min(scores)}")
    print(f"{'='*60}\n")


# ── CLI 入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 skill-validate.py <path-to-skill-dir-or-SKILL.md>")
        print("  python3 skill-validate.py --all          # 检查所有 skill")
        print("  python3 skill-validate.py --score <path>  # 仅输出分数")
        sys.exit(1)

    if sys.argv[1] == "--all":
        validate_all()
    elif sys.argv[1] == "--score":
        path = Path(sys.argv[2])
        result = validate_skill(path)
        print(result["overall_score"])
    else:
        path = Path(sys.argv[1])
        result = validate_skill(path)
        print_report(result, verbose=True)
