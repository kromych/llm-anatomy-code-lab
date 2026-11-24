# blocks.py DATADIR -- what the scale and what the block size contribute to
# the difference between MXFP4 and NVFP4: FP4 elements with blocks of 32 or
# 16 and a scale that is a power of two or an E4M3 number, on the tensor
# of errors.py.
import struct, sys, math, bisect
D = sys.argv[1]
raw = open(f"{D}/st15.bin", "rb").read()
u = struct.unpack(f"<{len(raw)//2}H", raw)
w = struct.pack(f"<{len(u)}I", *[v << 16 for v in u])
w = list(struct.unpack(f"<{len(u)}f", w))
N = len(w); S2 = sum(v*v for v in w)

FP4 = [0, 0.5, 1, 1.5, 2, 3, 4, 6]
def fp4(v):
    a = abs(v); j = bisect.bisect_left(FP4, a)
    if j == 0: r = 0.0
    elif j == len(FP4): r = 6.0
    else:
        lo, hi = FP4[j-1], FP4[j]; r = lo if a - lo <= hi - a else hi
    return math.copysign(r, v)
E4M3 = sorted({m/8 * 2**-6 for m in range(1, 8)} |
              {(1 + m/8) * 2**(ex-7)
               for ex in range(1, 16) for m in range(8)
               if not (ex == 15 and m == 7)})
def e4m3(v):
    j = bisect.bisect_left(E4M3, v)
    if j == 0: return E4M3[0]
    if j == len(E4M3): return E4M3[-1]
    lo, hi = E4M3[j-1], E4M3[j]; return lo if v - lo <= hi - v else hi

G = max(abs(v) for v in w) / (6 * 448)          # NVFP4's scale per tensor
def power_of_two(am): return 2.0 ** (math.floor(math.log2(am)) - 2)
def e4m3_scale(am): return G * e4m3(am / 6 / G)

def error(B, scale):
    e = clipped = 0
    for i in range(0, N, B):
        x = w[i:i+B]; am = max(abs(v) for v in x)
        if am == 0: continue
        s = scale(am)
        e += sum((v - s*fp4(v/s))**2 for v in x)
        clipped += sum((abs(v) - 6*s)**2 for v in x if abs(v) > 6*s)
    return math.sqrt(e / S2), clipped / e

res = {}
for B in (32, 16):
    for name, scale in (("power of two", power_of_two),
                        ("E4M3", e4m3_scale)):
        res[B, name] = error(B, scale)
        print(f"blocks of {B}, {name:12} scale: relative error "
              f"{res[B, name][0]:.4f}, {res[B, name][1]:.0%} of its square "
              f"from elements beyond 6 times the scale")
mx, nv = res[32, "power of two"][0], res[16, "E4M3"][0]
for B, name in ((32, "E4M3"), (16, "power of two")):
    print(f"blocks of {B} with the {name} scale close "
          f"{(mx - res[B, name][0]) / (mx - nv):.0%} of the gap between "
          f"MXFP4 ({mx:.4f}) and NVFP4 ({nv:.4f})")
