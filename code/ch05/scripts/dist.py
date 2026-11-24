# dist.py MODEL_DIR LOGITS.npy ID... -- run forward.py on the token IDs,
# store the logits of the last position, and print the data of the chart
# of next-token probabilities (NumPy only; tokenizer.json, if MODEL_DIR
# has one, supplies the text of the tokens)
import sys, json, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forward as F
from sample import softmax, top_p, min_p

d, out = sys.argv[1], sys.argv[2]
ids = [int(t) for t in sys.argv[3:]]
cfg = json.load(open(d + "/config.json"))
W = F.load(d + "/model.safetensors")
z = F.logits(np.array(ids), W, cfg)
np.save(out, z)
print("ids", ids, "->", out, z.dtype, z.shape)
z = z.astype(np.float64)

text = {}
if os.path.exists(d + "/tokenizer.json"):
    with open(d + "/tokenizer.json", encoding="utf-8") as f:
        vocab = json.load(f)["model"]["vocab"]
    text = {i: t.replace(chr(0x120), " ") for t, i in vocab.items()}

order = np.argsort(-z)
print("top logits", [(int(i), text.get(int(i), "?"),
                      round(float(z[i]), 3)) for i in order[:12]])
for T in (0.5, 1.0, 1.5):
    p = softmax(z / T)
    print(f"T={T}", [round(float(p[i]), 4) for i in order[:12]],
          "sum12", round(float(p[order[:12]].sum()), 4),
          "entropy", round(float(-(p * np.log(p + 1e-300)).sum()), 3))

def kept(y):
    return int(np.isfinite(y).sum())

print("top-p 0.9 keeps (T=1)", kept(top_p(z, 0.9)))
print("top-p 0.95 keeps (T=1)", kept(top_p(z, 0.95)))
print("min-p 0.05 keeps (T=1)", kept(min_p(z, 0.05)))
print("top-p 0.95 after T=0.6 keeps", kept(top_p(z / 0.6, 0.95)))
print("min-p 0.05 keeps (T=0.6)", kept(min_p(z / 0.6, 0.05)))
print("vocab", len(z))
