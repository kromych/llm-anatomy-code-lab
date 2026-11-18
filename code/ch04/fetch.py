# Fetch byte ranges of remote model files and locate one tensor.
# usage: fetch.py OUTDIR
import json, struct, sys, urllib.request, os

OUT = sys.argv[1]
ST = ("https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct/"
      "resolve/main/model.safetensors")
GG = ("https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/"
      "resolve/main/SmolLM2-135M-Instruct-{}.gguf")

def rng(url, a, b):
    req = urllib.request.Request(url, headers={"Range": f"bytes={a}-{b}"})
    with urllib.request.urlopen(req) as r:
        return r.read()

# --- safetensors
n = struct.unpack("<Q", rng(ST, 0, 7))[0]
hdr = json.loads(rng(ST, 8, 8 + n - 1))
for L in (0, 15):
    name = f"model.layers.{L}.mlp.down_proj.weight"
    t = hdr[name]; a, b = t["data_offsets"]
    print("safetensors", name, t["dtype"], t["shape"], b - a)
    open(os.path.join(OUT, f"st{L}.bin"), "wb").write(
        rng(ST, 8 + n + a, 8 + n + b - 1))
    json.dump(t, open(os.path.join(OUT, f"st{L}.json"), "w"))

# --- GGUF
TYPES = {0: "F32", 1: "F16", 2: "Q4_0", 3: "Q4_1", 8: "Q8_0", 12: "Q4_K",
         14: "Q6_K", 30: "BF16"}
SIZE = {0: (1, 4), 1: (1, 2), 2: (32, 18), 3: (32, 20), 8: (32, 34),
        30: (1, 2), 12: (256, 144), 14: (256, 210)}

def gguf_locate(url, want):
    buf = rng(url, 0, 8 * 1024 * 1024 - 1)
    p = 0
    def u(fmt):
        nonlocal p
        v = struct.unpack_from("<" + fmt, buf, p)[0]
        p += struct.calcsize(fmt); return v
    def s():
        nonlocal p
        L = u("Q"); v = buf[p:p + L].decode(); p += L; return v
    SCAL = {0: "B", 1: "b", 2: "H", 3: "h", 4: "I", 5: "i", 6: "f",
            7: "?", 10: "Q", 11: "q", 12: "d"}
    def val(ty):
        if ty == 8: return s()
        if ty == 9:
            et = u("I"); cnt = u("Q")
            return [val(et) for _ in range(cnt)]
        return u(SCAL[ty])
    assert buf[:4] == b"GGUF"; p = 4
    ver = u("I"); nt = u("Q"); nkv = u("Q")
    kv = {}
    for _ in range(nkv):
        k = s(); ty = u("I"); v = val(ty)
        if not isinstance(v, list): kv[k] = v
    align = kv.get("general.alignment", 32)
    infos = {}
    for _ in range(nt):
        nm = s(); nd = u("I"); dims = [u("Q") for _ in range(nd)]
        ty = u("I"); off = u("Q"); infos[nm] = (dims, ty, off)
    data0 = (p + align - 1) // align * align
    dims, ty, off = infos[want]
    ne = 1
    for d in dims: ne *= d
    blk, by = SIZE[ty]
    nbytes = ne // blk * by
    print("gguf", url.rsplit("/", 1)[1], "v%d" % ver, want, dims,
          TYPES.get(ty, ty), "file_type", kv.get("general.file_type"))
    return rng(url, data0 + off, data0 + off + nbytes - 1), dims, ty

for q in ("Q8_0", "Q4_0", "f16"):
    for L in (0, 15):
        data, dims, ty = gguf_locate(GG.format(q),
                                     f"blk.{L}.ffn_down.weight")
        open(os.path.join(OUT, f"gg_{q}_{L}.bin"), "wb").write(data)
        json.dump({"dims": dims, "type": ty},
                  open(os.path.join(OUT, f"gg_{q}_{L}.json"), "w"))
