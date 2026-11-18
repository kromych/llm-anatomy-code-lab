# cachetail.py SERVER -- the tokens of the two prompts of cachetest.py
# behind their common prefix, from llama-server's /apply-template and
# /tokenize. SERVER is the server's address, e.g. http://127.0.0.1:8080.
import json, sys, urllib.request

def post(path, body):
    req = urllib.request.Request(sys.argv[1] + path,
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)

doc = " ".join(f"Item {i} costs {i * 7 % 100} euros." for i in range(800))
prompts = []
for question in ("Which item costs 42 euros?", "Which costs 13 euros?"):
    text = post("/apply-template", {"messages": [
        {"role": "system", "content": "Answer from this list: " + doc},
        {"role": "user", "content": question}]})["prompt"]
    prompts.append(post("/tokenize", {"content": text, "add_special": True,
        "parse_special": True, "with_pieces": True})["tokens"])
a, b = prompts
n = 0
while a[n]["id"] == b[n]["id"]:
    n += 1
print(f"{len(a)} and {len(b)} tokens, the first {n} in common")
for p in prompts:
    print(len(p) - n, [t["piece"] for t in p[n:]])
