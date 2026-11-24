# stread.py -- inspect a safetensors file or URL (Algorithm S)
#   python3 stread.py SRC             list the tensors
#   python3 stread.py SRC NAME [K]    print K values of tensor NAME
import json, struct, sys, urllib.request

def read(src, start, n):
    """Return n bytes of src, a path or an http(s) URL, from start."""
    if src.startswith(("http://", "https://")):
        rng = {"Range": f"bytes={start}-{start + n - 1}"}
        req = urllib.request.Request(src, headers=rng)
        with urllib.request.urlopen(req) as resp:
            return resp.read()
    with open(src, "rb") as f:
        f.seek(start)
        return f.read(n)

def decode(raw, dtype):
    """Little-endian bytes -> floats (F32, F16 and BF16 only)."""
    if dtype == "F32":
        return list(struct.unpack(f"<{len(raw) // 4}f", raw))
    if dtype == "F16":
        return list(struct.unpack(f"<{len(raw) // 2}e", raw))
    if dtype == "BF16":                  # the upper half of a float32
        return [struct.unpack("<f", struct.pack("<I", u << 16))[0]
                for u in struct.unpack(f"<{len(raw) // 2}H", raw)]
    raise ValueError(f"cannot decode {dtype}")

src = sys.argv[1]
if src.startswith("hf:"):                       # hf:REPO/FILE shorthand
    repo, _, name = src[3:].rpartition("/")
    src = f"https://huggingface.co/{repo}/resolve/main/{name}"
(n,) = struct.unpack("<Q", read(src, 0, 8))          # S1
header = json.loads(read(src, 8, n))                  # S2
meta = header.pop("__metadata__", {})
if len(sys.argv) == 2:
    print(f"header: {n} bytes, metadata: {meta}")
    for name in sorted(header, key=lambda k: header[k]["data_offsets"]):
        t = header[name]
        b, e = t["data_offsets"]
        print(f"{name:44} {t['dtype']:5} {str(t['shape']):13} {e - b:>9}")
else:
    t = header[sys.argv[2]]                           # S3
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    size = {"F32": 4, "F16": 2, "BF16": 2}[t["dtype"]]
    begin = 8 + n + t["data_offsets"][0]              # S5
    print(decode(read(src, begin, k * size), t["dtype"]))   # S5, S6
