# cachetest.py -- send two requests that share a long system prompt to
# llama-server and print how much of each prompt came from the cache.
import json, urllib.request

URL = "http://127.0.0.1:8080/v1/chat/completions"
doc = " ".join(f"Item {i} costs {i * 7 % 100} euros." for i in range(800))
for question in ("Which item costs 42 euros?", "Which costs 13 euros?"):
    body = {"max_tokens": 32, "messages": [
        {"role": "system", "content": "Answer from this list: " + doc},
        {"role": "user", "content": question}]}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        t = json.load(resp)["timings"]
    print(f"from cache {t['cache_n']:5d}   computed {t['prompt_n']:5d}   "
          f"prefill {t['prompt_ms']:7.1f} ms")
