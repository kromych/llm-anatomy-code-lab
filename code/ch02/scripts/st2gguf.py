# st2gguf.py -- copy tensors of a safetensors file into a minimal GGUF
#   python3 st2gguf.py SRC DST ARCH NAME...     (tensors stored as F32)
import json, struct, sys

ALIGN = 32
def pad(k):
    return (ALIGN - k % ALIGN) % ALIGN

def gstr(s):
    b = s.encode("utf-8")
    return struct.pack("<Q", len(b)) + b

def to_f32(raw, dtype):
    if dtype == "F32":
        return raw
    if dtype == "BF16":                  # append two zero low bytes
        return b"".join(b"\0\0" + raw[i:i + 2]
                        for i in range(0, len(raw), 2))
    if dtype == "F16":
        vals = struct.unpack(f"<{len(raw) // 2}e", raw)
        return struct.pack(f"<{len(vals)}f", *vals)
    raise ValueError(dtype)

src, dst, arch, names = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
with open(src, "rb") as f:
    (n,) = struct.unpack("<Q", f.read(8))
    header = json.loads(f.read(n))
    datas = []
    for name in names:
        b, e = header[name]["data_offsets"]
        f.seek(8 + n + b)
        datas.append(to_f32(f.read(e - b), header[name]["dtype"]))
kv = gstr("general.architecture") + struct.pack("<I", 8) + gstr(arch)
infos, off = b"", 0
for name, data in zip(names, datas):
    dims = list(reversed(header[name]["shape"]))   # innermost first
    infos += gstr(name) + struct.pack("<I", len(dims))
    infos += struct.pack(f"<{len(dims)}Q", *dims)
    infos += struct.pack("<IQ", 0, off)            # type 0 = F32
    off += len(data) + pad(len(data))
head = b"GGUF" + struct.pack("<IQQ", 3, len(names), 1) + kv + infos
with open(dst, "wb") as g:
    g.write(head + b"\0" * pad(len(head)))
    for data in datas:
        g.write(data + b"\0" * pad(len(data)))
