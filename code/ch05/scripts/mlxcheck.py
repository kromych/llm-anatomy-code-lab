# mlxcheck.py MODEL_DIR SCRIPTS -- compare forward.py with mlx-lm
import sys, json
import numpy as np
sys.path.insert(0, sys.argv[2])
import forward as F
import mlx.core as mx
from mlx_lm import load

d = sys.argv[1]
model, tok = load(d)
ids = tok.encode("The capital of France is")
print("ids", ids)
y = model(mx.array([ids]))           # lazy: builds the graph only
print("type before eval", type(y), y.shape, y.dtype)
mx.eval(y)
ref = np.array(y[0, -1].astype(mx.float32))
cfg = json.load(open(d + "/config.json"))
W = F.load(d + "/model.safetensors")
ours = F.logits(np.array(ids), W, cfg)
print("max |diff|", float(np.abs(ours - ref).max()))
print("top5 ours", np.argsort(-ours)[:5], "mlx", np.argsort(-ref)[:5])
