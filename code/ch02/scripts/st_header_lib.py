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
