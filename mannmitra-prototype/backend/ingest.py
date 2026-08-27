# ingest.py
# Run this once (and again any time you update the files in knowledge/) to load
# your documents into the vector database. This is Phases D, E, F from your
# mentor's roadmap: chunk, embed, store.
#
# Usage:
#   python ingest.py

import os
import glob
import chromadb

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")


def chunk_text(text: str, source: str) -> list[dict]:
    """Splits a document into chunks by paragraph (blank-line separated).
    Simple and effective for FAQ-style documents. Skips empty chunks and
    the placeholder instruction line at the top of each file."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    for p in paragraphs:
        if p.startswith("PLACEHOLDER CONTENT"):
            continue
        chunks.append({"text": p, "source": source})
    return chunks


def main():
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Start fresh each time you re-ingest, so stale chunks don't linger
    try:
        client.delete_collection("lpu_knowledge")
    except Exception:
        pass
    collection = client.create_collection(name="lpu_knowledge")

    txt_files = glob.glob(os.path.join(KNOWLEDGE_DIR, "*.txt"))

    all_chunks = []
    for filepath in txt_files:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        all_chunks.extend(chunk_text(text, source=filename))

    if not all_chunks:
        print("No chunks found. Add .txt files to backend/knowledge/ first.")
        return

    collection.add(
        documents=[c["text"] for c in all_chunks],
        metadatas=[{"source": c["source"]} for c in all_chunks],
        ids=[f"chunk-{i}" for i in range(len(all_chunks))],
    )

    print(f"Ingested {len(all_chunks)} chunks from {len(txt_files)} file(s) into Chroma.")
    print("You can now run your backend normally - RAG retrieval is live.")


if __name__ == "__main__":
    main()
