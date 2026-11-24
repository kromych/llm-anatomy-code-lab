# toolchoice.py -- what a server does with tool_choice "auto", "required",
# a named function, and parallel calls.
# Usage: python3 toolchoice.py BASE_URL MODEL [MAX_TOKENS [EFFORT [SUFFIX]]]
# (standard library only).  MAX_TOKENS is the budget of each answer, 600
# unless given; EFFORT, for instance none, is sent as reasoning_effort
# unless it is "-"; SUFFIX, for instance " /no_think", is appended to the
# user's message.
import json, sys, urllib.request, urllib.error

BASE, MODEL = sys.argv[1], sys.argv[2]
MAX_TOKENS = int(sys.argv[3]) if len(sys.argv) > 3 else 600
EFFORT = sys.argv[4] if len(sys.argv) > 4 else "-"
SUFFIX = sys.argv[5] if len(sys.argv) > 5 else ""
TOOL = {"type": "function", "function": {
    "name": "get_weather", "description": "Current weather in a city",
    "parameters": {"type": "object", "required": ["city"],
                   "properties": {"city": {"type": "string"}}}}}
SYS = {"role": "system", "content": "Use the tools to answer."}

def ask(text, **extra):
    body = dict({"model": MODEL, "temperature": 0,
                 "max_tokens": MAX_TOKENS, "tools": [TOOL],
                 "messages": [SYS, {"role": "user",
                                    "content": text + SUFFIX}]},
                **extra)
    if EFFORT != "-":
        body["reasoning_effort"] = EFFORT
    req = urllib.request.Request(BASE + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=900))
    except urllib.error.HTTPError as e:
        return "status %d %s" % (e.code, e.read()[:110])
    m = r["choices"][0]["message"]
    calls = [json.loads(c["function"]["arguments"]).get("city")
             for c in m.get("tool_calls") or []]
    return "calls %s, %s after %d tokens, text %r" % (
        calls, r["choices"][0]["finish_reason"],
        r["usage"]["completion_tokens"], (m.get("content") or "")[:36])

cases = [("auto, weather", "What is the weather in Oslo?", {}),
         ("required, Hello!", "Hello!", {"tool_choice": "required"}),
         ("named, Hello!", "Hello!", {"tool_choice": {
             "type": "function", "function": {"name": "get_weather"}}}),
         ("two cities", "What is the weather in Oslo and Lima?", {}),
         ("two cities, parallel false",
          "What is the weather in Oslo and Lima?",
          {"parallel_tool_calls": False})]
for name, text, extra in cases:
    print("%-28s %s" % (name, ask(text, **extra)), flush=True)
