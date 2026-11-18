# agent_loop.py -- Algorithm R as a loop with one tool and a confirmation.
#   python3 agent_loop.py [base-url]
import json, subprocess, sys, urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080/v1"
URL = BASE + "/chat/completions"
HEADERS = {"Content-Type": "application/json"}
TOOLS = [{"type": "function", "function": {
    "name": "bash", "description": "Run a shell command",
    "parameters": {"type": "object",
                   "properties": {"command": {"type": "string"}},
                   "required": ["command"]}}}]

def chat(messages):                                   # steps R2-R9
    body = json.dumps({"messages": messages, "tools": TOOLS}).encode()
    req = urllib.request.Request(URL, body, HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["choices"][0]["message"]

messages = [{"role": "user", "content": input("> ")}]
while True:
    msg = chat(messages)
    messages.append(msg)
    if not msg.get("tool_calls"):                     # step R10
        print(msg["content"])
        break
    for call in msg["tool_calls"]:                    # step R11
        cmd = json.loads(call["function"]["arguments"])["command"]
        if input(f"run {cmd!r}? [y/N] ") == "y":
            p = subprocess.run(cmd, shell=True, capture_output=True,
                               text=True, timeout=60)
            out = (p.stdout + p.stderr)[-4000:]
        else:
            out = "the user declined to run this command"
        messages.append({"role": "tool",              # step R12
                         "tool_call_id": call["id"], "content": out})
