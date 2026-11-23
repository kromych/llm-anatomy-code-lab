# fit.py BENCH.txt [DEVICE] -- fit T0, B and F of sim.py's cost model on one
# device (named in the first line of output; the M1 Ultra GPU unless given),
# then compare the model with every measured configuration.
# BENCH.txt holds llama-batched-bench tables under "## gemma run k" and
# "## qwen run k" headers; for each configuration the fastest run counts.
#   one decode step, one sequence: t = T0 + (W + KVT*kv)/B, for two models
#     of different size, which separates T0 from B;
#   prefill of 2048 tokens, one sequence: t = T0 + 2*N*2048/F.
import re, sys
DEVICE = sys.argv[2] if len(sys.argv) > 2 else "the M1 Ultra GPU"
MODELS = {   # file bytes, parameters, KV bytes per token (F16 cache)
    "gemma": (806058240, 1.0e9, 2 * 26 * 1 * 256 * 2),   # Gemma 3 1B Q4_K_M
    "qwen": (8709518656, 8.19e9, 2 * 36 * 8 * 128 * 2),  # Qwen3-8B Q8_0
}
best, model = {}, None
for line in open(sys.argv[1]):
    m = re.match(r"## (\w+) run", line)
    if m: model = m.group(1); continue
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if model in MODELS and len(c) >= 8 and c[0].isdigit():
        pp, tg, b = int(c[0]), int(c[1]), int(c[2])
        tpp, step = float(c[4]), float(c[6]) / tg
        k = (model, pp, b)
        o = best.get(k, (tpp, step))
        best[k] = (min(o[0], tpp), min(o[1], step))
kv = lambda pp, b, tg=128: b * (pp + tg / 2)            # mean cached tokens
read = lambda m, pp, b: MODELS[m][0] + MODELS[m][2] * kv(pp, b)
sg, sq = best[("gemma", 128, 1)][1], best[("qwen", 128, 1)][1]
B = (read("qwen", 128, 1) - read("gemma", 128, 1)) / (sq - sg)
T0 = sq - read("qwen", 128, 1) / B
W, N, KVT = MODELS["qwen"]
F = 2 * N * 2048 / (best[("qwen", 2048, 1)][0] - T0)
print(f"fitted on {DEVICE}: B = {B / 1e9:.0f} GB/s, "
      f"F = {F / 1e12:.1f} TFLOP/s, T0 = {T0 * 1e3:.1f} ms")
step = lambda tok, kvc: T0 + max((W + KVT * kvc) / B, 2 * N * tok / F)
print(f"{'PP':>5} {'B':>3} {'step ms':>8} {'model':>6} {'ratio':>6}"
      f" {'prefill s':>10} {'model':>6} {'ratio':>6}")
for (m, pp, b), (tpp, s) in sorted(best.items()):
    if m != "qwen": continue
    mod = step(b, kv(pp, b))
    pre = sum(step(min(2048, b * pp - i), i) for i in range(0, b * pp, 2048))
    print(f"{pp:5d} {b:3d} {s * 1e3:8.1f} {mod * 1e3:6.1f} {s / mod:6.2f}"
          f" {tpp:10.2f} {pre:6.2f} {tpp / pre:6.2f}")
