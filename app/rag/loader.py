from pathlib import Path
from .embed import embed_text

DOCS = []


def load_docs():
    DOCS.clear()
    for file in Path("app/rag/docs").glob("*.md"):
        content = file.read_text()
        title = file.stem.replace("_", " ").title()
        text = f"{title}\n{content}"
        DOCS.append({
            "title": title,
            "text": content.strip(),
            "embedding": embed_text(text),
        })
