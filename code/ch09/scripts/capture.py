# capture.py -- record a streamed tool call with arrival times, and the same
# request in three dialects, from one llama-server.
import json, sys, time, urllib.request
sys.path.insert(0, sys.argv[2])
from stream import sse_events

BASE = sys.argv[1]
TOOL = {"name": "get_weather", "description": "Current weather in a city",
        "schema": {"type": "object", "required": ["city"],
                   "properties": {"city": {"type": "string"}}}}
Q = "What is the weather in Oslo? Answer briefly first, then use the tool."

def post(path, body, stream=False):
    req = urllib.request.Request(BASE + path, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=600)

# 1. timeline of a streamed Chat Completions tool call
body = {"model": "q", "temperature": 0, "max_tokens": 600, "stream": True,
        "stream_options": {"include_usage": True},
        "chat_template_kwargs": {"enable_thinking": False},
        "messages": [{"role": "user", "content": Q}],
        "tools": [{"type": "function", "function": {
            "name": TOOL["name"], "description": TOOL["description"],
            "parameters": TOOL["schema"]}}]}
t0 = time.perf_counter()
events = []
with post("/chat/completions", body) as resp:
    for d in sse_events(resp):
        events.append((time.perf_counter() - t0, d))
timeline = []
for t, d in events:
    if d == "[DONE]":
        timeline.append([round(t * 1000, 1), "done", ""]); continue
    c = json.loads(d)
    if not c.get("choices"):
        timeline.append([round(t * 1000, 1), "usage", json.dumps(c.get("usage"))]); continue
    ch = c["choices"][0]; delta = ch.get("delta", {})
    for tc in delta.get("tool_calls") or []:
        f = tc.get("function") or {}
        timeline.append([round(t * 1000, 1), "tool", json.dumps({"index": tc.get("index"), "id": tc.get("id"), "name": f.get("name"), "arguments": f.get("arguments")})])
    if delta.get("content"):
        timeline.append([round(t * 1000, 1), "content", delta["content"]])
    if delta.get("role") and not delta.get("content") and not delta.get("tool_calls"):
        timeline.append([round(t * 1000, 1), "role", delta["role"]])
    if ch.get("finish_reason"):
        timeline.append([round(t * 1000, 1), "finish", ch["finish_reason"]])

# 2. the same request in three dialects, non-streaming
out = {"timeline": timeline}
b = dict(body, stream=False); b.pop("stream_options")
with post("/chat/completions", b) as r:
    out["chat"] = json.load(r)["choices"][0]
with post("/responses", {"model": "q", "temperature": 0,
        "max_output_tokens": 600, "input": Q,
        "extra_params": {"chat_template_kwargs": {"enable_thinking": False}},
        "tools": [{"type": "function", "name": TOOL["name"],
                   "description": TOOL["description"],
                   "parameters": TOOL["schema"], "strict": False}]}) as r:
    out["responses"] = json.load(r).get("output")
with post("/messages", {"model": "q", "max_tokens": 600,
        "temperature": 0, "messages": [{"role": "user", "content": Q}],
        "extra_params": {"chat_template_kwargs": {"enable_thinking": False}},
        "tools": [{"name": TOOL["name"], "description": TOOL["description"],
                   "input_schema": TOOL["schema"]}]}) as r:
    m = json.load(r)
    out["messages"] = {"content": m.get("content"),
                       "stop_reason": m.get("stop_reason")}
print(json.dumps(out, indent=1))
