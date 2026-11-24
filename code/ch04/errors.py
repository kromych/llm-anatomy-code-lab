# errors.py DATADIR -- relative RMS error of several schemes on one tensor
import struct, sys, math, bisect, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quant import quantize_q4_0, dequantize_q4_0
D = sys.argv[1]
raw = open(f"{D}/st15.bin", "rb").read()
u = struct.unpack(f"<{len(raw)//2}H", raw)
w = struct.pack(f"<{len(u)}I", *[v << 16 for v in u])
w = list(struct.unpack(f"<{len(u)}f", w))
N = len(w); S2 = sum(v*v for v in w)
def rel(err2): return math.sqrt(err2 / S2)
def rnd(v): return math.floor(v + 0.5)

def per_tensor(b):
    L = 2**(b-1) - 1; d = max(abs(v) for v in w) / L
    return rel(sum((v - d*max(-L, min(L, rnd(v/d))))**2 for v in w))
def block_sym(b, B=32):
    L = 2**(b-1) - 1; e = 0.0
    for i in range(0, N, B):
        x = w[i:i+B]; d = max(abs(v) for v in x) / L
        if d: e += sum((v - d*rnd(v/d))**2 for v in x)
    return rel(e)
def block_asym(b, B=32):
    L = 2**b - 1; e = 0.0
    for i in range(0, N, B):
        x = w[i:i+B]; lo = min(x); d = (max(x) - lo) / L
        if d: e += sum((v - (lo + d*rnd((v-lo)/d)))**2 for v in x)
    return rel(e)
def q4_0():
    e = 0.0
    for i in range(0, N, 32):
        x = w[i:i+32]; y = dequantize_q4_0(quantize_q4_0(x))
        e += sum((a-b)**2 for a, b in zip(x, y))
    return rel(e)
FP4 = [0, 0.5, 1, 1.5, 2, 3, 4, 6]
def fp4(v):
    a = abs(v); j = bisect.bisect_left(FP4, a)
    if j == 0: r = 0.0
    elif j == len(FP4): r = 6.0
    else:
        lo, hi = FP4[j-1], FP4[j]; r = lo if a - lo <= hi - a else hi
    return math.copysign(r, v)
def mxfp4():
    e = 0.0
    for i in range(0, N, 32):
        x = w[i:i+32]; am = max(abs(v) for v in x)
        if am == 0: continue
        X = math.floor(math.log2(am)) - 2; s = 2.0**X
        e += sum((v - s*fp4(v/s))**2 for v in x)
    return rel(e)
E4M3 = sorted({m/8 * 2**-6 for m in range(1, 8)} |
              {(1 + m/8) * 2**(ex-7)
               for ex in range(1, 16) for m in range(8)
               if not (ex == 15 and m == 7)})
def e4m3(v):
    j = bisect.bisect_left(E4M3, v)
    if j == 0: return E4M3[0]
    if j == len(E4M3): return E4M3[-1]
    lo, hi = E4M3[j-1], E4M3[j]; return lo if v - lo <= hi - v else hi
def nvfp4():
    g = max(abs(v) for v in w) / (6 * 448); e = 0.0
    for i in range(0, N, 16):
        x = w[i:i+16]; am = max(abs(v) for v in x)
        if am == 0: continue
        s = g * e4m3(am / 6 / g)
        e += sum((v - s*fp4(v/s))**2 for v in x)
    return rel(e)
print("tensor: SmolLM2-135M-Instruct layer 15 down_proj, N =", N,
      "rms =", math.sqrt(S2/N))
res = {}
res["per_tensor"] = [(b, b, per_tensor(b)) for b in range(3, 9)]
res["block_sym"]  = [(b, b + 0.5, block_sym(b)) for b in range(2, 9)]
res["block_asym"] = [(b, b + 1.0, block_asym(b)) for b in range(2, 9)]
res["q4_0"] = q4_0(); res["mxfp4"] = mxfp4(); res["nvfp4"] = nvfp4()
for k, v in res.items(): print(k, v)
