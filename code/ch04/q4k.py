# q4k.py GGUF TENSOR [SAFETENSORS NAME] -- decode one Q4_K tensor of a
# local GGUF file with quant.py, show its first super-block, and compare:
# with the dequantizer of the gguf package (if it is installed) and with
# the BF16 original of a safetensors file (if one is given).
# results/q4k.txt: Qwen3-1.7B-Q4_K_M.gguf of ggml-org/Qwen3-1.7B-GGUF,
# blk.0.attn_k.weight; model-00001-of-00002.safetensors of
# Qwen/Qwen3-1.7B, model.layers.0.self_attn.k_proj.weight.
import json, math, mmap, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quant import dequantize_q4_k, quantize_q4_0, dequantize_q4_0

def locate(buf, want):            # GGUF header -> dims, type, offset
    p = 4
    def u(fmt):
        nonlocal p
        v = struct.unpack_from("<" + fmt, buf, p)[0]
        p += struct.calcsize(fmt); return v
    def s():
        nonlocal p
        n = u("Q"); v = bytes(buf[p:p + n]).decode(); p += n; return v
    SCAL = {0: "B", 1: "b", 2: "H", 3: "h", 4: "I", 5: "i", 6: "f",
            7: "?", 10: "Q", 11: "q", 12: "d"}
    def val(ty):
        if ty == 8: return s()
        if ty == 9:
            et, cnt = u("I"), u("Q")
            return [val(et) for _ in range(cnt)]
        return u(SCAL[ty])
    assert buf[:4] == b"GGUF"
    ver, nt, nkv = u("I"), u("Q"), u("Q")
    kv = {}
    for _ in range(nkv):
        k = s(); ty = u("I"); v = val(ty)
        if not isinstance(v, list): kv[k] = v
    align, infos = kv.get("general.alignment", 32), {}
    for _ in range(nt):
        nm = s(); nd = u("I"); dims = [u("Q") for _ in range(nd)]
        ty = u("I"); off = u("Q"); infos[nm] = (dims, ty, off)
    data0 = (p + align - 1) // align * align
    dims, ty, off = infos[want]
    imat = [k for k in kv if k.startswith("quantize.imatrix")]
    return dims, ty, data0 + off, kv.get("general.file_type"), imat

def bf16(path, name):             # one BF16 tensor of a safetensors file
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        t = json.loads(f.read(n))[name]
        a, b = t["data_offsets"]
        f.seek(8 + n + a); raw = f.read(b - a)
    assert t["dtype"] == "BF16"
    u = struct.unpack(f"<{len(raw) // 2}H", raw)
    w = struct.pack(f"<{len(u)}I", *[v << 16 for v in u])
    return list(struct.unpack(f"<{len(u)}f", w)), t["shape"]

def rel(x, y):                    # relative RMS error of y against x
    e = sum((a - b) ** 2 for a, b in zip(x, y))
    return math.sqrt(e / sum(a * a for a in x))

path, want = sys.argv[1], sys.argv[2]
f = open(path, "rb")
buf = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
dims, ty, at, ftype, imat = locate(buf, want)
assert ty == 12, "not a Q4_K tensor"
n = math.prod(dims)
data = bytes(buf[at:at + n // 256 * 144])
print(f"{os.path.basename(path)}: file type {ftype},"
      f" {len(imat)} quantize.imatrix keys")
print(f"{want} {dims}: Q4_K, {n} weights,")
print(f"  {len(data)} bytes at byte {at}, {n // 256} super-blocks")

blk = data[:144]
d, dmin = struct.unpack_from("<2e", blk)
x = dequantize_q4_k(blk)
print("super-block 0")
print("  bytes 0-3:", blk[:4].hex(" "))
print(f"  d = {d!r}, dmin = {dmin!r}")
print("  bytes 4-15:", blk[4:16].hex(" "))
sc = blk[4:16]
s = [sc[k] & 63 for k in range(4)] + \
    [(sc[k + 4] & 15) | (sc[k - 4] >> 6) << 4 for k in range(4, 8)]
m = [sc[k + 4] & 63 for k in range(4)] + \
    [(sc[k + 4] >> 4) | (sc[k] >> 6) << 4 for k in range(4, 8)]
print("  scales s_k:", s)
print("  minima m_k:", m)
for r in (0, 3):                  # the first and the last chunk of codes
    run = blk[16 + 32 * r:20 + 32 * r]
    print(f"  bytes {16 + 32 * r}-{19 + 32 * r}:", run.hex(" "))
    for k in (2 * r, 2 * r + 1):
        q = [b >> 4 if k % 2 else b & 15 for b in run]
        print(f"  sub-block {k}: step {d * s[k]:.7f},"
              f" offset {dmin * m[k]:.7f}, codes {q}")
        print("    weights", [round(v, 6) for v in x[32 * k:32 * k + 4]])

y = []
for i in range(0, len(data), 144):
    y += dequantize_q4_k(data[i:i + 144])
print("decoded", len(y), "weights")

try:
    import numpy as np, gguf
    from gguf.quants import dequantize
    from importlib.metadata import version
    ref = dequantize(np.frombuffer(data, np.uint8),
                     gguf.GGMLQuantizationType.Q4_K)
    mine = np.array(y, np.float32)
    print(f"gguf {version('gguf')}, dequantize: {int((ref != mine).sum())}"
          f" of {mine.size} values differ,")
    print(f"  largest difference {float(abs(ref - mine).max())}")
except ImportError:
    print("gguf package not installed; comparison skipped")

if len(sys.argv) > 4:
    w, shape = bf16(sys.argv[3], sys.argv[4])
    print(f"{os.path.basename(sys.argv[3])}:")
    print(f"  {sys.argv[4]} {shape}")
    z = []
    for i in range(0, len(w), 32):
        z += dequantize_q4_0(quantize_q4_0(w[i:i + 32]))
    print("relative RMS error against the BF16 weights:")
    print(f"  Q4_K of the file {rel(w, y):.4f},"
          f" Q4_0 by quant.py {rel(w, z):.4f}")
