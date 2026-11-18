# st_header.py -- list the tensors of a safetensors file or URL
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

src = sys.argv[1]
(n,) = struct.unpack("<Q", read(src, 0, 8))         # step S1
header = json.loads(read(src, 8, n))                 # step S2
meta = header.pop("__metadata__", {})
print(f"header: {n} bytes, metadata: {meta}")
order = sorted(header, key=lambda k: header[k]["data_offsets"])
for name in order:
    t = header[name]
    begin, end = t["data_offsets"]
    print(f"{name:42} {t['dtype']:5} {str(t['shape']):12}"
          f" {8 + n + begin:>10} {end - begin:>10}")
size = max(t["data_offsets"][1] for t in header.values())
print(f"{len(header)} tensors, {size} bytes of data")
