# rag.py
# The retrieval layer. This is what turns MannMitra from "guessing based on
# training data" into "answering only from real, verified LPU documents."

import os
import json
import chromadb

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
FACTS_PATH = os.path.join(KNOWLEDGE_DIR, "facts.json")

_client = chromadb.PersistentClient(path=CHROMA_DIR)
_collection = _client.get_or_create_collection(name="lpu_knowledge")

# Words that suggest the message is actually asking for information, not just
# chatting. Used to decide whether the (slower) semantic search is worth running.
INFO_SIGNAL_WORDS = [
    "where", "when", "how do i", "how can i", "what is the", "contact",
    "office", "block", "hostel", "deadline", "fee", "counsel", "wellbeing",
    "dsr", "location", "number", "email", "policy", "schedule", "exam date",
]

CASUAL_MESSAGES = {
    "hi", "hii", "hiii", "hello", "hey", "heya", "yo",
    "how are you", "good morning", "good night", "good afternoon",
    "thanks", "thank you", "ok", "okay", "bye", "goodbye", "cool", "nice",
}


def _load_facts():
    with open(FACTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _needs_semantic_search(query: str) -> bool:
    """Skip the (comparatively slow) embedding + vector search step for
    obvious small talk. This is the main fix for slow replies to 'hello'."""
    q = query.strip().lower()
    if q in CASUAL_MESSAGES:
        return False
    if len(q.split()) <= 2 and "?" not in q:
        return False
    if "?" in q:
        return True
    return any(word in q for word in INFO_SIGNAL_WORDS)


def search_facts(query: str) -> list[dict]:
    """Exact-match style lookup - cheap, always safe to run on every message."""
    query_lower = query.lower()
    facts = _load_facts()
    matches = []
    for fact in facts:
        for keyword in fact["keywords"]:
            if keyword in query_lower:
                matches.append(fact)
                break
    return matches


def retrieve_chunks(query: str, k: int = 3) -> list[dict]:
    """Semantic search over the document collection. Only call this when
    _needs_semantic_search says it's worth the extra time."""
    if _collection.count() == 0:
        return []
    results = _collection.query(query_texts=[query], n_results=min(k, _collection.count()))
    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({"text": doc, "source": meta.get("source", "unknown")})
    return chunks


def get_grounded_context(query: str) -> dict:
    """Main entry point main.py calls."""
    facts = search_facts(query)

    chunks = []
    if _needs_semantic_search(query):
        chunks = retrieve_chunks(query, k=3)

    if not facts and not chunks:
        return {"found": False, "context_text": ""}

    parts = []
    if facts:
        parts.append("VERIFIED STRUCTURED RECORDS:")
        for f in facts:
            parts.append(f"- {f['topic']}: {f['answer']} (source: {f['source']})")

    if chunks:
        parts.append("\nRELEVANT DOCUMENT EXCERPTS:")
        for c in chunks:
            parts.append(f"- ({c['source']}) {c['text']}")

    return {"found": True, "context_text": "\n".join(parts)}
