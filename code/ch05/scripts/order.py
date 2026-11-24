# order.py LOGITS.npy -- effect of the sampler order on one distribution,
# computed with the functions of sample.py from stored logits
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sample import (softmax, top_k, top_p, min_p, temperature, chain,
                    ORDER)

z = np.load(sys.argv[1]).astype(np.float64)
PARIS, THE = 7042, 260

def report(name, zz):
    p = softmax(zz); kept = int(np.isfinite(zz).sum())
    print(f"{name}: kept {kept}, P(Paris)={p[PARIS]:.4f}, "
          f"P(the)={p[THE]:.4f}")

par = {temperature: 0.8, top_k: 40, top_p: 0.95, min_p: 0.05}
# llama.cpp defaults: top_k 40 -> top_p 0.95 -> min_p 0.05 -> temp 0.8
report("llama.cpp default chain", chain(z, ORDER["llama.cpp"], par))
# vLLM order with the same values: temp -> min_p -> top_k -> top_p
report("vLLM order, same values", chain(z, ORDER["vLLM"], par))
# Transformers order: temp -> top_k -> top_p -> min_p
report("Transformers order, same values",
       chain(z, ORDER["Transformers"], par))
# T=0.6 and top-p 0.95, temperature first vs last
first = top_p(z / 0.6, 0.95); last = top_p(z, 0.95) / 0.6
report("T=0.6 first, top-p 0.95", first)
report("top-p 0.95, then T=0.6", last)
p = softmax(last); o = np.argsort(-z)
print("mass outside top 6 when temperature is last:",
      round(float(p[o[6:]][np.isfinite(last[o[6:]])].sum()), 4))
print("plain T=1: P(Paris)", round(float(softmax(z)[PARIS]), 4))
