import json, struct, sys
sys.path.insert(0, sys.argv[2])
from stlib import read, decode

def embedding_row(src, t):
    (n,) = struct.unpack("<Q", read(src, 0, 8))
    e = json.loads(read(src, 8, n))["model.embed_tokens.weight"]
    rows, d = e["shape"]
    start = 8 + n + e["data_offsets"][0] + 2 * d * t
    return decode(read(src, start, 2 * d), e["dtype"])

row = embedding_row(sys.argv[1], 1000)
print(len(row), row[:3])
