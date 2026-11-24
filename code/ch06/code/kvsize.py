# kvsize.py CFGDIR -- the KV-cache sizes of tab:ch6-sizes and the curves of
# figures/ch06-memory.tex, computed from the config.json files saved in
# CFGDIR (code/ch06/cfg). All sizes are for one sequence, 16-bit cache.
import json, os, sys

d = sys.argv[1]
KiB, MiB, GiB = 1024, 1024**2, 1024**3

def cfg(name):
    c = json.load(open(os.path.join(d, name)))
    return c.get("text_config", c)

def std(name, window=None, pattern=None, layer_types=None, all_local=False):
    """A model with ordinary keys and values; `loc` of its layers keep
    only a window of positions."""
    c = cfg(name)
    L, kv = c["num_hidden_layers"], c["num_key_value_heads"]
    hd = c.get("head_dim") or c["hidden_size"] // c["num_attention_heads"]
    per_layer = 2 * kv * hd * 2          # K and V, 2 bytes per number
    if all_local:
        loc = L
    elif layer_types:
        loc = sum(t == "sliding_attention" for t in layer_types)
    elif pattern:
        loc = sum(1 for i in range(L) if (i + 1) % pattern)
    else:
        loc = 0
    glob = L - loc
    def mem(n_tok):
        w = min(n_tok, window) if window else n_tok
        return per_layer * (glob * n_tok + loc * w)
    return dict(L=L, kv=kv, hd=hd, per_layer=per_layer, loc=loc, glob=glob,
                full_per_tok=per_layer * L, mem=mem)

models = {}
models["Llama 3.1 8B"] = std("unsloth_Meta-Llama-3.1-8B-Instruct.json")
models["Llama 3.1 70B"] = std("unsloth_Meta-Llama-3.1-70B-Instruct.json")
models["Qwen3-0.6B"] = std("Qwen_Qwen3-0.6B.json")
models["Qwen3-8B"] = std("Qwen_Qwen3-8B.json")
models["Qwen3-32B"] = std("Qwen_Qwen3-32B.json")
g = cfg("unsloth_gemma-3-27b-it.json")
models["Gemma 3 27B"] = std("unsloth_gemma-3-27b-it.json",
                            window=g["sliding_window"],
                            pattern=g["sliding_window_pattern"])
o = cfg("openai_gpt-oss-20b.json")
models["gpt-oss-20b"] = std("openai_gpt-oss-20b.json",
                            window=o["sliding_window"],
                            layer_types=o["layer_types"])
m = cfg("mistralai_Mistral-7B-v0.1.json")
models["Mistral 7B v0.1"] = std("mistralai_Mistral-7B-v0.1.json",
                                window=m["sliding_window"], all_local=True)

ds = cfg("deepseek-ai_DeepSeek-V3.json")                # latent attention
L = ds["num_hidden_layers"]
mla_layer = (ds["kv_lora_rank"] + ds["qk_rope_head_dim"]) * 2
mha_layer = ds["num_attention_heads"] * 2 * (
    ds["qk_nope_head_dim"] + ds["qk_rope_head_dim"] + ds["v_head_dim"])
models["DeepSeek-V3 (MLA)"] = dict(
    L=L, per_layer=mla_layer, full_per_tok=mla_layer * L, loc=0, glob=L,
    mem=lambda n: mla_layer * L * n)
print("DeepSeek-V3 MHA-equivalent per token:", mha_layer * L, "B =",
      mha_layer * L / MiB, "MiB; MLA", mla_layer * L, "B =",
      mla_layer * L / KiB, "KiB; ratio", mha_layer / mla_layer)

for k, v in models.items():                             # the table
    print(f"{k:20s} L={v['L']:3d} loc={v['loc']:2d} glob={v['glob']:2d} "
          f"per_layer={v['per_layer']:5d}B "
          f"full/tok={v['full_per_tok'] / KiB:7.1f}KiB  "
          f"4k={v['mem'](4096) / GiB:6.3f}  "
          f"32k={v['mem'](32768) / GiB:7.3f}  "
          f"128k={v['mem'](131072) / GiB:7.3f} GiB")

pts = [2**k for k in range(10, 18)]                     # the figure
for k in ["Llama 3.1 70B", "Llama 3.1 8B", "Gemma 3 27B",
          "DeepSeek-V3 (MLA)", "gpt-oss-20b"]:
    mem = models[k]["mem"]
    print(k, " ".join(f"({n},{mem(n) / GiB:.4g})" for n in pts))
print("gemma no SWA 128k",
      models["Gemma 3 27B"]["full_per_tok"] * 131072 / GiB)
