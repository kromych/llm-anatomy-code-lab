# spectest.py URL [REPLIES] -- drafted and accepted tokens of llama-server
# with a draft model, for a request that edits code and for one that asks
# for prose. URL is the base of the seam, e.g. http://127.0.0.1:8080/v1;
# the replies are appended to the file REPLIES as JSON lines.
import json, sys, urllib.request

URL = sys.argv[1] + "/chat/completions"
CODE = '''def mean(values):
    total = 0
    for v in values:
        total += v
    return total / len(values)

def variance(values):
    m = mean(values)
    total = 0
    for v in values:
        total += (v - m) ** 2
    return total / len(values)
'''
PROMPTS = {
    "edit": "Rename the parameter `values` to `xs` everywhere in this "
            "file and return the whole file without comment.\n\n" + CODE,
    "prose": "Explain in about 150 words why the sea is salty."}

for label, prompt in PROMPTS.items():
    body = {"max_tokens": 400, "temperature": 0,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        reply = json.load(resp)
    if len(sys.argv) > 2:
        with open(sys.argv[2], "a") as f:
            f.write(json.dumps({"request": label, "reply": reply}) + "\n")
    t = reply["timings"]
    d, a = t.get("draft_n", 0), t.get("draft_n_accepted", 0)
    print(f"{label:5s} generated {t['predicted_n']:4d}   drafted {d:4d}   "
          f"accepted {a:4d}" + (f"   ({100 * a / d:.0f}%)" if d else ""))
