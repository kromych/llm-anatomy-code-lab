# extra.py DATADIR -- Q4_1 and Q8_0 on the example tensor, the worked
# example of Algorithm Q, and the table of sizes
import struct, sys, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quant import *
D = sys.argv[1]
raw = open(f"{D}/st15.bin", "rb").read()
u = struct.unpack(f"<{len(raw)//2}H", raw)
w = struct.pack(f"<{len(u)}I", *[v << 16 for v in u])
w = list(struct.unpack(f"<{len(u)}f", w))
N = len(w); S2 = sum(v*v for v in w)
def q4_1(x):
    lo, hi = min(x), max(x); d = (hi - lo) / 15
    inv = 1/d if d else 0.0
    q = [min(15, int((v - lo)*inv + 0.5)) for v in x]
    d16, m16 = struct.unpack("<ee", struct.pack("<ee", d, lo))
    return [qq*d16 + m16 for qq in q]
e1 = e8 = 0.0
for i in range(0, N, 32):
    x = w[i:i+32]
    e1 += sum((a-b)**2 for a, b in zip(x, q4_1(x)))
    y = dequantize_q8_0(quantize_q8_0(x))
    e8 += sum((a-b)**2 for a, b in zip(x, y))
print("Q4_1 exact", math.sqrt(e1/S2), "Q8_0 exact", math.sqrt(e8/S2))
print("amax/rms of tensor", max(abs(v) for v in w)/math.sqrt(S2/N))
# worked example
x = [0.12, -0.40, 0.05, 0.31, -0.08, 0.22, -0.15, 0.03]
d = max(abs(v) for v in x) / 7
q = [round_half_away(v/d) for v in x]
y = [d*k for k in q]
print("d", d, "q", q)
print("y", [round(v, 4) for v in y])
print("err", [round(a-b, 4) for a, b in zip(x, y)])
print("rms err", math.sqrt(sum((a-b)**2 for a, b in zip(x, y))/8),
      "d/sqrt12", d/math.sqrt(12))
# Q4_0 decode example: d=0.0125 fp16?
print(struct.unpack("<e", struct.pack("<e", 0.0125))[0])
# sizes table
for name, b in [("F32", 32), ("BF16", 16), ("Q8_0", 8.5), ("Q6_K", 6.5625),
                ("Q5_K", 5.5), ("Q4_K", 4.5), ("MXFP4", 4.25),
                ("Q3_K", 3.4375), ("Q2_K", 2.625)]:
    s8 = 8e9*b/8/1e9; s70 = 70e9*b/8/1e9
    print(f"{name:6s} {b:7.4f} {s8:6.2f} {s70:7.1f} {400/s8:6.1f}")
