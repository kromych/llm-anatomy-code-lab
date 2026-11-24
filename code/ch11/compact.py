# compact.py -- Algorithm Z: elide old tool output when the context grows.
import json, urllib.request
from tools import TOOLS

def post(base, path, body):
    req = urllib.request.Request(base.removesuffix("/v1") + path,
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)

def count(messages, base):                       # exact, via the template
    prompt = post(base, "/apply-template", {
        "messages": messages,
        "tools": [schema for _, schema in TOOLS.values()],
        "chat_template_kwargs": {"enable_thinking": False}})["prompt"]
    return len(post(base, "/tokenize", {"content": prompt,
                                         "parse_special": True})["tokens"])

def compact(messages, base, high=3000, low=1800):
    n = count(messages, base)                    # step Z1
    if n <= high:
        return n, 0
    last_user = max(i for i, m in enumerate(messages)
                    if m["role"] == "user")      # step Z2
    names = {c["id"]: c["function"]["name"]
             for m in messages for c in m.get("tool_calls", [])}
    elided = 0
    for i in range(1, last_user):                # step Z3, oldest first
        m = messages[i]
        if m["role"] != "tool" or m["content"].startswith("[elided"):
            continue
        name = names.get(m["tool_call_id"], "a tool")
        m["content"] = (f"[elided: {len(m['content'])} characters from "
                        f"{name}; call it again if needed]")
        elided += 1
        n = count(messages, base)                # step Z4
        if n <= low:
            break
    return n, elided                             # step Z5: the caller
                                                 # summarizes if n > high
