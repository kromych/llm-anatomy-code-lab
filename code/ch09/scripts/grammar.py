# grammar.py -- send the GBNF grammar of unit.gbnf with a request to
# llama-server, with Qwen3's thinking off and on.
# Usage: python3 grammar.py BASE_URL   (standard library only)
import json, os, sys, urllib.request

G = open(os.path.join(os.path.dirname(__file__), "unit.gbnf")).read()
Q = "Which temperature unit is used in Norway? Answer in JSON."
for think in (False, True):
    body = {"messages": [{"role": "user", "content": Q}], "grammar": G,
            "temperature": 0, "max_tokens": 50,
            "chat_template_kwargs": {"enable_thinking": think}}
    req = urllib.request.Request(sys.argv[1] + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    msg = json.load(urllib.request.urlopen(req, timeout=120))[
        "choices"][0]["message"]
    print("thinking %-5s content %r reasoning %r" % (
        think, msg.get("content"), msg.get("reasoning_content") or ""))
