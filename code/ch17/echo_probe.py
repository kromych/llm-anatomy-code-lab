# echo_probe.py -- does a completions endpoint return the log-probabilities
# of the prompt? Sends one legacy completion request with echo and
# logprobs set and prints which tokens the reply has log-probabilities for.
# usage: python3 echo_probe.py [BASE] > results/echo-probe.txt
import json, sys, urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8086/v1"
PROMPT = "The capital of France is Paris"
body = {"model": "default", "prompt": PROMPT, "max_tokens": 1,
        "temperature": 0, "echo": True, "logprobs": 1}
req = urllib.request.Request(BASE + "/completions",
                             json.dumps(body).encode(),
                             {"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=120) as r:
    reply = json.load(r)

choice = reply["choices"][0]
lp = choice.get("logprobs") or {}
items = lp.get("content") or [                 # llama-server | OpenAI
    {"token": t, "logprob": p}
    for t, p in zip(lp.get("tokens", []), lp.get("token_logprobs", []))]
print("request:", json.dumps(body))
print("text:", json.dumps(choice.get("text")))
print("prompt echoed in text:", PROMPT in (choice.get("text") or ""))
print("prompt_tokens:", reply.get("usage", {}).get("prompt_tokens"))
print("tokens with a log-probability:", len(items))
for it in items:
    print(f"  {json.dumps(it['token'])} {it['logprob']:.4f}")
