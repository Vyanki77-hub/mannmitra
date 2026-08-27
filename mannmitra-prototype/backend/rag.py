# rag.py
# The retrieval layer. This is what turns MannMitra from "guessing based on
# training data" into "answering only from real, verified LPU documents."
#
# Two retrieval paths, matching your mentor's advice:
#   1. Structured facts (facts.json) - exact keyword lookup for hard facts like
#      block numbers, contact info, deadlines. These should never be left to
#      probabilistic semantic search.
#   2. Semantic search (Chroma) - for open-ended policy/FAQ questions where the
#      wording won't match exactly, so meaning-based search is more useful.

import os
import json
import chromadb

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
FACTS_PATH = os.path.join(KNOWLEDGE_DIR, "facts.json")

_client = chromadb.PersistentClient(path=CHROMA_DIR)
_collection = _client.get_or_create_collection(name="lpu_knowledge")


def _load_facts():
    with open(FACTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def search_facts(query: str) -> list[dict]:
    """Exact-match style lookup: does the query contain any keyword from a
    structured fact entry? This handles the 'hard facts' category your
    mentor flagged (block numbers, contacts, deadlines)."""
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
    """Semantic search over the document collection for open-ended questions."""
    if _collection.count() == 0:
        return []
    results = _collection.query(query_texts=[query], n_results=min(k, _collection.count()))
    chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({"text": doc, "source": meta.get("source", "unknown")})
    return chunks


def get_grounded_context(query: str) -> dict:
    """The main function main.py calls. Combines structured facts and semantic
    chunks into one context block, and tells the caller whether anything
    relevant was actually found (so the model can be told to say 'I don't
    have verified info' instead of guessing when nothing matches)."""
    facts = search_facts(query)
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
