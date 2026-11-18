# cached.py MODEL_DIR SCRIPTS -- forward.py with a KV cache, timed
import sys, json, time
import numpy as np
sys.path.insert(0, sys.argv[2])
import forward as F

def layer_cached(h, W, p, cfg, pos, cache):
    nh, nkv = cfg["num_attention_heads"], cfg["num_key_value_heads"]
    n, hd, eps = h.shape[0], h.shape[1] // nh, cfg["rms_norm_eps"]
    lin = lambda x, w: x @ W[p + w + ".weight"].T
    x = F.rmsnorm(h, W[p + "input_layernorm.weight"], eps)
    q = lin(x, "self_attn.q_proj").reshape(n, nh, hd).transpose(1, 0, 2)
    k = lin(x, "self_attn.k_proj").reshape(n, nkv, hd).transpose(1, 0, 2)
    v = lin(x, "self_attn.v_proj").reshape(n, nkv, hd).transpose(1, 0, 2)
    theta = cfg["rope_theta"]
    q, k = F.rope(q, pos, theta), F.rope(k, pos, theta)
    if p in cache:                                   # F4: append
        k = np.concatenate([cache[p][0], k], 1)
        v = np.concatenate([cache[p][1], v], 1)
    cache[p] = (k, v)
    t = k.shape[1]
    k, v = np.repeat(k, nh // nkv, 0), np.repeat(v, nh // nkv, 0)
    s = q @ k.transpose(0, 2, 1) / hd ** 0.5         # [nh, n, t]
    s = s + np.triu(np.full((n, t), -np.inf, np.float32), t - n + 1)
    a = np.exp(s - s.max(-1, keepdims=True))
    a = a / a.sum(-1, keepdims=True)
    o = (a @ v).transpose(1, 0, 2).reshape(n, nh * hd)
    h = h + lin(o, "self_attn.o_proj")
    x = F.rmsnorm(h, W[p + "post_attention_layernorm.weight"], eps)
    g, u = lin(x, "mlp.gate_proj"), lin(x, "mlp.up_proj")
    return h + lin(g / (1 + np.exp(-g)) * u, "mlp.down_proj")

def step(ids, start, W, cfg, cache):
    h = W["model.embed_tokens.weight"][ids]
    pos = np.arange(start, start + len(ids), dtype=np.float32)
    for i in range(cfg["num_hidden_layers"]):
        h = layer_cached(h, W, f"model.layers.{i}.", cfg, pos, cache)
    h = F.rmsnorm(h[-1], W["model.norm.weight"], cfg["rms_norm_eps"])
    return h @ W["model.embed_tokens.weight"].T

d = sys.argv[1]
cfg = json.load(open(d + "/config.json"))
W = F.load(d + "/model.safetensors")
prompt = [504, 3575, 282, 4649, 314]; N = 64
t0 = time.time(); ids = list(prompt)
for _ in range(N):
    ids.append(int(np.argmax(F.logits(np.array(ids), W, cfg))))
t_nocache = time.time() - t0
t0 = time.time(); cache = {}; seq = list(prompt)
z = step(np.array(seq), 0, W, cfg, cache)
for _ in range(N):
    seq.append(int(np.argmax(z)))
    z = step(np.array(seq[-1:]), len(seq) - 1, W, cfg, cache)
t_cache = time.time() - t0
print("same tokens:", ids == seq)
print(f"no cache {t_nocache:.2f} s, cache {t_cache:.2f} s, "
      f"speed-up {t_nocache / t_cache:.1f}")

def best(f, repeats=5):                  # the last step by itself
    times = []
    for _ in range(repeats):
        t0 = time.time(); f(); times.append(time.time() - t0)
    return min(times)

c = {}; step(np.array(ids[:-1]), 0, W, cfg, c)
t_all = best(lambda: F.logits(np.array(ids), W, cfg))
t_one = best(lambda: step(np.array(ids[-1:]), len(ids) - 1, W, cfg,
                          dict(c)))
print(f"last step: {len(ids)} rows {1000 * t_all:.0f} ms, one row "
      f"{1000 * t_one:.0f} ms, ratio {t_all / t_one:.1f}")
