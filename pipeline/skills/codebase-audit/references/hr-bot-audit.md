# HR Bot Audit — Python FastAPI + DingTalk + ChromaDB RAG

## Project Pattern

Python FastAPI app with DingTalk Stream mode chatbot + RAG pipeline (ChromaDB + DeepSeek Chat API). Custom ONNX embedding (all-MiniLM-L6-v2 via onnxruntime) avoids PyTorch overhead.

## Key Issues Found

| Severity | Issue | Fix |
|----------|-------|-----|
| 🔴 Critical | API keys hardcoded as `os.getenv(..., "literal-secret")` fallback defaults | Removed defaults, added startup validation |
| 🔴 Critical | `sentence-transformers` in requirements.txt pulls PyTorch (contradicts ONNX-only design) | Removed from requirements |
| 🟠 High | ChromaDB collection + ONNX model recreated on every `ask()` call | Module-level singleton with `_collection` sentinel |
| 🟠 High | System prompt passed as `role: "user"` instead of `role: "system"` | Split into system + user messages |
| 🟡 Medium | Fixed 500-char window chunking cuts sentences mid-word | Switched to sentence-boundary-aware chunks (。！？\n) |
| 🟡 Medium | ONNX model loaded lazily on first request (10s delay) | Warm-up on module import |
| 🟢 Low | No `.env.example`, no `.gitignore`, no log rotation | Defer to deployment |

## Anti-Patterns Present

- **Silent swallowing** — `rag_engine.py` catches `except Exception` on DeepSeek API call and returns a canned string. User gets "API 调用异常" with no ability to debug. Could log the full traceback in a better place.
- **Misdirected dependency** — `sentence-transformers` listed as required but never used. Logs showed it downloading bge-m3 at runtime anyway (ChromaDB auto-downloads it). The ONNX embedding function was the intended path but wasn't wired correctly at first.
- **No graceful shutdown** — DingTalk stream WebSocket `start_forever()` runs in a daemon thread with no `stop()` call on shutdown.

## Lessons for Future Audits

1. Always check `os.getenv()` fallback defaults — hardcoded secrets are the #1 credential leak vector in Python projects.
2. Cross-reference `requirements.txt` against actual imports. Mismatched dependencies waste hours debugging unexpected behavior.
3. RAG systems commonly recreate the ChromaDB client on every query — this is a universal performance smell to watch for.
4. Sentence-boundary chunking is a drop-in improvement over fixed-window that significantly improves retrieval quality.
