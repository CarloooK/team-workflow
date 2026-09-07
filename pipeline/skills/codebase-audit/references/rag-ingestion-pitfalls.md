# RAG Ingestion — Common Pitfalls

Session-specific findings from auditing and fixing an HR bot RAG pipeline
(ChromaDB + ONNX MiniLM + DeepSeek Chat API).

## ChromaDB Duplicate IDs from Multi-Page PDFs

**Symptom:** `chromadb.errors.DuplicateIDError: Expected IDs to be unique, found duplicates of: file_chunk_0, file_chunk_1`

**Root cause:** When a PDF has multiple pages and each page calls `chunk_text()` independently, `chunk_index` resets to 0 for every page. ChromaDB batch-add rejects the duplicate `source_chunk_0` / `source_chunk_1` IDs.

**Fix:** Pass `idx_start` across pages to make chunk indices globally unique:

```python
chunks = []
next_idx = 0
for page_data in pages:
    page_chunks = chunk_text(page_data["text"], page_data["page"], source, idx_start=next_idx)
    chunks.extend(page_chunks)
    next_idx += len(page_chunks)
```

Where `chunk_text` accepts an `idx_start` parameter instead of hardcoding `idx = 0`.

## sentence-transformers in requirements when ONNX is used

**Symptom:** Project uses onnxruntime + MiniLM-L6-v2 for zero-PyTorch embeddings, but `requirements.txt` lists `sentence-transformers` which pulls in PyTorch (~800MB). First request triggers downloading bge-m3 model.

**Fix:** Remove `sentence-transformers` from requirements. If ONNX embedding is the actual path, don't keep the PyTorch route as a dead dependency.

## pyngrok vs system ngrok CLI

**Symptom:** `pyngrok` Python package in requirements.txt but no Python code imports it. The actual ngrok usage is via the system `ngrok` binary in a shell script (`ngrok http 8000 &`).

**Fix:** Remove `pyngrok` from requirements. Use system ngrok binary directly. Load auth token from `.env` in the shell script if needed.

## Chunk Boundary Quality

Fixed-window chunking (500 chars with 50 overlap) cuts mid-sentence. Better: scan forward from the raw cutoff for sentence-ending punctuation (。！？\n) and adjust the boundary. Fall back to the last sentence end within the chunk if none found ahead.

This avoids broken retrieval contexts where a chunk starts/ends mid-word.

## ONNX Embedding Initialization on First Call

Creating the ChromaDB client + ONNX InferenceSession on every `retrieve()` call is expensive (~500ms). Cache the collection as a module-level singleton. Warm up on module import so the first user request is fast.
