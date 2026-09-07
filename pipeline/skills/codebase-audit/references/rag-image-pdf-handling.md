# Handling Image-Only / Screenshot PDFs in RAG Pipelines

## The Problem

Some PDFs contain no extractable text — they are composed entirely of screenshots (step-by-step UI guides, scanned documents, etc.). `pypdf.extract_text()` returns < 80 characters per page (just button labels and section headers), which is too sparse for meaningful vector embedding and retrieval.

Attempting OCR (tesseract) on these PDFs is possible but:
- **Slow** — tesseract takes ~5-30s per page depending on complexity
- **Heavy dependencies** — requires tesseract-ocr + chi_sim language pack + poppler-utils
- **Low marginal value** — even OCR output is noisy and may not significantly improve retrieval

## A Pragmatic Alternative: Topic Registration Fallback

Instead of OCR, use a lightweight two-tier approach:

### Tier 1: Vector Search (normal PDFs)
pypdf-extracted text → chunk → ChromaDB embedding. Works well for text-rich PDFs.

### Tier 2: Topic Registry (image-only PDFs)
Short page headers → JSON registry → keyword matching → user redirection.

**Detection:** Compute `avg_chars = total_chars / page_count` after pypdf extraction. If `avg_chars < 80`, classify as image-only.

**Registration:** Save page titles/headers (what little text pypdf got) into a JSON file alongside the document metadata.

**Matching:** When a user query doesn't get useful results from vector search, check the topic registry for keyword overlap. If found, inject a hint into the LLM prompt:

```
💡 您的问题涉及 **《document.pdf》** 的内容。
该文档为操作截图指南，详细步骤请直接查阅该 PDF 文件，
或咨询 HR/IT 部门获取具体操作指引。
```

### Chinese Keyword Matching with Bigrams

For Chinese text, single-character matching is too noisy and whole-phrase matching is too strict. Use **character bigrams** (2-grams):

```python
def tokenize(text: str) -> set:
    words = set()
    # Extract Chinese bigrams
    for seq in re.findall(r'[\u4e00-\u9fff]{2,}', text):
        for i in range(len(seq) - 1):
            words.add(seq[i:i+2])
    # English words (3+ chars)
    for seg in re.findall(r'[a-zA-Z]{3,}', text):
        words.add(seg.lower())
    return words
```

Example: "滴滴打车怎么用" → `{滴打, 滴滴, 打车, 车怎, 怎么, 么用}`
A page titled "差旅预定—滴滴" → `{差旅, 旅预, 预定, 滴滴}`
Overlap: `{滴滴}` — 1 bigram match → trigger hint.

Set threshold to **1 bigram** for image-only PDF hints (the hint is a soft suggestion to check the document, not a factual claim — false positive risk is low).

## Implementation Structure

```
project/
├── topic_registry.py      # Registry module: register, match, cleanup
│   ├── register_pdf()     # Called by ingest pipeline for image-only PDFs
│   ├── match_topic()      # Called by RAG engine before LLM call
│   └── remove_unregistered()  # Clean up deleted files from registry
└── db/
    └── topic_registry.json    # Persistent JSON storage
```

### Ingest Integration

In `process_file()`, after extracting pages with pypdf:

```python
avg_chars = sum(len(p["text"]) for p in pages) / len(pages)
if avg_chars < 80:
    register_pdf(source_name, pages, avg_chars)
    return 0  # Skip ChromaDB indexing
```

### RAG Integration

In `ask()`, before building the LLM payload:

```python
topic_hint = match_topic(question)
hint_prefix = (topic_hint["hint"] + "\n\n") if topic_hint else ""

payload = {
    "messages": [
        {"role": "system", ...},
        {"role": "user", "content": f"...{hint_prefix}员工问：{question}"},
    ]
}
```

## Tradeoffs vs OCR

| Approach | Speed | Dependencies | Quality |
|----------|-------|-------------|---------|
| OCR (tesseract) | 5-30s/page | tesseract, poppler, chi_sim lang pack | Noisy, may not help retrieval |
| Topic Registry | ~0.01s | None | Only redirects, no direct answers |

The topic registry approach is **orders of magnitude faster** and avoids dependency bloat. The tradeoff is that it can't answer the question directly — it redirects the user to the original document.

**Best for:** Internal operational PDFs (screenshot walkthroughs, UI guides) where the user can reasonably access and read the original document.

**Not suitable for:** External-facing bots, accessibility requirements, or cases where users can't access the original PDF.
