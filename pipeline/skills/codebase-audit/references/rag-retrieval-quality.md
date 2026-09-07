# RAG Retrieval Quality: Common Pitfalls and Fixes

Real-world patterns from auditing and fixing a ChromaDB + MiniLM-L6-v2 + DeepSeek RAG system (HR FAQ bot).

## 1. Fixed-Window Chunking Infinite Loop

```python
# BUG: infinite loop when end >= len(text)
start = 0
while start < len(text):
    end = min(start + CHUNK_SIZE, len(text))
    chunks.append(text[start:end])
    start = end - CHUNK_OVERLAP  # when end==len, start < len again → loop
```

**Fix:** Break when `end >= len(text)` after appending.

```python
while start < len(text):
    end = min(start + CHUNK_SIZE, len(text))
    chunks.append(text[start:end])
    if end >= len(text):
        break
    start = end - CHUNK_OVERLAP
```

**Trigger:** Always present when `CHUNK_OVERLAP > 0`. The final iteration sets `start = len - overlap`, which is always < `len`, creating an infinite loop.

## 2. Full-Text Concatenation Before Chunking

**Problem:** Per-page independent chunking breaks chapter/section continuity. A section titled "3.薪酬福利" on page 4 gets cut into isolation, losing context.

**Fix:** Concatenate all pages into one `full_text` (with `\n` separators for page boundaries), then chunk the full text, then map chunk positions back to original page numbers.

```python
# Build full text + page offset map
full_text = ""
page_map = []  # (char_start, char_end, page_number)
for p in pages:
    start = len(full_text)
    if full_text:
        full_text += "\n"
        start = len(full_text)
    full_text += p["text"]
    page_map.append((start, len(full_text), p["page"]))

# Chunk the full text
chunks = chunk_text(full_text, page=0, source=source_name)

# Map each chunk back to its page
for c in chunks:
    idx = full_text.find(c["text"])
    if idx >= 0:
        for ps, pe, pn in page_map:
            if ps <= idx < pe:
                c["metadata"]["page"] = pn
                break
```

## 3. Multi-Source Round-Robin Retrieval

**Problem:** When one document dominates the index (e.g., employee handbook: 102 chunks vs FAQ: 25 chunks), ChromaDB's top-K is flooded by the dominant document even for questions about other docs.

**Fix:** Query more (`top_k * 3`), group by source with per-source caps, then round-robin to fill final `top_k`.

```python
n_query = min(top_k * 3, collection.count())
results = collection.query(query_texts=[query], n_results=n_query)

# Cap per source
per_source = {}
for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    source = meta["source"]
    if source not in per_source:
        per_source[source] = []
    if len(per_source[source]) < 3:  # max 3 per source
        per_source[source].append((doc, meta))

# Round-robin pick
context_parts = []
idx = 0
while len(context_parts) < top_k:
    remaining = [s for s in per_source if idx < len(per_source[s])]
    if not remaining:
        break
    for source in remaining:
        doc, meta = per_source[source][idx]
        context_parts.append(f"...")
        idx += 1
```

## 4. Query Expansion for Weak Embedding Models

**Problem:** MiniLM-L6-v2 (384-dim) has poor semantic coverage. "公司福利" may not match chunks containing "饭贴", "精微币", "五险一金" — even though they're the same topic.

**Fix:** Keyword expansion table. Match known topic keywords in the query and append related terms.

```python
_QUERY_EXPANSIONS = {
    "福利": "福利 饭贴 精微币 补贴 薪资 年假 五险一金 社保",
    "年假": "年假 带薪年休假 休假 假期",
    "差旅": "差旅 出差 机票 酒店 交通",
    # ...
}

def _expand_query(query: str) -> str:
    for keyword, expansion in _QUERY_EXPANSIONS.items():
        if keyword in query:
            return f"{query} {expansion}"
    return query
```

**Cost:** Near-zero (string lookup), works immediately without model swap.

## 5. TOP_K Tuning

With multi-source round-robin retrieval, each source gets fewer slots. `TOP_K = 5` may yield only 1-2 chunks per source, not enough context for the LLM. Increase proportionally:

- Single document → `TOP_K = 5`
- 2-3 documents → `TOP_K = 9`
- 4+ documents → `TOP_K = 15`

The extra chunks add token cost but prevent "not enough context" failures.

## 6. Image-Only / Screenshot PDF Handling

See `rag-image-pdf-handling.md` for the topic-registry approach (avoid OCR, match via Chinese bigram keywords, hint user to read the original PDF).
