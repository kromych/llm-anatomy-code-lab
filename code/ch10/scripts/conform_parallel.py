# conform_parallel.py -- conform.py with a check for parallel tool calls.
# Usage: python3 conform_parallel.py BASE_URL MODEL
import json
from conform import post, ask_tools, assemble, WEATHER  # runs its checks

QUESTION = "What is the weather in Oslo and in Lima?"

def t_tool_parallel(extra, want):
    code, events = post(dict({"messages": ask_tools(QUESTION),
                              "tools": [WEATHER], "stream": True,
                              "max_tokens": 800}, **extra), True)
    assert code == 200, events
    chunks = [json.loads(e) for e in events if e != "[DONE]"]
    msg, finish, usage = assemble(chunks)   # one entry for each index
    calls = msg.get("tool_calls") or []
    cities = [json.loads(c["function"]["arguments"]).get("city")
              for c in calls]
    assert len(calls) == want, "%d calls, for %s" % (len(calls), cities)
    assert len({c["id"] for c in calls}) == want, "identifiers repeat"
    assert len(set(cities) & {"Oslo", "Lima"}) == want, cities
    assert finish == "tool_calls", finish

for extra, want in [({}, 2), ({"parallel_tool_calls": True}, 2),
                    ({"parallel_tool_calls": False}, 1)]:
    try:
        t_tool_parallel(extra, want)
        print("PASS ", "t_tool_parallel", extra, "calls:", want)
    except Exception as e:
        print("FAIL ", "t_tool_parallel", extra, "--",
              type(e).__name__, str(e)[:120])
