# mask.py -- constrained greedy decoding with Qwen3-0.6B (MLX) and a finite
# JSON language; records the size of the allowed set at every step.
import itertools, json, sys
import mlx.core as mx
import numpy as np
from mlx_lm import load

model_dir = sys.argv[1]
model, tok = load(model_dir)
hf = tok._tokenizer  # transformers tokenizer

# The language: {"unit": "celsius"} with an optional space at four places.
sp = ["", " "]
words = ["celsius", "fahrenheit"]
LANG = set()
for a, b, c, d in itertools.product(sp, sp, sp, sp):
    for w in words:
        LANG.add('{' + a + '"unit"' + b + ':' + c + '"' + w + '"' + d + '}')
PREFIXES = {s[:i] for s in LANG for i in range(len(s) + 1)}

# Decoded text of every token (byte-level BPE; skip special tokens).
special = set(hf.all_special_ids)
vocab = model.args.vocab_size if hasattr(model, "args") else len(hf)
text_of = {}
for i in range(len(hf)):
    if i in special:
        continue
    t = hf.decode([i])
    if "�" in t:          # partial UTF-8 sequence: never valid here
        continue
    text_of[i] = t
eos = hf.convert_tokens_to_ids("<|im_end|>")

def allowed(prefix):
    ok = [i for i, t in text_of.items() if prefix + t in PREFIXES]
    if prefix in LANG:
        ok.append(eos)
    return ok

msgs = [{"role": "user", "content":
         "Which temperature unit is used in Norway? Answer in JSON."}]
ids = hf.apply_chat_template(msgs, add_generation_prompt=True,
                             enable_thinking=False, tokenize=True)
ids = list(ids["input_ids"] if hasattr(ids, "keys") else ids)
out, steps = "", []
for step in range(12):
    logits = np.array(model(mx.array([ids]))[0, -1].astype(mx.float32))
    order = np.argsort(-logits)[:8]
    ok = allowed(out)
    okset = set(ok)
    best = max(ok, key=lambda i: logits[i])
    steps.append({"step": step, "prefix": out, "n_allowed": len(ok),
                  "top": [(hf.decode([int(i)]), float(logits[i]),
                           int(i) in okset) for i in order],
                  "chosen": hf.decode([best]), "chosen_logit":
                  float(logits[best]),
                  "allowed": sorted(((hf.decode([i]), float(logits[i]))
                                     for i in ok), key=lambda x: -x[1])})
    if best == eos:
        break
    ids.append(best)
    out += text_of[best]
mean_bytes = round(sum(len(t.encode("utf-8")) for t in text_of.values())
                   / len(text_of), 2)
print(json.dumps({"vocab_rows": int(vocab), "tokenizer_len": len(hf),
                  "candidates": len(text_of), "mean_bytes": mean_bytes,
                  "output": out, "steps": steps},
                 indent=1, ensure_ascii=True))
