# verify.py MODEL_DIR [SCRIPTS] -- forward.py against Transformers (fp32)
import os, sys, json, time
import numpy as np
sys.path.insert(0, sys.argv[2] if len(sys.argv) > 2
                else os.path.dirname(os.path.abspath(__file__)))
import forward as F
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

d = sys.argv[1]
tok = AutoTokenizer.from_pretrained(d)
prompt = "The capital of France is"
ids = tok(prompt)["input_ids"]
print("ids", ids, [tok.decode([i]) for i in ids])

cfg = json.load(open(d + "/config.json"))
W = F.load(d + "/model.safetensors")
t0 = time.time()
ours = F.logits(np.array(ids), W, cfg)
print("numpy forward", round(time.time() - t0, 3), "s,", ours.dtype)

m = AutoModelForCausalLM.from_pretrained(d, dtype=torch.float32)
m.eval()
print("attn impl", m.config._attn_implementation)
with torch.no_grad():
    ref = m(torch.tensor([ids])).logits[0, -1].numpy()
print("max |diff|", float(np.abs(ours - ref).max()),
      "max |ref|", float(np.abs(ref).max()))
print("top5 ours", np.argsort(-ours)[:5], "ref", np.argsort(-ref)[:5])

# greedy continuation, ours vs generate()
seq = list(ids)
for _ in range(8):
    seq.append(int(np.argmax(F.logits(np.array(seq), W, cfg))))
with torch.no_grad():
    g = m.generate(torch.tensor([ids]), max_new_tokens=8, do_sample=False)
print("ours", seq)
print("hf  ", g[0].tolist())
print("text", repr(tok.decode(seq)))
n = sum(v.size for v in W.values())
print("parameters", n)
