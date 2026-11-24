# ggufread.py -- print the metadata and tensor table of a GGUF file
import io, struct, sys, urllib.request

SCALARS = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i",
           6: "<f", 7: "<?", 10: "<Q", 11: "<q", 12: "<d"}
STRING, ARRAY = 8, 9
TYPES = {0: "F32", 1: "F16", 2: "Q4_0", 6: "Q5_0", 8: "Q8_0",
         12: "Q4_K", 13: "Q5_K", 14: "Q6_K", 30: "BF16"}

def open_src(src, head=1 << 24):
    """A file for a path, or the first 16 MiB of a URL or hf:REPO/FILE."""
    if src.startswith("hf:"):
        repo, _, name = src[3:].rpartition("/")
        src = f"https://huggingface.co/{repo}/resolve/main/{name}"
    if not src.startswith(("http://", "https://")):
        return open(src, "rb")
    rng = {"Range": f"bytes=0-{head - 1}"}
    req = urllib.request.Request(src, headers=rng)
    with urllib.request.urlopen(req) as resp:
        return io.BytesIO(resp.read())

def get(f, fmt):
    return struct.unpack(fmt, f.read(struct.calcsize(fmt)))[0]

def string(f):
    return f.read(get(f, "<Q")).decode("utf-8")

def value(f, vtype):
    if vtype == STRING:
        return string(f)
    if vtype == ARRAY:
        etype, count = get(f, "<I"), get(f, "<Q")
        return [value(f, etype) for _ in range(count)]
    return get(f, SCALARS[vtype])

with open_src(sys.argv[1]) as f:
    magic, version = f.read(4), get(f, "<I")          # G1
    assert magic == b"GGUF" and version == 3, (magic, version)
    n_tensors, n_kv = get(f, "<Q"), get(f, "<Q")
    meta = {}
    for _ in range(n_kv):                              # G2
        key = string(f)
        meta[key] = value(f, get(f, "<I"))
    tensors = []
    for _ in range(n_tensors):                         # G3
        name, ndim = string(f), get(f, "<I")
        dims = [get(f, "<Q") for _ in range(ndim)]
        tensors.append((name, dims, get(f, "<I"), get(f, "<Q")))
    align = meta.get("general.alignment", 32)          # G4
    data = (f.tell() + align - 1) // align * align

for key, v in meta.items():
    if isinstance(v, list):
        v = f"[{len(v)} items] {v[:3]}"
    print(f"{key:40} {str(v)[:32]!r}")
print(f"{n_tensors} tensors; data section starts at byte {data}")
for name, dims, t, off in tensors:
    print(f"{name:26} {str(dims):15} {TYPES.get(t, t):5} {data + off:>10}")
