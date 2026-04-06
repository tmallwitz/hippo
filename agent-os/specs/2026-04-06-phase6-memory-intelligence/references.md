# References for Phase 6: Memory Intelligence

## Lazy model loading pattern

- **Location**: `hippo/voice.py` (lines 17-30)
- **Relevance**: The `_loaded_model` singleton and lazy-import pattern to follow
  for the SentenceTransformer model in `embeddings.py`

## Current search_nodes (to be enhanced)

- **Location**: `hippo/memory/semantic.py:359` — `_search_nodes_sync`
- **Relevance**: The substring logic to replace/augment with cosine similarity
- **Key pattern**: loads all entities via `_load_all()`, filters, returns `KnowledgeGraph`

## create_entities (update trigger)

- **Location**: `hippo/memory/semantic.py:205` — `_create_entities_sync`
- **Relevance**: Where to hook in `update_entity_embeddings()` after creation

## Dream orchestration

- **Location**: `hippo/dream/runner.py:189` — `run_dream()`
- **Relevance**: Where to add episodic summarization step and embedding rebuild

## MCP tool registration

- **Location**: `hippo/memory/server.py:486` — `create_dream_server()`
- **Relevance**: Where to add `find_similar_entities` as a dream-only tool

## Store factory wiring

- **Location**: `hippo/memory/server.py:444` — `create_memory_server()`
- **Relevance**: Pattern for threading config through to stores

## asyncio.Lock + asyncio.to_thread pattern

- **Location**: `hippo/memory/semantic.py:192-213` — `ObsidianSemanticStore`
- **Relevance**: All blocking ops run in thread pool under `self._lock`
