# app/rag/retriever.py

import numpy as np
from .loader import DOCS
from .embed import embed_text


def retrieve(query: str, top_k: int = 3):
    if not DOCS:
        return []

    q_emb = embed_text(query)
    scores = []

    for doc in DOCS:
        score = float(np.dot(q_emb, doc["embedding"]))
        formatted = f"{doc['title']}: {doc['text']}"
        scores.append((score, formatted))

    scores.sort(reverse=True)
    return [text for _, text in scores[:top_k]]
