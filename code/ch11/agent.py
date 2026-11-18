# agent.py -- Algorithm N with the tools of tools.py; standard library only.
import json, os, sys, urllib.request
from tools import TOOLS

BASE = "http://127.0.0.1:8080/v1"
MODEL = os.environ.get("AGENT_MODEL", "default")     # Ollama needs a name
SYSTEM = ("You answer questions about the files in a workspace. Use the "
          "tools to look things up; do not guess. Answer briefly.")

def chat(messages, base=BASE, timeout=300):          # step N2
    body = {"model": MODEL, "messages": messages, "temperature": 0,
            "seed": 1, "tools": [schema for _, schema in TOOLS.values()],
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(base + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def call(name, arguments):                           # step N5
    if name not in TOOLS:
        return f"error: unknown tool {name!r}; known: {', '.join(TOOLS)}"
    try:
        args = json.loads(arguments or "{}")
        return str(TOOLS[name][0](**args))
    except Exception as e:             # bad JSON or arguments, or failure
        return f"error: {type(e).__name__}: {e}"

def clip(text, limit=3000):                          # step N6
    if len(text) <= limit:
        return text
    half = limit // 2
    return (text[:half] + f"\n[... {len(text) - limit} characters "
            "omitted ...]\n" + text[-half:])

def run(task, base=BASE, max_turns=12, log=None, messages=None):
    if messages is None:                             # a new conversation
        messages = [{"role": "system", "content": SYSTEM}]
    messages.append({"role": "user", "content": task})
    for turn in range(max_turns):                    # step N7
        reply = chat(messages, base)
        msg = reply["choices"][0]["message"]
        calls = msg.get("tool_calls") or []          # step N3
        messages.append({"role": "assistant", "content": msg.get("content"),
                         **({"tool_calls": calls} if calls else {})})
        if log:
            log(turn, reply)
        if not calls:                                # step N4
            return msg.get("content"), messages
        for c in calls:
            out = call(c["function"]["name"], c["function"]["arguments"])
            messages.append({"role": "tool", "tool_call_id": c["id"],
                             "content": clip(out)})
    return None, messages                            # out of turns

if __name__ == "__main__":
    base = sys.argv[2] if len(sys.argv) > 2 else BASE
    answer, messages = run(sys.argv[1], base)
    print(answer)
