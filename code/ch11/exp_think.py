import json, sys, agent, evaluate
think = sys.argv[2] == "on"
orig = agent.chat
def chat(messages, base=agent.BASE, timeout=300):
    import urllib.request
    body = {"model": agent.MODEL, "messages": messages,
            "temperature": float(sys.argv[3]), "seed": int(sys.argv[4]),
            "tools": [s for _, s in agent.TOOLS.values()],
            "chat_template_kwargs": {"enable_thinking": think}}
    req = urllib.request.Request(base + "/chat/completions", json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)
agent.chat = chat
rows = evaluate.evaluate(sys.argv[1])
for r in rows: print(json.dumps(r))
