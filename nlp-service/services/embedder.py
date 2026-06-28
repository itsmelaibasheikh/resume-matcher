"""
embedder.py

Wraps the sentence-transformers model. We load the model ONCE at startup
(it's loaded as a module-level singleton) because loading it on every
request would be slow and wasteful — this is a common pattern worth
mentioning in interviews: "model loaded once, reused across requests."

Model: all-mpnet-base-v2
- Larger (~420MB), slower than smaller alternatives, but noticeably more
  accurate at capturing semantic meaning — currently one of the strongest
  free general-purpose sentence embedding models available.
- Maps any sentence/phrase to a 768-dimension vector ("embedding").
- Phrases with similar MEANING end up with vectors that are close together,
  even if the exact words are different (e.g. "Jenkins" and "CI/CD pipeline").

Note: first run downloads the model (~420MB) — one-time, then cached locally.
"""

from sentence_transformers import SentenceTransformer
import numpy as np

# Loaded once when this module is first imported (i.e. at app startup).
_model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Convert a list of strings into a list of embedding vectors.
    """
    if not texts:
        return np.array([])
    return _model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)


def cosine_similarity_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Compute pairwise cosine similarity between two sets of embeddings.
    """
    if a.size == 0 or b.size == 0:
        return np.array([])
    return np.dot(a, b.T)