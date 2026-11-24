# overflow.py -- what a server answers at its limits: replies cut off by
# max_tokens in the middle of a tool call, and a prompt beyond the window.
# Usage: python3 overflow.py [BASE]   (run it next to the workspace ws)
import json, sys, urllib.error, urllib.request
import agent

def post(base, body):
    req = urllib.request.Request(base + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:          # the body says why
        return e.code, json.load(e)

if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else agent.BASE
    body = {"model": agent.MODEL, "temperature": 0, "seed": 1,
            "tools": [schema for _, schema in agent.TOOLS.values()],
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "system", "content": agent.SYSTEM},
                         {"role": "user", "content":
                          "What does docs/formats.md say about GGUF?"}]}
    for limit in (8, 20, 64):                    # the call needs 23 tokens
        status, reply = post(base, dict(body, max_tokens=limit))
        choice = reply["choices"][0]
        for c in choice["message"].get("tool_calls") or []:
            c["id"] = "..."                      # random, new in each run
        print(f"max_tokens {limit}: {choice['finish_reason']}",
              json.dumps(choice["message"]))
    body["messages"].append({"role": "user",
                             "content": "lorem ipsum dolor " * 20000})
    status, reply = post(base, body)
    print("long prompt:", status, json.dumps(
        reply.get("error") or reply.get("usage")))
