# verify.py DATADIR -- check quant.py against real GGUF bytes
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quant import *

D = sys.argv[1]
def bf16(path):
    raw = open(path, "rb").read()
    u = struct.unpack(f"<{len(raw)//2}H", raw)
    b = struct.pack(f"<{len(u)}I", *[v << 16 for v in u])
    return list(struct.unpack(f"<{len(u)}f", b))
def f16(path):
    raw = open(path, "rb").read()
    return list(struct.unpack(f"<{len(raw)//2}e", raw))

def q8_f64(x):   # quantize_q8_0 in Python's double precision, without f32
    d = max(abs(v) for v in x) / 127
    inv = 1 / d if d else 0.0
    q = [round_half_away(v * inv) for v in x]
    return struct.pack("<e32b", d, *q)

for L in (0, 15):
    w = bf16(f"{D}/st{L}.bin"); wf = f16(f"{D}/gg_f16_{L}.bin")
    g8 = open(f"{D}/gg_Q8_0_{L}.bin", "rb").read()
    nb = len(w) // 32
    diff = sum(1 for a, b in zip(w, wf) if a != b)
    print(f"layer {L}: {len(w)} weights;"
          f" bf16 vs f16-gguf differ in {diff}")
    for label, src, enc in (("bf16 src, f64 math", w, q8_f64),
                            ("bf16 src, f32 math", w, quantize_q8_0),
                            ("f16 src,  f32 math", wf, quantize_q8_0)):
        mism = sum(1 for i in range(nb)
                   if enc(src[32*i:32*i+32]) != g8[34*i:34*i+34])
        print(f"  Q8_0 re-encode ({label}): {mism}/{nb} blocks differ")
    # decode check: dequantized Q8_0 within d/2 of the source
    worst = 0.0
    for i in range(nb):
        blk = g8[34*i:34*i+34]; d = struct.unpack_from("<e", blk)[0]
        y = dequantize_q8_0(blk)
        for a, b in zip(w[32*i:32*i+32], y):
            worst = max(worst, abs(a - b) / (d if d else 1))
    print(f"  Q8_0 decode: max |error| = {worst:.3f} d")
g4 = open(f"{D}/gg_Q4_0_15.bin", "rb").read()
w = bf16(f"{D}/st15.bin"); nb = len(w) // 32
e_file = e_ref = s2 = 0.0
for i in range(nb):
    x = w[32*i:32*i+32]
    yf = dequantize_q4_0(g4[18*i:18*i+18])
    yr = dequantize_q4_0(quantize_q4_0(x))
    e_file += sum((a-b)**2 for a, b in zip(x, yf))
    e_ref += sum((a-b)**2 for a, b in zip(x, yr))
    s2 += sum(a*a for a in x)
print("layer 15 Q4_0: rel. rms error file (imatrix) "
      f"{(e_file/s2)**.5:.4f}, "
      f"plain round-to-nearest {(e_ref/s2)**.5:.4f}")
