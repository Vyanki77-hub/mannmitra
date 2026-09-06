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
# Only explicit institutional / informational signals should trigger RAG.
INFO_SIGNAL_WORDS = [
    "where", "when", "how do i", "how can i", "what is the", "contact",
    "office", "block", "hostel", "deadline", "fee", "counsel", "wellbeing",
    "dsr", "location", "number", "email", "policy", "schedule", "exam date",
    "support", "talk to", "who to talk",
]

CASUAL_MESSAGES = {
    "hi", "hii", "hiii", "hello", "hey", "heya", "yo",
    "how are you", "good morning", "good night", "good afternoon",
    "thanks", "thank you", "ok", "okay", "bye", "goodbye", "cool", "nice",
    "i'm bored", "im bored", "tell me something interesting",
}


def _load_facts():
    with open(FACTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _needs_semantic_search(query: str) -> bool:
    """Decide whether semantic (vector) search is worthwhile.

    RAG should only fire for explicit informational / institutional questions.
    A bare '?' without an INFO_SIGNAL_WORD must NOT trigger RAG - otherwise
    normal emotional messages like "Why am I so sad?" pull in counselling
    chunks unnecessarily.
    """
    q = query.strip().lower()
    if q in CASUAL_MESSAGES:
        return False
    if len(q.split()) <= 2 and "?" not in q:
        return False
    has_info_signal = any(word in q for word in INFO_SIGNAL_WORDS)
    if "?" in q:
        return has_info_signal
    return has_info_signal


def search_facts(query: str) -> list[dict]:
    """Exact-match style lookup - only returns facts when the query looks like
    an explicit informational request (contains an INFO_SIGNAL_WORD). This
    prevents normal emotional statements like 'I feel low' from accidentally
    pulling in DSR / counselling contact records via a stray keyword."""
    query_lower = query.lower()
    # Normal emotional / casual messages should not trigger structured facts.
    has_info_signal = any(word in query_lower for word in INFO_SIGNAL_WORDS)
    # Also treat an explicit '?' combined with a fact keyword as informational,
    # but a bare emotional '?' (e.g. "Why am I so sad?") must NOT trigger facts.
    if not has_info_signal:
        return []
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
