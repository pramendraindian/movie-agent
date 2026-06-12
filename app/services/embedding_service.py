from sentence_transformers import SentenceTransformer


_EMBEDDER = None


def get_embedder() -> SentenceTransformer:
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
    return _EMBEDDER


def embed_texts(texts):
    model = get_embedder()
    return model.encode(texts, normalize_embeddings=True).tolist()
