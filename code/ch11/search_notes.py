# search_notes.py -- retrieval as a tool: embed the query and return the
# nearest passages of a notes file that holds one passage per line.
# EMBED_BASE names the embeddings endpoint (Chapter 10), for example
#   EMBED_BASE=http://127.0.0.1:8081/v1 python3 search_notes.py QUERY...
import json, math, os, sys, urllib.request
from tools import tool

BASE = os.environ.get("EMBED_BASE", "http://127.0.0.1:8081/v1")
MODEL = os.environ.get("EMBED_MODEL", "embedding")   # Ollama needs a name
NOTES = os.environ.get("NOTES", "notes.txt")
TASK = ("Instruct: Given a web search query, retrieve relevant "
        "passages that answer the query\nQuery:")
VECTORS = {}                             # passage -> vector, filled once

def embed(texts):
    body = {"model": MODEL, "input": texts}
    req = urllib.request.Request(BASE + "/embeddings",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.load(r)["data"]
    return [d["embedding"] for d in sorted(data, key=lambda d: d["index"])]

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))

@tool
def search_notes(query: str) -> str:
    """Return the three notes nearest in meaning to the query."""
    if not VECTORS:                      # embed the notes on first use
        with open(NOTES, encoding="utf-8") as f:
            notes = [line.strip() for line in f if line.strip()]
        VECTORS.update(zip(notes, embed(notes)))
    q = embed([TASK + query])[0]
    near = sorted(VECTORS, key=lambda n: cosine(q, VECTORS[n]),
                  reverse=True)
    return "\n".join(near[:3])

if __name__ == "__main__":
    for query in sys.argv[1:]:
        print(query, search_notes(query), sep="\n", end="\n\n")
