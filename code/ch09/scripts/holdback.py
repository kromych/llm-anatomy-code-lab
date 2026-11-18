# holdback.py -- which generated token produced which delta of a streamed
# tool call.  llama-server reports the number of tokens generated so far
# in every chunk when the request sets "timings_per_token".
# Usage: python3 holdback.py BASE_URL   (standard library only)
import json, sys, urllib.request
from stream import sse_events

Q = "What is the weather in Oslo? Answer briefly first, then use the tool."
TOOL = {"type": "function", "function": {
    "name": "get_weather", "description": "Current weather in a city",
    "parameters": {"type": "object", "required": ["city"],
                   "properties": {"city": {"type": "string"}}}}}
body = {"model": "q", "temperature": 0, "max_tokens": 600, "stream": True,
        "stream_options": {"include_usage": True},
        "timings_per_token": True, "tools": [TOOL],
        "chat_template_kwargs": {"enable_thinking": False},
        "messages": [{"role": "user", "content": Q}]}
req = urllib.request.Request(sys.argv[1] + "/chat/completions",
                             json.dumps(body).encode(),
                             {"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=300) as resp:
    for d in sse_events(resp):
        if d == "[DONE]":
            break
        c = json.loads(d)
        n = (c.get("timings") or {}).get("predicted_n", "-")
        for ch in c.get("choices") or []:
            delta = ch.get("delta", {})
            for tc in delta.get("tool_calls") or []:
                f = tc.get("function") or {}
                print(n, "tool", f.get("name") or "", repr(f.get("arguments")))
            if delta.get("content"):
                print(n, "content", repr(delta["content"]))
            if ch.get("finish_reason"):
                print(n, "finish", ch["finish_reason"])
        if c.get("usage"):
            print(n, "usage", c["usage"]["completion_tokens"], "tokens")
