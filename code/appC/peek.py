"""peek.py -- the Python of this book in thirty-eight lines: read the
header of a GGUF file (with, mmap, struct) and stream a chat reply from a
local server (urllib, json, a generator, exceptions).

Usage: python3 peek.py MODEL.gguf [PORT]
"""
import json, mmap, struct, sys, urllib.request

def header(path):
    """Magic, version and counts at the start of a GGUF file."""
    with open(path, "rb") as f, \
         mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
        magic, version, n_tensors, n_kv = struct.unpack_from("<4sIQQ", m)
    return {"magic": magic.decode(), "version": version,
            "tensors": n_tensors, "metadata": n_kv}

def deltas(port, prompt):
    """Yield the pieces of a streamed reply as they arrive."""
    body = json.dumps({"messages": [{"role": "user", "content": prompt}],
                       "stream": True, "max_tokens": 32}).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions", data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        for line in resp:                   # one line of the event stream
            if line.startswith(b"data: {"):
                delta = json.loads(line[6:])["choices"][0]["delta"]
                yield delta.get("content") or ""

if __name__ == "__main__":
    print(header(sys.argv[1]))
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    try:
        for piece in deltas(port, "Name one prime number."):
            print(piece, end="", flush=True)
        print()
    except OSError as e:
        print(f"no server on port {port}: {e}")
