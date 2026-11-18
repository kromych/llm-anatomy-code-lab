"""empty_probe.py: where does the tool call go when Ollama returns nothing?

  python3 empty_probe.py N NAME [NAME ...]
Sends N requests to Ollama's /api/chat (qwen3:1.7b, the calculator's tool
under each NAME, question c02 or $PROBE_QUESTION) and reports for each reply whether it had a
tool call, text, and whether its thinking contains a written-out call.
"""
import json, sys, urllib.error, urllib.request
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from calc_server import TOOLS

import os
QUESTION = os.environ.get("PROBE_QUESTION") or json.load(open(
    __file__.rsplit("/", 1)[0] + "/questions.json"))[1]["question"]

def ask(name):
    t = TOOLS[0]
    tool = {"type": "function", "function": {
        "name": name, "description": t["description"],
        "parameters": t["inputSchema"]}}
    body = {"model": "qwen3:1.7b", "stream": False, "tools": [tool],
            "messages": [{"role": "user", "content": QUESTION}],
            "options": {"num_predict": 4096}}
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)

if __name__ == "__main__":
    n, names = int(sys.argv[1]), sys.argv[2:]
    for name in names:
        tally = {"call": 0, "text": 0, "empty": 0, "call in thinking": 0}
        for _ in range(n):
            try:
                r = ask(name)
            except urllib.error.HTTPError as e:
                tally["error"] = tally.get("error", 0) + 1
                print(name, "HTTP", e.code, e.read()[:200], flush=True)
                continue
            m = r["message"]
            think = m.get("thinking") or ""
            hidden = "<tool_call>" in think or '"name": "%s"' % name in think
            if m.get("tool_calls"):
                tally["call"] += 1
            elif (m.get("content") or "").strip():
                tally["text"] += 1
            else:
                tally["empty"] += 1
                tally["call in thinking"] += hidden
            print(name, r.get("done_reason"), bool(m.get("tool_calls")),
                  len(m.get("content") or ""), len(think), hidden,
                  repr(think[-160:]) if hidden else "", flush=True)
        print("==", name, tally, flush=True)
