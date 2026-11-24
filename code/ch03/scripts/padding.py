# padding.py -- what the software does with an ID beyond the tokenizer's
# last one: the vocabulary of the GGUF file, llama-server's /detokenize,
# and the tokenizer of Transformers.
# Usage: python3 padding.py FILE.gguf BASE_URL [TOKENIZER_DIR]
import json, struct, sys, urllib.error, urllib.request

IDS = [151668, 151669, 151700, 151935, 151936]
SCALARS = {0: "<B", 1: "<b", 2: "<H", 3: "<h", 4: "<I", 5: "<i",
           6: "<f", 7: "<?", 10: "<Q", 11: "<q", 12: "<d"}
KINDS = {1: "normal", 2: "unknown", 3: "control", 4: "user defined",
         5: "unused", 6: "byte"}

def get(f, fmt):
    return struct.unpack(fmt, f.read(struct.calcsize(fmt)))[0]

def string(f):
    return f.read(get(f, "<Q")).decode("utf-8")

def value(f, vtype):                     # as in ggufread.py of Chapter 2
    if vtype == 8:
        return string(f)
    if vtype == 9:
        etype, count = get(f, "<I"), get(f, "<Q")
        return [value(f, etype) for _ in range(count)]
    return get(f, SCALARS[vtype])

with open(sys.argv[1], "rb") as f:
    assert f.read(4) == b"GGUF" and get(f, "<I") == 3
    n_tensors, n_kv = get(f, "<Q"), get(f, "<Q")
    meta = {}
    for _ in range(n_kv):
        key = string(f)
        meta[key] = value(f, get(f, "<I"))
tokens = meta["tokenizer.ggml.tokens"]
kinds = meta["tokenizer.ggml.token_type"]
print(f"GGUF vocabulary: {len(tokens)} tokens")
for i in IDS:
    if i < len(tokens):
        print(f"  {i} {tokens[i]!r} ({KINDS[kinds[i]]})")
unused = [i for i, k in enumerate(kinds) if KINDS[k] == "unused"]
print(f"  unused: {len(unused)} tokens, IDs {unused[0]} to {unused[-1]}")

print("llama-server /detokenize")
for i in IDS:
    req = urllib.request.Request(sys.argv[2] + "/detokenize",
                                 json.dumps({"tokens": [i]}).encode(),
                                 {"Content-Type": "application/json"})
    try:
        print(f"  {i} {json.load(urllib.request.urlopen(req))}")
    except urllib.error.HTTPError as e:
        print(f"  {i} status {e.code} {e.read().decode()}")

if len(sys.argv) > 3:
    import transformers
    tok = transformers.AutoTokenizer.from_pretrained(sys.argv[3])
    print(f"Transformers {transformers.__version__}: {len(tok)} tokens")
    for i in IDS:
        print(f"  {i} {tok.decode([i])!r} {tok.convert_ids_to_tokens(i)!r}")
    print(f"  {tok.decode([9707, 151700, 1879])!r}")
