# verify2.py DATADIR -- Q8_0 blocks again, and Q4_0 with the nibbles swapped
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quant import quantize_q8_0, dequantize_q4_0, quantize_q4_0
D = sys.argv[1]
def bf16(path):
    raw = open(path, "rb").read()
    u = struct.unpack(f"<{len(raw)//2}H", raw)
    b = struct.pack(f"<{len(u)}I", *[v << 16 for v in u])
    return list(struct.unpack(f"<{len(u)}f", b))
for L in (0, 15):
    w = bf16(f"{D}/st{L}.bin")
    g8 = open(f"{D}/gg_Q8_0_{L}.bin", "rb").read()
    nb = len(w)//32
    bad = sum(1 for i in range(nb)
              if quantize_q8_0(w[32*i:32*i+32]) != g8[34*i:34*i+34])
    print(L, bad, "of", nb, "Q8_0 blocks differ")
# wrong nibble order sanity check
g4 = open(f"{D}/gg_Q4_0_15.bin", "rb").read(); w = bf16(f"{D}/st15.bin")
def bad(blk):
    d = struct.unpack_from("<e", blk)[0]
    out = []
    for b in blk[2:]: out += [((b & 15) - 8)*d, ((b >> 4) - 8)*d]
    return out
e_ok = e_bad = s2 = 0.0
for i in range(len(w)//32):
    x = w[32*i:32*i+32]; blk = g4[18*i:18*i+18]
    e_ok += sum((a-b)**2 for a, b in zip(x, dequantize_q4_0(blk)))
    e_bad += sum((a-b)**2 for a, b in zip(x, bad(blk)))
    s2 += sum(a*a for a in x)
print("Q4_0 rel err correct layout", (e_ok/s2)**.5,
      "interleaved layout", (e_bad/s2)**.5)
