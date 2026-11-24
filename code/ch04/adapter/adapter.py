# adapter.py MODEL_DIR ADAPTER_DIR [BASE_URL] -- the adapter of
# train_lora.py in the forward pass of Chapter 5: the next token with and
# without it, and the two ways in which it can meet Q4_0. With BASE_URL,
# asks a llama-server started with --lora for its own three best tokens.
import json, os, struct, sys, urllib.request
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("..", "../../ch05/scripts", "../../ch03/scripts"):
    sys.path.insert(0, os.path.join(HERE, d))
import forward as F, bpe, quant
from capitals import CAPITALS

model, adapter = sys.argv[1], sys.argv[2]
cfg = json.load(open(model + "/config.json"))
W = F.load(model + "/model.safetensors")
vocab, ranks = bpe.load(model + "/tokenizer.json")
word = {i: t.replace("Ġ", " ") for t, i in vocab.items()}
config = json.load(open(adapter + "/adapter_config.json"))
scale = config["lora_alpha"] / config["r"]

with open(adapter + "/adapter_model.safetensors", "rb") as f:
    (n,) = struct.unpack("<Q", f.read(8))
    header, raw = json.loads(f.read(n)), f.read()
delta = {}                               # name of W -> scale * B A
for name, t in header.items():
    if name.endswith("lora_A.weight"):
        def matrix(key):
            a, b = header[key]["data_offsets"]
            return np.frombuffer(raw[a:b], np.float32).reshape(
                header[key]["shape"])
        target = name[len("base_model.model."):].replace(".lora_A", "")
        delta[target] = scale * (matrix(name.replace("lora_A", "lora_B"))
                                 @ matrix(name))

def q4_0(w):                             # Algorithm Q as ggml's Q4_0 has it
    x = w.reshape(-1, 32)
    big = np.take_along_axis(x, np.abs(x).argmax(1)[:, None], 1)
    d = (big / -8).astype(np.float32)
    inv = np.divide(1, d, out=np.zeros_like(d), where=d != 0)
    q = np.minimum(15, (x * inv + np.float32(8.5)).astype(np.int8))
    return ((q - 8) * d.astype(np.float16).astype(np.float32)).reshape(
        w.shape)

block = W["model.layers.0.mlp.down_proj.weight"].reshape(-1)[:32]
assert np.allclose(q4_0(block), quant.dequantize_q4_0(
    quant.quantize_q4_0([float(v) for v in block])))   # as quant.py does

def weights(quantize, merge):
    """The matrices of the layers under one arrangement: the adapter
    merged before the quantizer, or added after it."""
    out = dict(W)
    for name, w in W.items():
        if w.ndim == 2 and ".layers." in name:
            d = delta.get(name, 0)
            out[name] = (quantize(w + d) if merge else quantize(w) + d)
    return out

def probs(weights, ids):
    z = F.logits(np.array(ids), weights, cfg).astype(np.float64)
    p = np.exp(z - z.max())
    return p / p.sum()

def best(p, k=3):
    return "  ".join(f"{word[i]!r} {p[i]:.3f}" for i in np.argsort(-p)[:k])

same = lambda w: w
ids = bpe.encode("The capital of France is", vocab, ranks)
print(f"{len(delta)} matrices adapted, scale {scale:g}; tokens {ids}")
print("  without the adapter ", best(probs(W, ids)))
print("  with the adapter    ", best(probs(weights(same, True), ids)))
if len(sys.argv) > 3:
    body = {"prompt": ids, "n_predict": 1, "n_probs": 3, "temperature": 0}
    req = urllib.request.Request(sys.argv[3] + "/completion",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    tops = json.load(urllib.request.urlopen(req))[
        "completion_probabilities"][0]["top_logprobs"]
    print("  llama-server, --lora ", "  ".join(
        f"{t['token']!r} {np.exp(t['logprob']):.3f}" for t in tops))

print(f"Q4_0 and the adapter, on all {len(CAPITALS)} countries:")
exact = weights(same, True)
for label, w in (("no quantization", exact),
                 ("merged, then quantized", weights(q4_0, True)),
                 ("quantized, then added", weights(q4_0, False)),
                 ("quantized, no adapter", {**weights(q4_0, False), **{
                     k: q4_0(W[k]) for k in delta}})):
    kl, right, p_city = 0.0, 0, 0.0
    for country, city in CAPITALS.items():
        ids = bpe.encode(f"The capital of {country} is", vocab, ranks)
        first = bpe.encode(" " + city, vocab, ranks)[0]
        p, ref = probs(w, ids), probs(exact, ids)
        kl += float(np.sum(ref * np.log(ref / p))) / len(CAPITALS)
        right += int(np.argmax(p) == first)
        p_city += p[first] / len(CAPITALS)
    print(f"  {label:23} divergence {kl:.4f}  right {right:2}  "
          f"mean p {p_city:.3f}")
