# account.py -- the engine's own account of two requests: the timings in
# each reply, the counters of /metrics, and the state of the slots.
# Usage: python3 account.py ROOT_URL   (llama-server started with --metrics)
import json, sys, urllib.request

ROOT = sys.argv[1]                           # e.g. http://127.0.0.1:8080

def get(path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(ROOT + path, data,
                                 {"Content-Type": "application/json"})
    return urllib.request.urlopen(req).read().decode()

msgs = [{"role": "system", "content": "Answer briefly."},
        {"role": "user", "content": "Name three prime numbers."}]
for more in ("And three more.", None):
    reply = json.loads(get("/v1/chat/completions", {
        "messages": msgs, "max_tokens": 64,
        "chat_template_kwargs": {"enable_thinking": False}}))
    t = reply["timings"]
    print("reply: cached %d, prompt %d in %.0f ms, predicted %d in %.0f ms"
          % (t["cache_n"], t["prompt_n"], t["prompt_ms"],
             t["predicted_n"], t["predicted_ms"]))
    msgs += [reply["choices"][0]["message"],
             {"role": "user", "content": more}]
for line in get("/metrics").splitlines():
    if line.startswith("llamacpp:") and "spec_decode" not in line:
        print(line)
for s in json.loads(get("/slots")):
    state = "busy" if s["is_processing"] else "idle"
    print("slot %d: %s, %d tokens" % (s["id"], state,
                                      s.get("n_prompt_tokens", 0)))
