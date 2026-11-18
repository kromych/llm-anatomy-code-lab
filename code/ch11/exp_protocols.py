# exp_protocols.py -- the comparison of native tool calls and the text
# protocol, repeated at temperature 0.7 with seeds 1 to 5.
# Usage: python3 exp_protocols.py LLAMA_BASE OLLAMA_BASE OUTDIR
import json, os, sys, urllib.request
import agent, evaluate, react

LLAMA, OLLAMA, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
TEMP = 0.7

def post(base, body):
    req = urllib.request.Request(base + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)

def native(think, seed):
    def chat(messages, base=agent.BASE, timeout=300):
        return post(base, {"model": agent.MODEL, "messages": messages,
                           "temperature": TEMP, "seed": seed,
                           "tools": [s for _, s in agent.TOOLS.values()],
                           "chat_template_kwargs":
                               {"enable_thinking": think}})
    agent.chat = chat
    return evaluate.evaluate(LLAMA)

def text(base, model, seed):
    def complete(messages, base, model_):
        return post(base, {"model": model, "messages": messages,
                           "temperature": TEMP, "seed": seed,
                           "stop": ["Observation:"],
                           "chat_template_kwargs":
                               {"enable_thinking": False}})
    react.complete = complete
    return evaluate.evaluate(base, run=lambda q, b, log=None:
                             react.run(q, b, model=model, log=log))

CONFIGS = {
    "native-off": lambda s: native(False, s),
    "native-on": lambda s: native(True, s),
    "text-qwen": lambda s: text(LLAMA, agent.MODEL, s),
    "text-gemma": lambda s: text(OLLAMA, "gemma3:1b", s),
}
os.makedirs(OUT, exist_ok=True)
for name, fn in CONFIGS.items():
    for seed in range(1, 6):
        rows = fn(seed)
        with open(f"{OUT}/{name}-{seed}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print(name, seed, sum(r["ok"] for r in rows),
              round(sum(r["seconds"] for r in rows), 1), flush=True)
