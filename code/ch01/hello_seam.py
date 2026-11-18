# hello_seam.py -- one request to an OpenAI-compatible server.
#   python3 hello_seam.py [base-url [model]]
import json, sys, urllib.request

base  = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080/v1"
model = sys.argv[2] if len(sys.argv) > 2 else "default"
body  = {"model": model, "max_tokens": 128,
         "messages": [{"role": "user",
                       "content": "In one sentence: what is a KV cache?"}]}
req = urllib.request.Request(base + "/chat/completions",
                             data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    print(json.load(resp)["choices"][0]["message"]["content"])
