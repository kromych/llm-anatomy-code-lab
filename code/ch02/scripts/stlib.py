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
