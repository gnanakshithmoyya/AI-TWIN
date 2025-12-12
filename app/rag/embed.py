from ollama import embeddings

def embed_text(text: str):
    return embeddings(
        model="nomic-embed-text",
        prompt=text
    )["embedding"]