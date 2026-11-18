# float64.py MODEL_DIR SCRIPTS -- what the float64 expressions of an
# earlier forward.py cost: each alone, and the three together.
import sys, json, time
import numpy as np
sys.path.insert(0, sys.argv[2])
import forward as F

EARLIER = [  # (as printed, as it was)
    ("theta ** (-np.arange(0, hd, 2, dtype=np.float32) / hd)",
     "theta ** (-np.arange(0, hd, 2) / hd)"),
    ("/ hd ** 0.5", "/ np.sqrt(hd)"),
    ("np.full((n, n), -np.inf, np.float32)", "np.full((n, n), -np.inf)"),
]
source = open(sys.argv[2] + "/forward.py").read()

def variant(pairs):                      # forward.py with these changes
    text = source
    for new, old in pairs:
        assert new in text
        text = text.replace(new, old)
    module = {"__name__": "forward_earlier"}
    exec(text, module)
    return module["logits"]

def best(f, repeats=5):
    times = []
    for _ in range(repeats):
        t0 = time.time(); f(); times.append(time.time() - t0)
    return min(times)

cfg = json.load(open(sys.argv[1] + "/config.json"))
W = F.load(sys.argv[1] + "/model.safetensors")
prompt = np.array([504, 3575, 282, 4649, 314])

def greedy(logits):
    ids = list(prompt)
    for _ in range(8):
        ids.append(int(np.argmax(logits(np.array(ids), W, cfg))))
    return ids

z, t = F.logits(prompt, W, cfg), best(lambda: F.logits(prompt, W, cfg))
print(f"as printed          {z.dtype}  {1000 * t:6.1f} ms")
NAMES = ["np.arange alone", "np.sqrt alone", "np.full alone"]
cases = [(name, [pair]) for name, pair in zip(NAMES, EARLIER)]
for name, pairs in cases + [("all three", EARLIER)]:
    f = variant(pairs)
    z64, t64 = f(prompt, W, cfg), best(lambda: f(prompt, W, cfg))
    print(f"{name:19} {z64.dtype}  {1000 * t64:6.1f} ms  "
          f"{t64 / t:4.1f} times, logits moved by "
          f"{np.abs(z64 - z).max():.1e}, "
          f"same tokens: {greedy(f) == greedy(F.logits)}")

E = W["model.embed_tokens.weight"]       # the output layer by itself
h = np.random.default_rng(0).standard_normal(E.shape[1]).astype(np.float32)
t32, t64 = best(lambda: h @ E.T), best(lambda: h.astype(np.float64) @ E.T)
print(f"output layer: float32 row {1000 * t32:.2f} ms, float64 row "
      f"{1000 * t64:.2f} ms, {t64 / t32:.0f} times")
