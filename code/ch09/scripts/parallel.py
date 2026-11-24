# parallel.py -- does a server return two tool calls in one response?
# Usage: python3 parallel.py BASE_URL MODEL [RUNS] (standard library only)
import json, sys, urllib.request

BASE, MODEL = sys.argv[1], sys.argv[2]
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 5
TOOL = {"type": "function", "function": {
    "name": "get_weather", "description": "Current weather in a city",
    "parameters": {"type": "object", "required": ["city"],
                   "properties": {"city": {"type": "string"}}}}}
MSGS = [{"role": "system", "content": "Use the tools to answer."},
        {"role": "user", "content": "What is the weather in Oslo and Lima?"}]

def calls(extra, seed):
    body = dict({"model": MODEL, "messages": MSGS, "tools": [TOOL],
                 "temperature": 0.7, "seed": seed, "max_tokens": 2000},
                **extra)
    req = urllib.request.Request(BASE + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    msg = json.load(urllib.request.urlopen(req, timeout=600))[
        "choices"][0]["message"]
    return [json.loads(c["function"]["arguments"]).get("city")
            for c in msg.get("tool_calls") or []]

for label, extra in [("field absent", {}),
                     ("parallel_tool_calls: true",
                      {"parallel_tool_calls": True}),
                     ("parallel_tool_calls: false",
                      {"parallel_tool_calls": False})]:
    results = [calls(extra, seed) for seed in range(1, RUNS + 1)]
    print("%-28s %s" % (label, results))
