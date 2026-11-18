import json, sys
t = json.load(open(sys.argv[1], encoding="utf-8"))
print("keys:", list(t.keys()))
for k in ("normalizer", "pre_tokenizer", "post_processor", "decoder"):
    print(k, ":", json.dumps(t[k], ensure_ascii=True)[:700])
m = t["model"]
print("model:", {k: (v if not isinstance(v, (dict, list)) else f"<{type(v).__name__} {len(v)}>") for k, v in m.items()})
merges = m.get("merges", [])
print("first merges:", merges[:8])
print("added_tokens:", len(t["added_tokens"]), [ (a["id"], a["content"], a["special"]) for a in t["added_tokens"][:30]])
