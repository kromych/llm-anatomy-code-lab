# embed.py -- rank passages for a query by the cosine similarity of
# their embeddings.  Usage: python3 embed.py BASE_URL FILE QUERY...
# (standard library only; FILE holds one passage per line)
import json, math, sys, urllib.request

MODEL = "embedding"          # llama-server ignores the name
TASK = ("Instruct: Given a web search query, retrieve relevant "
        "passages that answer the query\nQuery:")

def embed(base, texts):
    """One vector per text from the embeddings endpoint, in order."""
    body = {"model": MODEL, "input": texts}
    req = urllib.request.Request(base + "/embeddings",
            json.dumps(body).encode(),
            {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.load(resp)["data"]
    return [d["embedding"] for d in sorted(data, key=lambda d: d["index"])]

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))

def rank(base, query, passages, vectors=None, k=3):
    """The k passages nearest to the query, as (similarity, passage)."""
    vectors = vectors or embed(base, passages)
    q = embed(base, [TASK + query])[0]
    scored = sorted(zip((cosine(q, v) for v in vectors), passages),
                    reverse=True)
    return scored[:k]

if __name__ == "__main__":
    base, path, queries = sys.argv[1], sys.argv[2], sys.argv[3:]
    passages = [p.strip() for p in open(path) if p.strip()]
    vectors = embed(base, passages)
    print(len(vectors), "passages,", len(vectors[0]), "dimensions")
    for query in queries:
        print(query)
        for score, passage in rank(base, query, passages, vectors):
            print("  %.3f  %s" % (score, passage))
