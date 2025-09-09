from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import json
import os
import re
import difflib
from typing import Dict, List, Tuple

app = FastAPI()

class SearchQuery(BaseModel):
    query: str

# Load static synthetic corpus
CORPUS_PATH = os.path.join(os.path.dirname(__file__), "nth_corpus.json")
with open(CORPUS_PATH, "r") as f:
    mock_db: Dict[str, List[dict]] = json.load(f)

# Build a lightweight inverted index and alias map for better lookup
WORD_RE = re.compile(r"[a-z0-9]+")

def tokenize(text: str) -> List[str]:
    return [t for t in WORD_RE.findall(text.lower()) if len(t) >= 3]

# Alias phrases mapped to known keys (helps common natural queries)
alias_map = {
    "2024 annual report": "topic_001",
    "annual report": "topic_001",
    "project phoenix": "topic_069",
}

# Precompute per-key tokens and metadata tokens
key_tokens: Dict[str, List[str]] = {}
content_tokens: Dict[str, List[str]] = {}
meta_tokens: Dict[str, List[str]] = {}
meta_year: Dict[str, int] = {}

for key, docs in mock_db.items():
    key_tokens[key] = tokenize(key)
    # For each associated doc (typically one), aggregate tokens
    ctoks: List[str] = []
    mtoks: List[str] = []
    year_val = None
    for d in docs:
        ctoks.extend(tokenize(d.get("content", "")))
        md = d.get("metadata", {}) or {}
        # Include common metadata fields
        for mv in md.values():
            if isinstance(mv, str):
                mtoks.extend(tokenize(mv))
            elif isinstance(mv, list):
                for item in mv:
                    if isinstance(item, str):
                        mtoks.extend(tokenize(item))
            elif isinstance(mv, int):
                # capture year if present
                year_val = mv if (1900 <= mv <= 2100) else year_val
    content_tokens[key] = ctoks
    meta_tokens[key] = mtoks
    if year_val is not None:
        meta_year[key] = year_val


def score_key(query_text: str, query_tokens: List[str], key: str) -> float:
    # Token overlap scores
    s = 0.0
    kt = key_tokens.get(key, [])
    ct = content_tokens.get(key, [])
    mt = meta_tokens.get(key, [])

    # weights
    w_key = 2.0
    w_content = 3.0
    w_meta = 1.5

    # Count overlaps
    s += w_key * sum(1 for t in query_tokens if t in kt)
    s += w_content * sum(1 for t in query_tokens if t in ct)
    s += w_meta * sum(1 for t in query_tokens if t in mt)

    # Year bonus if query mentions a 4-digit year equal to metadata year
    y_match = re.search(r"(19|20)\d{2}", query_text)
    if y_match and key in meta_year and int(y_match.group(0)) == meta_year[key]:
        s += 4.0

    # Fuzzy similarity between query and key/content for weak matches
    sim_key = difflib.SequenceMatcher(None, query_text, key.lower()).ratio()
    s += 2.0 * sim_key

    # Add mild fuzzy boost against the first doc content (short corpus)
    doc = mock_db[key][0]
    content = doc.get("content", "").lower()[:400]
    if content:
        sim_content = difflib.SequenceMatcher(None, query_text, content).ratio()
        s += 1.0 * sim_content

    return s


@app.post("/search")
def search_nth_database(search_query: SearchQuery):
    query_text = search_query.query.strip().lower()

    # Alias exact/substring hit shortcut
    for alias, mapped_key in alias_map.items():
        if alias in query_text and mapped_key in mock_db:
            return {"status": "success", "results": mock_db[mapped_key]}

    # Tokenize and score across the corpus
    q_tokens = tokenize(query_text)
    scored: List[Tuple[str, float]] = []
    for key in mock_db.keys():
        sc = score_key(query_text, q_tokens, key)
        if sc > 0:
            scored.append((key, sc))

    if not scored:
        return {"status": "not_found", "results": []}

    # Sort by score desc and return top 5 results (flatten the docs)
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:5]
    results = []
    for key, sc in top:
        for d in mock_db[key]:
            item = dict(d)
            item["relevance"] = round(sc, 3)
            item["match_key"] = key
            results.append(item)

    return {"status": "success", "results": results}


if __name__ == "__main__":
    host = os.getenv("NTH_API_HOST", "0.0.0.0")
    port = int(os.getenv("NTH_API_PORT", "8002"))
    print(f"Starting NTH Placeholder API server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
