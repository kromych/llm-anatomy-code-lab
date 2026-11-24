# nostop.py -- the text protocol of react.py without the stop sequence.
# Usage: python3 nostop.py BASE_URL
import json, sys, urllib.request
import agent, evaluate, react

replies = []

def complete(messages, base, model):
    body = {"model": model, "messages": messages, "temperature": 0,
            "seed": 1,                          # no "stop" in this request
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(base + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        reply = json.load(r)
    replies.append(reply["choices"][0]["message"]["content"] or "")
    return reply

react.complete = complete
rows = evaluate.evaluate(sys.argv[1], run=lambda q, b, log=None:
                         react.run(q, b, log=log))
for r in rows:
    print(json.dumps(r))
invented = sum("Observation:" in text for text in replies)
both = sum("Action:" in t and "Answer:" in t for t in replies)
print(f"solved {sum(r['ok'] for r in rows)} of {len(rows)}; "
      f"{len(replies)} replies, {invented} with an Observation line "
      f"of the model's own, {both} with an Action and an Answer")
print("the first reply:")
print(replies[0])
