# quant.py -- Q8_0, Q4_0 and Q4_K blocks as ggml stores them (stdlib)
import struct

def f32(v):                       # round to single precision, as C does
    return struct.unpack("<f", struct.pack("<f", v))[0]

def round_half_away(v):           # C roundf: halves go away from zero
    return int(v + 0.5) if v >= 0 else -int(0.5 - v)

def quantize_q8_0(x):             # 32 floats -> 34 bytes
    d = f32(max(abs(v) for v in x) / 127)
    inv = f32(1 / d) if d else 0.0
    q = [round_half_away(f32(v * inv)) for v in x]
    return struct.pack("<e32b", d, *q)

def dequantize_q8_0(blk):         # 34 bytes -> 32 floats
    d, *q = struct.unpack("<e32b", blk)
    return [d * v for v in q]

def quantize_q4_0(x):             # 32 floats -> 18 bytes
    m = max(x, key=abs)           # the value of largest magnitude
    d = f32(m / -8)
    inv = f32(1 / d) if d else 0.0
    q = [min(15, int(f32(f32(v * inv) + 8.5))) for v in x]
    qs = bytes(q[j] | q[j + 16] << 4 for j in range(16))
    return struct.pack("<e", d) + qs

def dequantize_q4_0(blk):         # 18 bytes -> 32 floats
    d = struct.unpack_from("<e", blk)[0]
    lo = [(b & 15) - 8 for b in blk[2:]]
    hi = [(b >> 4) - 8 for b in blk[2:]]
    return [d * v for v in lo + hi]

def dequantize_q4_k(blk):         # 144 bytes -> 256 floats
    d, dmin = struct.unpack_from("<2e", blk)
    sc, qs, x = blk[4:16], blk[16:], []
    for k in range(8):            # sub-block k holds 32 weights
        if k < 4:                 # low six bits of bytes k and k + 4
            s, m = sc[k] & 63, sc[k + 4] & 63
        else:                     # byte k + 4, and two bits from above
            s = (sc[k + 4] & 15) | (sc[k - 4] >> 6) << 4
            m = (sc[k + 4] >> 4) | (sc[k] >> 6) << 4
        pair = qs[32 * (k // 2):32 * (k // 2) + 32]
        q = [b >> 4 if k % 2 else b & 15 for b in pair]
        x += [f32(d * s * v - dmin * m) for v in q]
    return x

if __name__ == "__main__":
    import random
    random.seed(1)
    x = [random.gauss(0, 0.02) for _ in range(32)]
    for name, enc, dec in (("Q8_0", quantize_q8_0, dequantize_q8_0),
                           ("Q4_0", quantize_q4_0, dequantize_q4_0)):
        blk = enc(x)
        err = [a - b for a, b in zip(x, dec(blk))]
        rms = (sum(e * e for e in err) / len(err)) ** 0.5
        print(f"{name}: {len(blk)} bytes = {8 * len(blk) / 32} bits"
              f" per weight, rms error {rms:.2e}")
