# truncate.py -- shorter vectors from the same embeddings: ask the
# server for 256 dimensions and for Base64, then keep the first D
# components of each vector and rank the passages again.
# Usage: python3 truncate.py BASE_URL FILE QUERY...
# (standard library only; uses embed.py)
import base64, json, sys, urllib.request
from embed import MODEL, TASK, cosine, embed

base, path, queries = sys.argv[1], sys.argv[2], sys.argv[3:]
for field, value in (("dimensions", 256), ("encoding_format", "base64")):
    body = {"model": MODEL, "input": "Hello, seam!", field: value}
    req = urllib.request.Request(base + "/embeddings",
            json.dumps(body).encode(),
            {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        e = json.load(resp)["data"][0]["embedding"]
    if isinstance(e, str):
        print("%s %r: a string of %d characters for %d bytes" % (
            field, value, len(e), len(base64.b64decode(e))))
    else:
        print("%s %r: %d numbers" % (field, value, len(e)))
passages = [p.strip() for p in open(path) if p.strip()]
vectors = embed(base, passages)
for query in queries:
    q = embed(base, [TASK + query])[0]
    print(query)
    for d in (1024, 256, 64, 32):
        order = sorted(range(len(passages)), reverse=True,
                       key=lambda i: cosine(q[:d], vectors[i][:d]))
        best = order[0]
        print("  %4d components: passages %s, best %.3f" % (
            d, [i + 1 for i in order[:3]],
            cosine(q[:d], vectors[best][:d])))
