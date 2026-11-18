# unanswered.py -- does a server accept a conversation in which a tool call
# has no answering tool message?
# Usage: python3 unanswered.py BASE_URL MODEL
import json, sys, urllib.request, urllib.error

BASE, MODEL = sys.argv[1], sys.argv[2]
TOOL = {"type": "function", "function": {
    "name": "read_file", "description": "Read a file",
    "parameters": {"type": "object", "required": ["path"],
                   "properties": {"path": {"type": "string"}}}}}

def call(i, path):
    return {"id": f"call_{i}", "type": "function", "function": {
        "name": "read_file", "arguments": json.dumps({"path": path})}}

head = [{"role": "user", "content": "Read a.txt and b.txt."},
        {"role": "assistant", "content": "",
         "tool_calls": [call("a", "a.txt"), call("b", "b.txt")]}]
cases = {
    "both answered": head + [
        {"role": "tool", "tool_call_id": "call_a", "content": "alpha"},
        {"role": "tool", "tool_call_id": "call_b", "content": "beta"}],
    "one answered": head + [
        {"role": "tool", "tool_call_id": "call_a", "content": "alpha"}],
    "none answered": head + [{"role": "user", "content": "Go on."}],
}
for name, msgs in cases.items():
    body = {"model": MODEL, "messages": msgs, "tools": [TOOL],
            "max_tokens": 800, "temperature": 0,
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(BASE + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
        m = r["choices"][0]["message"]
        calls = [c["function"]["arguments"]
                 for c in m.get("tool_calls") or []]
        print("%-14s 200 %r %s" % (name, m.get("content") or "",
                                   calls or "no calls"))
    except urllib.error.HTTPError as e:
        print("%-14s %d %s" % (name, e.code, e.read()[:120]))
