# steer.py MODEL_DIR OUT.gguf [BASE_URL] -- a control vector for the model
# of forward.py: one direction for each layer, the mean difference of the
# hidden states that two groups of prompts leave at their last token.
# Writes the directions as a GGUF file for llama.cpp's --control-vector and
# prints what adding them, or projecting them out, does to the next token.
# With BASE_URL, asks a llama-server there for its own three best tokens.
import json, os, struct, sys, urllib.request
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "ch03", "scripts"))
import forward as F, bpe

PLUS = ["I love this movie. It is", "What a wonderful day. I feel",
        "The food was delicious and the service was",
        "She smiled because the news was"]
MINUS = ["I hate this movie. It is", "What a terrible day. I feel",
         "The food was disgusting and the service was",
         "She cried because the news was"]
PROMPT = "The movie was"

d = sys.argv[1]
cfg = json.load(open(d + "/config.json"))
W = F.load(d + "/model.safetensors")
vocab, ranks = bpe.load(d + "/tokenizer.json")
text = {i: t.replace(chr(0x120), " ") for t, i in vocab.items()}
L = cfg["num_hidden_layers"]

def run(ids, steer=None):
    """Algorithm F for all layers, layers counted from 0; steer(i, h)
    may change the hidden states that leave layer i."""
    h = W["model.embed_tokens.weight"][np.array(ids)]
    pos = np.arange(len(ids), dtype=np.float32)
    last = []
    for i in range(L):
        h = F.layer(h, W, f"model.layers.{i}.", cfg, pos)
        if steer:
            h = steer(i, h)
        last.append(h[-1])
    h = F.rmsnorm(h[-1], W["model.norm.weight"], cfg["rms_norm_eps"])
    return h @ W["model.embed_tokens.weight"].T, np.array(last)

def states(prompt):
    return run(bpe.encode(prompt, vocab, ranks))[1]

V = np.mean([states(a) - states(b) for a, b in zip(PLUS, MINUS)], 0)
V = V.astype(np.float32)                 # V[i]: the direction of layer i

def gstr(s):
    return struct.pack("<Q", len(s)) + s.encode()

def write_gguf(path):                    # direction.1, ..., direction.L-1
    kv = [gstr("general.architecture") + struct.pack("<I", 8)
          + gstr("controlvector"),
          gstr("controlvector.model_hint") + struct.pack("<I", 8)
          + gstr("llama"),
          gstr("controlvector.layer_count") + struct.pack("<II", 4, L - 1)]
    size = V.shape[1] * 4                # a multiple of the alignment, 32
    infos = [gstr(f"direction.{i}") + struct.pack("<IQIQ", 1, V.shape[1],
                                                  0, (i - 1) * size)
             for i in range(1, L)]
    head = (b"GGUF" + struct.pack("<IQQ", 3, len(infos), len(kv))
            + b"".join(kv) + b"".join(infos))
    with open(path, "wb") as f:
        f.write(head + b"\0" * (-len(head) % 32) + V[1:].tobytes())

def best(z, k=3):
    p = np.exp(z - z.max())
    p /= p.sum()
    return "  ".join(f"{text[i]!r} {p[i]:.3f}" for i in np.argsort(-p)[:k])

def add(scale):                          # what llama.cpp does: h + v
    return lambda i, h: h + scale * V[i] if i >= 1 else h

def project(alpha):                      # h - alpha (h . d) d, d = v / |v|
    def steer(i, h):
        if i < 1:
            return h
        unit = V[i] / np.linalg.norm(V[i])
        return h - alpha * np.outer(h @ unit, unit)
    return steer

write_gguf(sys.argv[2])
ids = bpe.encode(PROMPT, vocab, ranks)
h = states(PROMPT)
print(f"{sys.argv[2]}: {L - 1} directions of {V.shape[1]} numbers, "
      f"{os.path.getsize(sys.argv[2])} bytes")
print("length of the direction and of the hidden state, by layer:")
for i in (1, 10, 20, 29):
    print(f"  layer {i:2}  {np.linalg.norm(V[i]):6.1f}  "
          f"{np.linalg.norm(h[i]):6.1f}")
unit = V[20] / np.linalg.norm(V[20])
print("component of the state along the direction, layer 20:")
for prompt in (PLUS[0], PROMPT, MINUS[0]):
    print(f"  {states(prompt)[20] @ unit:6.1f}  {prompt!r}")
print(f"the next token after {PROMPT!r}, tokens {ids}:")
for name, steer in [("as it is", None), ("added", add(1.0)),
                    ("subtracted", add(-1.0)),
                    ("projected out", project(1.0))]:
    print(f"  {name:14}", best(run(ids, steer)[0]))
if len(sys.argv) > 3:
    body = {"prompt": ids, "n_predict": 1, "n_probs": 3, "temperature": 0}
    req = urllib.request.Request(sys.argv[3] + "/completion",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    tops = json.load(urllib.request.urlopen(req))[
        "completion_probabilities"][0]["top_logprobs"]
    print("  llama-server  ", "  ".join(
        f"{t['token']!r} {np.exp(t['logprob']):.3f}" for t in tops))
