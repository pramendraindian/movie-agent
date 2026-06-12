## Plan: Non-Breaking Local-First RAG for Movie Agent

Add a parallel, feature-flagged RAG path that activates only on fallback/low-confidence and selected movie queries, while preserving the current intent + TF-IDF flow as the default. Use ChromaDB (persistent local vector store, Windows-friendly) + sentence-transformers all-MiniLM-L6-v2 embeddings + Ollama chat model (phi3:mini default, llama3.1:8b optional).

**Steps**
1. Phase 1 - Architecture Guardrails and Routing (blocks downstream)
1.1 Define RAG feature flags and safe defaults so existing behavior remains unchanged when flags are off.
1.2 Add explicit routing policy: current intent path remains primary; RAG is used only for low-confidence fallback and optional semantic movie augmentation.
1.3 Preserve response schema compatibility (`response`, `movies`) and keep formatting centralized in existing recommendation formatting.

2. Phase 2 - Data and Indexing Layer (depends on 1)
2.1 Introduce a vector indexing service that reads the same TMDB dataset already used by `MovieDataLoader` and builds persistent embeddings.
2.2 Use all-MiniLM-L6-v2 for embedding consistency with existing semantic components and low CPU cost.
2.3 Build a one-time + incremental indexing command/script (rebuild allowed, no runtime blocking on startup).
2.4 Store document metadata needed by UI rendering (title, genres, overview, poster path, rating, runtime, year) to avoid downstream object mismatches.

3. Phase 3 - Retrieval Service (depends on 2)
3.1 Add a retrieval abstraction with `retrieve(query, top_k)` and backend strategy enum (`chroma` now, future cloud backend later).
3.2 Implement deterministic retrieval + score thresholds (minimum similarity cutoff) to avoid noisy context.
3.3 Add timeout and exception fallbacks so retrieval failures automatically defer to current recommendation/fallback logic.

4. Phase 4 - LLM Generation Service (parallel with 3 after interface agreement)
4.1 Extend the LLM service from mock fallback to retrieval-aware generation without removing the existing fallback string path.
4.2 Use Ollama provider adapter with model configurable by env (`phi3:mini` for latency target, optional `llama3.1:8b` for better quality).
4.3 Enforce prompt templates for: concise answer, movie-grounded output, no hallucinated fields, and output shape compatible with API response expectations.
4.4 Add strict guard: if generation fails/timeouts, return existing fallback response.

5. Phase 5 - Non-Breaking Integration Points (depends on 3 and 4)
5.1 Integrate into `get_intent_response` only at the existing low-confidence/fallback branch first (safest insertion from architecture diagram).
5.2 Add optional semantic augmentation in movie recommendations: run retrieval first, then merge with existing TF-IDF/trending results under feature flag.
5.3 Keep current extraction and recommendation branches untouched as fallback-of-last-resort.
5.4 Add retrieval metadata tag in logs only (not API contract) for observability.

6. Phase 6 - Evaluation and Rollout (depends on 5)
6.1 Add offline evaluation set from existing intents/movie queries (fallback queries, ambiguous queries, mood/genre/runtime queries).
6.2 Compare baseline vs RAG on: relevance, latency, fallback rate, and malformed response rate.
6.3 Rollout strategy: `RAG_ENABLED=false` (baseline), then internal shadow mode, then selective enable for fallback only, then optional movie-path enable.

**Relevant files**
- `/app/services/intent_service.py` - primary safe routing hook at fallback/threshold branch.
- `/app/services/llm_service.py` - extend mock fallback into provider-based retrieval-aware generator.
- `/app/services/recommendation_service.py` - optional semantic augmentation while preserving existing TF-IDF branching.
- `/app/utils/movie_utils.py` - source dataset and movie metadata contract for indexing consistency.
- `/app/models/semantic_intent_model.py` - reusable semantic model pattern and embedding precedent.
- `/app/models/intent_classifier_factory.py` - strategy/factory pattern to mirror for retriever backend selection.
- `/app/api/routes.py` - verify no API contract changes at endpoint layer.
- `/requirements.txt` - add only minimal new dependencies for chosen stack.
- `/diagrams/ArchDiagram.png` - confirms intended fallback branch insertion point.

**Verification**
1. Run current tests unchanged first (`test_intent.py`, `test_recommendations.py`) to confirm baseline unaffected.
2. Add retrieval unit tests: index creation, retrieval top_k determinism, empty/no-match behavior, timeout fallback.
3. Add service integration tests: low-confidence intent triggers RAG path when enabled; disabled flag preserves original fallback text.
4. Add recommendation integration tests: semantic augmentation enabled/disabled without changing existing schema.
5. Run latency checks locally (Windows): p50 and p95 under <=1.5s for fallback RAG responses with `phi3:mini`.
6. Manual smoke via `/chat`: genre, runtime, ambiguous and out-of-domain prompts; verify response formatting and movie cards remain valid.

**Decisions**
- Chosen vector DB: ChromaDB (local persistent, simple Python integration, Windows-friendly).
- Chosen embedding model: all-MiniLM-L6-v2 (already aligned with current semantic stack).
- Chosen LLM mode: local open-source via Ollama; default `phi3:mini` for latency, optional `llama3.1:8b` for quality.
- Included scope: fallback-path RAG first, optional movie semantic augmentation second.
- Excluded scope (initial rollout): replacing intent classifier, removing TF-IDF recommender, changing API response schema.

**Further Considerations**
1. Future cloud migration path: keep retriever interface backend-agnostic to later support Pinecone/Qdrant without route/service rewrites.
2. Index freshness policy: define reindex trigger when dataset changes (startup hash check or explicit script).
3. Prompt safety: add lightweight response validator to prevent non-JSON/format drift when movie cards are expected.