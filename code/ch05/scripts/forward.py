# forward.py -- a Llama-style forward pass in NumPy (Algorithm F)
import json, struct, sys
import numpy as np

def load(path):                          # safetensors, BF16 -> float32
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        head, base = json.loads(f.read(n)), 8 + n
    raw = np.memmap(path, dtype=np.uint8, mode="r")
    W = {}
    for name, t in head.items():
        if name == "__metadata__":
            continue
        a, b = t["data_offsets"]
        u = raw[base + a : base + b].view(np.uint16).astype(np.uint32)
        W[name] = (u << 16).view(np.float32).reshape(t["shape"])
    return W

def rmsnorm(x, w, eps):
    return x / np.sqrt((x * x).mean(-1, keepdims=True) + eps) * w

def rope(x, pos, theta):                 # x: [heads, n, hd], halves
    hd = x.shape[-1]
    f = theta ** (-np.arange(0, hd, 2, dtype=np.float32) / hd)
    ang = pos[:, None] * f
    c, s = np.cos(ang), np.sin(ang)
    x1, x2 = x[..., : hd // 2], x[..., hd // 2 :]
    return np.concatenate([x1 * c - x2 * s, x2 * c + x1 * s], -1)

def layer(h, W, p, cfg, pos):            # steps F1-F7
    nh, nkv = cfg["num_attention_heads"], cfg["num_key_value_heads"]
    n, hd, eps = h.shape[0], h.shape[1] // nh, cfg["rms_norm_eps"]
    lin = lambda x, w: x @ W[p + w + ".weight"].T
    x = rmsnorm(h, W[p + "input_layernorm.weight"], eps)
    q = lin(x, "self_attn.q_proj").reshape(n, nh, hd).transpose(1, 0, 2)
    k = lin(x, "self_attn.k_proj").reshape(n, nkv, hd).transpose(1, 0, 2)
    v = lin(x, "self_attn.v_proj").reshape(n, nkv, hd).transpose(1, 0, 2)
    q, k = rope(q, pos, cfg["rope_theta"]), rope(k, pos, cfg["rope_theta"])
    k, v = np.repeat(k, nh // nkv, 0), np.repeat(v, nh // nkv, 0)
    s = q @ k.transpose(0, 2, 1) / hd ** 0.5         # [nh, n, n]
    s = s + np.triu(np.full((n, n), -np.inf, np.float32), 1)  # mask
    a = np.exp(s - s.max(-1, keepdims=True))
    a = a / a.sum(-1, keepdims=True)
    o = (a @ v).transpose(1, 0, 2).reshape(n, nh * hd)
    h = h + lin(o, "self_attn.o_proj")
    x = rmsnorm(h, W[p + "post_attention_layernorm.weight"], eps)
    g, u = lin(x, "mlp.gate_proj"), lin(x, "mlp.up_proj")
    return h + lin(g / (1 + np.exp(-g)) * u, "mlp.down_proj")

def logits(ids, W, cfg):
    h = W["model.embed_tokens.weight"][ids]
    pos = np.arange(len(ids), dtype=np.float32)
    for i in range(cfg["num_hidden_layers"]):
        h = layer(h, W, f"model.layers.{i}.", cfg, pos)
    h = rmsnorm(h[-1], W["model.norm.weight"], cfg["rms_norm_eps"])
    return h @ W["model.embed_tokens.weight"].T      # tied LM head

if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1] + "/config.json"))
    W = load(sys.argv[1] + "/model.safetensors")
    ids = [int(t) for t in sys.argv[2:]]
    for _ in range(8):                                # greedy decoding
        ids.append(int(np.argmax(logits(np.array(ids), W, cfg))))
    print(ids)
